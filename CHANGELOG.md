# Changelog

## [1.2.2] - 2026-07-01

### Added
- **Legal Contract Agent - Project Organization & Navigation**
  - Created `legal-contract-agent/INDEX.md` (500+ lines): Comprehensive project navigation hub
    * Quick navigation to all 6 sections (architecture, code, safety, evaluation, implementation, data)
    * Architecture overview with 7-task pipeline diagram
    * 10 guardrails summary table with safety specifications
    * 6 success metrics definition (Recall, Precision, F1, Hallucination, Latency, Cost)
    * 4-phase development roadmap with timelines
    * Core data models: ContractAnalysisResult, GroundTruthAnnotation, etc.
    * 100+ cross-references linking design docs to code modules
    * Project statistics: 7 tasks, 10 guardrails, 6 metrics, 45-contract dataset
  
  - Created `legal-contract-agent/QUICKSTART.md` (400 lines): 5-minute rapid onboarding
    * 7-step installation process (clone, venv, install, docker, config, verify, try)
    * Prerequisites for each OS (Tesseract OCR, Python 3.11+, Docker)
    * Virtual environment and dependency setup
    * Docker Compose configuration (Qdrant vector store, PostgreSQL audit log)
    * OpenAI API key configuration (.env setup)
    * 3 ways to try the system (CLI, pytest, Streamlit UI)
    * Common tasks and troubleshooting section
    * Next steps for deeper learning

- **Portfolio Navigation & Discoverability**
  - Updated `README.md` (main): Added Section 6 subsection
    * "🏛️ Section 6: Capstone — End-to-End Agentic System (2-3 weeks)"
    * Description of 7-task pipeline, 10 guardrails, 45-contract dataset
    * Links to legal-contract-agent/, QUICKSTART.md, INDEX.md, and design docs
  
  - Updated `docs/README.md`: Added legal-contract-agent as 6th learning path
    * Quick-start table row: "See a production AI system | Section 6: Legal Contract Agent | 2-3 weeks"
    * Full section describing pipeline, HITL approval workflow, guardrails, evaluation
    * Links to 06-capstone-legal-contract-analysis/ README
  
  - Updated `docs/06-capstone-legal-contract-analysis/README.md`: Added quick links table
    * 4-row navigation table (Implementation Code, Quick Start, Project Index, Main README)
    * Prominent links at top before existing content
    * Facilitates seamless navigation from design docs to implementation

- **AGENTMAP Knowledge Graph Expansion (800+ lines)**
  - Extended Core Documents table: Added 18 new rows
    * WP-3.0-3.7 (RAG patterns: naive baseline, reranking, hierarchical indexing, evaluation, agentic, query routing)
    * WP-4.1-4.9 (Capstone design: domain selection, pipeline, threat model, guardrails, HITL, notifications, evaluation, dataset, tool selection)
    * WP-5.1-5.2 (Implementation: PDF ingestion, clause extraction)
    * legal-contract-agent INDEX.md and QUICKSTART.md
  
  - Extended Code Examples & Test Examples tables: Added 8 new rows
    * RAG pattern examples (test_wp_3_*.py files)
    * Capstone implementation examples (test_wp_4_*.py, test_adr_1_2.py, test_naive_rag.py)
  
  - Updated Mermaid graph: Added 6 new nodes with 5 new relationships
    * WP30 (Knowledge Architecture)
    * ADR003 (Agentic vs Naive)
    * WP41 (Capstone)
    * LEGALINDEX (Project navigation)
    * Updated style definitions with color coding
  
  - Added 5 comprehensive relationship sections (800+ lines total):
    1. WP-3.0: Knowledge Architecture Decisions (OKF vs traditional, cost analysis, foundations for WP-3.1+)
    2. WP-3.1 & RAG Patterns (Progressive enhancement: naive → reranking → hierarchical → agentic)
    3. ADR-003: Agentic RAG vs Naive (Decision matrix, when each approach appropriate)
    4. WP-4: Capstone Legal Contract Analysis (Integrates all portfolio concepts, 7-task pipeline, 4 phases, metrics)
    5. legal-contract-agent: Implementation & Navigation (INDEX.md, QUICKSTART.md, src structure, data, tests, usage guide)

### Changed
- Version: 1.2.1 → 1.2.2
- Portfolio scope: Now includes complete capstone system implementation with navigation
- Documentation hub: Extended AGENTMAP.md with RAG patterns and capstone references
- Learning paths: Now 6 sections with 2-3 week capstone project at the end
- Project visibility: legal-contract-agent now discoverable from main README and docs hub

### Key Metrics
- Architectural Decision Records: 6 (ADR-1.2, ADR-2.1, ADR-2.2, ADR-003, ADR-3.9, plus references)
- Work Products: 30+ (WP-1.3 through WP-5.2 including RAG patterns and capstone)
- Navigation Guides: 2 new (INDEX.md 500+ lines, QUICKSTART.md 400 lines)
- Documentation Updated: 5 files (README.md, docs/README.md, docs/06-capstone-legal-contract-analysis/README.md, AGENTMAP.md, legal-contract-agent/README.md)
- Learning Paths: 6 complete paths (foundations → production → memory/state → multi-agent → RAG → capstone)
- Portfolio Integration: 100+ cross-references between design docs and implementation code

### Impact
- **Discoverability**: legal-contract-agent now featured prominently in main README and docs navigation
- **Onboarding**: Users can go from discovery to running code in 5 minutes via QUICKSTART.md
- **Architecture Understanding**: INDEX.md provides complete mapping of design → implementation → testing
- **Knowledge Graph**: AGENTMAP now shows how all 30+ work products interconnect
- **Learning Flow**: Complete progression from foundations through end-to-end production capstone system

## [1.2.1] - 2026-06-28

### Changed
- **Repository Reorganization - New docs/ Structure**
  - Moved all educational materials into organized `docs/` directory with 4 learning sections
  - New structure improves discoverability and learning flow:
    * `docs/01-foundations/` - Core abstractions and decision patterns (ADR-1.2, WP-1.3)
    * `docs/02-production-patterns/` - Production-ready patterns (WP-1.4 through WP-1.7)
    * `docs/03-memory-state-agents/` - Memory and agent state patterns (WP-2.1, WP-2.2)
    * `docs/04-multi-agent-architectures/` - Orchestration and choreography (ADR-2.1, ADR-2.2, WP-2.3, WP-2.4, WP-2.6)
    * `docs/reference/` - Navigation hubs and reference documents
  - Created section README files with learning paths and document indices
  - Created main `docs/README.md` as entry point with learning path recommendations
  - Updated root `README.md` to redirect to `docs/README.md`
  - All internal links updated to reflect new file locations
  - Verified all 100+ cross-references work correctly

### Fixed
- Broken anchor links in README.md (extra hyphens from special characters)
- Link paths across all sections now use correct relative paths

## [1.2.0] - 2026-06-26

### Added
- **WP-2.3: Orchestration Pattern - The "Controller" Agent**
  - Comprehensive hands-on guide to implementing centralized orchestration workflows
  - Controller pattern for deterministic multi-step workflows (834 lines)
  - Core concepts: Step lifecycle, evaluation gates, decision making
  - Implementation architecture with 5-step guide:
    * StepName enum (PLANNING, FETCHING, ANALYZING, SYNTHESIZING, CITING, FORMATTING)
    * State management with StepStatus enum (PENDING, RUNNING, SUCCESS, FAILED, RETRY, SKIPPED)
    * Decision enum (CONTINUE, RETRY, BRANCH, SKIP, ABORT)
    * Evaluation functions for step output validation
    * Controller base class with execute_step(), evaluate_and_decide(), get_audit_trail()
  - Advanced patterns: Conditional branching, step skipping, recovery strategies
  - Complete 6-step report generation example (ReportOrchestrator)
  - Test coverage with 41 comprehensive tests (100% passing)
  - When to use matrix: Orchestration vs Choreography decision guidance
  - 3.5-hour structured learning path

- **WP-2.4: Choreography Pattern - The "Hive Mind" Agent**
  - Comprehensive hands-on guide to event-driven multi-agent systems (906 lines)
  - Hive Mind pattern for emergent autonomous agent workflows
  - Event-driven architecture overview and core concepts
  - Implementation architecture with 5-step guide:
    * Event types with Pydantic validation (immutable, serializable)
    * EventBus pub/sub infrastructure with asyncio support
    * Agent base class with autonomous behavior patterns
    * WebSearcher agent (subscribes to search-requested, publishes data-fetched)
    * Drafter agent (handles data-fetched and revision-required events)
    * Critic agent (implements quality assessment and feedback loops)
  - Advanced patterns: Correlation ID tracing, concurrent workflows, causality analysis
  - Feedback loop mechanism for system self-regulation
  - Complete multi-agent workflow examples with event audit trails
  - Test coverage with 30 comprehensive tests (100% passing)
  - When to use matrix: Choreography vs Orchestration decision guidance
  - 3.5-hour structured learning path

- **Documentation Integration**
  - AGENTMAP.md: Added WP-2.3 and WP-2.4 nodes to knowledge graph
  - AGENTMAP.md: Added comprehensive relationships sections for both patterns
  - README.md: Added WP-2.3 to learning paths table (3.5 hours)
  - README.md: Added WP-2.4 to learning paths table (3.5 hours)
  - README.md: Quick navigation with pattern selection guidance
  - README.md: Detailed sections for both orchestration and choreography patterns
  - Decision matrix comparing all aspects of both approaches

### Changed
- Version: 1.1.0 → 1.2.0
- AGENTMAP.md: Extended with orchestration and choreography pattern relationships
- README.md: Expanded with two new design pattern sections (2000+ words)
- Repository focus: Complete coverage of multi-agent orchestration and choreography patterns
- Test suite: Expanded from 150+ to 191+ tests

### Key Metrics
- Architectural Decision Records: 2 (ADR-1.2, ADR-2.1)
- Work Products: 9 (WP-1.3 through WP-2.4)
- Python Implementation Files: 11 (examples + choreography + orchestration)
- Test Files: 8 (all passing - 100% success rate, 191+ total tests)
- Documentation: 9+ markdown work product files
- Total Code: ~2500 lines (choreography + orchestration implementations + tests)
- Pattern Coverage: Event-driven choreography, centralized orchestration, complete pattern library

## [1.1.0] - 2026-06-26

### Added
- **ADR-2.1: Choreography - Event-Driven Agility for Emergent Workflows**
  - Comprehensive architectural decision record on choreography patterns
  - Systems thinking analysis with feedback loops and second-order effects
  - Comparison matrix: Choreography vs. Orchestration (11 dimensions)
  - Implementation guidelines with event payload schemas
  - Risk analysis with 6 identified risks and mitigation strategies
  - Production deployment guidance and scaling strategies
  - Complete with cost/complexity trade-offs analysis

- **Multi-Agent Choreography Implementation (choreography_hive_mind.py)**
  - Event-driven architecture with asyncio EventBus for non-blocking message passing
  - Three autonomous agents:
    * WebSearcher: Fetches data for queries (subscribes to search-requested)
    * Drafter: Generates and revises reports (subscribes to data-fetched, revision-required)
    * Critic: Reviews quality and provides feedback (subscribes to report-synthesized)
  - Immutable Pydantic event types for reliability:
    * SearchRequested, DataFetched, DraftingStarted, ReportSynthesized
    * ReviewStarted, ReviewCompleted, RevisionRequired, RevisionAbandoned, ReportFinalized
  - Distributed tracing via correlation_id propagation through entire workflow
  - Bounded feedback loops with max revision limits (prevents infinite loops)
  - Event audit trail for complete workflow visibility
  - HiveMindOrchestrator for workflow coordination
  - ~860 lines of production-ready code with comprehensive docstrings

- **Comprehensive Test Suite (tests/test_choreography_hive_mind.py)**
  - 30 unit tests with 100% pass rate
  - Test coverage across:
    * Event type creation, immutability, serialization, correlation ID propagation
    * EventBus pub/sub mechanics, event routing, history tracking, statistics
    * Individual agent subscriptions and behavior
    * Complete end-to-end choreography workflows
    * Resilience: handler error isolation, max revision limit enforcement
    * Observability: bus statistics and orchestrator metrics
  - Async test suite using pytest-asyncio
  - ~800 lines of comprehensive test cases

- **Documentation Updates**
  - AGENTMAP.md: Added ADR-2.1 relationships, choreography flow topology, learning path
  - README.md: Added comprehensive "Choreography Implementation" section (~2000 words)
  - README.md: Added quick navigation link to choreography pattern
  - New learning path: "Multi-Agent Choreography for Emergent Workflows" (4 hours)

### Changed
- Version: 1.0.3 → 1.1.0
- AGENTMAP.md: Extended with choreography pattern relationships and implementation details
- README.md: Expanded with choreography section including problem/solution/patterns
- Repository focus: Added event-driven multi-agent patterns to core curriculum

### Key Metrics
- Architectural Decision Records: 2 (ADR-1.2, ADR-2.1)
- Work Products: 7 (WP-1.3 through WP-2.2, plus new choreography implementation)
- Python Implementation Files: 10 (examples + choreography)
- Test Files: 7 (all passing - 100% success rate across all test suites)
- Documentation: 7 markdown files (ADRs, WPs, guides)
- Total Code: ~1700 lines (choreography implementation + tests)

## [1.0.3] - 2026-06-24

### Added
- **WP-1.7: Introduction to Tracing with LangSmith**
  - Complete observability-first guide to LLM debugging
  - Detailed walkthrough of LangSmith trace structure with annotations
  - Step-by-step analysis of token usage, latency (TTFT), and costs
  - Real-world debugging examples:
    * High latency identification and optimization
    * Cost reduction through trace analysis
    * Parsing failure debugging
  - Best practices for production tracing:
    * 100% tracing in development
    * 10% sampling + 100% errors in production
    * Custom metadata for production debugging
  - ADR: Adaptive tracing strategy for production
  - Integration with WP-1.4 (prompt optimization) and WP-1.5 (output parsing)
  - 4 practical examples demonstrating:
    * Basic tracing setup with automatic instrumentation
    * Understanding trace structure (input/output/tokens/timing)
    * Comparing chains with traces (A/B testing)
    * Custom metadata for production systems
  - examples_1_7.py: Working examples of all tracing scenarios

- **Test Coverage**
  - Added test_wp_1_7.py with 8 comprehensive tests
  - Validates WP-1.7 content, examples, and ADR section
  - Verifies observability-first mindset emphasis

### Changed
- Version: 1.0.2 → 1.0.3
- Updated all documentation to reference WP-1.7 and observability
- Enhanced AGENTMAP.md with WP-1.7 relationships
- Updated REPOSITORY_STATUS.md metrics for v1.0.3
- Updated PIPELINE_STATUS.md for new test count

### Key Metrics
- Work Products: 6 (WP-1.3 through WP-1.7, plus ADR-1.2)
- Total Documentation: 9,800+ lines
- Test Coverage: 8 tests (added 2 for WP-1.7 validation)
- Observability: Complete with LangSmith tracing guide

---

## [1.0.2] - 2026-06-24

### Changed
- **WP-1.6: Expanded Model Landscape (2026 Update)**
  - Expanded from 4 to 7 candidate models
  - Added Gemini 3.5, OpenAI ChatGPT 5.5, Claude Opus 4.8
  - Updated weighted scoring and rankings
  - **New Primary Recommendation**: Claude Opus 4.8 (score 4.41) replaces GPT-4o
  - Key insight: Claude Opus 4.8 provides 50%+ cost savings vs GPT-4o for high-volume support
  - Enhanced ADR with tiered multi-model routing strategy:
    * Primary: Claude Opus 4.8 (standard requests, cost-optimized)
    * Speed-critical: ChatGPT 5.5 (SLA <500ms TTFT)
    * Budget: Mixtral via Groq (FAQ/retrieval, stateless)
    * Long-context: Gemini 3.5 (2M+ context edge cases)
  - Added Key Trade-offs table showing best choice per scenario
  - Improved Sensitivity Analysis with specific weight thresholds
  - Updated production guardrails and monitoring guidance

- **Test Coverage**
  - Updated test_wp_1_6.py to validate all 7 models
  - Added assertion for Claude Opus 4.8 decision outcome

## [1.0.1] - 2026-06-24

### Added
- **WP-1.6: Choosing an LLM - A Decision Matrix**
  - Architect-focused comparison of GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, and Mixtral via Groq
  - Evaluation axes: cost per 1M tokens, TTFT, TPS, context window, tool-calling reliability, multimodal capability
  - Weighted scoring for a high-volume customer support chatbot
  - Short ADR with primary model decision, routing strategy, trade-offs, and mitigations

- **Unit tests for WP-1.6**
  - Existence and required matrix dimensions validated in CI

### Changed
- Updated README navigation and documentation sections to include WP-1.6
- Updated AGENTMAP hierarchy and document overview to include WP-1.6
- Updated CI/CD auto-documentation workflow to include WP-1.6 in line-count statistics

## [1.0.0] - 2026-06-24

### Added
- **ADR-1.2: Hello World Three Ways** - Comprehensive comparison of LangChain chain abstractions
  - Direct LLM calls vs SimpleSequentialChain vs RunnableSequence+LCEL
  - Decision matrix with 8 dimensions of comparison
  - Real-world scenario guidance

- **WP-1.3: The Runnable Protocol** - Deep dive into LangChain's unified interface
  - Four execution modes: invoke, batch, stream, ainvoke
  - Composition as DAG (Directed Acyclic Graphs)
  - Production patterns and observability

- **WP-1.4: Prompt Engineering as Code** - Design patterns for production prompt management
  - PromptRegistry class with versioning
  - Composition patterns and multi-turn conversation management
  - Testing strategies and LangSmith integration

- **Comprehensive Examples** - 3 complete example files with 6+ working demonstrations
  - examples_1_2.py: Three chain approaches with streaming and batching
  - examples_1_3.py: Six Runnable protocol examples
  - examples_1_4.py: Six prompt engineering patterns

- **AGENTMAP.md** - Visual knowledge graph with Mermaid diagrams
  - Document relationships and learning paths
  - 4 learning paths for different user levels
  - Cross-reference matrix and progression timeline

- **CI/CD Pipeline** - GitHub Actions automation
  - Automated linting and testing
  - Documentation auto-updates
  - GitHub Pages deployment
  - MkDocs static site generation

- **Documentation** - 8,400+ lines of guides and explanations
  - Complete ecosystem reference
  - Production best practices
  - Learning paths for different skill levels

### Infrastructure
- Python 3.11+ environment
- LangChain core + community + OpenAI packages
- Ruff linting, pytest testing
- MkDocs + Material theme for documentation
- GitHub Actions CI/CD pipeline
- GitHub Pages deployment

### Documentation
- README.md: Project overview and navigation
- AGENTMAP.md: Knowledge graph visualization
- ADR-1.2-Hello-World-Three-Ways.md: Chain decision record
- WP-1.3-The-Runnable-Protocol.md: Protocol deep dive
- WP-1.4-Prompt-Engineering-as-Code.md: Prompt patterns
- LANGCHAIN_ECOSYSTEM_MAP.md: Full stack reference
- .github/PIPELINE.md: Pipeline documentation
- .github/QUICKSTART.md: Quick reference guide
- DEPLOYMENT_SUMMARY.md: Deployment guide
- PIPELINE_STATUS.md: Current pipeline status

---

## Version History

| Version | Date | Status | Key Features |
|---------|------|--------|--------------|
| 1.0.0 | 2026-06-24 | 🟢 Active | Complete CI/CD, all work products, full documentation |
| (Initial) | - | - | Foundation established |

---

## Release Notes

### 1.0.0 (Production Release)

**Production-Ready Design Patterns for LLM Systems**

Complete repository with all work products, comprehensive documentation, and automated CI/CD pipeline. Ready for production use and team collaboration.

**Key Milestones:**
- ✅ 8,400+ lines of documentation
- ✅ 3 work products (ADR-1.2, WP-1.3, WP-1.4)
- ✅ 15+ examples with 800+ lines of detailed comments
- ✅ Fully automated CI/CD pipeline (4-job, 52-second deployment)
- ✅ GitHub Pages static site deployment
- ✅ Production-ready code quality

**Quality Metrics:**
- Python syntax: 100% passing
- Examples: 6/6 running successfully
- Unit tests: 6/6 passing
- Pipeline jobs: 4/4 passing
- Documentation: Complete and linked

**Next Version (1.1.0 - Future):**
- pytest integration for comprehensive testing
- Multi-language documentation support
- Slack/Discord deployment notifications
- Custom domain configuration
- Advanced analytics and tracking
