"""Tests for lockfile determinism, schema-version migration, and timestamp rules."""

from __future__ import annotations

import json
from pathlib import Path

from aidriven.install._lockfile import read_lockfile, write_lockfile
from aidriven.install._models import InstallMode, Lockfile, LockfileEntry, Scope


def _make_entry(
    targets: tuple[str, ...] = ("claude",),
    computed_hash: str = "sha256:" + "a" * 64,
    scope: Scope = Scope.PROJECT,
    install_mode: InstallMode = InstallMode.SYMLINK,
) -> LockfileEntry:
    return LockfileEntry(
        source="aidriven-resources",
        source_commit_sha="a" * 40,
        computed_hash=computed_hash,
        targets=targets,
        scope=scope,
        install_mode=install_mode,
    )


# ── Determinism ───────────────────────────────────────────────────────


class TestLockfileDeterminism:
    """Tests for deterministic lockfile serialisation."""

    def test_same_skills_different_insertion_order_produce_identical_json(
        self, tmp_path: Path
    ) -> None:
        """
        Given the same skills inserted in different orders into two Lockfile objects,
        When both are written and read back,
        Then the JSON content is byte-for-byte identical.
        """
        # ── Given ──
        entry_a = _make_entry(targets=("claude",))
        entry_b = _make_entry(targets=("copilot",), computed_hash="sha256:" + "b" * 64)

        lf1 = Lockfile(skills={"alpha": entry_a, "beta": entry_b})
        lf2 = Lockfile(skills={"beta": entry_b, "alpha": entry_a})

        path1 = tmp_path / "lock1.json"
        path2 = tmp_path / "lock2.json"

        # ── When ──
        write_lockfile(lf1, path1)
        write_lockfile(lf2, path2)

        # ── Then ──
        assert path1.read_text(encoding="utf-8") == path2.read_text(encoding="utf-8")

    def test_project_lockfile_contains_no_timestamp_fields(self, tmp_path: Path) -> None:
        """
        Given a project-scope lockfile with a skill entry,
        When written to disk,
        Then the JSON contains no 'lastInstalledAt' or timestamp-like keys.
        """
        # ── Given ──
        lf = Lockfile(skills={"my-skill": _make_entry()})
        path = tmp_path / "aidriven-lock.json"

        # ── When ──
        write_lockfile(lf, path, include_timestamps=False)
        raw = json.loads(path.read_text(encoding="utf-8"))

        # ── Then ──
        for skill_data in raw.get("skills", {}).values():
            assert "lastInstalledAt" not in skill_data
            # No other timestamp-like keys
            for key in skill_data:
                assert "timestamp" not in key.lower()
                assert "date" not in key.lower()

    def test_targets_are_sorted_alphabetically(self, tmp_path: Path) -> None:
        """
        Given a skill with targets inserted as ('copilot', 'claude'),
        When written and read back,
        Then targets in JSON are ['claude', 'copilot'] (sorted).
        """
        # ── Given ──
        entry = _make_entry(targets=("copilot", "claude"))
        lf = Lockfile(skills={"s": entry})
        path = tmp_path / "lock.json"

        # ── When ──
        write_lockfile(lf, path)
        raw = json.loads(path.read_text(encoding="utf-8"))

        # ── Then ──
        assert raw["skills"]["s"]["targets"] == ["claude", "copilot"]


# ── Schema version migration guard ───────────────────────────────────


class TestSchemaVersionMigration:
    """Tests for schema-version mismatch handling."""

    def test_version_mismatch_triggers_migration_not_silent_loss(self, tmp_path: Path) -> None:
        """
        Given a lockfile with schema_version != 1 but parseable entries,
        When read_lockfile is called,
        Then entries are preserved (migrated), not silently discarded.
        """
        # ── Given ──
        legacy_lock = {
            "version": 99,
            "skills": {
                "my-skill": {
                    "source": "aidriven-resources",
                    "sourceCommitSha": "a" * 40,
                    "computedHash": "sha256:" + "c" * 64,
                    "targets": ["claude"],
                    "scope": "project",
                    "installMode": "symlink",
                }
            },
        }
        path = tmp_path / "aidriven-lock.json"
        path.write_text(json.dumps(legacy_lock), encoding="utf-8")

        # ── When ──
        lockfile = read_lockfile(path)

        # ── Then ──
        assert "my-skill" in lockfile.skills
        assert lockfile.version == 1  # migrated to current version

    def test_missing_lockfile_returns_empty_lockfile(self, tmp_path: Path) -> None:
        """
        Given a path with no lockfile,
        When read_lockfile is called,
        Then an empty Lockfile is returned.
        """
        # ── Given ──
        path = tmp_path / "no-lock.json"

        # ── When ──
        result = read_lockfile(path)

        # ── Then ──
        assert result.version == 1
        assert result.skills == {}


# ── Round-trip ────────────────────────────────────────────────────────


class TestLockfileRoundTrip:
    """Tests for write → read round-trip fidelity."""

    def test_round_trip_preserves_all_fields(self, tmp_path: Path) -> None:
        """
        Given a lockfile with a fully-specified entry,
        When written and read back,
        Then all field values are preserved exactly.
        """
        # ── Given ──
        entry = LockfileEntry(
            source="aidriven-resources",
            source_commit_sha="f" * 40,
            computed_hash="sha256:" + "d" * 64,
            targets=("claude", "copilot"),
            scope=Scope.PROJECT,
            install_mode=InstallMode.COPY,
        )
        lf = Lockfile(skills={"my-skill": entry})
        path = tmp_path / "lock.json"

        # ── When ──
        write_lockfile(lf, path)
        result = read_lockfile(path)

        # ── Then ──
        assert "my-skill" in result.skills
        back = result.skills["my-skill"]
        assert back.source == "aidriven-resources"
        assert back.source_commit_sha == "f" * 40
        assert back.computed_hash == "sha256:" + "d" * 64
        assert set(back.targets) == {"claude", "copilot"}
        assert back.scope == Scope.PROJECT
        assert back.install_mode == InstallMode.COPY
