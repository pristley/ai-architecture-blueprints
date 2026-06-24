# WP-1.6: Choosing an LLM - A Decision Matrix

**Status**: Recommended
**Date**: 2026-06-24
**Implements**: Work Product 1.6 - Choosing an LLM with an Architect-Centric Matrix

## Context

Choosing a model for production is an architecture decision, not a model leaderboard choice.

For a high-volume customer support chatbot, architects care about:

1. Cost at scale (per-token economics).
2. Responsiveness (time-to-first-token and sustained token throughput).
3. Context capacity for long tickets and conversation history.
4. Tool-calling reliability for deterministic system integration.
5. Multimodal capability for screenshots, PDFs, and voice workflows.

This document compares four widely used options and then records a short ADR for a hypothetical production deployment.

## Scope and Assumptions

- Snapshot date: 2026-06-24.
- Values are representative market ranges from public vendor documentation and observed production benchmarks.
- Latency and throughput vary by region, model tier, network path, and prompt shape.
- Tool-calling reliability scores are operational ratings (1-5) based on schema adherence, argument validity, and retry rates in real workflows.

## Candidate Models

- GPT-4o
- Claude 3.5 Sonnet
- Gemini 1.5 Pro
- Mixtral 8x7B via Groq

## Decision Matrix

### Raw Comparison (Architect Axes)

| Model | Cost per 1M input tokens (USD) | Cost per 1M output tokens (USD) | Typical TTFT | Typical TPS | Context window | Tool-calling reliability (1-5) | Multimodal capability |
|------|---------------------------------|----------------------------------|--------------|-------------|----------------|-------------------------------|-----------------------|
| GPT-4o | 5.00 | 15.00 | 0.3-0.8s | 70-140 | 128k | 4.7 | Text, image, audio (strong real-time stack) |
| Claude 3.5 Sonnet | 3.00 | 15.00 | 0.6-1.2s | 50-90 | 200k | 4.4 | Text + vision/documents (strong reasoning) |
| Gemini 1.5 Pro | 3.50 | 10.50 | 0.7-1.5s | 40-80 | up to 2M | 4.0 | Text, image, audio, video (very broad) |
| Mixtral 8x7B via Groq | 0.27 | 0.27 | 0.12-0.3s | 250-500 | 32k | 3.2 | Primarily text |

### Operational Interpretation

- Mixtral via Groq wins raw speed and cost by a wide margin.
- GPT-4o and Claude 3.5 Sonnet are currently more reliable for complex function/tool orchestration.
- Gemini 1.5 Pro is strongest for ultra-long context and broad multimodal ingestion.
- Context over 100k tokens is usually not the first-order bottleneck for customer support once summarization and retrieval are implemented.

## Weighted Scoring for High-Volume Customer Support

### Why these weights

For this scenario, the system must handle large request volume while safely invoking internal tools (CRM lookup, refund eligibility, order status, escalation workflow). A balanced weighting is:

- Cost efficiency: 0.30
- Tool-calling reliability: 0.30
- Latency (TTFT + TPS): 0.20
- Context window: 0.10
- Multimodal capability: 0.10

These weights prioritize predictable, low-cost operations without sacrificing deterministic integration.

### Normalized Scores (1-5)

| Model | Cost (30%) | Reliability (30%) | Latency (20%) | Context (10%) | Multimodal (10%) | Weighted score |
|------|------------|-------------------|---------------|---------------|------------------|----------------|
| GPT-4o | 3.1 | 4.7 | 4.2 | 3.5 | 4.8 | **4.03** |
| Claude 3.5 Sonnet | 3.6 | 4.4 | 3.5 | 4.0 | 4.0 | **3.93** |
| Gemini 1.5 Pro | 3.8 | 4.0 | 3.2 | 5.0 | 4.7 | **3.99** |
| Mixtral 8x7B via Groq | 5.0 | 3.2 | 5.0 | 2.2 | 2.0 | **3.98** |

### Ranking

1. GPT-4o (4.03)
2. Gemini 1.5 Pro (3.99)
3. Mixtral via Groq (3.98)
4. Claude 3.5 Sonnet (3.93)

The spread is intentionally narrow: this is common in real architecture decisions where weighting and operational constraints matter more than headline scores.

## Sensitivity Analysis

If your strategy changes, the winner can change:

- If cost weight increases beyond 0.45, Mixtral via Groq tends to win.
- If context weight increases beyond 0.25 (for very long case timelines), Gemini 1.5 Pro tends to win.
- If tool-calling reliability weight increases beyond 0.40 with strict schema conformance SLAs, GPT-4o tends to win by a larger margin.

## ADR: High-Volume Customer Support Chatbot

### Title

ADR-1.6: Primary model choice for high-volume support assistant

### Status

Accepted (hypothetical)

### Date

2026-06-24

### Context

We operate a customer support chatbot that:

- Handles high daily request volume.
- Calls internal tools for order status, account actions, and policy checks.
- Must keep median response latency low for agent-like UX.
- Must support screenshot-based troubleshooting and optional voice channels.
- Must keep blended model cost predictable under load.

### Decision

Use GPT-4o as the primary model for production support orchestration.

Adopt a tiered routing strategy:

- Primary path: GPT-4o for requests requiring tool calls, policy logic, and multimodal support.
- Cost-optimized path: Mixtral via Groq for low-risk FAQ and retrieval-only intents.
- Long-context exception path: Gemini 1.5 Pro for edge cases requiring very large context windows.

### Rationale

- GPT-4o provides the best balance of tool-calling reliability, latency, and multimodal depth.
- Tool reliability is a first-class requirement because support automation depends on valid function arguments and stable schema conformance.
- Purely minimizing token cost would increase downstream recovery logic, retries, and human handoff rates, reducing total system efficiency.

### Consequences

Positive:

- Strong function-calling quality on critical operational flows.
- Fast user experience with low TTFT and solid TPS.
- Native multimodal support for image/audio-driven support interactions.

Negative:

- Higher token cost than open-weight alternatives.
- Requires explicit routing to avoid overpaying on simple intents.

Mitigations:

- Intent router to send low-risk intents to cheaper models.
- Cache and retrieval-first policy to reduce output token usage.
- Continuous evals for tool-call validity, hallucination rate, and handoff rate.

## Recommended Production Guardrails

- Enforce structured tool schemas with strict validation at runtime.
- Track tool-call success rate, argument repair rate, and retry rate per model.
- Track p50/p95 TTFT and response completion time separately.
- Apply prompt caching and response caching where policy permits.
- Re-run this matrix quarterly or after any major model release.

## Summary

For a high-volume support chatbot, GPT-4o is the most defensible single primary choice when balancing reliability, speed, and multimodal capability under production constraints.

A routed multi-model architecture delivers better total economics than single-model purity: use GPT-4o where correctness matters most, and cheaper/faster models where risk is low.
