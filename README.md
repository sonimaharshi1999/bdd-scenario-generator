# BDD Scenario Generator

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg) ![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

Automatically generate complete Gherkin/Cucumber BDD scenarios (`.feature` files) from plain English requirements or user stories. Powered by NLP (NLTK), this tool parses natural language, extracts actors, actions, conditions, and assertions, then produces well-structured Given/When/Then scenarios -- including edge cases -- ready for behave, pytest-bdd, or any Cucumber-compatible runner.

---

## Overview

Writing BDD scenarios by hand is time-consuming and error-prone, especially when dealing with large backlogs. **BDD Scenario Generator** bridges the gap between product requirements and test automation by:

1. Accepting plain English requirements (user stories or free-form text).
2. Using NLP to extract actors, actions, preconditions, and expected outcomes.
3. Generating a complete `.feature` file with happy-path, negative, boundary, and edge-case scenarios.
4. Supporting batch processing from CSV or JSON files for large-scale generation.

No paid APIs are required -- the entire pipeline runs locally using NLTK.

---

## Features

- **User Story Parsing** -- Understands the standard "As a [role], I want to [action] so that [benefit]" format.
- **Free-Text Parsing** -- Also handles plain requirements like "The user should be able to register with email."
- **Smart Actor Extraction** -- Identifies user roles (admin, customer, visitor, etc.) and named entities.
- **Action Detection** -- Recognises 50+ common UI/domain verbs (login, search, upload, checkout, ...).
- **Assertion & Condition Extraction** -- Finds "should", "must", "when", "if", "given" clauses automatically.
- **Negative Scenario Generation** -- Creates error-handling scenarios for every feature.
- **Boundary/Validation Scenarios** -- Generates empty-input and max-length validation scenarios for form-related actions.
- **Domain-Aware Edge Cases** -- Adds security (SQL injection, XSS, session timeout), search, file-upload, payment, and navigation edge cases based on the requirement context.
- **Concurrency Edge Case** -- Always includes a concurrent-access scenario.
- **Gherkin-Compliant Output** -- Produces `.feature` files with proper tags, Background, and indentation.
- **CLI Interface** -- Single requirement, interactive mode, or batch mode.
- **Batch Processing** -- Reads requirements from CSV or JSON files.
- **Verbose Mode** -- Inspect the NLP parsing output for debugging.

---

## Architecture

```
requirement (text)
        |
        v
+-------------------+
|  NLP Processor    |  -- tokenisation, POS tagging, NER, pattern matching
+-------------------+
        |
        v
  ParsedRequirement (actors, actions, conditions, assertions)
        |
        v
+-------------------+
| Scenario Generator|  -- happy path, negative, boundary scenarios
+-------------------+
        |
        v
+-------------------+
| Edge Case Generator| -- domain-specific edge-case templates
+-------------------+
        |
        v
      Feature (name, tags, background, scenarios[])
        |
        v
+-------------------+
|  Feature Writer   |  -- serialise to .feature file
+-------------------+
        |
        v
   output/*.feature
```

### Module Responsibilities

| Module | File | Purpose |
|---|---|---|
| NLP Processor | `bdd_generator/nlp_processor.py` | Tokenise, POS-tag, extract actors/actions/conditions/assertions |
| Scenario Generator | `bdd_generator/scenario_generator.py` | Build Feature/Scenario/Step structures (happy, negative, boundary) |
| Edge Case Generator | `bdd_generator/edge_case_generator.py` | Add domain-aware edge-case scenarios (security, search, payments, ...) |
| Feature Writer | `bdd_generator/feature_writer.py` | Render Feature objects to valid Gherkin `.feature` files |
| Batch Processor | `bdd_generator/batch_processor.py` | Read requirements from CSV / JSON files |
| CLI | `main.py` | Argument parsing, mode dispatch |

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.8+ |
| NLP | NLTK (tokenisation, POS tagging, named-entity recognition) |
| Testing | pytest |
| Output Format | Gherkin (.feature) -- compatible with behave, pytest-bdd, Cucumber |
| Input Formats | Plain text, CSV, JSON |

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/sonimaharshi1999/bdd-scenario-generator.git
cd bdd-scenario-generator

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

NLTK data packages are downloaded automatically on first run.

---

## Usage

### 1. Single Requirement (CLI)

```bash
python main.py "As a user, I want to login with my email and password so that I can access my dashboard"
```

### 2. Free-Text Requirement

```bash
python main.py "The customer should be able to search for products and filter results by price"
```

### 3. Interactive Mode

```bash
python main.py --interactive
```

You will be prompted to enter requirements one at a time. Type `quit` to stop.

### 4. Batch Mode (CSV)

```bash
python main.py --file examples/sample_requirements.csv --output ./features
```

### 5. Batch Mode (JSON)

```bash
python main.py --batch examples/sample_requirements.json --output ./features
```

### 6. Disable Edge Cases

```bash
python main.py "As a user, I want to login so that I can access the app" --no-edge-cases
```

### 7. Verbose Mode

```bash
python main.py "As a user, I want to register so that I can use the app" --verbose
```

### Full CLI Reference

```
usage: bdd-scenario-generator [-h] [-i] [-f FILE] [-b BATCH] [-o OUTPUT]
                                [-e] [--no-edge-cases] [-v]
                                [requirement]

positional arguments:
  requirement           A single requirement or user story in plain English.

options:
  -h, --help            show this help message and exit
  -i, --interactive     Run in interactive mode.
  -f, --file FILE       Path to a CSV or JSON file (batch mode).
  -b, --batch BATCH     Alias for --file (batch mode).
  -o, --output OUTPUT   Output directory (default: ./output).
  -e, --edge-cases      Include edge-case scenarios (default: True).
  --no-edge-cases       Disable edge-case generation.
  -v, --verbose         Show detailed NLP parsing output.
```

---

## Sample Input / Output

### Input

```
As a user, I want to login with my email and password so that I can access my dashboard
```

### Output (`output/login_with_my_email_and_password.feature`)

```gherkin
@user @authentication
Feature: Login With My Email And Password
  I can access my dashboard

  @happy_path @smoke
  Scenario: Successfully login with my email and password
    Given the user is on the relevant page
    When the user logins with my email and password
    Then the system should I can access my dashboard

  @negative @error_handling
  Scenario: Unsuccessful login with invalid data
    Given the user is on the relevant page
    When the user tries to login with invalid with my email and password
    Then the system should display an appropriate error message
    And the user should remain on the current page

  @security @edge_case
  Scenario: Login with SQL injection attempt
    Given the user is on the login page
    When the user enters "' OR 1=1 --" as the username
    And the user enters any value as the password
    And the user clicks the login button
    Then the system should reject the input
    And the system should not expose any database errors

  @security @edge_case
  Scenario: Login with XSS attempt
    Given the user is on the login page
    When the user enters "<script>alert('xss')</script>" as the username
    And the user clicks the login button
    Then the system should sanitize the input
    And no script should be executed

  ...additional edge-case scenarios...
```

---

## Project Structure

```
bdd-scenario-generator/
|-- main.py                           # CLI entry point
|-- requirements.txt                  # Python dependencies
|-- .gitignore                        # Git ignore rules
|-- LICENSE                           # MIT License
|-- README.md                         # This file
|-- bdd_generator/
|   |-- __init__.py                   # Package init
|   |-- nlp_processor.py             # NLP parsing module
|   |-- scenario_generator.py        # BDD scenario generation
|   |-- edge_case_generator.py       # Edge-case scenario generation
|   |-- feature_writer.py            # .feature file writer
|   |-- batch_processor.py           # CSV/JSON batch reader
|-- tests/
|   |-- __init__.py
|   |-- test_nlp_processor.py        # NLP processor tests
|   |-- test_scenario_generator.py   # Scenario generator tests
|   |-- test_edge_case_generator.py  # Edge-case generator tests
|   |-- test_feature_writer.py       # Feature writer tests
|   |-- test_batch_processor.py      # Batch processor tests
|   |-- test_main.py                 # CLI integration tests
|-- examples/
|   |-- sample_requirements.csv      # Example CSV input
|   |-- sample_requirements.json     # Example JSON input
|-- output/                           # Default output directory
```

---

## Tests

Run the full test suite with pytest:

```bash
pytest tests/ -v
```

Run a specific test module:

```bash
pytest tests/test_nlp_processor.py -v
pytest tests/test_scenario_generator.py -v
pytest tests/test_feature_writer.py -v
```

Run with coverage (requires `pytest-cov`):

```bash
pip install pytest-cov
pytest tests/ -v --cov=bdd_generator --cov-report=term-missing
```

---

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

Please ensure all existing tests pass and add new tests for any new functionality.

---

## Roadmap

- [ ] **Scenario Outline support** -- Generate parameterised scenarios with Examples tables from data-driven requirements.
- [ ] **Step definition scaffolding** -- Auto-generate matching step definition stubs for behave/pytest-bdd.
- [ ] **Requirement priority handling** -- Order feature files and scenarios based on priority metadata.
- [ ] **Custom edge-case templates** -- Allow users to define domain-specific edge-case templates via YAML config.
- [ ] **Jira/GitHub integration** -- Pull user stories directly from issue trackers.
- [ ] **Multi-language Gherkin** -- Support Gherkin keywords in languages other than English.
- [ ] **Web UI** -- Simple Flask/Streamlit interface for non-technical stakeholders.
- [ ] **spaCy backend** -- Optional spaCy NLP backend for improved entity extraction.
- [ ] **Duplicate detection** -- Warn when generated scenarios are semantically similar to existing `.feature` files.

---

## Author

**Maharshi Soni**

- GitHub: [github.com/sonimaharshi1999](https://github.com/sonimaharshi1999)
- LinkedIn: [linkedin.com/in/maharshi-soni-b56736170](https://linkedin.com/in/maharshi-soni-b56736170)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [NLTK](https://www.nltk.org/) -- Natural Language Toolkit for Python.
- [Cucumber / Gherkin](https://cucumber.io/) -- The BDD framework and language that inspired this project.
- [behave](https://behave.readthedocs.io/) -- BDD framework for Python.
- [pytest-bdd](https://pytest-bdd.readthedocs.io/) -- BDD plugin for pytest.
