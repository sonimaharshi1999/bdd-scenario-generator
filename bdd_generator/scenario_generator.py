# Author: Maharshi Soni | License: MIT
"""
Scenario Generator module - Converts parsed requirements into structured BDD scenarios
with Given/When/Then steps.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .nlp_processor import (
    Action,
    Actor,
    Assertion,
    Condition,
    ParsedRequirement,
)


@dataclass
class Step:
    """A single Gherkin step (Given / When / Then / And / But)."""
    keyword: str  # Given | When | Then | And | But
    text: str


@dataclass
class Scenario:
    """A complete BDD scenario."""
    name: str
    steps: List[Step] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    description: str = ""
    examples: Optional[List[dict]] = None  # for Scenario Outline


@dataclass
class Feature:
    """A complete Gherkin feature."""
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    background: Optional[List[Step]] = None
    scenarios: List[Scenario] = field(default_factory=list)


class ScenarioGenerator:
    """Generates BDD scenarios from ParsedRequirement objects."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, parsed: ParsedRequirement) -> Feature:
        """Generate a complete Feature with scenarios from a parsed requirement."""
        feature = Feature(
            name=parsed.feature_name or "Unnamed Feature",
            description=parsed.context or parsed.original_text,
            tags=self._generate_feature_tags(parsed),
        )

        # Background steps from shared preconditions
        feature.background = self._build_background(parsed)

        # Happy-path scenario
        happy = self._build_happy_path(parsed)
        feature.scenarios.append(happy)

        # Negative / error scenarios from negative assertions
        for neg_scenario in self._build_negative_scenarios(parsed):
            feature.scenarios.append(neg_scenario)

        # Boundary / validation scenarios
        for boundary_scenario in self._build_boundary_scenarios(parsed):
            feature.scenarios.append(boundary_scenario)

        return feature

    def generate_batch(self, parsed_list: List[ParsedRequirement]) -> List[Feature]:
        """Generate features for a batch of parsed requirements."""
        return [self.generate(p) for p in parsed_list]

    # ------------------------------------------------------------------
    # Background
    # ------------------------------------------------------------------

    def _build_background(self, parsed: ParsedRequirement) -> List[Step]:
        steps: List[Step] = []
        actor = parsed.actors[0] if parsed.actors else Actor(name="user", role="user")

        # Common setup conditions
        preconditions = [
            c for c in parsed.conditions if c.condition_type == "precondition"
        ]
        if preconditions:
            steps.append(
                Step(keyword="Given", text=f"the {actor.name} is on the application")
            )
            for i, cond in enumerate(preconditions):
                kw = "And" if i > 0 or steps else "Given"
                steps.append(Step(keyword=kw, text=self._format_condition(cond.text)))

        return steps if steps else []

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def _build_happy_path(self, parsed: ParsedRequirement) -> Scenario:
        actor = parsed.actors[0] if parsed.actors else Actor(name="user", role="user")
        scenario_name = self._make_scenario_name(parsed, "happy")

        steps: List[Step] = []

        # Given
        if not parsed.conditions:
            steps.append(
                Step(
                    keyword="Given",
                    text=f"the {actor.name} is on the relevant page",
                )
            )
        else:
            first_cond = parsed.conditions[0]
            steps.append(
                Step(keyword="Given", text=self._format_condition(first_cond.text))
            )
            for cond in parsed.conditions[1:]:
                steps.append(
                    Step(keyword="And", text=self._format_condition(cond.text))
                )

        # When
        for i, action in enumerate(parsed.actions):
            kw = "When" if i == 0 else "And"
            steps.append(Step(keyword=kw, text=self._format_action(actor, action)))

        # Then
        positive_assertions = [
            a for a in parsed.assertions if a.assertion_type == "positive"
        ]
        if positive_assertions:
            for i, assertion in enumerate(positive_assertions):
                kw = "Then" if i == 0 else "And"
                steps.append(
                    Step(keyword=kw, text=self._format_assertion(assertion))
                )
        else:
            steps.append(
                Step(keyword="Then", text="the operation should be successful")
            )

        return Scenario(
            name=scenario_name,
            steps=steps,
            tags=["@happy_path", "@smoke"],
        )

    # ------------------------------------------------------------------
    # Negative / error scenarios
    # ------------------------------------------------------------------

    def _build_negative_scenarios(self, parsed: ParsedRequirement) -> List[Scenario]:
        scenarios: List[Scenario] = []
        actor = parsed.actors[0] if parsed.actors else Actor(name="user", role="user")

        negative_assertions = [
            a for a in parsed.assertions if a.assertion_type == "negative"
        ]

        for idx, assertion in enumerate(negative_assertions):
            name = self._make_scenario_name(parsed, f"negative_{idx + 1}")
            steps = [
                Step(
                    keyword="Given",
                    text=f"the {actor.name} is on the relevant page",
                ),
                Step(
                    keyword="When",
                    text=f"the {actor.name} attempts an invalid operation",
                ),
                Step(keyword="Then", text=self._format_assertion(assertion)),
            ]
            scenarios.append(
                Scenario(name=name, steps=steps, tags=["@negative"])
            )

        # Auto-generate a generic negative scenario if none exist
        if not negative_assertions and parsed.actions:
            primary_action = parsed.actions[0]
            name = f"Unsuccessful {primary_action.verb} with invalid data"
            steps = [
                Step(
                    keyword="Given",
                    text=f"the {actor.name} is on the relevant page",
                ),
                Step(
                    keyword="When",
                    text=f"the {actor.name} tries to {primary_action.verb} with invalid {primary_action.object}",
                ),
                Step(
                    keyword="Then",
                    text="the system should display an appropriate error message",
                ),
                Step(
                    keyword="And",
                    text=f"the {actor.name} should remain on the current page",
                ),
            ]
            scenarios.append(
                Scenario(name=name, steps=steps, tags=["@negative", "@error_handling"])
            )

        return scenarios

    # ------------------------------------------------------------------
    # Boundary / validation
    # ------------------------------------------------------------------

    def _build_boundary_scenarios(self, parsed: ParsedRequirement) -> List[Scenario]:
        scenarios: List[Scenario] = []
        actor = parsed.actors[0] if parsed.actors else Actor(name="user", role="user")

        for action in parsed.actions:
            obj_lower = action.object.lower()

            # Input-field related actions get validation scenarios
            if any(
                kw in action.verb.lower()
                for kw in ("enter", "type", "input", "fill", "submit", "create", "add", "register", "sign up", "login", "log in")
            ) or any(
                kw in obj_lower
                for kw in ("form", "field", "input", "password", "email", "name", "username", "data")
            ):
                # Empty input
                scenarios.append(
                    Scenario(
                        name=f"Validate empty {action.object}",
                        steps=[
                            Step(
                                keyword="Given",
                                text=f"the {actor.name} is on the relevant page",
                            ),
                            Step(
                                keyword="When",
                                text=f"the {actor.name} leaves the {action.object} field empty",
                            ),
                            Step(
                                keyword="And",
                                text=f"the {actor.name} submits the form",
                            ),
                            Step(
                                keyword="Then",
                                text="the system should display a validation error for the required field",
                            ),
                        ],
                        tags=["@validation", "@boundary"],
                    )
                )

                # Maximum-length input
                scenarios.append(
                    Scenario(
                        name=f"Validate maximum length for {action.object}",
                        steps=[
                            Step(
                                keyword="Given",
                                text=f"the {actor.name} is on the relevant page",
                            ),
                            Step(
                                keyword="When",
                                text=f"the {actor.name} enters extremely long text in the {action.object} field",
                            ),
                            Step(
                                keyword="And",
                                text=f"the {actor.name} submits the form",
                            ),
                            Step(
                                keyword="Then",
                                text="the system should handle the input gracefully",
                            ),
                        ],
                        tags=["@validation", "@boundary"],
                    )
                )

        return scenarios

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_action(actor: Actor, action: Action) -> str:
        text = f"the {actor.name} {action.verb}s {action.object}"
        # Fix double-s at end (e.g., "loginss" -> "logins")
        text = re.sub(r"ss\b", "s", text)
        return text.strip()

    @staticmethod
    def _format_condition(text: str) -> str:
        text = text.strip()
        # Normalise to start lowercase after keyword
        if text and text[0].isupper():
            text = text[0].lower() + text[1:]
        return text

    @staticmethod
    def _format_assertion(assertion: Assertion) -> str:
        text = assertion.text.strip()
        # Ensure it contains "should" for Gherkin readability
        if "should" not in text.lower():
            text = f"the system should {text}"
        return text

    def _make_scenario_name(self, parsed: ParsedRequirement, variant: str) -> str:
        if parsed.actions:
            primary = parsed.actions[0]
            base = f"{primary.verb.title()} {primary.object}"
        else:
            words = parsed.original_text.split()[:6]
            base = " ".join(words)

        if variant == "happy":
            return f"Successfully {base.lower()}"
        elif variant.startswith("negative"):
            return f"Unsuccessfully {base.lower()}"
        return f"{base} - {variant}"

    @staticmethod
    def _generate_feature_tags(parsed: ParsedRequirement) -> List[str]:
        tags: List[str] = []
        if parsed.actors:
            tags.append(f"@{parsed.actors[0].role or parsed.actors[0].name}")
        # Infer domain tags from keywords
        text_lower = parsed.original_text.lower()
        domain_map = {
            "login": "@authentication",
            "register": "@registration",
            "password": "@authentication",
            "payment": "@payments",
            "checkout": "@checkout",
            "cart": "@shopping_cart",
            "search": "@search",
            "profile": "@profile",
            "admin": "@admin",
            "report": "@reporting",
            "upload": "@file_management",
            "download": "@file_management",
            "email": "@notifications",
            "notification": "@notifications",
        }
        for keyword, tag in domain_map.items():
            if keyword in text_lower and tag not in tags:
                tags.append(tag)
        return tags
