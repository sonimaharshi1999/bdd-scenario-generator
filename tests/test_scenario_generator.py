# Author: Maharshi Soni | License: MIT
"""Tests for the Scenario Generator module."""

import pytest
from bdd_generator.nlp_processor import (
    NLPProcessor,
    ParsedRequirement,
    Actor,
    Action,
    Condition,
    Assertion,
)
from bdd_generator.scenario_generator import ScenarioGenerator, Feature, Scenario, Step


@pytest.fixture
def nlp():
    return NLPProcessor()


@pytest.fixture
def gen():
    return ScenarioGenerator()


class TestFeatureGeneration:
    """Tests for Feature generation from parsed requirements."""

    def test_generate_feature_from_user_story(self, nlp, gen):
        text = "As a user, I want to login with my email so that I can access my dashboard"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        assert isinstance(feature, Feature)
        assert feature.name != ""
        assert len(feature.scenarios) >= 1

    def test_feature_has_happy_path(self, nlp, gen):
        text = "As a user, I want to register so that I can use the application"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        happy = [s for s in feature.scenarios if "@happy_path" in s.tags]
        assert len(happy) >= 1

    def test_feature_has_negative_scenario(self, nlp, gen):
        text = "As a user, I want to login so that I can access the system"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        negative = [s for s in feature.scenarios if "@negative" in s.tags]
        assert len(negative) >= 1

    def test_feature_has_tags(self, nlp, gen):
        text = "As a user, I want to login so that I can access the system"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        assert len(feature.tags) >= 1


class TestScenarioSteps:
    """Tests for Given/When/Then step generation."""

    def test_happy_path_has_given_when_then(self, nlp, gen):
        text = "As a user, I want to search products so that I can find what I need"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        happy = [s for s in feature.scenarios if "@happy_path" in s.tags][0]

        keywords = [step.keyword for step in happy.steps]
        assert "Given" in keywords
        assert "When" in keywords
        assert "Then" in keywords

    def test_steps_have_non_empty_text(self, nlp, gen):
        text = "As a user, I want to login so that I can access the dashboard"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        for scenario in feature.scenarios:
            for step in scenario.steps:
                assert step.text.strip() != ""

    def test_negative_scenario_has_error_handling(self, nlp, gen):
        text = "As a user, I want to submit a form so that I can register"
        parsed = nlp.parse(text)
        feature = gen.generate(parsed)
        negative = [s for s in feature.scenarios if "@negative" in s.tags]
        assert len(negative) >= 1
        # Negative scenario should mention error
        neg_text = " ".join(step.text for step in negative[0].steps)
        assert "error" in neg_text.lower() or "invalid" in neg_text.lower()


class TestManualParsedRequirement:
    """Tests using manually constructed ParsedRequirement objects."""

    def test_generate_from_manual_parsed(self, gen):
        parsed = ParsedRequirement(
            original_text="User logs in with credentials",
            actors=[Actor(name="user", role="user")],
            actions=[Action(verb="login", object="credentials")],
            conditions=[Condition(text="the user is on the login page")],
            assertions=[
                Assertion(text="should see the dashboard", assertion_type="positive")
            ],
            feature_name="User Login",
        )
        feature = gen.generate(parsed)
        assert feature.name == "User Login"
        assert len(feature.scenarios) >= 1

    def test_generate_with_no_conditions(self, gen):
        parsed = ParsedRequirement(
            original_text="Delete a record",
            actors=[Actor(name="admin", role="admin")],
            actions=[Action(verb="delete", object="record")],
            feature_name="Delete Record",
        )
        feature = gen.generate(parsed)
        happy = [s for s in feature.scenarios if "@happy_path" in s.tags][0]
        # Should still have a Given step (fallback)
        assert any(s.keyword == "Given" for s in happy.steps)


class TestBatchGeneration:
    """Tests for batch feature generation."""

    def test_batch_generation(self, nlp, gen):
        texts = [
            "As a user, I want to login so that I can access the app",
            "As a customer, I want to search so that I can find items",
        ]
        parsed_list = nlp.parse_batch(texts)
        features = gen.generate_batch(parsed_list)
        assert len(features) == 2
        assert all(isinstance(f, Feature) for f in features)
