import re
import logging

logger = logging.getLogger("triage")


def parse_triage_response(raw_text):
    try:
        verdict_match = re.search(r"VERDICT:\s*(\S+)", raw_text)
        confidence_match = re.search(r"CONFIDENCE:\s*(\S+)", raw_text)
        action_match = re.search(r"RECOMMENDED_ACTION:\s*(.+)", raw_text)
        reasoning_match = re.search(r"REASONING:\s*(.+)", raw_text, re.DOTALL)

        verdict = verdict_match.group(1) if verdict_match else "PARSE_ERROR"
        confidence = confidence_match.group(1) if confidence_match else "UNKNOWN"
        action = action_match.group(1).strip() if action_match else ""
        reasoning = reasoning_match.group(1).strip() if reasoning_match else ""

        if action_match and reasoning_match:
            action = raw_text[action_match.start(1):reasoning_match.start()].strip()

        result = {
            "verdict": verdict,
            "confidence": confidence,
            "recommended_action": action,
            "reasoning": reasoning,
            "parse_success": verdict_match is not None
        }

        if not verdict_match:
            logger.error(f"Failed to parse verdict from response: {raw_text[:200]}")

        return result

    except Exception as e:
        logger.error(f"Response parsing exception: {e}")
        return {
            "verdict": "PARSE_ERROR",
            "confidence": "UNKNOWN",
            "recommended_action": "",
            "reasoning": "",
            "parse_success": False
        }
