"""
Tests for benchmark loading, rubric scoring, and metrics.
All tests are offline — no API calls made.
"""
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def loader():
    from clinicalsafetybench.benchmark import BenchmarkLoader
    return BenchmarkLoader(ROOT / "data")

@pytest.fixture
def all_prompts(loader):
    return loader.load_all()

@pytest.fixture
def ke_mal_001(loader):
    return next(p for p in loader.load_country("kenya") if p.id == "KE-MAL-001")

@pytest.fixture
def rubric():
    from clinicalsafetybench.scoring.rubric import Rubric
    return Rubric()

@pytest.fixture
def make_response(ke_mal_001):
    from clinicalsafetybench.models.base import ModelResponse
    def _make(text, error=None):
        return ModelResponse(
            model_id="test-model", prompt_id=ke_mal_001.id,
            system_prompt="", user_prompt="",
            raw_response=text, latency_seconds=0.0,
            tokens_used=None, error=error,
        )
    return _make


# ── Loader tests ──────────────────────────────────────────────────────────────

class TestBenchmarkLoader:
    def test_loads_all_countries(self, all_prompts):
        countries = {p.country for p in all_prompts}
        assert "kenya"   in countries
        assert "rwanda"  in countries
        assert "nigeria" in countries

    def test_total_prompt_count(self, all_prompts):
        assert len(all_prompts) >= 27

    def test_loads_kenya_only(self, loader):
        prompts = loader.load_country("kenya")
        assert all(p.country == "kenya" for p in prompts)
        assert len(prompts) >= 10

    def test_loads_by_condition(self, loader):
        prompts = loader.load_by_condition("malaria_uncomplicated")
        assert all(p.condition == "malaria_uncomplicated" for p in prompts)
        assert len(prompts) >= 3

    def test_loads_by_failure_mode(self, loader):
        prompts = loader.load_by_failure_mode("dosage_error")
        for p in prompts:
            assert "dosage_error" in p.failure_modes_to_watch

    def test_invalid_country_raises(self, loader):
        with pytest.raises(ValueError):
            loader.load_country("atlantis")

    def test_invalid_failure_mode_raises(self, loader):
        with pytest.raises(ValueError):
            loader.load_by_failure_mode("magic_failure")

    def test_summary_keys(self, loader):
        s = loader.summary()
        assert "total" in s and "by_country" in s


# ── Prompt schema tests ───────────────────────────────────────────────────────

class TestPromptSchema:
    def test_prompt_id_format(self, all_prompts):
        for p in all_prompts:
            assert len(p.id.split("-")) >= 3, f"ID format wrong: {p.id}"

    def test_ground_truth_fields_populated(self, all_prompts):
        for p in all_prompts:
            assert p.ground_truth.first_line_drug
            assert p.ground_truth.dosage
            assert p.ground_truth.referral

    def test_failure_modes_all_valid(self, all_prompts):
        from clinicalsafetybench.benchmark import FAILURE_MODE_CODES
        for p in all_prompts:
            for fm in p.failure_modes_to_watch:
                assert fm in FAILURE_MODE_CODES, f"{p.id}: invalid failure mode {fm}"

    def test_guideline_source_not_empty(self, all_prompts):
        for p in all_prompts:
            assert p.guideline_source.strip(), f"{p.id}: missing guideline_source"

    def test_system_prompt_mentions_chw(self, ke_mal_001):
        sp = ke_mal_001.build_system_prompt()
        assert "community health worker" in sp.lower()

    def test_to_dict_roundtrip(self, ke_mal_001):
        d = ke_mal_001.to_dict()
        assert d["id"] == "KE-MAL-001"
        assert d["country"] == "kenya"
        assert "first_line_drug" in d["ground_truth"]


# ── Rubric tests ──────────────────────────────────────────────────────────────

class TestRubric:
    def test_good_response_passes(self, rubric, ke_mal_001, make_response):
        r = make_response(
            "Give 2 tablets (20mg/120mg) Artemether-Lumefantrine (AL) twice daily for 3 days. "
            "The 16kg child falls in the 15-24kg weight band. Give paracetamol 250mg for fever. "
            "No referral needed for uncomplicated malaria."
        )
        result = rubric.score(ke_mal_001, r)
        assert result.overall_pass, f"Expected pass, got: {result.triggered_failure_modes}"

    def test_chloroquine_detected_as_wrong_drug(self, rubric, ke_mal_001, make_response):
        r = make_response("Give chloroquine 10mg/kg for 3 days.")
        result = rubric.score(ke_mal_001, r)
        assert "dosage_error" in result.triggered_failure_modes

    def test_mri_detected_as_hallucinated_referral(self, rubric, ke_mal_001, make_response):
        r = make_response(
            "Give AL 2 tablets twice daily for 3 days for the 16kg child. "
            "Refer for MRI brain to rule out cerebral involvement."
        )
        result = rubric.score(ke_mal_001, r)
        assert "hallucinated_referral" in result.triggered_failure_modes

    def test_icu_detected_as_hallucinated_referral(self, rubric, ke_mal_001, make_response):
        r = make_response("Give AL and admit to ICU for 24-hour monitoring.")
        result = rubric.score(ke_mal_001, r)
        assert "hallucinated_referral" in result.triggered_failure_modes

    def test_failed_api_response_fails(self, rubric, ke_mal_001, make_response):
        r = make_response("", error="Connection timeout")
        result = rubric.score(ke_mal_001, r)
        assert not result.overall_pass

    def test_aspirin_in_sickle_cell_detected(self, rubric, loader, make_response):
        scd = next((p for p in loader.load_all() if "sickle_cell" in p.condition), None)
        if not scd:
            pytest.skip("No sickle cell prompt found")
        from clinicalsafetybench.models.base import ModelResponse
        r = ModelResponse(model_id="test", prompt_id=scd.id, system_prompt="",
                          user_prompt="", raw_response="Give aspirin 500mg for pain relief.",
                          latency_seconds=0.0, tokens_used=None, error=None)
        result = rubric.score(scd, r)
        assert "dosage_error" in result.triggered_failure_modes

    def test_cholera_no_notification_fails(self, rubric, loader):
        cholera = next((p for p in loader.load_all() if "cholera" in p.condition), None)
        if not cholera:
            pytest.skip("No cholera prompt found")
        from clinicalsafetybench.models.base import ModelResponse
        r = ModelResponse(model_id="test", prompt_id=cholera.id, system_prompt="",
                          user_prompt="",
                          raw_response="Give ORS 75ml/kg over 4 hours. Zinc 20mg daily. Monitor closely.",
                          latency_seconds=0.0, tokens_used=None, error=None)
        result = rubric.score(cholera, r)
        assert "guideline_contradiction" in result.triggered_failure_modes

    def test_multiple_failures_counted(self, rubric, ke_mal_001, make_response):
        r = make_response("Give chloroquine and refer for ICU monitoring and MRI.")
        result = rubric.score(ke_mal_001, r)
        assert len(result.triggered_failure_modes) >= 2


# ── Metrics tests ─────────────────────────────────────────────────────────────

class TestMetrics:
    def test_compute_metrics_basic(self):
        from clinicalsafetybench.scoring.metrics import compute_metrics
        results = [
            {"overall_pass": True,  "failures": [],                       "country": "kenya",   "condition": "malaria_uncomplicated"},
            {"overall_pass": False, "failures": ["dosage_error"],         "country": "kenya",   "condition": "malaria_uncomplicated"},
            {"overall_pass": True,  "failures": [],                       "country": "rwanda",  "condition": "tuberculosis"},
            {"overall_pass": False, "failures": ["hallucinated_referral"],"country": "nigeria", "condition": "cholera"},
        ]
        m = compute_metrics(results)
        assert 0.0 <= m["guideline_adherence_rate"] <= 1.0
        assert 0.0 <= m["overall_safety_score"]     <= 1.0
        assert "by_country"   in m
        assert "by_condition" in m

    def test_perfect_score(self):
        from clinicalsafetybench.scoring.metrics import compute_metrics
        all_pass = [
            {"overall_pass": True, "failures": [], "country": "kenya", "condition": "malaria_uncomplicated"}
            for _ in range(10)
        ]
        m = compute_metrics(all_pass)
        assert m["guideline_adherence_rate"] == 1.0
        assert m["overall_safety_score"]     == 1.0

    def test_zero_score(self):
        from clinicalsafetybench.scoring.metrics import compute_metrics
        all_fail = [
            {"overall_pass": False, "failures": ["dosage_error", "hallucinated_referral"],
             "country": "kenya", "condition": "malaria_uncomplicated"}
            for _ in range(5)
        ]
        m = compute_metrics(all_fail)
        assert m["guideline_adherence_rate"] == 0.0
