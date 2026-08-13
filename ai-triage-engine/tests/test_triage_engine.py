import pytest
from src.triage_engine import TriageEngine


class FakeConfig(dict):
    """Minimal config for testing should_triage() without a real API key."""
    pass


def make_test_engine(min_level=10):
    config = {
        "anthropic": {
            "api_key": "test-key-not-used",
            "model": "claude-sonnet-5",
            "max_tokens": 1024
        },
        "thresholds": {
            "min_rule_level_for_ai_triage": min_level
        }
    }
    return TriageEngine(config)


class TestShouldTriage:

    def test_high_severity_alert_triggers_triage(self):
        engine = make_test_engine(min_level=10)
        alert = {"rule": {"level": 12}}
        assert engine.should_triage(alert) is True

    def test_low_severity_alert_skipped(self):
        engine = make_test_engine(min_level=10)
        alert = {"rule": {"level": 3}}
        assert engine.should_triage(alert) is False

    def test_exact_threshold_triggers_triage(self):
        engine = make_test_engine(min_level=10)
        alert = {"rule": {"level": 10}}
        assert engine.should_triage(alert) is True

    def test_missing_level_defaults_to_zero_and_skips(self):
        engine = make_test_engine(min_level=10)
        alert = {"rule": {}}
        assert engine.should_triage(alert) is False

    def test_zero_threshold_triages_everything(self):
        engine = make_test_engine(min_level=0)
        alert = {"rule": {"level": 3}}
        assert engine.should_triage(alert) is True
