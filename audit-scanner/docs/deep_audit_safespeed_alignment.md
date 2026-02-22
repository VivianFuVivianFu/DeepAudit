# Deep-Audit × Safe Speed Alignment

## Overview

This document maps Deep-Audit findings to the Safe Speed governance framework's four protection layers. It identifies current coverage, gaps, and provides a phased rollout plan for enterprises adopting Safe Speed based on Deep-Audit audit results.

**Document Version:** 2.0.0
**Last Updated:** 2026-02-22

---

## Safe Speed Layer Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Layer 4: Observability & Drift              │
│          (Continuous monitoring, metric dashboards, alerts)     │
├────────────────────────────────────────────────────────────────┤
│                    Layer 3: Runtime Enforcement                │
│         (Input/output guardrails, PII filters, blocklists)     │
├────────────────────────────────────────────────────────────────┤
│                    Layer 2: Policy & Governance                │
│        (Approval workflows, escalation, audit trails)          │
├────────────────────────────────────────────────────────────────┤
│                    Layer 1: Foundation & Identity              │
│       (Auth, RBAC, API gateways, secrets management)           │
└────────────────────────────────────────────────────────────────┘
```

---

## Current Coverage by Layer

### Layer 1: Foundation & Identity (~15% coverage)

| Deep-Audit Capability | Coverage | Gap |
|----------------------|----------|-----|
| API authentication testing | ✅ Basic | No RBAC enumeration |
| Secret exposure detection | ✅ System prompt extraction | Limited to prompt-based |
| Gateway bypass testing | ❌ Not covered | Need direct gateway probes |

**Recommendation:** Expand attack library with API key rotation, RBAC boundary, and gateway bypass test cases.

### Layer 2: Policy & Governance (~25% coverage)

| Deep-Audit Capability | Coverage | Gap |
|----------------------|----------|-----|
| Policy bypass detection | ✅ ACT-002 urgency claims | No workflow approval testing |
| Escalation testing | ✅ ACT-001 unauthorized refund | No manager-escalation flows |
| Audit trail validation | ✅ Evidence pack + encrypted store | No external audit log integration |

**Recommendation:** Add attack cases for policy circumvention via multi-step conversations and role escalation chains.

### Layer 3: Runtime Enforcement (~70% coverage)

| Deep-Audit Capability | Coverage | Gap |
|----------------------|----------|-----|
| Injection attacks | ✅ 4 cases (INJ-001 to 004) | Strong |
| Hallucination detection | ✅ 4 cases (HAL-001 to 004) | Strong |
| PII leak detection | ✅ 4 cases (PII-001 to 004) | Strong |
| Action abuse detection | ✅ 4 cases (ACT-001 to 004) | Strong |
| Output sanitization | ✅ PII redactor in pipeline | ✅ |
| Input validation | ✅ Delimiter injection testing | ✅ |

**This is Deep-Audit's strongest layer.** The 16 attack cases, LLM judge evaluation, and evidence pack pipeline provide comprehensive runtime enforcement testing.

### Layer 4: Observability & Drift (~5% coverage)

| Deep-Audit Capability | Coverage | Gap |
|----------------------|----------|-----|
| Consistency measurement | ✅ 3x repetition per attack | Limited to session-level |
| Drift detection | ⚠️ Baseline comparison available | No longitudinal tracking |
| Metric dashboards | ❌ Not covered | Need integration API |
| Alert triggers | ❌ Not covered | Need webhook/notification support |

**Recommendation:** Add CI/CD integration for longitudinal drift tracking across deployments.

---

## Failure-to-Layer Mapping

Each Deep-Audit finding maps to a Safe Speed protection layer, enabling targeted remediation.

| Attack Category | Primary Layer | Secondary Layer | Safe Speed Profile |
|----------------|---------------|-----------------|-------------------|
| Injection (INJ-*) | Layer 3 (Runtime) | Layer 1 (Foundation) | `strict-runtime` |
| Hallucination (HAL-*) | Layer 3 (Runtime) | Layer 4 (Observability) | `grounded-runtime` |
| PII Leak (PII-*) | Layer 3 (Runtime) | Layer 2 (Policy) | `pii-guarded` |
| Action Abuse (ACT-*) | Layer 2 (Policy) | Layer 3 (Runtime) | `action-controlled` |

---

## Recommended Safe Speed Profiles

Based on Deep-Audit findings, the readiness engine (`readiness/engine.py`) outputs one of these profiles:

### Profile: `strict-runtime`
- **Triggered by:** Injection failures ≥ 2 or any severity-5 injection
- **Configuration:** Maximum input sanitization, output filtering, system prompt isolation
- **Estimated risk reduction:** 60-80%

### Profile: `grounded-runtime`
- **Triggered by:** Hallucination failures ≥ 2
- **Configuration:** Fact-checking layer, citation requirements, confidence thresholds
- **Estimated risk reduction:** 40-60%

### Profile: `pii-guarded`
- **Triggered by:** Any PII leak failure
- **Configuration:** PII detection on all outputs, data masking, retention policies
- **Estimated risk reduction:** 70-90%

### Profile: `action-controlled`
- **Triggered by:** Action abuse failures ≥ 1
- **Configuration:** Action approval workflows, rate limiting, human-in-the-loop for destructive ops
- **Estimated risk reduction:** 50-70%

---

## 90-Day Rollout Plan

### Phase 1: Assessment (Days 1-14)
- Run Deep-Audit full scan against production AI endpoints
- Generate evidence pack and executive report
- Map findings to Safe Speed layers using this document
- Identify `recommended_safe_speed_profile` from readiness engine

### Phase 2: Layer 3 Deployment (Days 15-45)
- Deploy runtime guardrails based on profile
- Implement PII redaction pipeline
- Configure injection detection rules
- **Validation:** Re-run Deep-Audit to confirm failure rate reduction

### Phase 3: Layer 2 Integration (Days 46-70)
- Implement approval workflows for high-risk actions
- Configure escalation policies for flagged interactions
- Set up audit trail integration
- **Validation:** Re-run ACT-* attack cases with baseline comparison

### Phase 4: Observability (Days 71-90)
- Enable continuous monitoring dashboard
- Configure drift alerts on safety score changes
- Set up automated weekly Deep-Audit scans
- Establish baseline comparison pipeline
- **Validation:** Compare longitudinal safety scores

---

## Evidence Pack Integration

The Deep-Audit evidence pack (`evidence_pack.py`) includes Safe Speed mapping:

```json
{
  "header": { "tool": "deep-audit", "version": "2.0.0" },
  "privacy": { "store_raw": false, "redacted": true },
  "scoring": { "overall_score": 72, "scoring_version": "1.0.0" },
  "safe_speed_mapping": {
    "recommended_profile": "pii-guarded",
    "layer_coverage": { "L1": 0.15, "L2": 0.25, "L3": 0.70, "L4": 0.05 }
  },
  "cases": [ ... ]
}
```

---

## Gap Analysis Summary

| Priority | Gap | Impact | Effort |
|----------|-----|--------|--------|
| **High** | Layer 4 observability integration | No drift detection | Medium |
| **Medium** | Layer 1 RBAC testing | Limited identity coverage | High |
| **Medium** | Layer 2 workflow testing | Policy bypass gaps | Medium |
| **Low** | Multi-turn conversation attacks | Single-turn only currently | High |
| **Low** | Webhook/notification support | No automated alerts | Low |

---

**Document Status:** Approved for production deployment
**Next Review:** After Phase 1 completion (~Day 14)
