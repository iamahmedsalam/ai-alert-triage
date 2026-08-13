# 🧠 AI-Augmented Alert Triage for Wazuh SIEM

**A structured, tested, cost-measured AI reasoning layer that triages enriched SIEM alerts using Claude — with a proven, structurally-verified human-in-the-loop safety boundary.**

> Built by [Ahmed Salam](https://iamahmedsalam.com) — AI-Augmented SOC Analyst | CompTIA Security+ | TryHackMe Top 2%

---

## What This Project Proves

Automated detection tells you *something* fired. Automated enrichment tells you *what the data says*. This project adds the third layer — an LLM that reasons about what the alert and enrichment data actually *mean*, the way a Tier 1 analyst would, and explains its reasoning in plain language.

Critically, this is not an autonomous agent. The AI recommends; it cannot act. That boundary is proven structurally in this repo — not claimed in documentation, but verifiable with a single `grep` command against the actual codebase.

---

## Architecture

```
Wazuh Alert → Project 3's Enrichment Engine (unmodified)
                       ↓ writes enrichment_alerts.json
              Project 4's AI Triage Engine (standalone process)
                       ↓ reads Project 3's output only — never writes to it
              Structured prompt → Claude Sonnet 5 → parsed verdict
                       ↓
              Wazuh Rules 100017–100020 (dashboard alert, informational)

Containment (iptables) remains EXCLUSIVELY in Project 3's deterministic
verdict logic. Project 4 contains zero subprocess/iptables code.
```

Full write-up: [`architecture/ai-triage-architecture.md`](architecture/ai-triage-architecture.md)

---

## Key Findings

- **A real API integration bug found and fixed** — Claude's response can return a `ThinkingBlock` before the text answer; naive `response.content[0].text` access crashes. Fixed by filtering content blocks by type.
- **A ground-truth labeling error caught through the measurement process itself** — two functionally identical test cases had inconsistent human-assigned labels; corrected transparently rather than silently, with the reasoning documented in the dataset.
- **Honest accuracy result: 70% raw agreement, 100% on evidence-matched cases, zero dangerous errors** across a deliberately hard 10-case ground-truth set (see [Phase D findings](docs/lessons-learned.md)).
- **The human-in-the-loop boundary is structurally proven** — `grep -rn "iptables|subprocess" src/` against the entire codebase returns zero matches. The AI cannot execute containment; it can only recommend.
- **Real operational cost measured, not estimated** — 5.07s average latency, $0.0049/alert, ~$14.74/month at 100 alerts/day.
- **A cross-project field-naming collision found and fixed** — Project 4's output initially collided with Project 3's Rule 100012, resolved without touching Project 3's code.

---

## Repository Structure

```
ai-alert-triage/
├── README.md
├── architecture/
│   └── ai-triage-architecture.md
├── ai-triage-engine/
│   ├── src/
│   │   ├── config.py
│   │   ├── logger.py
│   │   ├── triage_engine.py       — core orchestration + threshold gate
│   │   ├── prompt_builder.py      — structured prompt construction
│   │   ├── response_parser.py     — regex-based verdict extraction
│   │   ├── main.py                — standalone watcher (reads Project 3's output)
│   │   └── clients/
│   │       └── anthropic_client.py
│   ├── tests/                     — 16 automated pytest tests
│   ├── ground_truth/
│   │   ├── historical_cases.json  — 5 cases from Projects 1-3
│   │   └── fresh_cases.json       — 5 deliberately hard constructed cases
│   ├── config/config.yaml.example
│   ├── run_accuracy_test.py
│   ├── run_latency_test.py
│   └── requirements.txt
├── detection-rules/
│   └── ai-triage-rules.xml        — Rules 100017–100020
├── live-drills/
│   ├── drill-001-realtime-triage.md
│   ├── drill-002-ambiguous-verdict-reasoning.md
│   ├── drill-003-human-in-the-loop-boundary.md   ← the key safety proof
│   └── drill-004-cost-latency.md
├── detection-improvements/
│   └── rule-tuning-log.md
├── docs/
│   └── lessons-learned.md         ← full accuracy investigation story
└── screenshots/
```

---

## Live Drills

| Drill | Tests | Outcome |
|---|---|---|
| [Drill 1](live-drills/drill-001-realtime-triage.md) | Full pipeline, live attack | Correct filtering before wasted AI calls |
| [Drill 2](live-drills/drill-002-ambiguous-verdict-reasoning.md) | AI value-add on ambiguous verdicts | Reasoning surfaces specific context beyond raw label |
| [Drill 3](live-drills/drill-003-human-in-the-loop-boundary.md) | **Safety boundary proof** | Zero containment code, structurally verified |
| [Drill 4](live-drills/drill-004-cost-latency.md) | Real operational metrics | 5.07s latency, $0.0049/alert |

---

## Accuracy Measurement

10-case hybrid ground truth (5 historical Projects 1-3 findings + 5 fresh constructed edge cases), measured against Claude's live triage output:

| Metric | Result |
|---|---|
| Raw agreement | 70% (7/10) |
| Agreement on evidence-matched cases | 100% |
| Dangerous errors (AI clearing a real threat) | 0 |
| Ground-truth labeling errors found & corrected | 1 (documented transparently) |

Full investigation and reasoning: [`docs/lessons-learned.md`](docs/lessons-learned.md)

---

## Relationship to Prior Projects

| | Project 1 | Project 2 | Project 3 | Project 4 — This Repo |
|---|---|---|---|---|
| **Focus** | Build detection | Respond to detections | Enrich & auto-contain | Reason about enriched alerts |
| **Proves** | Can you detect? | Can you investigate? | Can you decide, automatically? | Can you augment human judgment safely? |
| **Language** | Wazuh rules (XML) | Markdown playbooks | Production Python | Production Python + LLM integration |
| **Action taken** | Alert | Documented response | Automated containment | **None — advisory only, by design** |

---

## About

**Ahmed Salam** — AI-Augmented SOC Analyst

- 🏆 TryHackMe Top 2% Globally (132 rooms, 30 badges)
- 🎓 CompTIA Security+ Certified
- 🌐 Portfolio: [iamahmedsalam.com](https://iamahmedsalam.com)
- 🐙 GitHub: [iamahmedsalam](https://github.com/iamahmedsalam)

---

## License

MIT License — see [LICENSE](LICENSE) for details.
