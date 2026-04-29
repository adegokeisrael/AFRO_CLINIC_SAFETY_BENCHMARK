# /// script
# requires-python = ">=3.9"
# dependencies = ["pandas", "rich"]
# ///
"""
01_explore_benchmark.py
-----------------------
Explore the ClinicalSafetyBench dataset: counts, conditions, failure modes.
Run with: python notebooks/01_explore_benchmark.py
"""
import sys, json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from clinicalsafetybench.benchmark import BenchmarkLoader
from rich.console import Console
from rich.table import Table

console = Console()
loader  = BenchmarkLoader(ROOT / "data")
prompts = loader.load_all()

# ── Summary ───────────────────────────────────────────────────────────────────
summary = loader.summary()
console.print(f"\n[bold blue]ClinicalSafetyBench Dataset Explorer[/bold blue]")
console.print(f"Total prompts: [bold]{summary['total']}[/bold]\n")

# By country
t = Table("Country", "Prompts", title="By Country")
for k, v in sorted(summary["by_country"].items()):
    t.add_row(k.title(), str(v))
console.print(t)

# By condition
t2 = Table("Condition", "Prompts", title="By Condition")
for k, v in sorted(summary["by_condition"].items(), key=lambda x: -x[1]):
    t2.add_row(k.replace("_", " ").title(), str(v))
console.print(t2)

# By failure mode
t3 = Table("Failure Mode", "Prompts Tested", title="By Failure Mode")
for k, v in sorted(summary["by_failure_mode"].items(), key=lambda x: -x[1]):
    t3.add_row(k.replace("_", " ").title(), str(v))
console.print(t3)

# ── Sample prompts ─────────────────────────────────────────────────────────
console.print("\n[bold]Sample Prompt: KE-MAL-001[/bold]")
sample = next((p for p in prompts if p.id == "KE-MAL-001"), None)
if sample:
    console.print(f"  Country:   {sample.country}")
    console.print(f"  Condition: {sample.condition}")
    console.print(f"  Scenario:  {sample.scenario[:200]}...")
    console.print(f"  Guideline: {sample.guideline_source}")
    console.print(f"  1st line:  {sample.ground_truth.first_line_drug}")
    console.print(f"  Dosage:    {sample.ground_truth.dosage}")
    console.print(f"  Failures tested: {sample.failure_modes_to_watch}")
