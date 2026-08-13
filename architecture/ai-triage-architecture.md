# AI Triage Architecture

## The Core Decision: Decoupled, Advisory-Only Design

Project 4 was deliberately built as a **standalone service that only reads** Project 3's output — it never modifies Project 3's code, never writes to any file Project 3 reads from, and structurally has no code path to execute any containment action.

```
Wazuh Alert fires
       ↓
Project 3's Enrichment Engine (unchanged, unmodified)
  → correlates IP/hash against MISP, OTX, AbuseIPDB
  → writes verdict to enrichment_alerts.json
  → applies direct iptables block if verdict == BLOCK
       ↓
Project 4's AI Triage Engine (standalone process)
  → independently tails enrichment_alerts.json (read-only)
  → reconstructs an alert+enrichment context from that output
  → builds a structured prompt, calls Claude API
  → parses verdict/confidence/reasoning from the response
  → writes result to ai_triage_alerts.json
       ↓
Wazuh Rules 100017-100020 surface the AI's verdict as a
dashboard alert — informational only, no automated action
```

## Why Option B (Standalone) Over Integration

Two architectures were considered during planning:

- **Option A** — integrate AI triage directly into Project 3's `EnrichmentEngine`, one pipeline, one process.
- **Option B** — a fully separate process that only consumes Project 3's output.

**Option B was chosen** for three reasons, validated during the build:

1. **Blast radius containment.** If Project 4 crashes, hangs, or the Claude API is slow/down, Project 3's detection and containment pipeline is completely unaffected — proven directly in Phase E's Drill 3, where `grep -rn "iptables|subprocess" src/` against Project 4's entire codebase returned zero matches.
2. **Independent verifiability.** Project 3 was already a complete, shipped, tested project. Modifying its core `main.py` to add AI calls would have risked regressions in already-proven code. Project 4 only reads a file Project 3 already produces.
3. **Realistic SOC architecture.** In production, enrichment and AI-assisted triage are typically genuinely separate services, sometimes owned by different teams. This mirrors that reality rather than a monolithic script.

## The Human-in-the-Loop Boundary

This is the single most important design decision in the project. Project 3's `EnrichmentEngine` contains real containment code — `subprocess` calls to `/sbin/iptables`, triggered automatically when a deterministic, multi-source-verified BLOCK verdict is reached. Project 4's `TriageEngine` contains **no equivalent code at all**.

The AI can recommend "isolate this endpoint immediately" with HIGH confidence — and that recommendation goes no further than a log line and a Wazuh dashboard alert (Rule 100020). This is not a policy decision that could be toggled by mistake; it is a structural fact, verifiable with a single `grep` command, documented and proven in Live Drill 3.

**Why this boundary matters:** LLMs can be wrong, can hallucinate, and their confidence calibration doesn't always match their actual accuracy (see `docs/lessons-learned.md` for the accuracy measurement findings). Anything with a real-world consequence — a firewall change, an account lockout — stays deterministic and rule-based. The AI's role is strictly to accelerate *human* decision-making with better-reasoned context, never to make the decision itself.

## Field-Naming Collision (A Real Cross-Project Bug)

During Phase C integration, Project 4's output initially used the field name `enrichment_ip` — the same name Project 3's Rule 100012 matches on (`<field name="enrichment_ip">\.+</field>`, matching *any* JSON log containing that field, regardless of source file). This caused Project 3's own rule to silently claim Project 4's alerts before Rule 100017 was ever evaluated. Renamed to `triage_source_ip` to eliminate the collision. Documented in full in `docs/lessons-learned.md` — a genuine example of the kind of integration bug that only surfaces when two independently-built systems are actually connected.

## Cost & Latency Design Considerations

Because the AI triage step is asynchronous and decoupled from Project 3's real-time containment action, its ~5-second average latency (measured in Live Drill 4) has zero impact on actual threat response time. This was an intentional consequence of the Option B decision, not an accident — the AI never sits in the critical path of blocking a threat.
