# Contributing to ClinicalSafetyBench

Thank you for your interest in contributing. Contributions most needed:

## Priority contributions
1. **New country datasets** — any African country with public national clinical guidelines
2. **Clinician review** — review and validate existing ground truth answers
3. **New model adapters** — adapters for Mistral, Llama, or African-hosted models
4. **Improved scoring** — better automated rubrics or LLM judge integration

## Process
1. Open an issue describing your planned contribution before writing code
2. Fork the repository and create a feature branch
3. For data contributions: every prompt must cite a specific page/section of a
   publicly available national guideline
4. All new prompts must be clinician-reviewed before merging
5. Run tests: `pytest tests/ -v`
6. Run data validation: `python scripts/validate_data.py`
7. Submit a pull request with a clear description

## Clinical accuracy requirement
**Never submit clinical content without expert review.**
Every ground_truth field and every failure_definition must be verified by a qualified
clinician familiar with the relevant national guidelines. Include the reviewer's
credentials (with their consent) in your pull request description.

## Code of conduct
This project follows the Contributor Covenant Code of Conduct.
