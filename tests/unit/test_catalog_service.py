import pytest
from aidev.services.catalog_service import list_resources
from aidev.domain.enums import ResourceType


def test_list_resources_returns_all():
    resources = list_resources()
    assert len(resources) > 0


def test_list_resources_have_required_attributes():
    resources = list_resources()
    for r in resources:
        assert r.slug
        assert r.name
        assert r.resource_type in ResourceType
        assert isinstance(r.description, str)
        assert isinstance(r.tags, list)


def test_list_resources_filter_by_skill_type():
    resources = list_resources(resource_type=ResourceType.SKILL)
    assert len(resources) > 0
    assert all(r.resource_type == ResourceType.SKILL for r in resources)


def test_list_resources_filter_by_rule_type():
    resources = list_resources(resource_type=ResourceType.RULE)
    assert len(resources) > 0
    assert all(r.resource_type == ResourceType.RULE for r in resources)


def test_list_resources_filter_by_spec_type():
    resources = list_resources(resource_type=ResourceType.SPEC)
    assert len(resources) > 0
    assert all(r.resource_type == ResourceType.SPEC for r in resources)


def test_list_resources_search_by_term():
    resources = list_resources(search="python")
    assert len(resources) > 0
    for r in resources:
        combined = (r.slug + r.name + r.description + " ".join(r.tags)).lower()
        assert "python" in combined


def test_list_resources_search_no_match():
    resources = list_resources(search="xyznonexistentterm123")
    assert resources == []


def test_list_resources_combined_filter():
    resources = list_resources(resource_type=ResourceType.SKILL, search="python")
    assert all(r.resource_type == ResourceType.SKILL for r in resources)
    assert len(resources) > 0
