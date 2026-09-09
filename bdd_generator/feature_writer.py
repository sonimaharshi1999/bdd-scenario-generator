# Author: Maharshi Soni | License: MIT
"""
Feature Writer module - Serialises Feature objects into valid .feature file content
compatible with Cucumber / behave / pytest-bdd.
"""

import os
import re
from typing import List, Optional

from .scenario_generator import Feature, Scenario, Step


class FeatureWriter:
    """Writes Feature objects to Gherkin .feature files."""

    INDENT = "  "

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(self, feature: Feature, output_dir: str) -> str:
        """Write a Feature to a .feature file and return the path."""
        os.makedirs(output_dir, exist_ok=True)
        filename = self._safe_filename(feature.name) + ".feature"
        filepath = os.path.join(output_dir, filename)

        content = self.render(feature)
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(content)

        return filepath

    def write_batch(self, features: List[Feature], output_dir: str) -> List[str]:
        """Write multiple features to .feature files."""
        return [self.write(f, output_dir) for f in features]

    def render(self, feature: Feature) -> str:
        """Render a Feature to a Gherkin-formatted string."""
        lines: List[str] = []

        # Feature-level tags
        if feature.tags:
            lines.append(" ".join(feature.tags))

        lines.append(f"Feature: {feature.name}")
        if feature.description:
            for desc_line in feature.description.splitlines():
                lines.append(f"{self.INDENT}{desc_line.strip()}")
        lines.append("")

        # Background
        if feature.background:
            lines.append(f"{self.INDENT}Background:")
            for step in feature.background:
                lines.append(f"{self.INDENT}{self.INDENT}{step.keyword} {step.text}")
            lines.append("")

        # Scenarios
        for scenario in feature.scenarios:
            lines.extend(self._render_scenario(scenario))
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def _render_scenario(self, scenario: Scenario) -> List[str]:
        lines: List[str] = []

        # Tags
        if scenario.tags:
            lines.append(f"{self.INDENT}{' '.join(scenario.tags)}")

        # Scenario Outline vs Scenario
        if scenario.examples:
            lines.append(f"{self.INDENT}Scenario Outline: {scenario.name}")
        else:
            lines.append(f"{self.INDENT}Scenario: {scenario.name}")

        # Description
        if scenario.description:
            for desc_line in scenario.description.splitlines():
                lines.append(f"{self.INDENT}{self.INDENT}{desc_line.strip()}")

        # Steps
        for step in scenario.steps:
            lines.append(f"{self.INDENT}{self.INDENT}{step.keyword} {step.text}")

        # Examples table
        if scenario.examples:
            lines.append("")
            lines.append(f"{self.INDENT}{self.INDENT}Examples:")
            headers = list(scenario.examples[0].keys())
            header_row = " | ".join(headers)
            lines.append(f"{self.INDENT}{self.INDENT}{self.INDENT}| {header_row} |")
            for row in scenario.examples:
                values = " | ".join(str(row[h]) for h in headers)
                lines.append(f"{self.INDENT}{self.INDENT}{self.INDENT}| {values} |")

        return lines

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Convert a feature name to a safe filename slug."""
        slug = name.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "_", slug)
        slug = slug.strip("_")
        return slug or "unnamed_feature"
