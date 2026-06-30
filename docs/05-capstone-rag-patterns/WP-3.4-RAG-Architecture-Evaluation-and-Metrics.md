# Work Product 3.4: RAG Architecture — Evaluation & Metrics

**Measuring RAG Quality and Debugging Failures**

---

## 1. Executive Summary

Evaluation is critical for RAG systems. Without measurement, you cannot:
- Detect degradation in production
- Know which RAG pattern to use (naive vs reranking vs hierarchical vs agentic)
- Validate that optimization efforts worked
- Debug failures reliably

This work product provides a **general evaluation framework** applicable to any RAG architecture. You'll learn to measure retrieval quality, answer quality, cost, and latency — then use this data to iterate intelligently.

### Key Outcomes

By the end of this WP, you will:
- Understand the complete evaluation lifecycle (metrics → datasets → comparison → iteration)
- Implement retrieval evaluation (precision, recall, MRR, NDCG)
- Implement answer evaluation (relevance, completeness, hallucination detection)
- Measure citation accuracy and source attribution
- Profile latency at each stage
- Calculate cost per query and per task
- Compare RAG architectures quantitatively
- Set monitoring thresholds for production
- Debug failures using evaluation data

### Time & Difficulty

- **Time:** 2.5 hours
- **Difficulty:** Medium (some LLM integration, but straightforward metrics)
- **Prerequisites:** Completed WP-3.1, WP-3.2, or WP-3.3

---

## 2. The Evaluation Problem

### Why Evaluation Matters

**Without metrics, you're blind:**

```
Scenario A: "My RAG is great!"
Reality: Accuracy 45% (hallucinations, wrong sources)

Scenario B: "Should I use reranking?"
Without data: Guess and waste $2K/month on unnecessary reranking
With data: See that WP-3.2 adds 25 pp accuracy for $0.05/query

Scenario C: "Production latency spiked"
Without metrics: Blame the model, add servers, waste $5K/month
With data: See that semantic search slowed 200ms (database issue)
```

### The Evaluation Lifecycle

```
1. COLLECT
   ↓
   Run RAG on benchmark dataset
   Record: retrieval results, answers, latency, cost
   ↓
2. MEASURE
   ↓
   Calculate metrics (precision, recall, relevance, cost)
   Build comparison table
   ↓
3. DEBUG
   ↓
   Find failure patterns (wrong retrieval? poor ranking?)
   Identify which queries fail
   ↓
4. ITERATE
   ↓
   Try new approach (reranking, different chunking, etc.)
   Re-measure and compare
   ↓
5. DEPLOY
   ↓
   Set monitoring thresholds
   Alert if metrics degrade
```

### Metrics Hierarchy

```
COST per query
    ↓
LATENCY (total and per-stage)
    ↓
ANSWER QUALITY
    ├─ Relevance (does answer address query?)
    ├─ Completeness (comprehensive?)
    └─ Hallucination (made-up facts?)
    ↓
RETRIEVAL QUALITY
    ├─ Precision (top-k relevant?)
    ├─ Recall (find all relevant docs?)
    ├─ MRR (how far to first relevant?)
    └─ NDCG (ranking quality?)
    ↓
CITATION ACCURACY
    ├─ Source attribution (cited docs actually used?)
    └─ Claim traceability (can find claims in sources?)
```

---

## 3. Retrieval Evaluation Metrics

### The Retrieval Evaluation Problem

Given a query, your RAG system retrieves k documents. How good are those documents?

### Metrics Overview

| Metric | Formula | Interpretation | Best For |
|--------|---------|-----------------|----------|
| **Precision@k** | (relevant docs in top-k) / k | Of top-k results, % relevant? | Quick sanity check |
| **Recall@k** | (relevant in top-k) / (total relevant) | Of all relevant, % found? | Comprehensive retrieval |
| **MRR** | 1 / (rank of first relevant) | How far to first relevant? | One-shot queries |
| **NDCG@k** | (DCG@k) / (iDCG@k) | Are results ranked well? | Ranking quality |
| **MAP** | Average Precision | Mean precision across queries | Overall retrieval quality |

### Example Calculations

```
Query: "What is the termination fee?"
Corpus: [Doc A, B, C, D, E]
Relevant docs: [A, C]  (only these address termination fees)
Retrieved top-5: [B, A, D, C, E]

Precision@5 = 2/5 = 0.40 (40% of top-5 are relevant)
Recall@5 = 2/2 = 1.00 (found all relevant docs)
MRR = 1/2 = 0.50 (first relevant is rank 2)
```

### When to Use Each

- **Precision**: You have limited tokens for context. Want high-quality top-5.
  - Target: >0.80 (80% of top-5 should be relevant)

- **Recall**: You need comprehensive information. Must find all relevant docs.
  - Target: >0.90 (find 90%+ of relevant docs)

- **MRR**: Single-turn, simple queries. First result is critical.
  - Target: >0.70 (first relevant in top 3-4)

- **NDCG**: Ranked results matter. Some docs more relevant than others.
  - Target: >0.75 (good ranking correlation with relevance)

---

## 4. Answer Quality Evaluation

### The Answer Evaluation Problem

Even with perfect retrieval, the LLM can:
- Hallucinate facts (make up information)
- Miss important details
- Answer off-topic
- Contradict the source

### Evaluation Approaches

#### A. Manual Evaluation (Gold Standard)

**Method:** Human annotators score each answer.

**Scoring Rubric (1-5 scale):**
- 1: Completely irrelevant or hallucinated
- 2: Partially relevant, major issues
- 3: Addresses query but incomplete
- 4: Good, mostly complete
- 5: Excellent, comprehensive and accurate

**Pros:**
- Most accurate
- Catches subtle hallucinations
- Reveals user preferences

**Cons:**
- Slow (30 seconds per answer)
- Expensive ($0.50-1.00 per answer)
- Not scalable

**When to use:** Validation sets, production spot-checks, failure analysis

#### B. LLM-Based Evaluation (Fast & Scalable)

**Method:** Another LLM scores the answer.

```python
evaluation_prompt = """
Question: {query}
Source documents: {sources}
Generated answer: {answer}

Score this answer 1-5:
- Did it address the question?
- Is it supported by the sources?
- Are there unsupported claims?

Score and explain:
"""

score = evaluate_llm.invoke(evaluation_prompt)
```

**Pros:**
- Fast ($0.001-0.005 per answer)
- Scalable to 1000s
- Agrees with humans ~75-85%

**Cons:**
- Misses some hallucinations
- Can be influenced by answer formatting
- Requires validation on sample

**When to use:** Production monitoring, A/B testing, bulk evaluation

#### C. Reference-Based Metrics

**ROUGE (Recall-Oriented Understudy for Gisting Evaluation):**
```
Compare generated answer to gold-standard reference answers
Higher ROUGE = more overlap with reference
```

**BLEU (Bilingual Evaluation Understudy):**
```
Compare n-grams with reference
Common in ML but has issues with paraphrasing
```

**BERTScore:**
```
Semantic similarity using BERT embeddings
Better at catching paraphrasing
```

**Pros:**
- Fast and deterministic
- Good for detecting major changes

**Cons:**
- Penalizes paraphrasing (even if correct)
- Requires multiple reference answers
- Can miss hallucinations

**When to use:** Regression testing (detect changes), quality drift monitoring

#### D. Consistency Checks

**Self-Contradiction Detection:**
```
Generate answer twice (different temperature/prompts)
If answers contradict, likely hallucination
```

**Source Verification:**
```
Extract claims from answer
Search for claim in source documents
Score % of claims found in sources
```

**Factual Consistency:**
```
Use NLI model (Natural Language Inference)
Can source entail the generated claim?
Model: microsoft/deberta-large-mnli
```

**Pros:**
- Fast and cheap
- Catches obvious hallucinations
- Automated

**Cons:**
- Misses subtle hallucinations
- High false positive rate sometimes

**When to use:** First-pass filtering, quality gates

### Recommended Evaluation Strategy

**Phase 1: Development (build & iterate)**
- Use LLM-based evaluation (fast, cheap)
- Validate on small manual sample (100 answers)
- Measure: Relevance (4.0/5), Completeness (3.8/5), Hallucination rate <5%

**Phase 2: Staging (pre-production)**
- Run manual evaluation on 200-300 answers
- Compare LLM scores vs manual scores
- Calibrate LLM evaluation thresholds
- Measure: Consistency between LLM and human

**Phase 3: Production (monitor)**
- Use LLM-based evaluation for all queries
- Sample 50/week for manual spot-checks
- Set alerting: If avg relevance drops below 3.8, investigate
- Measure: Production quality trends

---

## 5. Citation Accuracy & Source Attribution

### The Citation Problem

```
Question: "What is the termination fee?"
Answer: "The termination fee is 10% of remaining contract value."
Sources: [Section 5, Section 12, Appendix B]

Problem: Where in those sources is this claim?
```

### Citation Evaluation Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **Citation Coverage** | % of claims with explicit citations | >90% |
| **Citation Accuracy** | % of citations that actually support the claim | >95% |
| **Source Relevance** | % of cited sources that address the query | >90% |
| **Hallucination Detection** | % of unsupported claims caught | >85% |

### Evaluation Method

**For each claim in answer:**

1. Extract span: `"The termination fee is 10% of remaining contract value"`
2. Find supporting source: Search sources for text matching claim
3. Score:
   - ✅ Found exactly: Citation is accurate
   - ⚠️ Found paraphrase: Citation is mostly accurate
   - ❌ Not found: Hallucination

**Implementation:**

```python
for claim in extract_claims(answer):
    found = False
    for source in sources:
        if claim_in_source(claim, source):
            citation_accuracy += 1
            found = True
            break
    if not found:
        hallucinations += 1

accuracy_rate = citation_accuracy / len(claims)
hallucination_rate = hallucinations / len(claims)
```

### Tools & Models

- **spaCy**: Extract claims/entities
- **BERTScore**: Semantic matching between claim and source
- **Span extraction**: Use question-answering model to find span in source
- **LLM verification**: Use LLM to judge if source supports claim

---

## 6. Latency & Performance Profiling

### The Latency Problem

```
Total latency: 3.2 seconds
User experience: "It's slow"

But which part?
- Retrieval: 0.1s
- Reranking: 1.8s ← HERE!
- LLM generation: 1.2s
- Other: 0.1s

Solution: Reranking not needed. Move to hierarchical indexing.
```

### Latency Breakdown

**End-to-End:** Total time from query to answer
- Target: <2s for good UX (under 1s is excellent)

**Per-Stage Breakdown:**

1. **Embedding query** (50-100ms typical)
   - Query vectorization
   - Depends on: embedding model, query length

2. **Vector search** (50-500ms typical)
   - Database lookup
   - Depends on: vector store size, k, indexing

3. **Reranking** (500-2000ms typical if used)
   - Cross-encoder scoring
   - Depends on: number of results, model

4. **LLM generation** (500-3000ms typical)
   - Token generation
   - Depends on: LLM, context length, output length

5. **Other** (network, parsing, etc.)

### Measuring Latency

```python
import time

# Measure end-to-end
start = time.time()
result = rag.query(question)
end = time.time()
latency_total = end - start

# Measure per-stage
stages = {
    "embedding": time_embedding(question),
    "search": time_search(embedding),
    "reranking": time_rerank(search_results),
    "generation": time_generate(reranked, question),
}

# Report
for stage, latency in stages.items():
    percentage = (latency / latency_total) * 100
    print(f"{stage}: {latency:.3f}s ({percentage:.1f}%)")
```

### Percentiles, Not Averages

**Important:** Report percentiles, not just averages.

```
Average latency: 1.5s (sounds good)
P50 (median): 1.2s
P95: 2.8s ← User frustration!
P99: 4.2s

True picture: Most queries fast, but 5% take 3+ seconds
```

**Targets:**
- P50: <1.5s
- P95: <2.5s
- P99: <4.0s

---

## 7. Cost Analysis

### Cost Components

**Per Query:**

1. **Embedding API** (OpenAI example)
   - Query: $0.0001-0.0002
   - Retrieved docs: $0.0002-0.0005 (depends on k)
   - Total: ~$0.0005/query

2. **Reranking** (if used)
   - Cross-encoder inference: $0.0010-0.0020 (cloud) or free (local)
   - Or API cost: $0.0050-0.0100

3. **LLM Generation**
   - Prompt: $0.001-0.010 (depends on context length)
   - Completion: $0.001-0.010
   - Total: ~$0.003-0.020/query

4. **Vector Database**
   - Hosted: $0.0001-0.0005/query
   - Self-hosted: $0 (just infrastructure cost)

**Total: $0.005-0.040 per query**

### Cost Calculation

```python
cost_breakdown = {
    "embedding_query": num_query_tokens * embedding_cost_per_token,
    "embedding_documents": (num_docs * avg_doc_tokens) * embedding_cost_per_token,
    "reranking": num_results * reranking_cost,
    "llm_prompt": num_prompt_tokens * prompt_cost_per_token,
    "llm_completion": num_completion_tokens * completion_cost_per_token,
}

total_cost = sum(cost_breakdown.values())

# Monitor
monthly_cost = total_cost * queries_per_month
```

### Cost vs Quality Tradeoff

| Pattern | Latency | Accuracy | Cost/Query | When to Use |
|---------|---------|----------|-----------|------------|
| Naive RAG (WP-3.1) | 1-2s | 60-70% | $0.01 | Prototype, low-cost |
| + Reranking (WP-3.2) | 2-3s | 85-95% | $0.05 | Production quality |
| + Hierarchical (WP-3.3) | 0.9-1.2s | 88-92% | $0.03 | 100K+ docs |
| + Agent (WP-3.5) | 3.2s | 87% (complex) | $0.16 | Complex multi-step |

---

## 8. Building Evaluation Datasets

### Types of Datasets

#### 1. Manual Golden Dataset

**Create:** You manually write Q&A pairs.

```
Query: "What is the termination fee for early contract cancellation?"
Answer: "10% of remaining contract value (Section 5.2)"
Sources: [contracts.pdf page 15]
Relevant docs: [Section 5.2, Section 5.3]
```

**Pros:**
- High quality
- Perfect ground truth

**Cons:**
- Expensive and slow (1-2 per hour)
- Small scale (100-500 questions)

**Use case:** Development validation, critical path testing

#### 2. Crowdsourced Dataset

**Create:** Use services (Scale, Surge, Amazon Mechanical Turk)

**Cost:** $0.10-0.50 per item

**Size:** Can get 1000+ quickly

**Quality:** ~90% agreement with experts (after filtering)

**Use case:** Validation at scale

#### 3. Synthetic Dataset

**Create:** Generate Q&A from documents using LLM

```python
qa_generator = ChatOpenAI(model="gpt-4")

qa_generator.invoke(f"""
Document: {document}

Generate 5 diverse questions that can be answered from this document.
For each question, provide:
1. Question
2. Answer (2-3 sentences)
3. Relevant sections

Format: JSON
""")
```

**Pros:**
- Fast and cheap
- Unlimited scale
- Domain-specific

**Cons:**
- LLM bias (generates easier questions)
- Not representative of real user queries

**Use case:** Initial testing, load testing

#### 4. Production Query Dataset

**Create:** Log real user queries (with consent)

**Collection:**
```
Sample 1% of production queries
Manual annotation by product team (3-4 hours/week)
Build dataset organically
```

**Quality:** Representative of real usage

**Use case:** Continuous evaluation, production validation

### Dataset Size Recommendations

| Purpose | Size | Notes |
|---------|------|-------|
| Development | 50-100 | Enough to catch major issues |
| Staging/Pre-prod | 200-500 | Validate before launch |
| Monitoring | 30/week | Continuous spot-checks |
| Annual review | 1000+ | Comprehensive analysis |

---

## 9. Comparison Framework

### Comparing RAG Architectures

**Setup:** Evaluate all approaches on same dataset

```python
# Create evaluation dataset
dataset = create_dataset(500_queries)

# Run each architecture
results = {}
for pattern in [naive_rag, rag_with_reranking, hierarchical_rag, agentic_rag]:
    results[pattern_name] = evaluate(pattern, dataset)

# Compare
comparison = {
    "accuracy": {name: r["accuracy"] for name, r in results.items()},
    "latency_p95": {name: r["latency_p95"] for name, r in results.items()},
    "cost_per_query": {name: r["cost"] for name, r in results.items()},
}
```

### Comparison Table Example

| Metric | Naive | + Reranking | Hierarchical | Agent | Winner |
|--------|-------|------------|--------------|-------|--------|
| Accuracy | 65% | 88% | 90% | 87% | Hierarchical |
| P95 Latency | 2.1s | 2.9s | 1.1s | 3.2s | Hierarchical |
| Cost/Query | $0.01 | $0.06 | $0.03 | $0.16 | Naive |
| Best For | Fast | Quality | Scale | Complex | — |

### Decision Framework

```
IF queries < 10K docs AND accuracy > 75%:
    Use Naive RAG (cheapest, simplest)

ELSE IF queries < 10K docs AND accuracy < 75%:
    Use Reranking (add 25 pp accuracy)

ELSE IF documents > 10K AND accuracy critical:
    Use Hierarchical (handles scale + quality)

ELSE IF task is complex multi-step:
    Use Agentic Workflow (iterative refinement)

ELSE:
    Combine approaches (hierarchical retrieval + agent wrapper)
```

---

## 10. Production Monitoring

### Setting Alerting Thresholds

Based on your evaluation data, define thresholds:

```python
THRESHOLDS = {
    "accuracy_min": 0.80,        # Alert if below 80%
    "latency_p95_max": 2.5,      # Alert if P95 > 2.5s
    "cost_per_query_max": 0.10,  # Alert if > $0.10
    "hallucination_rate_max": 0.05,  # Alert if > 5%
    "citation_accuracy_min": 0.95,   # Alert if < 95%
}

# In production
def monitor_query(question, answer, sources):
    metrics = evaluate_query(question, answer, sources)
    
    for metric, value in metrics.items():
        threshold_key = f"{metric}_max" or f"{metric}_min"
        if metric in THRESHOLDS:
            if value < THRESHOLDS[threshold_key]:  # For _min
                alert(f"{metric} degraded: {value}")
```

### Dashboards

**Real-time (last hour):**
- Average latency and P95
- Error rate
- Cost trend
- Top failing queries

**Daily:**
- Accuracy metrics
- Hallucination rate
- Citation accuracy
- Cost per query

**Weekly:**
- Compare to baseline
- Identify trends
- Resource utilization
- Cost projection

### Debugging Failures

**When accuracy drops:**

1. **Quick checks:**
   - Did data change? (new documents added?)
   - Did LLM settings change? (temperature? model?)
   - Did retrieval degrade? (check precision@5)

2. **Deep analysis:**
   - Which queries failed? (find pattern)
   - Do all patterns fail, or specific one?
   - Is it retrieval or generation issue?

3. **Root cause analysis:**
   ```
   Sample failed queries → Run through each component
   - Does retrieval find good docs? (check precision)
   - Does reranker break things? (compare with/without)
   - Does LLM hallucinate? (check citations)
   ```

---

## 11. Implementation Strategy

### Phase 1: Build Evaluation Infrastructure (4-6 hours)

1. **Implement metrics:**
   - RetrievalEvaluator (precision, recall, MRR, NDCG)
   - AnswerEvaluator (LLM-based + manual scoring)
   - CitationEvaluator (source verification)
   - LatencyProfiler (per-stage breakdown)
   - CostAnalyzer (per-component cost)

2. **Create evaluation dataset:**
   - Manual golden dataset (100 Q&A pairs)
   - Synthetic dataset (500 Q&A pairs)
   - Production dataset (start collection)

3. **Build comparison framework:**
   - Run all RAG patterns on dataset
   - Generate comparison table
   - Document tradeoffs

### Phase 2: Integrate with RAG Systems (2-3 hours)

1. **Add evaluation to existing RAG:**
   - Wrap query methods to collect metrics
   - Log to evaluation database
   - Generate daily reports

2. **Set up A/B testing:**
   - Route % of queries to different patterns
   - Collect metrics separately
   - Run statistical significance tests

### Phase 3: Production Deployment (1-2 hours)

1. **Set monitoring:**
   - Define alert thresholds
   - Deploy metrics collection
   - Build dashboards

2. **Continuous evaluation:**
   - Weekly manual spot-checks
   - Monthly comprehensive audit
   - Quarterly architecture review

---

## 12. Summary & Checklist

### Key Takeaways

- **Measurement drives improvement:** Without metrics, you can't iterate effectively
- **Use multiple metrics:** No single metric tells full story
- **Combine automated + manual evaluation:** LLM-based is fast, manual is accurate
- **Start simple, evolve:** Begin with basic metrics, add sophistication over time
- **Benchmark early:** Establish baseline before optimization
- **Monitor in production:** Catch degradation before users notice

### Evaluation Checklist

**Before Production:**
- [ ] Manual evaluation of 100+ queries (gold standard)
- [ ] Comparison of RAG patterns on evaluation dataset
- [ ] P95 latency measured and acceptable
- [ ] Cost per query calculated and budgeted
- [ ] Citation accuracy >95% on test set
- [ ] Hallucination rate <5%

**In Production (Week 1):**
- [ ] Metrics collection enabled
- [ ] Dashboard visible to team
- [ ] Alert thresholds configured
- [ ] Spot-checks scheduled (daily)

**Ongoing:**
- [ ] Weekly metric review
- [ ] Monthly deep-dive analysis
- [ ] Quarterly architecture review
- [ ] Annual cost/benefit analysis

---

## 13. Next Steps

**Read Next:**
- Production Deployment patterns (scaling to 1000s QPS)
- Advanced patterns (combining multiple RAG approaches)
- Domain-specific evaluation (legal, medical, technical)

**Build Next:**
- Your evaluation dataset (start with 100 Q&A)
- Implement RetrievalEvaluator and AnswerEvaluator
- Run comparison of WP-3.1 vs WP-3.2 vs WP-3.3
- Set up production monitoring

---

## References

**Evaluation Metrics:**
- Precision/Recall: https://en.wikipedia.org/wiki/Precision_and_recall
- NDCG: https://en.wikipedia.org/wiki/Discounted_cumulative_gain
- ROUGE: Lin et al. 2004
- BERTScore: Zhang et al. 2020

**Frameworks:**
- RAGAS: https://github.com/explodinggradients/ragas
- TruLens: https://www.trulens.org/
- LangSmith: https://smith.langchain.com/

**Tools:**
- spaCy: https://spacy.io/
- Hugging Face Transformers: https://huggingface.co/
- LLM evaluators: Claude, GPT-4, etc.
