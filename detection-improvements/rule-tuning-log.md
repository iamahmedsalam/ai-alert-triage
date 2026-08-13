# Detection Improvements — Rule Tuning Log (Project 4)

Improvements identified through building and validating the AI triage layer across Phases A–E.

---

## New Capabilities Built

### Custom Rules 100017–100020 (AI Triage Verdict Tiers)
Four new Wazuh rules turning the AI's structured triage response into dashboard alerts, scaled by verdict:
- 100017 (Level 3) — base "AI triage result received"
- 100018 (Level 6) — NEEDS_INVESTIGATION
- 100019 (Level 4) — FALSE_POSITIVE
- 100020 (Level 12) — TRUE_POSITIVE

Custom rule count: 16 (end of Project 3) → **20**.

### Structured Prompt Template
A strict `VERDICT / CONFIDENCE / RECOMMENDED_ACTION / REASONING` response format that made regex-based parsing reliable across all 10 ground-truth test cases and every live drill.

---

## Prompt Engineering Improvements

### Explicit Handling of sources_responding = 0
Identified during Phase D accuracy testing (case `hist-005`): the model initially conflated "0 sources responded because enrichment was skipped" with "sources responded and came back clean." Fixed by adding an explicit note to the prompt whenever `sources_responding == 0`, distinguishing a skipped lookup from a verified-clean result.

---

## Recommended Future Improvements

### Feed Full Investigation Context, Not Just the Alert Summary
Phase D's remaining 3 mismatches all traced to one root cause: the AI was given a single compressed log line, while the human ground-truth verdict was based on a full live investigation (decoded payloads, confirmed quarantines, real-time terminal observation). A future iteration could feed the AI a richer context object — e.g. linked playbook steps already completed, or prior related alerts from the same agent within a time window — closing the evidence gap that caused the AI to appropriately-but-conservatively ask for more investigation.

### Confidence-Weighted Escalation
Currently all TRUE_POSITIVE verdicts trigger the same Rule 100020 regardless of stated confidence (LOW/MEDIUM/HIGH). A future rule could differentiate — e.g., only HIGH-confidence TRUE_POSITIVE verdicts trigger an immediate notification, while MEDIUM/LOW confidence verdicts queue for batch review — reducing alert fatigue while preserving the human-in-the-loop principle.

### Ground Truth Dataset Expansion
The current 10-case dataset deliberately weights toward hard/ambiguous cases. Expanding it with more constructed false-positive scenarios (misconfigurations, authorized automation, known benign artifacts like the PowerShell Script Policy Test pattern) would sharpen the FALSE_POSITIVE detection measurement specifically, since only 2 of the current 10 cases test that category.

---

## Architectural Improvement: Field-Naming Discipline Across Projects

**Finding:** Project 4's output initially used `enrichment_ip` as a field name, which collided with Project 3's Rule 100012 (matches on any JSON log containing that field, regardless of source file). Project 3's rule silently claimed Project 4's alerts before Rule 100017 was ever evaluated.

**Resolution:** Renamed the field to `triage_source_ip`. No changes needed to Project 3's code or rules — the fix stayed entirely within Project 4's boundary, validating the value of the decoupled Option B architecture even when integration surprises occur.

**Recommendation for future projects:** when building a new component that reads or writes JSON consumed by an existing Wazuh rule set, explicitly check existing custom rule field-name patterns first (`grep '<field name=' local_rules.xml`) to avoid this class of collision before it happens rather than after.
