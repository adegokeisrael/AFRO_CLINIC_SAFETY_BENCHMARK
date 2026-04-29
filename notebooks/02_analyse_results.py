# /// script
# requires-python = ">=3.9"
# dependencies = ["pandas", "rich"]
# ///
"""
02_analyse_results.py
---------------------
Load and analyse saved evaluation results.
Run with: python notebooks/02_analyse_results.py --results results/

Usage:
    python notebooks/02_analyse_results.py
    python notebooks/02_analyse_results.py --results results/my_run/
"""
import sys, json, argparse
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rich.console import Console
from rich.table import Table

console = Console()

parser = argparse.ArgumentParser()
parser.add_argument("--results", default=str(ROOT / "results"), type=Path)
args = parser.parse_args()

results_dir = Path(args.results)
jsonl_files = list(results_dir.glob("*.jsonl"))

if not jsonl_files:
    console.print(f"[red]No result files in {results_dir}[/red]")
    sys.exit(1)

# ── Load all results ──────────────────────────────────────────────────────────
all_results = []
for f in jsonl_files:
    with open(f) as fh:
        for line in fh:
            line = line.strip()
            if line:
                all_results.append(json.loads(line))

console.print(f"\n[bold blue]Results Analysis[/bold blue]  ({len(all_results)} scored responses)\n")

# ── Per-model summary ─────────────────────────────────────────────────────────
by_model = defaultdict(list)
for r in all_results:
    by_model[r["model_id"]].append(r)

t = Table("Model", "Total", "Passed", "GAR %", "Failures", title="Overall Results by Model")
for model_id, rows in sorted(by_model.items()):
    total  = len(rows)
    passed = sum(1 for r in rows if r["overall_pass"])
    gar    = f"{100 * passed / total:.1f}%" if total else "N/A"
    fails  = total - passed
    t.add_row(model_id, str(total), str(passed), gar, str(fails))
console.print(t)

# ── Per-model per-country breakdown ──────────────────────────────────────────
t2 = Table("Model", "Country", "GAR %", title="Results by Model × Country")
for model_id, rows in sorted(by_model.items()):
    by_country = defaultdict(list)
    for r in rows:
        by_country[r["country"]].append(r)
    for country, c_rows in sorted(by_country.items()):
        gar = f"{100 * sum(1 for r in c_rows if r['overall_pass']) / len(c_rows):.1f}%"
        t2.add_row(model_id, country.title(), gar)
console.print(t2)

# ── Most common failure modes ─────────────────────────────────────────────────
fm_count = defaultdict(int)
for r in all_results:
    for fm in r.get("failures", []):
        fm_count[fm] += 1

t3 = Table("Failure Mode", "Count", title="Most Common Failures (all models)")
for fm, count in sorted(fm_count.items(), key=lambda x: -x[1]):
    t3.add_row(fm.replace("_", " ").title(), str(count))
console.print(t3)
