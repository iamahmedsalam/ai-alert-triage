import time
import yaml
from src.triage_engine import TriageEngine
from src.logger import setup_logger

logger = setup_logger()

with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

config["thresholds"]["min_rule_level_for_ai_triage"] = 0

engine = TriageEngine(config)

test_alerts = [
    {
        "name": "SSH Brute Force (Rule 100011)",
        "alert": {
            "rule": {"id": "100011", "level": 12, "description": "CRITICAL: SSH brute force attack confirmed"},
            "agent": {"name": "ubuntu-soc-agent"},
            "full_log": "Failed password for invalid user fakeuser from 192.168.56.50"
        },
        "enrichment": {"verdict": "CLEAN", "sources_responding": 0, "summary": {"abuse_score": 0, "otx_pulses": 0, "misp_matched": False}}
    },
    {
        "name": "C2 Callback BLOCK (Rule 92050)",
        "alert": {
            "rule": {"id": "92050", "level": 10, "description": "Simulated: Suspicious outbound network connection detected"},
            "agent": {"name": "WIN11-SOC-Endpoint"},
            "full_log": "Outbound connection to 45.148.10.151"
        },
        "enrichment": {"verdict": "BLOCK", "sources_responding": 3, "summary": {"abuse_score": 100, "otx_pulses": 50, "misp_matched": False}}
    },
    {
        "name": "Registry Persistence (Rule 100004)",
        "alert": {
            "rule": {"id": "100004", "level": 10, "description": "Registry persistence detected - Run key modification"},
            "agent": {"name": "WIN11-SOC-Endpoint"},
            "full_log": "reg.exe added HKLM Run key pointing to C:\\Users\\Public\\update.exe"
        },
        "enrichment": {"verdict": "REVIEW", "sources_responding": 3, "summary": {"abuse_score": 55, "otx_pulses": 1, "misp_matched": False}}
    }
]

print("Running latency + cost test across 3 alert types...\n")

total_latency = 0
total_input_tokens = 0
total_output_tokens = 0

for test in test_alerts:
    print(f"Testing: {test['name']}")

    start = time.time()
    result = engine.triage_alert(test["alert"], test["enrichment"])
    end = time.time()

    latency = end - start
    total_latency += latency

    if result:
        tokens = result["tokens_used"]
        total_input_tokens += tokens["input_tokens"]
        total_output_tokens += tokens["output_tokens"]

        print(f"  Verdict: {result['ai_verdict']} ({result['ai_confidence']})")
        print(f"  Latency: {latency:.2f}s")
        print(f"  Tokens: {tokens['input_tokens']} in / {tokens['output_tokens']} out")
    print()

    time.sleep(1)

avg_latency = total_latency / len(test_alerts)

# Claude Sonnet 5 pricing: $3/M input tokens, $15/M output tokens
input_cost = (total_input_tokens / 1_000_000) * 3
output_cost = (total_output_tokens / 1_000_000) * 15
total_cost = input_cost + output_cost
cost_per_alert = total_cost / len(test_alerts)

print("=" * 60)
print(f"Average latency per alert: {avg_latency:.2f}s")
print(f"Total tokens: {total_input_tokens} in / {total_output_tokens} out")
print(f"Estimated cost for this run: ${total_cost:.4f}")
print(f"Estimated cost per alert: ${cost_per_alert:.4f}")
print(f"Estimated monthly cost at 100 alerts/day: ${cost_per_alert * 100 * 30:.2f}")
print("=" * 60)
