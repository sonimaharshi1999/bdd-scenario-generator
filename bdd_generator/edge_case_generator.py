# Author: Maharshi Soni | License: MIT
"""
Edge Case Generator module - Automatically generates edge-case and corner-case
BDD scenarios based on the actions and assertions found in a parsed requirement.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from .nlp_processor import ParsedRequirement, Actor
from .scenario_generator import Feature, Scenario, Step


@dataclass
class EdgeCaseRule:
    """A rule that maps a keyword/pattern to a set of edge-case scenarios."""
    keywords: List[str]
    scenarios_fn_name: str  # method name on EdgeCaseGenerator


# ---------------------------------------------------------------------------
# Pre-built edge-case templates keyed by domain
# ---------------------------------------------------------------------------

AUTHENTICATION_EDGE_CASES = [
    {
        "name": "Login with SQL injection attempt",
        "tags": ["@security", "@edge_case"],
        "steps": [
            ("Given", "the {actor} is on the login page"),
            ("When", "the {actor} enters \"' OR 1=1 --\" as the username"),
            ("And", "the {actor} enters any value as the password"),
            ("And", "the {actor} clicks the login button"),
            ("Then", "the system should reject the input"),
            ("And", "the system should not expose any database errors"),
        ],
    },
    {
        "name": "Login with XSS attempt",
        "tags": ["@security", "@edge_case"],
        "steps": [
            ("Given", "the {actor} is on the login page"),
            ("When", "the {actor} enters \"<script>alert('xss')</script>\" as the username"),
            ("And", "the {actor} clicks the login button"),
            ("Then", "the system should sanitize the input"),
            ("And", "no script should be executed"),
        ],
    },
    {
        "name": "Login with account lockout after multiple failures",
        "tags": ["@security", "@edge_case"],
        "steps": [
            ("Given", "the {actor} is on the login page"),
            ("When", "the {actor} enters invalid credentials 5 times consecutively"),
            ("Then", "the account should be temporarily locked"),
            ("And", "the system should display an account lockout message"),
        ],
    },
    {
        "name": "Session timeout handling",
        "tags": ["@security", "@edge_case"],
        "steps": [
            ("Given", "the {actor} has been inactive for an extended period"),
            ("When", "the {actor} tries to perform an action"),
            ("Then", "the system should redirect to the login page"),
            ("And", "the system should display a session expired message"),
        ],
    },
]

FORM_INPUT_EDGE_CASES = [
    {
        "name": "Submit form with special characters in input",
        "tags": ["@edge_case", "@validation"],
        "steps": [
            ("Given", "the {actor} is on the form page"),
            ("When", "the {actor} enters special characters (!@#$%^&*) in the input fields"),
            ("And", "the {actor} submits the form"),
            ("Then", "the system should handle special characters gracefully"),
        ],
    },
    {
        "name": "Submit form with unicode characters",
        "tags": ["@edge_case", "@validation"],
        "steps": [
            ("Given", "the {actor} is on the form page"),
            ("When", "the {actor} enters unicode characters in the input fields"),
            ("And", "the {actor} submits the form"),
            ("Then", "the system should handle unicode input correctly"),
        ],
    },
    {
        "name": "Submit form with leading and trailing whitespace",
        "tags": ["@edge_case", "@validation"],
        "steps": [
            ("Given", "the {actor} is on the form page"),
            ("When", "the {actor} enters values with leading and trailing spaces"),
            ("And", "the {actor} submits the form"),
            ("Then", "the system should trim whitespace appropriately"),
        ],
    },
    {
        "name": "Double-click submit button",
        "tags": ["@edge_case", "@ui"],
        "steps": [
            ("Given", "the {actor} has filled out the form"),
            ("When", "the {actor} double-clicks the submit button rapidly"),
            ("Then", "the system should prevent duplicate submissions"),
            ("And", "only one record should be created"),
        ],
    },
]

SEARCH_EDGE_CASES = [
    {
        "name": "Search with empty query",
        "tags": ["@edge_case", "@search"],
        "steps": [
            ("Given", "the {actor} is on the search page"),
            ("When", "the {actor} submits an empty search query"),
            ("Then", "the system should handle the empty query gracefully"),
        ],
    },
    {
        "name": "Search with very long query string",
        "tags": ["@edge_case", "@search"],
        "steps": [
            ("Given", "the {actor} is on the search page"),
            ("When", "the {actor} enters a search query exceeding 1000 characters"),
            ("Then", "the system should handle the long query without errors"),
        ],
    },
    {
        "name": "Search with no matching results",
        "tags": ["@edge_case", "@search"],
        "steps": [
            ("Given", "the {actor} is on the search page"),
            ("When", "the {actor} searches for a term with no matching results"),
            ("Then", "the system should display a no results found message"),
            ("And", "the system should suggest alternative search terms if possible"),
        ],
    },
]

FILE_UPLOAD_EDGE_CASES = [
    {
        "name": "Upload file exceeding maximum size",
        "tags": ["@edge_case", "@file_management"],
        "steps": [
            ("Given", "the {actor} is on the upload page"),
            ("When", "the {actor} selects a file larger than the maximum allowed size"),
            ("And", "the {actor} clicks the upload button"),
            ("Then", "the system should display a file size exceeded error"),
            ("And", "the file should not be uploaded"),
        ],
    },
    {
        "name": "Upload unsupported file format",
        "tags": ["@edge_case", "@file_management"],
        "steps": [
            ("Given", "the {actor} is on the upload page"),
            ("When", "the {actor} selects a file with an unsupported format"),
            ("And", "the {actor} clicks the upload button"),
            ("Then", "the system should display an unsupported format error"),
        ],
    },
    {
        "name": "Upload file with zero bytes",
        "tags": ["@edge_case", "@file_management"],
        "steps": [
            ("Given", "the {actor} is on the upload page"),
            ("When", "the {actor} selects an empty file with zero bytes"),
            ("And", "the {actor} clicks the upload button"),
            ("Then", "the system should reject the empty file"),
        ],
    },
]

PAYMENT_EDGE_CASES = [
    {
        "name": "Payment with expired card",
        "tags": ["@edge_case", "@payments"],
        "steps": [
            ("Given", "the {actor} is on the payment page"),
            ("When", "the {actor} enters an expired credit card"),
            ("And", "the {actor} submits the payment"),
            ("Then", "the system should display a card expired error"),
            ("And", "the payment should not be processed"),
        ],
    },
    {
        "name": "Payment with insufficient funds",
        "tags": ["@edge_case", "@payments"],
        "steps": [
            ("Given", "the {actor} is on the payment page"),
            ("When", "the {actor} submits payment with insufficient funds"),
            ("Then", "the system should display an insufficient funds error"),
            ("And", "the order should remain in pending state"),
        ],
    },
    {
        "name": "Payment network timeout",
        "tags": ["@edge_case", "@payments", "@timeout"],
        "steps": [
            ("Given", "the {actor} is on the payment page"),
            ("When", "the {actor} submits the payment"),
            ("And", "the payment gateway times out"),
            ("Then", "the system should display a timeout message"),
            ("And", "the system should not charge the {actor} without confirmation"),
        ],
    },
]

NAVIGATION_EDGE_CASES = [
    {
        "name": "Browser back button after form submission",
        "tags": ["@edge_case", "@navigation"],
        "steps": [
            ("Given", "the {actor} has successfully submitted a form"),
            ("When", "the {actor} presses the browser back button"),
            ("Then", "the system should handle the navigation gracefully"),
            ("And", "the form should not be resubmitted"),
        ],
    },
    {
        "name": "Direct URL access without authentication",
        "tags": ["@edge_case", "@security"],
        "steps": [
            ("Given", "the {actor} is not logged in"),
            ("When", "the {actor} tries to access a protected page via direct URL"),
            ("Then", "the system should redirect to the login page"),
        ],
    },
]

# Mapping from domain keywords to edge-case templates
DOMAIN_EDGE_CASES: Dict[str, list] = {
    "login": AUTHENTICATION_EDGE_CASES,
    "log in": AUTHENTICATION_EDGE_CASES,
    "sign in": AUTHENTICATION_EDGE_CASES,
    "authenticate": AUTHENTICATION_EDGE_CASES,
    "password": AUTHENTICATION_EDGE_CASES,
    "register": FORM_INPUT_EDGE_CASES,
    "sign up": FORM_INPUT_EDGE_CASES,
    "form": FORM_INPUT_EDGE_CASES,
    "input": FORM_INPUT_EDGE_CASES,
    "submit": FORM_INPUT_EDGE_CASES,
    "enter": FORM_INPUT_EDGE_CASES,
    "search": SEARCH_EDGE_CASES,
    "filter": SEARCH_EDGE_CASES,
    "find": SEARCH_EDGE_CASES,
    "upload": FILE_UPLOAD_EDGE_CASES,
    "download": FILE_UPLOAD_EDGE_CASES,
    "file": FILE_UPLOAD_EDGE_CASES,
    "attachment": FILE_UPLOAD_EDGE_CASES,
    "pay": PAYMENT_EDGE_CASES,
    "payment": PAYMENT_EDGE_CASES,
    "checkout": PAYMENT_EDGE_CASES,
    "purchase": PAYMENT_EDGE_CASES,
    "buy": PAYMENT_EDGE_CASES,
    "cart": PAYMENT_EDGE_CASES,
    "navigate": NAVIGATION_EDGE_CASES,
    "redirect": NAVIGATION_EDGE_CASES,
    "page": NAVIGATION_EDGE_CASES,
}


class EdgeCaseGenerator:
    """Generates edge-case BDD scenarios based on parsed requirements."""

    def generate(self, parsed: ParsedRequirement, feature: Feature) -> Feature:
        """Add edge-case scenarios to an existing Feature."""
        actor = parsed.actors[0] if parsed.actors else Actor(name="user", role="user")
        text_lower = parsed.original_text.lower()

        added_names: set = {s.name for s in feature.scenarios}

        # Collect matching edge-case templates
        matched_templates: List[dict] = []
        seen_sets: set = set()

        for keyword, templates in DOMAIN_EDGE_CASES.items():
            if keyword in text_lower:
                tpl_id = id(templates)
                if tpl_id not in seen_sets:
                    seen_sets.add(tpl_id)
                    matched_templates.extend(templates)

        # Also check action verbs
        for action in parsed.actions:
            verb_lower = action.verb.lower()
            if verb_lower in DOMAIN_EDGE_CASES:
                tpl_id = id(DOMAIN_EDGE_CASES[verb_lower])
                if tpl_id not in seen_sets:
                    seen_sets.add(tpl_id)
                    matched_templates.extend(DOMAIN_EDGE_CASES[verb_lower])

        # Convert templates to Scenario objects
        for template in matched_templates:
            name = template["name"]
            if name in added_names:
                continue
            added_names.add(name)

            steps = [
                Step(
                    keyword=kw,
                    text=txt.format(actor=actor.name),
                )
                for kw, txt in template["steps"]
            ]
            scenario = Scenario(
                name=name,
                steps=steps,
                tags=template.get("tags", ["@edge_case"]),
            )
            feature.scenarios.append(scenario)

        # Always add concurrency / timeout generic edge case
        concurrency_name = "Concurrent access handling"
        if concurrency_name not in added_names:
            feature.scenarios.append(
                Scenario(
                    name=concurrency_name,
                    steps=[
                        Step(keyword="Given", text=f"multiple {actor.name}s are accessing the same resource simultaneously"),
                        Step(keyword="When", text="they perform conflicting operations"),
                        Step(keyword="Then", text="the system should handle concurrent access gracefully"),
                        Step(keyword="And", text="data integrity should be maintained"),
                    ],
                    tags=["@edge_case", "@concurrency"],
                )
            )

        return feature
