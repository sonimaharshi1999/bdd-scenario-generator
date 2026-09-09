# Author: Maharshi Soni | License: MIT
"""
Batch Processor module - Reads requirements from CSV and JSON files
and processes them in batch mode.
"""

import csv
import json
import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RequirementRecord:
    """A single requirement from a batch input file."""
    id: str
    text: str
    category: Optional[str] = None
    priority: Optional[str] = None


class BatchProcessor:
    """Reads and processes requirements from CSV and JSON files."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def read_file(self, filepath: str) -> List[RequirementRecord]:
        """Read requirements from a CSV or JSON file."""
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".csv":
            return self.read_csv(filepath)
        elif ext == ".json":
            return self.read_json(filepath)
        else:
            raise ValueError(
                f"Unsupported file format '{ext}'. Use .csv or .json."
            )

    def read_csv(self, filepath: str) -> List[RequirementRecord]:
        """Read requirements from a CSV file.

        Expected columns: id, requirement (or text), category (optional), priority (optional).
        """
        records: List[RequirementRecord] = []
        with open(filepath, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for i, row in enumerate(reader):
                req_id = row.get("id", row.get("ID", str(i + 1)))
                text = row.get("requirement", row.get("text", row.get("description", "")))
                if not text:
                    continue
                records.append(
                    RequirementRecord(
                        id=str(req_id),
                        text=text.strip(),
                        category=row.get("category", None),
                        priority=row.get("priority", None),
                    )
                )
        return records

    def read_json(self, filepath: str) -> List[RequirementRecord]:
        """Read requirements from a JSON file.

        Expected format:
            [
                {"id": "REQ-001", "requirement": "...", "category": "...", "priority": "..."},
                ...
            ]
        or:
            {"requirements": [...]}
        """
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        if isinstance(data, dict):
            items = data.get("requirements", data.get("stories", []))
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError("JSON file must contain a list or an object with a 'requirements' key.")

        records: List[RequirementRecord] = []
        for i, item in enumerate(items):
            if isinstance(item, str):
                records.append(RequirementRecord(id=str(i + 1), text=item.strip()))
                continue
            req_id = item.get("id", str(i + 1))
            text = item.get("requirement", item.get("text", item.get("description", "")))
            if not text:
                continue
            records.append(
                RequirementRecord(
                    id=str(req_id),
                    text=text.strip(),
                    category=item.get("category", None),
                    priority=item.get("priority", None),
                )
            )
        return records

    @staticmethod
    def extract_texts(records: List[RequirementRecord]) -> List[str]:
        """Extract plain text from requirement records."""
        return [r.text for r in records]
