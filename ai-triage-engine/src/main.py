import json
import time
import logging
from src.config import load_config
from src.logger import setup_logger
from src.triage_engine import TriageEngine

logger = logging.getLogger("triage")

AI_TRIAGE_ALERT_FILE = "/home/wazuhuser/ai-triage-engine/logs/ai_triage_alerts.json"

# Project 3's enrichment output - this project only READS this file,
# never writes to it or touches any Project 3 code. Clean separation
# per the Option B architecture decision (see architecture docs).
ENRICHMENT_OUTPUT_FILE = "/home/wazuhuser/enrichment-engine/logs/enrichment_alerts.json"


def reconstruct_alert(enriched_line):
    """
    Rebuild an 'alert-shaped' dict and an 'enrichment-shaped' dict
    from Project 3's enrichment_alerts.json output format, so we can
    feed both into the existing prompt_builder without modifying it
    or Project 3's code.
    """
    alert = {
        "rule": {
            "id": enriched_line.get("wazuh_rule_id", "unknown"),
            "level": 0,
            "description": enriched_line.get("wazuh_rule_description", "")
        },
        "agent": {"name": enriched_line.get("agent", "unknown")},
        "full_log": f"Source IP: {enriched_line.get('enrichment_ip', 'unknown')}"
    }

    enrichment = {
        "verdict": enriched_line.get("verdict", "UNKNOWN"),
        "sources_responding": enriched_line.get("sources_responding", 0),
        "summary": {
            "abuse_score": enriched_line.get("abuse_score", 0),
            "otx_pulses": enriched_line.get("otx_pulses", 0),
            "misp_matched": enriched_line.get("misp_matched", False)
        }
    }

    return alert, enrichment


def write_ai_triage_alert(rule_id, ip, triage_result):
    try:
        # NOTE: this field was originally named "enrichment_ip", which
        # accidentally collided with Project 3's Rule 100012 (which
        # matches on ANY JSON log containing an "enrichment_ip" field,
        # regardless of source file). That caused Project 3's own
        # rule to claim these alerts before Project 4's Rule 100017
        # ever got evaluated. Renamed to triage_source_ip to eliminate
        # the field-name collision between the two independently-built
        # rule sets.
        alert_line = {
            "source_rule_id": rule_id,
            "triage_source_ip": ip,
            "ai_verdict": triage_result["ai_verdict"],
            "ai_confidence": triage_result["ai_confidence"],
            "recommended_action": triage_result["recommended_action"],
            "reasoning": triage_result["reasoning"],
            "parse_success": triage_result["parse_success"]
        }

        with open(AI_TRIAGE_ALERT_FILE, "a") as f:
            f.write(json.dumps(alert_line) + "\n")

    except Exception as e:
        logger.error(f"Failed to write AI triage alert: {e}")


def watch_enriched_alerts(config, engine):
    logger.info(f"Watching Project 3 output: {ENRICHMENT_OUTPUT_FILE}")

    try:
        file = open(ENRICHMENT_OUTPUT_FILE, "r")
        file.seek(0, 2)
        logger.info("Moved to end of file, waiting for new enriched alerts...")

        while True:
            line = file.readline()

            if not line:
                time.sleep(1)
                continue

            line = line.strip()
            if not line:
                continue

            try:
                enriched_line = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Project 3's output doesn't carry the original Wazuh rule
            # level, so we derive a synthetic severity from the
            # enrichment verdict itself to drive the AI triage
            # threshold gate.
            verdict = enriched_line.get("verdict", "CLEAN")
            severity_map = {
                "BLOCK": 13, "LIKELY_MALICIOUS": 10,
                "REVIEW": 8, "SUSPICIOUS": 6, "CLEAN": 3
            }
            synthetic_level = severity_map.get(verdict, 3)

            alert, enrichment = reconstruct_alert(enriched_line)
            alert["rule"]["level"] = synthetic_level

            if not engine.should_triage(alert):
                continue

            result = engine.triage_alert(alert, enrichment)

            if result:
                write_ai_triage_alert(
                    enriched_line.get("wazuh_rule_id", "unknown"),
                    enriched_line.get("enrichment_ip", "unknown"),
                    result
                )
                print(f"[AI: {result['ai_verdict']}] Rule {result['rule_id']} — "
                      f"Confidence: {result['ai_confidence']}")

    except KeyboardInterrupt:
        logger.info("AI triage engine stopped by user")
        print("\nEngine stopped.")
    except Exception as e:
        logger.error(f"Watch error: {e}")


def main():
    logger = setup_logger()
    config = load_config()

    logger.info("=== AI Triage Engine Starting ===")
    print("AI Triage Engine starting...")
    print("Watching Project 3's enrichment output for alerts to triage...")

    engine = TriageEngine(config)

    print("Engine ready.")
    print("Press Ctrl+C to stop.\n")

    watch_enriched_alerts(config, engine)

    logger.info("=== AI Triage Engine Stopped ===")


if __name__ == "__main__":
    main()
