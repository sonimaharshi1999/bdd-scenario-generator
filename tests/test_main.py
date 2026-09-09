# Author: Maharshi Soni | License: MIT
"""Tests for the main CLI entry point."""

import json
import os
import tempfile
import pytest

from main import main, process_requirement
from bdd_generator.nlp_processor import NLPProcessor
from bdd_generator.scenario_generator import ScenarioGenerator
from bdd_generator.edge_case_generator import EdgeCaseGenerator
from bdd_generator.feature_writer import FeatureWriter


@pytest.fixture
def components():
    return (
        NLPProcessor(),
        ScenarioGenerator(),
        EdgeCaseGenerator(),
        FeatureWriter(),
    )


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestProcessRequirement:
    """Tests for the process_requirement helper."""

    def test_process_single_requirement(self, components, tmp_dir):
        nlp, gen, edge_gen, writer = components
        filepath = process_requirement(
            "As a user, I want to login so that I can access the dashboard",
            nlp, gen, edge_gen, writer,
            output_dir=tmp_dir,
            include_edge_cases=True,
        )
        assert os.path.exists(filepath)
        assert filepath.endswith(".feature")

    def test_process_without_edge_cases(self, components, tmp_dir):
        nlp, gen, edge_gen, writer = components
        filepath = process_requirement(
            "As a user, I want to search products so that I can find items",
            nlp, gen, edge_gen, writer,
            output_dir=tmp_dir,
            include_edge_cases=False,
        )
        assert os.path.exists(filepath)

    def test_process_free_text_requirement(self, components, tmp_dir):
        nlp, gen, edge_gen, writer = components
        filepath = process_requirement(
            "The user should be able to register with email and password",
            nlp, gen, edge_gen, writer,
            output_dir=tmp_dir,
        )
        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as fh:
            content = fh.read()
        assert "Feature:" in content
        assert "Scenario:" in content


class TestCLIMain:
    """Tests for the main() CLI dispatcher."""

    def test_main_single_requirement(self, tmp_dir):
        main([
            "As a user, I want to login so that I can access the system",
            "-o", tmp_dir,
        ])
        features = [f for f in os.listdir(tmp_dir) if f.endswith(".feature")]
        assert len(features) >= 1

    def test_main_batch_json(self, tmp_dir):
        json_path = os.path.join(tmp_dir, "reqs.json")
        data = [
            {"id": "1", "requirement": "As a user, I want to login so that I can access the app"},
            {"id": "2", "requirement": "As a user, I want to search so that I can find items"},
        ]
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)

        out_dir = os.path.join(tmp_dir, "out")
        main(["--file", json_path, "-o", out_dir])
        features = [f for f in os.listdir(out_dir) if f.endswith(".feature")]
        assert len(features) >= 1

    def test_main_batch_csv(self, tmp_dir):
        csv_path = os.path.join(tmp_dir, "reqs.csv")
        with open(csv_path, "w", encoding="utf-8") as fh:
            fh.write("id,requirement\n")
            fh.write('1,"As a user, I want to login so that I can access the system"\n')

        out_dir = os.path.join(tmp_dir, "out")
        main(["--batch", csv_path, "-o", out_dir])
        features = [f for f in os.listdir(out_dir) if f.endswith(".feature")]
        assert len(features) >= 1

    def test_main_no_edge_cases(self, tmp_dir):
        main([
            "As a user, I want to login so that I can access the system",
            "-o", tmp_dir,
            "--no-edge-cases",
        ])
        features = [f for f in os.listdir(tmp_dir) if f.endswith(".feature")]
        assert len(features) >= 1

    def test_main_no_args_exits(self):
        with pytest.raises(SystemExit):
            main([])
