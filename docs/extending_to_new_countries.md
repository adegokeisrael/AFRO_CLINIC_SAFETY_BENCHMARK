# Extending ClinicalSafetyBench to New Countries

Any African country with publicly available national treatment guidelines can extend this benchmark
in under a week.

## Step 1 — Identify Source Documents

Find official, publicly available national clinical documents:
- Ministry of Health website
- WHO AFRO country pages
- National disease programme websites

Minimum needed: malaria treatment guidelines + one of: TB, MCH, cholera, sickle cell.

## Step 2 — Create the Data Directory

```bash
mkdir data/{your_country}/
```

## Step 3 — Write Prompts (JSONL format)

Follow the schema in data/kenya/prompts.jsonl. Each line is one JSON object:

```json
{
  "id": "GH-MAL-001",
  "country": "ghana",
  "condition": "malaria_uncomplicated",
  "severity": "uncomplicated",
  "guideline_source": "Ghana National Malaria Treatment Guidelines 2022, p.XX",
  "scenario": "Realistic CHW scenario...",
  "ground_truth": {
    "first_line_drug": "...", "dosage": "...",
    "additional": "...", "referral": "..."
  },
  "failure_modes_to_watch": ["dosage_error", "guideline_contradiction"],
  "failure_definitions": {
    "dosage_error": "Specific failure description",
    "guideline_contradiction": "What contradicts the guideline"
  },
  "tags": ["pediatric", "malaria"]
}
```

## Step 4 — Clinician Review (MANDATORY)

Every ground_truth and failure_definition must be reviewed by a clinician who has
read the source guideline. Never publish results from unreviewed prompts.

## Step 5 — Rebuild Combined Dataset

```bash
python scripts/validate_data.py
cat data/*/prompts.jsonl > data/combined/all_prompts.jsonl
```

## Naming Conventions

- Prompt IDs: {COUNTRY_CODE}-{CONDITION}-{NUMBER} e.g. GH-MAL-001
- Country codes: ISO 3166-1 alpha-2 (GH, TZ, ZA, ET, UG, CM...)
