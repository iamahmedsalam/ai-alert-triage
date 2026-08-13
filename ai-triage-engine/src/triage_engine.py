import logging
from src.clients.anthropic_client import AnthropicClient
from src.prompt_builder import build_triage_prompt
from src.response_parser import parse_triage_response

logger = logging.getLogger("triage")


class TriageEngine:

    def __init__(self, config):
        self.config = config
        self.min_level = config["thresholds"]["min_rule_level_for_ai_triage"]

        self.anthropic = AnthropicClient(
            api_key=config["anthropic"]["api_key"],
            model=config["anthropic"]["model"],
            max_tokens=config["anthropic"]["max_tokens"]
        )

        logger.info("Triage engine initialized")

    def should_triage(self, alert):
        rule_level = alert.get("rule", {}).get("level", 0)
        return rule_level >= self.min_level

    def triage_alert(self, alert, enrichment=None):
        rule_id = alert.get("rule", {}).get("id", "unknown")

        if not self.should_triage(alert):
            logger.info(f"Rule {rule_id}: below AI triage threshold, skipping")
            return None

        logger.info(f"Rule {rule_id}: sending to AI triage")

        prompt = build_triage_prompt(alert, enrichment)
        api_result = self.anthropic.get_triage(prompt)

        if api_result is None:
            logger.error(f"Rule {rule_id}: AI triage failed (API error)")
            return None

        parsed = parse_triage_response(api_result["raw_text"])

        result = {
            "rule_id": rule_id,
            "ai_verdict": parsed["verdict"],
            "ai_confidence": parsed["confidence"],
            "recommended_action": parsed["recommended_action"],
            "reasoning": parsed["reasoning"],
            "parse_success": parsed["parse_success"],
            "tokens_used": api_result["usage"]
        }

        logger.info(f"Rule {rule_id}: AI verdict={parsed['verdict']} "
                    f"confidence={parsed['confidence']} "
                    f"(tokens: in={api_result['usage']['input_tokens']}, "
                    f"out={api_result['usage']['output_tokens']})")

        return result
