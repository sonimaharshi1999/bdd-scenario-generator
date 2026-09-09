# Author: Maharshi Soni | License: MIT
"""
NLP Processor module - Parses plain English requirements and extracts structured components
using NLTK for tokenization, POS tagging, and entity extraction.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk


def ensure_nltk_data():
    """Download required NLTK data packages if not already present."""
    packages = [
        "punkt",
        "punkt_tab",
        "averaged_perceptron_tagger",
        "averaged_perceptron_tagger_eng",
        "maxent_ne_chunker",
        "maxent_ne_chunker_tab",
        "words",
    ]
    for pkg in packages:
        try:
            nltk.data.find(f"tokenizers/{pkg}" if "punkt" in pkg else pkg)
        except LookupError:
            nltk.download(pkg, quiet=True)


ensure_nltk_data()


@dataclass
class Actor:
    """Represents a user/actor in the requirement."""
    name: str
    role: Optional[str] = None


@dataclass
class Action:
    """Represents an action extracted from a requirement."""
    verb: str
    object: str
    modifiers: List[str] = field(default_factory=list)


@dataclass
class Condition:
    """Represents a precondition or postcondition."""
    text: str
    condition_type: str = "precondition"  # precondition | postcondition


@dataclass
class Assertion:
    """Represents an expected outcome / assertion."""
    text: str
    assertion_type: str = "positive"  # positive | negative


@dataclass
class ParsedRequirement:
    """Structured representation of a parsed requirement."""
    original_text: str
    actors: List[Actor] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    conditions: List[Condition] = field(default_factory=list)
    assertions: List[Assertion] = field(default_factory=list)
    feature_name: str = ""
    context: str = ""


# ---------------------------------------------------------------------------
# Keyword / pattern banks
# ---------------------------------------------------------------------------

USER_STORY_PATTERN = re.compile(
    r"[Aa]s\s+(?:a|an)\s+(?P<role>.+?),?\s+"
    r"[Ii]\s+want\s+(?:to\s+)?(?P<action>.+?)\s+"
    r"[Ss]o\s+that\s+(?P<benefit>.+)",
    re.IGNORECASE,
)

ACTOR_KEYWORDS = [
    "user", "admin", "administrator", "customer", "visitor", "guest",
    "manager", "developer", "operator", "member", "subscriber", "buyer",
    "seller", "agent", "moderator", "editor", "viewer", "owner",
]

ACTION_VERBS = [
    "login", "log in", "register", "sign up", "sign in", "sign out",
    "logout", "log out", "click", "press", "submit", "enter", "type",
    "select", "choose", "upload", "download", "delete", "remove",
    "update", "edit", "modify", "create", "add", "search", "filter",
    "sort", "view", "open", "close", "navigate", "scroll", "drag",
    "drop", "refresh", "reset", "cancel", "confirm", "approve",
    "reject", "send", "receive", "purchase", "buy", "pay", "checkout",
    "subscribe", "unsubscribe", "share", "export", "import", "save",
]

ASSERTION_KEYWORDS = [
    "should", "must", "shall", "expect", "verify", "ensure",
    "confirm", "validate", "check", "assert", "display", "show",
    "appear", "visible", "enabled", "disabled", "redirect",
    "receive", "notified", "message", "error", "success",
    "see", "sees", "shown",
]

NEGATIVE_KEYWORDS = [
    "not", "cannot", "shouldn't", "must not", "shall not",
    "won't", "don't", "doesn't", "unable", "prevent",
    "denied", "forbidden", "unauthorized", "invalid", "fail",
    "error", "block", "restrict", "reject", "disable",
]

CONDITION_KEYWORDS = [
    "when", "if", "given", "after", "before", "while",
    "during", "once", "provided", "assuming", "with",
    "has", "have", "having", "already", "existing",
    "logged in", "authenticated", "authorized",
]


class NLPProcessor:
    """Processes plain English requirements into structured components."""

    def __init__(self):
        ensure_nltk_data()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, requirement_text: str) -> ParsedRequirement:
        """Parse a plain-English requirement into structured components."""
        text = requirement_text.strip()
        parsed = ParsedRequirement(original_text=text)

        # Try user-story format first
        story_match = USER_STORY_PATTERN.search(text)
        if story_match:
            parsed = self._parse_user_story(text, story_match)
        else:
            parsed = self._parse_free_text(text)

        # Derive a feature name if not already set
        if not parsed.feature_name:
            parsed.feature_name = self._derive_feature_name(parsed)

        return parsed

    def parse_batch(self, requirements: List[str]) -> List[ParsedRequirement]:
        """Parse a list of requirements."""
        return [self.parse(req) for req in requirements if req.strip()]

    # ------------------------------------------------------------------
    # User-story parsing
    # ------------------------------------------------------------------

    def _parse_user_story(
        self, text: str, match: re.Match
    ) -> ParsedRequirement:
        role = match.group("role").strip()
        action_text = match.group("action").strip()
        benefit = match.group("benefit").strip()

        parsed = ParsedRequirement(original_text=text)
        parsed.actors.append(Actor(name=role, role=role))
        parsed.context = benefit

        # Extract actions from the "I want to ..." part
        parsed.actions = self._extract_actions(action_text)

        # Extract assertions from the benefit clause
        parsed.assertions = self._extract_assertions(benefit)
        if not parsed.assertions:
            parsed.assertions.append(
                Assertion(text=benefit, assertion_type="positive")
            )

        # Attempt conditions from the full text
        parsed.conditions = self._extract_conditions(text)

        return parsed

    # ------------------------------------------------------------------
    # Free-text parsing
    # ------------------------------------------------------------------

    def _parse_free_text(self, text: str) -> ParsedRequirement:
        parsed = ParsedRequirement(original_text=text)

        sentences = sent_tokenize(text)
        for sentence in sentences:
            # Actors
            actors = self._extract_actors(sentence)
            for a in actors:
                if not any(existing.name == a.name for existing in parsed.actors):
                    parsed.actors.append(a)

            # Actions
            parsed.actions.extend(self._extract_actions(sentence))

            # Conditions
            parsed.conditions.extend(self._extract_conditions(sentence))

            # Assertions
            parsed.assertions.extend(self._extract_assertions(sentence))

        # Fallback: if no actor found, default to "user"
        if not parsed.actors:
            parsed.actors.append(Actor(name="user", role="user"))

        # Fallback: create at least one action from the whole text
        if not parsed.actions:
            parsed.actions.append(
                Action(verb="perform", object=self._clean_text(text))
            )

        # Fallback: create at least one assertion
        if not parsed.assertions:
            last_sentence = sentences[-1] if sentences else text
            parsed.assertions.append(
                Assertion(text=self._clean_text(last_sentence), assertion_type="positive")
            )

        return parsed

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_actors(self, text: str) -> List[Actor]:
        actors: List[Actor] = []
        text_lower = text.lower()
        for kw in ACTOR_KEYWORDS:
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, text_lower):
                actors.append(Actor(name=kw, role=kw))
        # NER pass
        try:
            tokens = word_tokenize(text)
            tagged = pos_tag(tokens)
            tree = ne_chunk(tagged)
            for subtree in tree:
                if hasattr(subtree, "label") and subtree.label() == "PERSON":
                    name = " ".join(word for word, tag in subtree.leaves())
                    if not any(a.name == name.lower() for a in actors):
                        actors.append(Actor(name=name.lower(), role="user"))
        except Exception:
            pass
        return actors

    def _extract_actions(self, text: str) -> List[Action]:
        actions: List[Action] = []
        text_lower = text.lower()

        # Check against known action verbs
        for verb in ACTION_VERBS:
            pattern = rf"\b{re.escape(verb)}\b"
            match = re.search(pattern, text_lower)
            if match:
                obj = self._extract_object_after_verb(text, match.end())
                actions.append(Action(verb=verb, object=obj))

        # POS-tag pass for additional verb-object pairs
        if not actions:
            try:
                tokens = word_tokenize(text)
                tagged = pos_tag(tokens)
                i = 0
                while i < len(tagged):
                    word, tag = tagged[i]
                    if tag.startswith("VB"):
                        obj_parts: List[str] = []
                        j = i + 1
                        while j < len(tagged) and tagged[j][1] in (
                            "NN", "NNS", "NNP", "NNPS", "JJ", "DT", "IN",
                            "PRP", "PRP$", "CD", "RB",
                        ):
                            obj_parts.append(tagged[j][0])
                            j += 1
                        obj = " ".join(obj_parts) if obj_parts else ""
                        if obj:
                            actions.append(Action(verb=word.lower(), object=obj))
                        i = j
                    else:
                        i += 1
            except Exception:
                pass

        return actions

    def _extract_conditions(self, text: str) -> List[Condition]:
        conditions: List[Condition] = []
        text_lower = text.lower()

        for kw in CONDITION_KEYWORDS:
            pattern = rf"\b{re.escape(kw)}\b\s+(.+?)(?:[,;.]|$)"
            for m in re.finditer(pattern, text_lower):
                cond_text = m.group(1).strip().rstrip(",;.")
                if len(cond_text) > 3:
                    conditions.append(
                        Condition(text=cond_text, condition_type="precondition")
                    )

        return conditions

    def _extract_assertions(self, text: str) -> List[Assertion]:
        assertions: List[Assertion] = []
        text_lower = text.lower()

        for kw in ASSERTION_KEYWORDS:
            pattern = rf"\b{re.escape(kw)}\b\s+(.+?)(?:[,;.]|$)"
            for m in re.finditer(pattern, text_lower):
                assert_text = m.group(0).strip().rstrip(",;.")
                is_negative = any(
                    neg in assert_text.lower() for neg in NEGATIVE_KEYWORDS
                )
                a_type = "negative" if is_negative else "positive"
                assertions.append(Assertion(text=assert_text, assertion_type=a_type))

        return assertions

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_object_after_verb(text: str, start_pos: int) -> str:
        remaining = text[start_pos:].strip()
        # Grab until punctuation or end
        match = re.match(r"(.+?)(?:[,;.]|$)", remaining)
        if match:
            return match.group(1).strip()
        return remaining.strip()

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip().rstrip(".,;:")

    def _derive_feature_name(self, parsed: ParsedRequirement) -> str:
        if parsed.actions:
            primary = parsed.actions[0]
            name = f"{primary.verb.title()} {primary.object.title()}"
            return re.sub(r"\s+", " ", name).strip()[:80]
        # Fallback: first 8 words of original text
        words = parsed.original_text.split()[:8]
        return " ".join(words).title()
