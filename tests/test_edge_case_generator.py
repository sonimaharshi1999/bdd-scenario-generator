# Author: Maharshi Soni | License: MIT
"""Tests for the Edge Case Generator module."""

import pytest
from bdd_generator.nlp_processor import NLPProcessor
from bdd_generator.scenario_generator import ScenarioGenerator, Feature
from bdd_generator.edge_case_generator import EdgeCaseGenerator


@pytest.fixture
def nlp():
    return NLPProcessor()


@pytest.fixture
def gen():
    return ScenarioGenerator()


@pytest.fixture
def edge_gen():
    return EdgeCaseGenerator()


class TestEdgeCaseGeneration:
    """Tests for domain-aware edge-case generation."""

    def test_login_generates_security_edge_cases(self, nlp, gen, edge_gen):
        text = "As a user, I want to login so that I can access my dashboard"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        original_count = len(feature.scenarios)
        feature = edge_gen.generate(parsed, feature)
        assert len(feature.scenarios) > original_count
        tags = [tag for s in feature.scenarios for tag in s.tags]
        assert "@security" in tags or "@edge_case" in tags

    def test_search_generates_search_edge_cases(self, nlp, gen, edge_gen):
        text = "As a user, I want to search for products so that I can find what I need"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        feature = edge_gen.generate(parsed, feature)
        names = [s.name.lower() for s in feature.scenarios]
        assert any("search" in n for n in names)

    def test_upload_generates_file_edge_cases(self, nlp, gen, edge_gen):
        text = "As an admin, I want to upload a CSV file so that I can import data"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        feature = edge_gen.generate(parsed, feature)
        names = [s.name.lower() for s in feature.scenarios]
        assert any("file" in n or "upload" in n for n in names)

    def test_payment_generates_payment_edge_cases(self, nlp, gen, edge_gen):
        text = "As a buyer, I want to pay with my credit card so that I can purchase items"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        feature = edge_gen.generate(parsed, feature)
        tags = [tag for s in feature.scenarios for tag in s.tags]
        assert "@payments" in tags or "@edge_case" in tags

    def test_concurrency_edge_case_always_added(self, nlp, gen, edge_gen):
        text = "As a user, I want to view my profile so that I can check my info"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        feature = edge_gen.generate(parsed, feature)
        names = [s.name for s in feature.scenarios]
        assert "Concurrent access handling" in names

    def test_no_duplicate_edge_cases(self, nlp, gen, edge_gen):
        text = "As a user, I want to login with my password so that I can sign in"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        feature = edge_gen.generate(parsed, feature)
        names = [s.name for s in feature.scenarios]
        assert len(names) == len(set(names)), "Duplicate scenario names found"
