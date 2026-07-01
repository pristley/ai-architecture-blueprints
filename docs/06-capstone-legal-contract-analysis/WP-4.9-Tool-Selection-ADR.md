# WP-4.9: Tool Selection ADR

**Work Product Type**: Architecture Decision Record (ADR)  
**Phase**: 4 — Capstone: End-to-End Agentic System  
**Date**: 2026-04-02  
**Status**: ✅ Accepted  

---

## Executive Summary

This ADR documents **tool and infrastructure decisions** for the legal contract analysis agent. Each decision is justified with tradeoffs analysis, cost considerations, and deployment readiness.

**Decisions Made**:
1. **PDF Parser**: Docling (over PyPDF2, Unstructured)
2. **Vector Store**: Qdrant (over Chroma)
3. **Legal Search API**: Tavily (over custom, LLM-only)
4. **HITL Notifications**: Slack + Email (dual-channel)

---

## ADR-1: PDF Parser — Docling vs. PyPDF2 vs. Unstructured

### Context

**Problem**: Legal contracts are PDFs with complex layouts, tables, multi-column text, and scanned images. We need robust OCR + layout parsing.

**Candidates**:
- **PyPDF2**: Fast, lightweight, text extraction only
- **Docling**: IBM research tool; table detection, layout parsing
- **Unstructured.io**: Enterprise PDF/Doc parser; handles images, tables

### Decision

✅ **Use Docling**

### Justification

| Criteria | PyPDF2 | Docling | Unstructured |
|----------|--------|---------|--------------|
| **Accuracy on Legal PDFs** | ⭐⭐ (simple text only) | ⭐⭐⭐⭐⭐ (tables, layout) | ⭐⭐⭐⭐ (good but heavy) |
| **Table Detection** | ❌ No | ✅ Yes (specialized) | ✅ Yes |
| **OCR for Scans** | ❌ No | ✅ Yes (via Tesseract) | ✅ Yes |
| **Latency** | ~0.5 sec | ~2-3 sec | ~5-10 sec |
| **Memory** | ~50 MB | ~200 MB | ~500 MB+ |
| **Cost** | $0 (open source) | $0 (open source) | $0-500/mo (API) |
| **Self-Hosted** | ✅ Yes | ✅ Yes | ⚠ Limited (API) |
| **Active Maintenance** | ✅ Medium | ✅ High (IBM) | ✅ High |

### Why Docling Wins

1. **Layout Preservation**: Maintains table structure, multi-column layout → better clause extraction
2. **Open Source + Self-Hosted**: No API keys, no rate limits, no data leakage risk (critical for legal)
3. **Purpose-Built**: Designed specifically for document intelligence (not generic OCR)
4. **Speed/Accuracy Tradeoff**: 2-3 sec per contract is acceptable (within 28 sec latency budget, Task 1 budget ~1 sec extended to 3 sec)
5. **Active Maintenance**: IBM backing ensures LLM-era improvements

### Tradeoffs

- **Con**: Slower than PyPDF2 (~2-3 sec vs 0.5 sec)
  - *Mitigated*: Acceptable latency budget, can parallelize
- **Con**: Requires Tesseract for OCR
  - *Mitigated*: Lightweight dependency; works on Linux/Docker
- **Con**: ~200 MB memory footprint
  - *Mitigated*: Fine for cloud deployment; memory not bottleneck

### Implementation

```python
# src/tools/pdf_parser.py

from docling.document_converter import DocumentConverter
from pathlib import Path

def parse_contract_pdf(pdf_path: str) -> dict:
    """
    Parse PDF contract using Docling.
    
    Returns:
        {
            "text": str,           # Full extracted text
            "tables": list,        # Extracted tables
            "images": list,        # Extracted images
            "metadata": {
                "num_pages": int,
                "num_tables": int,
                "layout_preserved": bool
            }
        }
    """
    converter = DocumentConverter()
    doc_result = converter.convert(pdf_path)
    
    return {
        "text": doc_result.document.export_to_markdown(),
        "tables": extract_tables(doc_result),
        "images": extract_images(doc_result),
        "metadata": {
            "num_pages": len(doc_result.document.pages),
            "num_tables": len(extract_tables(doc_result)),
            "layout_preserved": True
        }
    }
```

### Dependencies

```
docling>=1.0.0
pdf2image>=1.16.3
pytesseract>=0.3.10
pillow>=10.0.0
```

---

## ADR-2: Vector Store — Qdrant vs. Chroma

### Context

**Problem**: Need to store & retrieve clause embeddings for RAG (retrieve similar clauses from past contracts). Two main options: Chroma (local/simple) vs. Qdrant (cloud-ready/scalable).

**Use Case**: Given a clause, find similar clauses from 45-contract database and 10,000+ legal clause corpus.

**Candidates**:
- **Chroma**: Lightweight, in-memory, good for prototyping
- **Qdrant**: Distributed, cloud-native, scales to millions

### Decision

✅ **Use Qdrant**

### Justification

| Criteria | Chroma | Qdrant |
|----------|--------|--------|
| **Latency (100k vectors)** | ~500ms | ~100ms |
| **Scalability** | ~100k vectors | ~1B+ vectors |
| **Cloud Deployment** | ⚠ Tricky (no built-in clustering) | ✅ Native cloud support |
| **Multi-User Access** | ❌ Limited (SQLite-based) | ✅ Full RBAC, multi-tenant |
| **Filtering** | ⭐⭐⭐ (basic) | ⭐⭐⭐⭐⭐ (advanced) |
| **Self-Hosted** | ✅ Yes | ✅ Yes (Docker) |
| **Cost (Cloud)** | Free tier limited | $25/mo+ (scalable) |
| **Learning Curve** | ⭐⭐ (simple) | ⭐⭐⭐ (moderate) |

### Why Qdrant Wins

1. **Future-Proof**: Designed for production ML systems; scales as corpus grows (thousands → millions of clauses)
2. **Metadata Filtering**: Filter vectors by `contract_type`, `risk_level`, `clause_type` → better RAG quality
3. **Cloud-Ready**: Qdrant Cloud is fully managed; can go from laptop to production easily
4. **RBAC**: Important for enterprise deployment (different users see different contracts)
5. **Battle-Tested**: Used by major LLM apps (e.g., LangChain default recommendation)

### Tradeoffs

- **Con**: Chroma is simpler to set up locally
  - *Mitigated*: Qdrant Docker setup is straightforward; 5 min setup
- **Con**: Requires Docker for self-hosted (vs. Chroma Python-only)
  - *Mitigated*: Essential for production anyway; good practice
- **Con**: Learning curve slightly steeper
  - *Mitigated*: Well-documented; LangChain integration built-in

### Implementation Strategy

```python
# src/tools/vector_store.py

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import json

class QdrantVectorStore:
    def __init__(self, url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=url)
        self.collection_name = "contract_clauses"
        
    def create_collection(self):
        """Initialize vector store."""
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
    
    def add_clause(self, clause_id: str, embedding: list, metadata: dict):
        """Add clause embedding with metadata."""
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=hash(clause_id) % (2**63),
                    vector=embedding,
                    payload={
                        "clause_id": clause_id,
                        "contract_type": metadata.get("contract_type"),
                        "clause_type": metadata.get("clause_type"),
                        "risk_level": metadata.get("risk_level"),
                        "text": metadata.get("text")
                    }
                )
            ]
        )
    
    def search_similar_clauses(
        self, 
        query_embedding: list, 
        limit: int = 5,
        filter_type: str = None
    ) -> list:
        """Find similar clauses with optional filtering."""
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter={
                "must": [
                    {"key": "clause_type", "match": {"value": filter_type}}
                ]
            } if filter_type else None,
            limit=limit
        )
        return search_result
```

### Docker Compose for Local Development

```yaml
# docker-compose.yml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./data/qdrant_storage:/qdrant/storage
    environment:
      QDRANT_SNAPSHOT_RECOVER: "true"
```

### Dependencies

```
qdrant-client>=2.7.0
langchain>=0.0.350
sentence-transformers>=2.2.0  # For embeddings
```

---

## ADR-3: Legal Search API — Tavily vs. Custom LLM vs. None

### Context

**Problem**: For Task 6 (Triage), need to check if a clause is a "standard market term" or unusual. Can:
1. Use Tavily API (legal research tool)
2. Use custom embeddings against legal corpus
3. Use LLM-only (ask GPT: "Is this common?")

**Use Case**: Given a clause about "automatic renewal", retrieve similar clauses from 1000+ contracts to show prevalence.

### Decision

✅ **Use Tavily API + Fallback to LLM**

### Justification

| Criteria | Custom Corpus | Tavily API | LLM-Only |
|----------|----------------|-----------|----------|
| **Accuracy** | ⭐⭐ (small dataset) | ⭐⭐⭐⭐⭐ (legal DB) | ⭐⭐⭐ (decent) |
| **Cost** | $0 (upfront effort) | $5/month (free tier) | $0.01-0.10/query |
| **Setup Time** | ~1 week | ~10 minutes | ~5 minutes |
| **Scope** | 45-contract data only | Legal corpus (1000s) | General knowledge |
| **Recency** | Static | Updated | GPT-4 knowledge cutoff |
| **Integration** | LangChain built-in | LangChain built-in | LangChain built-in |

### Why Tavily + LLM Hybrid Wins

1. **Cost-Effective**: Free tier covers early usage; scales linearly
2. **Accuracy**: Tavily trained on legal documents; far better than our 45-contract corpus
3. **Fast Fallback**: If Tavily fails/rate-limited, LLM provides answer (no user-facing latency)
4. **Minimal Setup**: API key + 1 function call; done

### Hybrid Strategy

```python
# src/tools/legal_search.py

from tavily import TavilyClient
from langchain.chat_models import ChatOpenAI

class LegalSearchTool:
    def __init__(self, tavily_api_key: str, openai_api_key: str):
        self.tavily = TavilyClient(api_key=tavily_api_key)
        self.llm = ChatOpenAI(model="gpt-4", api_key=openai_api_key)
    
    def search_clause_precedent(self, clause_text: str) -> dict:
        """
        Search for similar clauses in legal literature.
        Falls back to LLM if Tavily fails.
        """
        try:
            # Try Tavily first (more authoritative)
            result = self.tavily.search(
                query=f"contract clause: {clause_text[:100]}",
                topic="legal",
                max_results=5
            )
            
            return {
                "source": "tavily",
                "precedents": result["results"],
                "common": len(result["results"]) >= 3,
                "confidence": 0.95
            }
        
        except Exception as e:
            # Fallback to LLM if Tavily fails
            print(f"Tavily error: {e}, falling back to LLM")
            response = self.llm.invoke(
                f"Is this clause standard market practice? {clause_text}\n\n"
                f"Answer: common, uncommon, or unusual."
            )
            
            return {
                "source": "llm_fallback",
                "reasoning": response.content,
                "common": "common" in response.content.lower(),
                "confidence": 0.70
            }
```

### Cost Estimate

```
Tavily API:
  - Free tier: 100 queries/month
  - Pro: $5/month (10k queries)
  - Scale: $0.0005 per query

Estimate for 1000 contracts:
  - 1000 contracts × 0.5 queries average = 500 queries
  - Cost: $0 (free tier) to $2.50/month (pro with headroom)
  
Very economical for Task 6
```

### Fallback Mechanism

Importance: If Tavily is down, LLM fallback ensures system doesn't break. Human can override if needed (via HITL).

---

## ADR-4: HITL Notifications — Slack + Email

### Context

**Problem**: Task 7 (Human Review) requires alerting humans to pending contracts. Need reliable, multi-channel notification system for enterprise deployment.

**Candidates**:
- **Slack only**: Fast, real-time, but requires Slack workspace
- **Email only**: Universal, but slower, less interactive
- **Dual Slack + Email**: Best of both; Slack for speed, email as fallback

### Decision

✅ **Use Slack (Primary) + Email (Fallback)**

### Justification

| Criteria | Slack | Email | Dual |
|----------|-------|-------|------|
| **Delivery Time** | ~1 sec | ~30 sec (SES/SendGrid) | ~1 sec (Slack) + ~30 sec backup |
| **User Experience** | ⭐⭐⭐⭐⭐ (threads, reactions) | ⭐⭐⭐ (basic) | ⭐⭐⭐⭐⭐ |
| **Cost** | Free (Slack workspace) | $0.10-1 per 1000 | $0.1-1 per 1000 |
| **Reliability** | ⭐⭐⭐⭐ (99.99%) | ⭐⭐⭐⭐⭐ (universal) | ⭐⭐⭐⭐⭐ |
| **Spam Risk** | Low | ⭐⭐⭐ (high) | Low |
| **Setup** | ~15 minutes | ~5 minutes | ~20 minutes |

### Why Dual Wins

1. **Slack Primary**: Fast, reduces review latency (SLA: 5-30 min depends on priority)
   - Reviewers can respond in Slack itself (approve/reject)
   - Thread = audit trail for compliance

2. **Email Fallback**: Ensures critical escalations reach humans even if Slack is down
   - SMS for CRITICAL priority

3. **Enterprise Ready**: Supports organizations with different communication preferences

### Architecture

```python
# src/tools/notifications.py

from slack_sdk import WebClient
import smtplib
from email.mime.text import MIMEText
import os

class NotificationManager:
    def __init__(self):
        self.slack = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
        self.sendgrid_api_key = os.environ["SENDGRID_API_KEY"]
    
    def send_review_notification(
        self, 
        contract_id: str,
        priority: str,  # CRITICAL, HIGH, MEDIUM, LOW
        recipient: dict,  # {"email": str, "slack_id": str}
        metadata: dict  # {"contract_type", "num_clauses", "anomalies", ...}
    ) -> dict:
        """
        Send HITL notification via Slack + Email fallback.
        """
        
        slack_success = False
        email_success = False
        
        # Try Slack first
        try:
            slack_msg = self._format_slack_message(
                contract_id, priority, metadata
            )
            response = self.slack.chat_postMessage(
                channel=recipient["slack_id"],
                blocks=slack_msg
            )
            slack_success = response["ok"]
        except Exception as e:
            print(f"Slack send failed: {e}")
        
        # Email fallback if Slack failed
        if not slack_success:
            try:
                email_success = self._send_email(
                    to=recipient["email"],
                    subject=f"[{priority}] Review Needed: {contract_id}",
                    body=self._format_email_message(
                        contract_id, priority, metadata
                    )
                )
            except Exception as e:
                print(f"Email send failed: {e}")
        
        return {
            "contract_id": contract_id,
            "slack_sent": slack_success,
            "email_sent": email_success,
            "status": "delivered" if (slack_success or email_success) else "failed"
        }
    
    def _format_slack_message(self, contract_id: str, priority: str, metadata: dict) -> list:
        """Format Slack block kit message."""
        priority_color = {
            "CRITICAL": "#FF0000",
            "HIGH": "#FF9900",
            "MEDIUM": "#FFFF00",
            "LOW": "#00FF00"
        }
        
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔍 Contract Review Needed: {contract_id}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{metadata['contract_type']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:*\n{priority}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Clauses:*\n{metadata['num_clauses']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Anomalies:*\n{metadata['num_anomalies']}"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✓ Approve"},
                        "style": "primary",
                        "value": f"{contract_id}_approve",
                        "action_id": f"{contract_id}_approve"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✗ Reject"},
                        "style": "danger",
                        "value": f"{contract_id}_reject",
                        "action_id": f"{contract_id}_reject"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "ℹ View Details"},
                        "value": f"{contract_id}_details",
                        "action_id": f"{contract_id}_details"
                    }
                ]
            }
        ]
    
    def _send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via SendGrid."""
        # Implementation using SendGrid API
        # Returns: bool (success)
        pass
```

### Configuration

```yaml
# config/notifications.yml
slack:
  enabled: true
  bot_token: ${SLACK_BOT_TOKEN}
  channel_mapping:
    CRITICAL: "#critical-reviews"
    HIGH: "@lead-reviewer"
    MEDIUM: "#general-reviews"
    LOW: "#batched-reviews"
  retry_attempts: 3
  retry_delay_seconds: 30

email:
  enabled: true
  provider: "sendgrid"  # or "ses", "smtp"
  api_key: ${SENDGRID_API_KEY}
  from_address: "contracts-review@company.com"
  retry_attempts: 2

sms:
  enabled: false  # Optional for CRITICAL only
  provider: "twilio"
  api_key: ${TWILIO_API_KEY}
  only_critical: true
```

### Dependencies

```
slack-sdk>=3.23.0
sendgrid>=6.10.0
twilio>=9.0.0  # Optional, for SMS
```

---

## Summary Table: All Tool Decisions

| Component | Decision | Justification | Cost | Deployment |
|-----------|----------|---------------|------|-----------|
| **PDF Parser** | Docling | Layout-preserving, OCR, IBM-backed | $0 | Self-hosted |
| **Vector Store** | Qdrant | Scalable, cloud-ready, filtering | $0-25/mo | Docker or Qdrant Cloud |
| **Legal Search** | Tavily + LLM | Cost-effective, reliable, fallback | $0-5/mo | API |
| **Notifications** | Slack + Email | Multi-channel, enterprise-ready | $0-5/mo | Slack workspace + SendGrid |

---

## Dependencies Summary

Add to `requirements.txt`:

```
# PDF Parsing
docling>=1.0.0
pdf2image>=1.16.3
pytesseract>=0.3.10
pillow>=10.0.0

# Vector Store
qdrant-client>=2.7.0
sentence-transformers>=2.2.0

# Search API
tavily-python>=0.3.0

# Notifications
slack-sdk>=3.23.0
sendgrid>=6.10.0

# Core LangChain
langchain>=0.0.350
langchain-community>=0.0.20
```

---

## Implementation Roadmap

| Week | Task | Deliverable |
|------|------|-------------|
| 3 | PDF Parser Integration | Task 1 reads PDFs using Docling |
| 3 | Vector Store Setup | Qdrant running locally; 45 clauses indexed |
| 4 | Legal Search Tool | Tavily API key configured; fallback tested |
| 4 | Notification System | Slack + Email alerts working in Task 7 |
| 5 | End-to-End Testing | All tools integrated; production simulation |

---

## References

- WP-4.2: Task Decomposition (tools used in Tasks 1, 4, 6, 7)
- WP-4.4: Guardrail Specification (G4 PII redaction relevant to data handling)
- WP-4.5: HITL Checkpoint Architecture (notifications in PENDING_HUMAN_REVIEW state)
- WP-4.6: HITL Queue & Notification Design

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-02  
**Author**: Architecture Portfolio  
**Status**: ✅ Approved for Implementation
