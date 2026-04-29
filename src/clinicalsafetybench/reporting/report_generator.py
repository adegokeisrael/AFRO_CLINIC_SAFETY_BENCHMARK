"""
report_generator.py
-------------------
Generates a self-contained HTML report from ClinicalSafetyBench results.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from clinicalsafetybench.scoring.metrics import compute_metrics


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ClinicalSafetyBench Report</title>
<style>
  :root {{
    --blue-dark: #1F3864; --blue-mid: #2E75B6; --gold: #C9A227;
    --bg: #F8FAFC; --white: #FFFFFF; --text: #1A1A1A; --muted: #666;
    --pass: #16a34a; --fail: #dc2626; --warn: #d97706;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: var(--bg); color: var(--text); font-size: 15px; line-height: 1.6; }}
  header {{ background: var(--blue-dark); color: white; padding: 2rem 2.5rem; }}
  header h1 {{ font-size: 1.8rem; margin-bottom: 0.25rem; }}
  header p  {{ color: #b0c8e0; font-size: 0.9rem; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem; }}
  section {{ background: var(--white); border-radius: 8px; padding: 1.5rem;
             margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,.06); }}
  h2 {{ color: var(--blue-dark); font-size: 1.1rem; margin-bottom: 1rem;
        padding-bottom: 0.5rem; border-bottom: 2px solid var(--gold); }}
  .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                  gap: 1rem; margin-bottom: 1rem; }}
  .metric {{ background: var(--bg); border-radius: 8px; padding: 1rem; text-align: center; }}
  .metric .val {{ font-size: 2rem; font-weight: 700; color: var(--blue-mid); }}
  .metric .lbl {{ font-size: 0.78rem; color: var(--muted); margin-top: 0.25rem; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th {{ background: var(--blue-dark); color: white; padding: 0.5rem 0.75rem; text-align: left; }}
  td {{ padding: 0.45rem 0.75rem; border-bottom: 1px solid #eee; }}
  tr:nth-child(even) td {{ background: #f5f8fc; }}
  .pass {{ color: var(--pass); font-weight: 600; }}
  .fail {{ color: var(--fail); font-weight: 600; }}
  .badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px;
            font-size: 0.78rem; font-weight: 600; }}
  .badge-pass {{ background: #dcfce7; color: var(--pass); }}
  .badge-fail {{ background: #fee2e2; color: var(--fail); }}
  footer {{ text-align: center; color: var(--muted); font-size: 0.8rem; padding: 2rem; }}
</style>
</head>
<body>
<header>
  <h1>🏥 ClinicalSafetyBench — Evaluation Report</h1>
  <p>Generated: {generated_at} &nbsp;|&nbsp; Models: {models_str} &nbsp;|&nbsp; Total prompts evaluated: {total}</p>
</header>
<main>

<!-- Overall metrics -->
<section>
  <h2>Overall Safety Metrics (All Models)</h2>
  <div class="metric-grid">
    <div class="metric"><div class="val">{gar_pct}%</div><div class="lbl">Guideline Adherence Rate</div></div>
    <div class="metric"><div class="val">{dar_pct}%</div><div class="lbl">Dosage Accuracy Rate</div></div>
    <div class="metric"><div class="val">{rhr_pct}%</div><div class="lbl">Hallucination Rate ↓</div></div>
    <div class="metric"><div class="val">{oss_pct}%</div><div class="lbl">Overall Safety Score</div></div>
    <div class="metric"><div class="val">{passed}/{total}</div><div class="lbl">Prompts Passed</div></div>
  </div>
</section>

<!-- By model -->
<section>
  <h2>Results by Model</h2>
  <table>
    <tr><th>Model</th><th>Total</th><th>Passed</th><th>GAR %</th><th>Failures</th></tr>
    {model_rows}
  </table>
</section>

<!-- By country -->
<section>
  <h2>Results by Country</h2>
  <table>
    <tr><th>Country</th><th>Total</th><th>Passed</th><th>GAR %</th></tr>
    {country_rows}
  </table>
</section>

<!-- By condition -->
<section>
  <h2>Results by Condition</h2>
  <table>
    <tr><th>Condition</th><th>Total</th><th>Passed</th><th>GAR %</th></tr>
    {condition_rows}
  </table>
</section>

<!-- Failures detail -->
<section>
  <h2>Failed Prompts Detail</h2>
  <table>
    <tr><th>Prompt ID</th><th>Country</th><th>Condition</th><th>Model</th><th>Failures</th></tr>
    {failure_rows}
  </table>
</section>

</main>
<footer>ClinicalSafetyBench · CC BY 4.0 · Africa AI Safety Prize Competition 2026</footer>
</body>
</html>"""


class ReportGenerator:
    def generate(self, results: List[Dict[str, Any]], output_path: Path) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        metrics = compute_metrics(results)

        # ── Model breakdown ───────────────────────────────────────────────
        from collections import defaultdict
        by_model: Dict[str, list] = defaultdict(list)
        for r in results:
            by_model[r["model_id"]].append(r)

        model_rows = ""
        for mid, rows in sorted(by_model.items()):
            t = len(rows); p = sum(1 for r in rows if r["overall_pass"])
            gar = f"{100*p/t:.1f}" if t else "0.0"
            cls = "pass" if p == t else ("warn" if p / t >= 0.5 else "fail")
            model_rows += f"<tr><td>{mid}</td><td>{t}</td><td class='{cls}'>{p}</td><td>{gar}%</td><td>{t-p}</td></tr>\n"

        # ── Country rows ──────────────────────────────────────────────────
        country_rows = ""
        for c, d in sorted(metrics["by_country"].items()):
            t = d["total"]; p = d["passed"]
            country_rows += f"<tr><td>{c.title()}</td><td>{t}</td><td>{p}</td><td>{d['gar']*100:.1f}%</td></tr>\n"

        # ── Condition rows ────────────────────────────────────────────────
        condition_rows = ""
        for cond, d in sorted(metrics["by_condition"].items(), key=lambda x: -x[1]["total"]):
            t = d["total"]; p = d["passed"]
            condition_rows += f"<tr><td>{cond.replace('_',' ').title()}</td><td>{t}</td><td>{p}</td><td>{d['gar']*100:.1f}%</td></tr>\n"

        # ── Failed detail rows ────────────────────────────────────────────
        failures = [r for r in results if not r["overall_pass"]]
        failure_rows = ""
        for r in failures[:100]:  # cap at 100 rows
            fms = ", ".join(r.get("failures", []))
            failure_rows += (
                f"<tr><td>{r['prompt_id']}</td><td>{r['country'].title()}</td>"
                f"<td>{r['condition'].replace('_',' ').title()}</td>"
                f"<td>{r['model_id']}</td>"
                f"<td><span class='badge badge-fail'>{fms}</span></td></tr>\n"
            )
        if not failure_rows:
            failure_rows = "<tr><td colspan='5' style='text-align:center;color:green'>No failures detected 🎉</td></tr>"

        html = _HTML_TEMPLATE.format(
            generated_at   = datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
            models_str     = ", ".join(sorted(by_model.keys())),
            total          = metrics["total"],
            passed         = metrics["passed"],
            gar_pct        = f"{metrics['guideline_adherence_rate']*100:.1f}",
            dar_pct        = f"{metrics['dosage_accuracy_rate']*100:.1f}",
            rhr_pct        = f"{metrics['hallucination_rate']*100:.1f}",
            oss_pct        = f"{metrics['overall_safety_score']*100:.1f}",
            model_rows     = model_rows,
            country_rows   = country_rows,
            condition_rows = condition_rows,
            failure_rows   = failure_rows,
        )

        output_path.write_text(html, encoding="utf-8")
