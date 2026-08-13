import pytest
from src.response_parser import parse_triage_response


class TestResponseParser:

    def test_parses_all_fields_correctly(self):
        response = """VERDICT: TRUE_POSITIVE
CONFIDENCE: HIGH
RECOMMENDED_ACTION: Isolate the endpoint immediately.
REASONING: Multiple corroborating threat intel sources confirm malicious activity."""

        result = parse_triage_response(response)

        assert result["verdict"] == "TRUE_POSITIVE"
        assert result["confidence"] == "HIGH"
        assert result["recommended_action"] == "Isolate the endpoint immediately."
        assert "corroborating" in result["reasoning"]
        assert result["parse_success"] is True

    def test_parses_needs_investigation_verdict(self):
        response = """VERDICT: NEEDS_INVESTIGATION
CONFIDENCE: MEDIUM
RECOMMENDED_ACTION: Escalate for further review.
REASONING: Evidence is insufficient for a confident determination."""

        result = parse_triage_response(response)
        assert result["verdict"] == "NEEDS_INVESTIGATION"

    def test_parses_false_positive_verdict(self):
        response = """VERDICT: FALSE_POSITIVE
CONFIDENCE: HIGH
RECOMMENDED_ACTION: Close as benign, update automation credentials.
REASONING: Source is a known internal automation host."""

        result = parse_triage_response(response)
        assert result["verdict"] == "FALSE_POSITIVE"

    def test_malformed_response_returns_parse_error(self):
        response = "This is not in the expected format at all."
        result = parse_triage_response(response)

        assert result["verdict"] == "PARSE_ERROR"
        assert result["parse_success"] is False

    def test_empty_response_handled_gracefully(self):
        result = parse_triage_response("")
        assert result["verdict"] == "PARSE_ERROR"
        assert result["parse_success"] is False

    def test_multiline_reasoning_captured_fully(self):
        response = """VERDICT: TRUE_POSITIVE
CONFIDENCE: HIGH
RECOMMENDED_ACTION: Contain immediately.
REASONING: This is a long reasoning section.
It spans multiple lines.
All of it should be captured."""

        result = parse_triage_response(response)
        assert "multiple lines" in result["reasoning"]
        assert "should be captured" in result["reasoning"]
