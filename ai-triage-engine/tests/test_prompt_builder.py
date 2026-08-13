import pytest
from src.prompt_builder import build_triage_prompt


class TestPromptBuilder:

    def test_includes_rule_id(self):
        alert = {"rule": {"id": "100011", "level": 12, "description": "Test"}}
        prompt = build_triage_prompt(alert)
        assert "100011" in prompt

    def test_includes_rule_description(self):
        alert = {"rule": {"id": "100011", "level": 12, "description": "SSH brute force"}}
        prompt = build_triage_prompt(alert)
        assert "SSH brute force" in prompt

    def test_no_enrichment_shows_fallback_message(self):
        alert = {"rule": {"id": "100001", "level": 10, "description": "Test"}}
        prompt = build_triage_prompt(alert, enrichment=None)
        assert "No threat intelligence enrichment available" in prompt

    def test_enrichment_included_when_provided(self):
        alert = {"rule": {"id": "100016", "level": 13, "description": "Test"}}
        enrichment = {
            "verdict": "BLOCK",
            "sources_responding": 3,
            "summary": {"abuse_score": 100, "otx_pulses": 50, "misp_matched": True}
        }
        prompt = build_triage_prompt(alert, enrichment)
        assert "BLOCK" in prompt
        assert "100/100" in prompt
        assert "50" in prompt

    def test_zero_sources_responding_adds_warning_note(self):
        alert = {"rule": {"id": "100011", "level": 12, "description": "Test"}}
        enrichment = {
            "verdict": "CLEAN",
            "sources_responding": 0,
            "summary": {"abuse_score": 0, "otx_pulses": 0, "misp_matched": False}
        }
        prompt = build_triage_prompt(alert, enrichment)
        assert "IMPORTANT" in prompt
        assert "SKIPPED" in prompt

    def test_nonzero_sources_responding_no_warning_note(self):
        alert = {"rule": {"id": "100011", "level": 12, "description": "Test"}}
        enrichment = {
            "verdict": "CLEAN",
            "sources_responding": 3,
            "summary": {"abuse_score": 0, "otx_pulses": 0, "misp_matched": False}
        }
        prompt = build_triage_prompt(alert, enrichment)
        assert "IMPORTANT" not in prompt

    def test_response_format_instructions_present(self):
        alert = {"rule": {"id": "100011", "level": 12, "description": "Test"}}
        prompt = build_triage_prompt(alert)
        assert "VERDICT:" in prompt
        assert "CONFIDENCE:" in prompt
        assert "RECOMMENDED_ACTION:" in prompt
        assert "REASONING:" in prompt
