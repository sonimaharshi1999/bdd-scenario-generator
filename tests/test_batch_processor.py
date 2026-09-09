# Author: Maharshi Soni | License: MIT
"""Tests for the Batch Processor module."""

import json
import os
import tempfile
import pytest

from bdd_generator.batch_processor import BatchProcessor, RequirementRecord


@pytest.fixture
def batch():
    return BatchProcessor()


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestCSVReading:
    """Tests for reading requirements from CSV files."""

    def test_read_csv_standard(self, batch, tmp_dir):
        csv_path = os.path.join(tmp_dir, "reqs.csv")
        with open(csv_path, "w", encoding="utf-8") as fh:
            fh.write("id,requirement,category,priority\n")
            fh.write('REQ-001,"User can login",auth,high\n')
            fh.write('REQ-002,"User can register",reg,medium\n')
        records = batch.read_csv(csv_path)
        assert len(records) == 2
        assert records[0].id == "REQ-001"
        assert records[0].text == "User can login"

    def test_read_csv_with_text_column(self, batch, tmp_dir):
        csv_path = os.path.join(tmp_dir, "reqs.csv")
        with open(csv_path, "w", encoding="utf-8") as fh:
            fh.write("id,text\n")
            fh.write('1,"As a user I want to login"\n')
        records = batch.read_csv(csv_path)
        assert len(records) == 1
        assert "login" in records[0].text

    def test_read_csv_skips_empty_text(self, batch, tmp_dir):
        csv_path = os.path.join(tmp_dir, "reqs.csv")
        with open(csv_path, "w", encoding="utf-8") as fh:
            fh.write("id,requirement\n")
            fh.write('1,"Valid requirement"\n')
            fh.write('2,""\n')
        records = batch.read_csv(csv_path)
        assert len(records) == 1


class TestJSONReading:
    """Tests for reading requirements from JSON files."""

    def test_read_json_array_of_objects(self, batch, tmp_dir):
        json_path = os.path.join(tmp_dir, "reqs.json")
        data = [
            {"id": "REQ-001", "requirement": "User can login"},
            {"id": "REQ-002", "requirement": "User can register"},
        ]
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        records = batch.read_json(json_path)
        assert len(records) == 2

    def test_read_json_with_requirements_key(self, batch, tmp_dir):
        json_path = os.path.join(tmp_dir, "reqs.json")
        data = {
            "requirements": [
                {"id": "1", "requirement": "Login feature"},
                {"id": "2", "requirement": "Search feature"},
            ]
        }
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        records = batch.read_json(json_path)
        assert len(records) == 2

    def test_read_json_array_of_strings(self, batch, tmp_dir):
        json_path = os.path.join(tmp_dir, "reqs.json")
        data = ["Login requirement", "Search requirement"]
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        records = batch.read_json(json_path)
        assert len(records) == 2
        assert records[0].text == "Login requirement"


class TestFileAutoDetection:
    """Tests for automatic file-format detection."""

    def test_read_file_csv(self, batch, tmp_dir):
        csv_path = os.path.join(tmp_dir, "reqs.csv")
        with open(csv_path, "w", encoding="utf-8") as fh:
            fh.write("id,requirement\n")
            fh.write('1,"Test requirement"\n')
        records = batch.read_file(csv_path)
        assert len(records) == 1

    def test_read_file_json(self, batch, tmp_dir):
        json_path = os.path.join(tmp_dir, "reqs.json")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump([{"id": "1", "requirement": "Test"}], fh)
        records = batch.read_file(json_path)
        assert len(records) == 1

    def test_read_file_unsupported_format(self, batch, tmp_dir):
        txt_path = os.path.join(tmp_dir, "reqs.txt")
        with open(txt_path, "w", encoding="utf-8") as fh:
            fh.write("test")
        with pytest.raises(ValueError, match="Unsupported file format"):
            batch.read_file(txt_path)


class TestExtractTexts:
    """Tests for extracting plain text from records."""

    def test_extract_texts(self, batch):
        records = [
            RequirementRecord(id="1", text="First"),
            RequirementRecord(id="2", text="Second"),
        ]
        texts = batch.extract_texts(records)
        assert texts == ["First", "Second"]
