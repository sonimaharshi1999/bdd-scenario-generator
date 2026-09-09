# Author: Maharshi Soni | License: MIT
"""Tests for the NLP Processor module."""

import pytest
from bdd_generator.nlp_processor import NLPProcessor, ParsedRequirement


@pytest.fixture
def nlp():
    return NLPProcessor()


class TestUserStoryParsing:
    """Tests for user-story format parsing."""

    def test_parse_standard_user_story(self, nlp):
        text = "As a user, I want to login with my email and password so that I can access my dashboard"
        parsed = nlp.parse(text)
        assert isinstance(parsed, ParsedRequirement)
        assert len(parsed.actors) >= 1
        assert parsed.actors[0].name == "user"
        assert len(parsed.actions) >= 1
        assert any("login" in a.verb.lower() for a in parsed.actions)

    def test_parse_user_story_extracts_benefit(self, nlp):
        text = "As a customer, I want to search products so that I can find items quickly"
        parsed = nlp.parse(text)
        assert parsed.context != ""
        assert "find" in parsed.context.lower() or "quickly" in parsed.context.lower()

    def test_parse_user_story_with_admin_role(self, nlp):
        text = "As an admin, I want to delete users so that I can manage the system"
        parsed = nlp.parse(text)
        assert any(a.name == "admin" for a in parsed.actors)
        assert any("delete" in a.verb.lower() for a in parsed.actions)

    def test_parse_user_story_multiple_actions(self, nlp):
        text = "As a user, I want to upload and download files so that I can manage my documents"
        parsed = nlp.parse(text)
        verbs = [a.verb.lower() for a in parsed.actions]
        assert "upload" in verbs or "download" in verbs


class TestFreeTextParsing:
    """Tests for free-text (non user-story) requirement parsing."""

    def test_parse_simple_requirement(self, nlp):
        text = "The user should be able to register with a valid email address."
        parsed = nlp.parse(text)
        assert len(parsed.actors) >= 1
        assert any("register" in a.verb.lower() for a in parsed.actions)

    def test_parse_requirement_with_assertions(self, nlp):
        text = "The system should display an error message when the user enters an invalid password."
        parsed = nlp.parse(text)
        assert len(parsed.assertions) >= 1

    def test_parse_requirement_with_conditions(self, nlp):
        text = "When the user is logged in, they should see their profile page."
        parsed = nlp.parse(text)
        assert len(parsed.conditions) >= 1

    def test_parse_default_actor_when_none_found(self, nlp):
        text = "The system must handle concurrent requests gracefully."
        parsed = nlp.parse(text)
        assert len(parsed.actors) >= 1

    def test_parse_negative_assertions(self, nlp):
        text = "The user should not be able to access the admin panel without proper authorization."
        parsed = nlp.parse(text)
        negative = [a for a in parsed.assertions if a.assertion_type == "negative"]
        assert len(negative) >= 1


class TestFeatureNameDerivation:
    """Tests for automatic feature name generation."""

    def test_feature_name_from_action(self, nlp):
        text = "As a user, I want to login so that I can access the app"
        parsed = nlp.parse(text)
        assert parsed.feature_name != ""
        assert len(parsed.feature_name) > 0

    def test_feature_name_fallback(self, nlp):
        text = "Handle the edge case properly"
        parsed = nlp.parse(text)
        assert parsed.feature_name != ""


class TestBatchParsing:
    """Tests for batch requirement parsing."""

    def test_batch_parse_multiple(self, nlp):
        reqs = [
            "As a user, I want to login so that I can access my account",
            "As a customer, I want to search products so that I can find items",
        ]
        results = nlp.parse_batch(reqs)
        assert len(results) == 2
        assert all(isinstance(r, ParsedRequirement) for r in results)

    def test_batch_parse_skips_empty(self, nlp):
        reqs = ["Valid requirement", "", "  ", "Another requirement"]
        results = nlp.parse_batch(reqs)
        assert len(results) == 2
