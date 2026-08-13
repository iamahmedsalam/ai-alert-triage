def build_triage_prompt(alert, enrichment=None):
    rule_id = alert.get("rule", {}).get("id", "unknown")
    rule_level = alert.get("rule", {}).get("level", 0)
    rule_desc = alert.get("rule", {}).get("description", "")
    agent_name = alert.get("agent", {}).get("name", "unknown")
    full_log = alert.get("full_log", "")

    enrichment_section = "No threat intelligence enrichment available for this alert."

    if enrichment:
        verdict = enrichment.get("verdict", "UNKNOWN")
        summary = enrichment.get("summary", {})
        sources_responding = enrichment.get("sources_responding", 0)

        # Fix identified during Phase D accuracy testing (case hist-005):
        # the model was treating "0 sources responded" the same as
        # "sources responded and came back clean" - conflating a
        # SKIPPED enrichment (e.g. private IP) with a VERIFIED-CLEAN
        # result. Made this distinction explicit rather than assuming
        # the model would infer it from the raw number alone.
        sources_note = ""
        if sources_responding == 0:
            sources_note = (" (IMPORTANT: 0 sources responded — this likely means "
                             "enrichment was SKIPPED, e.g. because the IP is private/"
                             "internal, NOT that all sources checked and came back clean. "
                             "Do not treat this the same as a verified-clean result.)")

        enrichment_section = f"""Threat Intelligence Enrichment:
- Verdict: {verdict}
- AbuseIPDB Score: {summary.get('abuse_score', 'N/A')}/100
- OTX Pulses: {summary.get('otx_pulses', 'N/A')}
- MISP Match: {summary.get('misp_matched', 'N/A')}
- Sources Responding: {sources_responding}/3{sources_note}"""

    prompt = f"""You are a Tier 1 SOC analyst assistant. Analyze this security alert and provide a triage recommendation.

ALERT DETAILS:
- Rule ID: {rule_id}
- Severity Level: {rule_level}
- Description: {rule_desc}
- Affected Agent: {agent_name}
- Raw Log: {full_log}

{enrichment_section}

Respond in EXACTLY this format, with no other text:

VERDICT: [TRUE_POSITIVE / FALSE_POSITIVE / NEEDS_INVESTIGATION]
CONFIDENCE: [LOW / MEDIUM / HIGH]
RECOMMENDED_ACTION: [one short sentence]
REASONING: [2-3 sentences explaining your assessment, referencing specific evidence from the alert and enrichment data above]"""

    return prompt
