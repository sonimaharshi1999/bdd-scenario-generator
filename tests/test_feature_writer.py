# Author: Maharshi Soni | License: MIT
"""Tests for the Feature Writer module."""

import os
import tempfile
import pytest

from bdd_generator.nlp_processor import NLPProcessor
from bdd_generator.scenario_generator import ScenarioGenerator, Feature, Scenario, Step
from bdd_generator.feature_writer import FeatureWriter


@pytest.fixture
def nlp():
    return NLPProcessor()


@pytest.fixture
def gen():
    return ScenarioGenerator()


@pytest.fixture
def writer():
    return FeatureWriter()


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestFeatureRendering:
    """Tests for Gherkin feature rendering."""

    def test_render_contains_feature_keyword(self, nlp, gen, writer):
        text = "As a user, I want to login so that I can access the system"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        content = writer.render(feature)
        assert "Feature:" in content

    def test_render_contains_scenario_keyword(self, nlp, gen, writer):
        text = "As a user, I want to login so that I can access the system"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        content = writer.render(feature)
        assert "Scenario:" in content

    def test_render_contains_given_when_then(self, nlp, gen, writer):
        text = "As a user, I want to login so that I can access the system"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        content = writer.render(feature)
        assert "Given " in content
        assert "When " in content
        assert "Then " in content

    def test_render_contains_tags(self, nlp, gen, writer):
        text = "As a user, I want to login so that I can access the system"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        content = writer.render(feature)
        assert "@" in content

    def test_render_manual_feature(self, writer):
        feature = Feature(
            name="Sample Feature",
            description="A test feature",
            tags=["@test"],
            scenarios=[
                Scenario(
                    name="Sample Scenario",
                    steps=[
                        Step(keyword="Given", text="a precondition"),
                        Step(keyword="When", text="an action is performed"),
                        Step(keyword="Then", text="an outcome is observed"),
                    ],
                    tags=["@smoke"],
                )
            ],
        )
        content = writer.render(feature)
        assert "Feature: Sample Feature" in content
        assert "Scenario: Sample Scenario" in content
        assert "Given a precondition" in content
        assert "When an action is performed" in content
        assert "Then an outcome is observed" in content


class TestFileWriting:
    """Tests for writing .feature files to disk."""

    def test_write_creates_file(self, nlp, gen, writer, tmp_dir):
        text = "As a user, I want to login so that I can access the system"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        filepath = writer.write(feature, tmp_dir)
        assert os.path.exists(filepath)
        assert filepath.endswith(".feature")

    def test_written_file_has_content(self, nlp, gen, writer, tmp_dir):
        text = "As a user, I want to search products so that I can find items"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        filepath = writer.write(feature, tmp_dir)
        with open(filepath, "r", encoding="utf-8") as fh:
            content = fh.read()
        assert len(content) > 0
        assert "Feature:" in content

    def test_write_batch(self, nlp, gen, writer, tmp_dir):
        texts = [
            "As a user, I want to login so that I can access the app",
            "As a user, I want to search so that I can find items",
        ]
        parsed_list = nlp.parse_batch(texts)
        features = gen.generate_batch(parsed_list)
        paths = writer.write_batch(features, tmp_dir)
        assert len(paths) == 2
        assert all(os.path.exists(p) for p in paths)

    def test_safe_filename(self, writer):
        assert writer._safe_filename("User Login") == "user_login"
        assert writer._safe_filename("Add to Cart!") == "add_to_cart"
        assert writer._safe_filename("") == "unnamed_feature"
        assert writer._safe_filename("  spaces  ") == "spaces"
