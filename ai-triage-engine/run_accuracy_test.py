import json
import time
import yaml
from src.triage_engine import TriageEngine
from src.logger import setup_logger

logger = setup_logger()

with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

# Lower the threshold so every ground-truth case gets triaged regardless
# of its rule level - this test is about accuracy, not the cost gate
config["thresholds"]["min_rule_level_for_ai_triage"] = 0

engine = TriageEngine(config)

with open("ground_truth/historical_cases.json") as f:
    historical = json.load(f)

with open("ground_truth/fresh_cases.json") as f:
    fresh = json.load(f)

all_cases = historical + fresh

results = []
correct = 0
total_input_tokens = 0
total_output_tokens = 0

print(f"Running accuracy test against {len(all_cases)} ground truth cases...\n")

for case in all_cases:
    print(f"Testing {case['case_id']} ({case['source']})...")

    ai_result = engine.triage_alert(case["alert"], case.get("enrichment"))

    if ai_result is None:
        print(f"  SKIPPED (below threshold or API error)\n")
        continue

    ai_verdict = ai_result["ai_verdict"]
    human_verdict = case["human_verdict"]
    match = ai_verdict == human_verdict

    if match:
        correct += 1

    total_input_tokens += ai_result["tokens_used"]["input_tokens"]
    total_output_tokens += ai_result["tokens_used"]["output_tokens"]

    results.append({
        "case_id": case["case_id"],
        "source": case["source"],
        "human_verdict": human_verdict,
        "ai_verdict": ai_verdict,
        "ai_confidence": ai_result["ai_confidence"],
        "match": match,
        "ai_reasoning": ai_result["reasoning"],
        "human_reasoning": case["human_reasoning"]
    })

    status = "MATCH" if match else "MISMATCH"
    print(f"  Human: {human_verdict} | AI: {ai_verdict} | {status}\n")

    time.sleep(1)

accuracy = (correct / len(results)) * 100 if results else 0

print("=" * 60)
print(f"RESULTS: {correct}/{len(results)} correct ({accuracy:.1f}% agreement)")
print(f"Total tokens used: {total_input_tokens} in / {total_output_tokens} out")
print("=" * 60)

with open("logs/accuracy_results.json", "w") as f:
    json.dump({
        "total_cases": len(results),
        "correct": correct,
        "accuracy_percent": round(accuracy, 1),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "results": results
    }, f, indent=2)

print("\nFull results saved to logs/accuracy_results.json")

mismatches = [r for r in results if not r["match"]]
if mismatches:
    print(f"\n{len(mismatches)} MISMATCH(ES) — worth reviewing:")
    for m in mismatches:
        print(f"\n  {m['case_id']}: Human said {m['human_verdict']}, AI said {m['ai_verdict']}")
        print(f"  AI reasoning: {m['ai_reasoning'][:200]}...")
