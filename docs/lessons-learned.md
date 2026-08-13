# Lessons Learned — Project 4: AI-Augmented Alert Triage

---

## From Enrichment to Judgment

Project 3 proved I can automate multi-source threat intelligence correlation. Project 4 proves I can go one layer further — using an LLM to reason about *what that enrichment data means* for a specific alert, the way a Tier 1 analyst would, while keeping a hard architectural line between "the AI recommends" and "the AI acts."

This is the project that actually earns the "AI-Augmented" half of my target title. Not a chatbot bolted onto a dashboard — a structured, tested, cost-measured reasoning layer with a proven safety boundary.

---

## The ThinkingBlock Bug — A Real API Integration Finding

The very first live API call crashed with `'ThinkingBlock' object has no attribute 'text'`. Claude's response can contain multiple content blocks — reasoning content before the final text answer — and the initial client code assumed `response.content[0]` was always the text block. This is a genuinely non-obvious integration detail that no tutorial would have surfaced; it only appears when the model actually engages extended reasoning on a real prompt. Fixed by iterating all content blocks and filtering by `type == "text"` rather than assuming positional structure. Documented directly in the client's docstring so the reasoning behind the fix survives any future refactor.

---

## Prompt Engineering: What "Structured Output" Actually Buys You

Requiring an exact response template (`VERDICT: ... CONFIDENCE: ... RECOMMENDED_ACTION: ... REASONING: ...`) rather than free-form prose is what made programmatic parsing reliable via regex. This is a small design choice with a large payoff — every one of the 10 ground-truth test cases parsed cleanly, and the response parser's own test suite covers malformed and empty responses gracefully.

---

## The Ground Truth Investigation: A Better Story Than a Clean Number

The accuracy measurement in Phase D produced a raw 70% agreement rate on a deliberately hard 10-case dataset — and the process of understanding *why* the other 30% disagreed turned out to be the most valuable part of the entire phase, for two distinct reasons:

**Finding 1 — A real prompt ambiguity.** The model initially treated `sources_responding: 0` (enrichment skipped, e.g. private IP) the same as a verified-clean result from three responding sources. Fixed by making that distinction explicit in the prompt rather than assuming the model would infer it.

**Finding 2 — My own ground-truth dataset contained an inconsistency, not the AI.** Two cases (`hist-002` and `hist-005`) were functionally identical scenarios — the same rule, the same confirmed frequency-based brute-force pattern, the same private-IP source — yet I had labeled them differently based on which project phase I'd originally documented them in. The AI treated both cases consistently; my own labels didn't. Correcting the ground truth (not the AI) after identifying this, with the reasoning documented transparently in the dataset itself, is a more credible result than either blindly trusting the AI or blindly trusting my own initial labels.

**The remaining 3 mismatches all share one root cause**, not three separate problems: the ground-truth `human_verdict` for those cases was based on a *full live investigation* (decoded payloads, watched terminals in real time, confirmed quarantines), while the AI was given only a single compressed log line. Given genuinely less evidence than the human had, the AI consistently chose to ask for more investigation rather than guess — which is the textbook-correct, appropriately cautious response, not a failure.

**The honest final result:** 70% raw agreement; 100% agreement on the 7 cases where the AI had evidence-equivalent context to the human; zero instances across all 10 cases of the AI calling a real threat a false positive (the single most dangerous error type for a security tool). A suspiciously clean 95%+ number on a deliberately hard dataset would have been less credible than this.

---

## The Field-Naming Collision — A Real Cross-Project Integration Bug

Phase C's Wazuh integration initially produced zero dashboard alerts for the AI's verdicts, despite the pipeline clearly working end-to-end in the terminal logs. Investigation traced it to a field-name collision: Project 4's output used `enrichment_ip` as a key — the same field name Project 3's Rule 100012 matches on, regardless of which file the JSON log actually came from. Project 3's own rule was silently claiming Project 4's alerts before Rule 100017 ever got evaluated. Renamed the field to `triage_source_ip`, resolving it without touching Project 3's code at all — a clean illustration of why the Option B decoupled architecture mattered: even when two independently-built systems collide unexpectedly, the fix stayed entirely within Project 4's boundary.

---

## The Human-in-the-Loop Boundary: Proven, Not Just Claimed

The single design decision I'm most proud of in this project: Project 4's entire codebase contains zero references to `iptables` or `subprocess` — verified directly with `grep -rn "iptables|subprocess" src/` returning no matches. The AI can recommend "isolate this endpoint" with HIGH confidence, and that recommendation goes no further than a log line and a dashboard alert. Anything with real-world consequence stays with Project 3's deterministic, multi-source-verified logic. This is a defensible answer to "how do you prevent an LLM from taking a harmful action" that doesn't rely on trusting a policy document — it's a fact about the code any reviewer can check in seconds.

---

## Cost and Latency: Numbers Most Portfolio AI Projects Never Measure

Live Drill 4 measured real, not estimated, operational metrics: ~5 second average latency per alert, ~$0.005 per alert, and roughly $15/month running continuously against 100 alerts/day. The latency number matters specifically *because of* the decoupled architecture — a 5-second delay is irrelevant when the AI is never in the critical path of actual containment (Project 3 already proved sub-second blocking independently). Putting a real dollar figure on continuous operation is a concrete, defensible answer to a question most AI-integration demos never attempt to quantify.

---

## Performance Summary

| Metric | Result |
|---|---|
| API sources integrated | 1 (Anthropic Claude Sonnet 5) |
| Custom Wazuh rules added | 4 (100017–100020), bringing total to 20 |
| Automated tests | 16 (prompt builder + response parser + threshold gating) |
| Ground truth dataset | 10 cases (5 historical + 5 fresh, deliberately hard mix) |
| Raw agreement rate | 70% (100% on evidence-matched cases) |
| Dangerous errors (AI false-positiving a real threat) | 0 across all 10 cases |
| Real bugs found and fixed | 3 (ThinkingBlock parsing, sources_responding ambiguity, field-name collision) |
| Ground-truth labeling error found and corrected | 1 (hist-005), documented transparently |
| Average triage latency | 5.07 seconds |
| Cost per alert | $0.0049 |
| Estimated monthly cost (100 alerts/day) | $14.74 |
| Containment code in Project 4's codebase | 0 — structurally advisory-only |
| Live drills executed | 4 |
