# Author: Maharshi Soni | License: MIT
"""
BDD Scenario Generator - CLI entry point.

Generates Gherkin/Cucumber BDD scenarios (.feature files) from plain English
requirements or user stories.  Supports single requirement, interactive, and
batch mode (CSV / JSON).

Usage:
    python main.py "As a user, I want to login so that I can access my dashboard"
    python main.py --file requirements.csv --output ./features
    python main.py --interactive
    python main.py --batch requirements.json --output ./features --edge-cases
"""

import argparse
import os
import sys
import textwrap

from bdd_generator.nlp_processor import NLPProcessor
from bdd_generator.scenario_generator import ScenarioGenerator
from bdd_generator.edge_case_generator import EdgeCaseGenerator
from bdd_generator.feature_writer import FeatureWriter
from bdd_generator.batch_processor import BatchProcessor


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _banner() -> str:
    return textwrap.dedent("""\
    ============================================================
      BDD Scenario Generator  v1.0.0
      Author: Maharshi Soni | License: MIT
    ============================================================
    """)


def process_requirement(
    text: str,
    nlp: NLPProcessor,
    gen: ScenarioGenerator,
    edge_gen: EdgeCaseGenerator,
    writer: FeatureWriter,
    output_dir: str,
    include_edge_cases: bool = True,
    verbose: bool = False,
) -> str:
    """Process a single requirement string and write the .feature file."""
    parsed = nlp.parse(text)

    if verbose:
        print(f"\n  [NLP] Actors:      {[a.name for a in parsed.actors]}")
        print(f"  [NLP] Actions:     {[(a.verb, a.object) for a in parsed.actions]}")
        print(f"  [NLP] Conditions:  {[c.text for c in parsed.conditions]}")
        print(f"  [NLP] Assertions:  {[a.text for a in parsed.assertions]}")

    feature = gen.generate(parsed)

    if include_edge_cases:
        feature = edge_gen.generate(parsed, feature)

    filepath = writer.write(feature, output_dir)
    return filepath


# -----------------------------------------------------------------------
# CLI modes
# -----------------------------------------------------------------------

def run_single(args, nlp, gen, edge_gen, writer):
    """Process a single requirement passed as a positional argument."""
    text = args.requirement
    filepath = process_requirement(
        text, nlp, gen, edge_gen, writer,
        output_dir=args.output,
        include_edge_cases=args.edge_cases,
        verbose=args.verbose,
    )
    print(f"\n  Feature file generated: {filepath}")
    # Also print the content
    with open(filepath, "r", encoding="utf-8") as fh:
        print("\n" + fh.read())


def run_interactive(args, nlp, gen, edge_gen, writer):
    """Interactive mode - prompt the user for requirements one at a time."""
    print("\n  Interactive mode.  Type a requirement and press Enter.")
    print("  Type 'quit' or 'exit' to stop.\n")
    count = 0
    while True:
        try:
            text = input("  Requirement > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text or text.lower() in ("quit", "exit", "q"):
            break
        filepath = process_requirement(
            text, nlp, gen, edge_gen, writer,
            output_dir=args.output,
            include_edge_cases=args.edge_cases,
            verbose=args.verbose,
        )
        count += 1
        print(f"  [{count}] Generated: {filepath}\n")
    print(f"\n  Done. {count} feature file(s) generated in {args.output}")


def run_batch(args, nlp, gen, edge_gen, writer):
    """Batch mode - read requirements from a CSV or JSON file."""
    batch = BatchProcessor()
    filepath = args.file or args.batch
    print(f"\n  Reading requirements from: {filepath}")

    records = batch.read_file(filepath)
    print(f"  Found {len(records)} requirement(s).\n")

    generated: list = []
    for record in records:
        out = process_requirement(
            record.text, nlp, gen, edge_gen, writer,
            output_dir=args.output,
            include_edge_cases=args.edge_cases,
            verbose=args.verbose,
        )
        generated.append(out)
        print(f"  [{record.id}] Generated: {out}")

    print(f"\n  Done. {len(generated)} feature file(s) generated in {args.output}")


# -----------------------------------------------------------------------
# Argument parser
# -----------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bdd-scenario-generator",
        description="Generate Gherkin/Cucumber BDD scenarios from plain English requirements.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python main.py "As a user, I want to login so that I can access my dashboard"
          python main.py --interactive
          python main.py --file requirements.csv -o ./features
          python main.py --batch stories.json -o ./features --edge-cases --verbose
        """),
    )

    parser.add_argument(
        "requirement",
        nargs="?",
        default=None,
        help="A single requirement or user story in plain English.",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode (prompt for requirements).",
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        default=None,
        help="Path to a CSV or JSON file containing requirements (batch mode).",
    )
    parser.add_argument(
        "-b", "--batch",
        type=str,
        default=None,
        help="Alias for --file (batch mode).",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output",
        help="Output directory for generated .feature files (default: ./output).",
    )
    parser.add_argument(
        "-e", "--edge-cases",
        action="store_true",
        default=True,
        help="Include auto-generated edge-case scenarios (default: True).",
    )
    parser.add_argument(
        "--no-edge-cases",
        action="store_true",
        help="Disable edge-case generation.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed NLP parsing output.",
    )
    return parser


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main(argv=None):
    print(_banner())

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.no_edge_cases:
        args.edge_cases = False

    # Initialise components
    nlp = NLPProcessor()
    gen = ScenarioGenerator()
    edge_gen = EdgeCaseGenerator()
    writer = FeatureWriter()

    # Dispatch
    if args.interactive:
        run_interactive(args, nlp, gen, edge_gen, writer)
    elif args.file or args.batch:
        run_batch(args, nlp, gen, edge_gen, writer)
    elif args.requirement:
        run_single(args, nlp, gen, edge_gen, writer)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
