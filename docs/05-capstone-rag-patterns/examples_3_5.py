"""
Work Product 3.5: RAG Architecture — Agentic Workflow

This module demonstrates an agentic workflow system for complex document tasks:
- Agent uses search tools iteratively
- Makes decisions based on gathered information
- Tracks reasoning trail and findings
- Synthesizes results into comprehensive answers

Example Usage:
    >>> from examples_3_5 import create_agentic_workflow
    >>> workflow = create_agentic_workflow()
    >>> result = workflow.execute_task("Summarize contract + identify termination clauses")
    >>> print(result["answer"])
    >>> print(f"Searches: {len(result['searches'])}")
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import json

# LangChain
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SECTION 1: SEARCH TOOL
# ============================================================================

class SearchTool:
    """Tool for agents to search document vector store."""
    
    def __init__(self, vector_store):
        """
        Initialize search tool with vector store backend.
        
        Args:
            vector_store: Chroma or other VectorStore instance
        """
        self.vector_store = vector_store
        self.search_history = []
    
    def search(
        self,
        query: str,
        k: int = 5,
    ) -> List[Dict]:
        """
        Search documents in vector store.
        
        Args:
            query: Search query from agent
            k: Number of results to return
            
        Returns:
            List of search results with content and metadata
        """
        logger.info(f"Search: '{query}' (k={k})")
        
        try:
            # Execute search
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content[:500],  # Limit length
                    "source": doc.metadata.get("source", "unknown"),
                    "score": float(score),
                    "metadata": doc.metadata,
                })
            
            # Track search
            self.search_history.append({
                "query": query,
                "k": k,
                "results_count": len(formatted_results),
                "timestamp": datetime.now().isoformat(),
            })
            
            logger.debug(f"Found {len(formatted_results)} results")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_search_history(self) -> List[Dict]:
        """Get history of all searches performed."""
        return self.search_history.copy()


# ============================================================================
# SECTION 2: AGENT MEMORY
# ============================================================================

class AgentMemory:
    """Track agent's gathered information and reasoning."""
    
    def __init__(self, task: str):
        """
        Initialize memory for a task.
        
        Args:
            task: The task the agent is working on
        """
        self.task = task
        self.gathered_info = {}  # key → list of findings
        self.reasoning_trail = []  # Steps taken
        self.searches_performed = []  # Search queries
        self.start_time = datetime.now()
    
    def add_finding(self, key: str, value: str, source: str = ""):
        """
        Add information to memory.
        
        Args:
            key: Category of information
            value: Information content
            source: Source document
        """
        if key not in self.gathered_info:
            self.gathered_info[key] = []
        
        self.gathered_info[key].append({
            "value": value,
            "source": source,
            "timestamp": datetime.now().isoformat(),
        })
        
        logger.debug(f"Memory: Added '{key}'")
    
    def add_reasoning_step(self, step: str, decision: str):
        """
        Log a reasoning step and decision.
        
        Args:
            step: Description of reasoning
            decision: Decision made
        """
        self.reasoning_trail.append({
            "step": step,
            "decision": decision,
            "timestamp": datetime.now().isoformat(),
        })
        logger.debug(f"Reasoning: {step} → {decision[:50]}...")
    
    def add_search(self, query: str, result_count: int):
        """Log a search performed."""
        self.searches_performed.append({
            "query": query,
            "result_count": result_count,
            "timestamp": datetime.now().isoformat(),
        })
    
    def get_findings_summary(self) -> str:
        """Get formatted summary of findings."""
        if not self.gathered_info:
            return "(No findings yet)"
        
        summary = ""
        for key, findings in self.gathered_info.items():
            summary += f"\n{key}:\n"
            for i, finding in enumerate(findings[:2], 1):  # Show first 2
                summary += f"  {i}. {finding['value'][:100]}...\n"
        
        return summary
    
    def get_summary(self) -> Dict:
        """Get summary of memory."""
        return {
            "task": self.task,
            "findings_count": sum(len(f) for f in self.gathered_info.values()),
            "searches_count": len(self.searches_performed),
            "reasoning_steps": len(self.reasoning_trail),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
        }


# ============================================================================
# SECTION 3: AGENTIC WORKFLOW
# ============================================================================

class AgentWorkflow:
    """
    Agentic workflow for complex document tasks.
    
    Uses iterative search-think-decide loop to solve tasks.
    """
    
    def __init__(
        self,
        vector_store,
        llm_model: str = "gpt-4-turbo",
        max_iterations: int = 10,
        max_search_results: int = 5,
    ):
        """
        Initialize agentic workflow.
        
        Args:
            vector_store: Chroma or other VectorStore
            llm_model: LLM model to use for agent
            max_iterations: Maximum loop iterations
            max_search_results: Results per search
        """
        self.vector_store = vector_store
        self.search_tool = SearchTool(vector_store)
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
        self.max_iterations = max_iterations
        self.max_search_results = max_search_results
    
    def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a complex task using agentic loop.
        
        Args:
            task: Complex task description
            
        Returns:
            Results with search trail, reasoning, and final answer
        """
        logger.info(f"Starting agentic workflow for: {task[:60]}...")
        
        memory = AgentMemory(task)
        iteration = 0
        stop_reason = None
        
        # Main agentic loop
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Iteration {iteration}/{self.max_iterations}")
            
            # Step 1: Agent decides what to search
            search_query = self._decide_search_query(task, memory)
            
            if search_query is None:
                # Agent decided to stop searching
                stop_reason = "agent_decided_done"
                logger.info("Agent decided to stop searching")
                break
            
            if search_query.upper() == "SYNTHESIZE":
                # Agent ready to synthesize
                stop_reason = "ready_to_synthesize"
                logger.info("Agent ready to synthesize")
                break
            
            # Check for duplicate searches
            if self._is_duplicate_search(search_query, memory):
                logger.info(f"Duplicate search detected: '{search_query}'")
                stop_reason = "duplicate_search_detected"
                break
            
            # Step 2: Execute search
            results = self.search_tool.search(
                query=search_query,
                k=self.max_search_results
            )
            
            if not results:
                logger.warning("Search returned no results, stopping")
                stop_reason = "no_results"
                break
            
            memory.add_search(search_query, len(results))
            
            # Step 3: Agent analyzes results
            self._analyze_results(search_query, results, memory)
            
            logger.debug(f"Iteration {iteration} complete")
        
        if iteration >= self.max_iterations:
            stop_reason = "max_iterations_reached"
            logger.warning(f"Max iterations ({self.max_iterations}) reached")
        
        # Step 4: Synthesize findings
        final_answer = self._synthesize(task, memory)
        
        # Return results
        results = {
            "task": task,
            "answer": final_answer,
            "iterations": iteration,
            "stop_reason": stop_reason,
            "searches": memory.searches_performed,
            "findings": memory.gathered_info,
            "reasoning_trail": memory.reasoning_trail,
            "memory_summary": memory.get_summary(),
            "duration_seconds": (datetime.now() - memory.start_time).total_seconds(),
        }
        
        logger.info(f"Workflow complete: {iteration} iterations, {stop_reason}")
        return results
    
    def _decide_search_query(self, task: str, memory: AgentMemory) -> Optional[str]:
        """
        Agent decides what to search next using Chain-of-Thought reasoning.
        
        Returns None or "SYNTHESIZE" to stop searching.
        """
        # Prepare context for agent
        current_findings = memory.get_findings_summary()
        previous_searches = "\n".join([
            f"  - '{s['query']}' ({s['result_count']} results)"
            for s in memory.searches_performed[-5:]
        ]) if memory.searches_performed else "  (None yet)"
        
        reasoning_steps = len(memory.reasoning_trail)
        
        prompt = f"""You are an intelligent agent analyzing documents to complete a task.

TASK: {task}

CURRENT FINDINGS:
{current_findings}

PREVIOUS SEARCHES (last 5):
{previous_searches}

REASONING: Based on the task and what you've found so far:
1. What is the task asking for?
2. What information do you already have?
3. What gaps remain?
4. Do you need to search for more information?

Respond with ONE of:
- SEARCH: [your optimal search query] (if you need more info)
- DONE (if you have enough info to complete the task)

Choose wisely. Respond now:"""
        
        try:
            response = self.llm.invoke(prompt).content.strip()
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None
        
        logger.debug(f"Agent decision: {response[:60]}...")
        
        # Parse response
        if response.startswith("SEARCH:"):
            query = response.replace("SEARCH:", "").strip()
            memory.add_reasoning_step(
                f"Analyzed task + findings (iteration {reasoning_steps})",
                f"Decided to search for: '{query}'"
            )
            return query
        elif "DONE" in response or "done" in response.lower():
            memory.add_reasoning_step(
                f"Assessed information completeness",
                "Decided to synthesize findings"
            )
            return "SYNTHESIZE"
        else:
            # Treat as search query
            logger.debug(f"Parsed response as search query")
            memory.add_reasoning_step(
                "Agent reasoning",
                f"Extracted search from response"
            )
            return response[:100]
    
    def _is_duplicate_search(self, query: str, memory: AgentMemory) -> bool:
        """Check if this query was already searched."""
        query_lower = query.lower()
        for search in memory.searches_performed:
            if search["query"].lower() == query_lower:
                return True
        return False
    
    def _analyze_results(
        self,
        query: str,
        results: List[Dict],
        memory: AgentMemory
    ):
        """
        Agent analyzes search results and extracts key information.
        """
        if not results:
            return
        
        # Extract findings from top results
        for i, result in enumerate(results[:2]):  # Analyze top 2
            category = self._categorize_finding(query)
            memory.add_finding(
                key=category,
                value=result["content"][:200],
                source=result.get("source", "unknown")
            )
            logger.debug(f"Extracted finding #{i+1}: {category}")
    
    @staticmethod
    def _categorize_finding(query: str) -> str:
        """Categorize finding based on search query."""
        query_lower = query.lower()
        
        if any(w in query_lower for w in ["termination", "terminate", "end", "cancel"]):
            return "termination_clauses"
        elif any(w in query_lower for w in ["payment", "fee", "penalty", "cost", "price"]):
            return "financial_terms"
        elif any(w in query_lower for w in ["definition", "define", "meaning"]):
            return "definitions"
        elif any(w in query_lower for w in ["liability", "indemnif", "responsible"]):
            return "liability_terms"
        elif any(w in query_lower for w in ["force majeure", "hardship", "exception"]):
            return "exceptions"
        else:
            return "general_findings"
    
    def _synthesize(self, task: str, memory: AgentMemory) -> str:
        """
        Agent synthesizes gathered information into final answer.
        """
        # Prepare findings for synthesis
        findings_text = ""
        for key, findings in memory.gathered_info.items():
            findings_text += f"\n{key}:\n"
            for finding in findings:
                findings_text += f"  - {finding['value']}\n"
        
        if not findings_text:
            findings_text = "(No findings gathered)"
        
        prompt = f"""You are synthesizing information to complete a document analysis task.

TASK: {task}

GATHERED INFORMATION FROM SEARCHES:
{findings_text}

SEARCH QUERIES PERFORMED:
{chr(10).join([f"  - '{s['query']}'" for s in memory.searches_performed])}

Please synthesize this information into a comprehensive answer for the task.
Be specific and cite findings when possible.

COMPREHENSIVE ANSWER:"""
        
        try:
            response = self.llm.invoke(prompt).content.strip()
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            response = "Synthesis failed. Here are the gathered findings:\n" + findings_text
        
        logger.info("Synthesis complete")
        return response


# ============================================================================
# SECTION 4: EXAMPLE USAGE & HELPERS
# ============================================================================

def create_sample_vector_store():
    """Create sample vector store with contract data."""
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain.schema import Document
    
    # Sample contract data
    contract_chunks = [
        Document(
            page_content="TERMINATION: Either party may terminate this agreement with 30 days written notice. Termination is effective on the date specified in the notice.",
            metadata={"section": "Termination", "page": 15}
        ),
        Document(
            page_content="EARLY TERMINATION FEE: If terminated before the end of the initial term, the terminating party shall pay 10% of the remaining contract value as an early termination fee.",
            metadata={"section": "Fees", "page": 16}
        ),
        Document(
            page_content="PAYMENT TERMS: Payment is due within 30 days of invoice. Late payments incur a 1.5% monthly interest charge.",
            metadata={"section": "Payment", "page": 5}
        ),
        Document(
            page_content="LIABILITY LIMITATION: Neither party shall be liable for indirect, incidental, or consequential damages. Total liability limited to fees paid in the 12 months prior to the claim.",
            metadata={"section": "Liability", "page": 20}
        ),
        Document(
            page_content="FORCE MAJEURE: Neither party is liable for failure to perform due to force majeure events including acts of God, natural disasters, or war. Party must notify within 5 days.",
            metadata={"section": "Force Majeure", "page": 22}
        ),
        Document(
            page_content="INDEMNIFICATION: Each party shall indemnify the other against third-party claims arising from its breach of this agreement or violation of applicable law.",
            metadata={"section": "Indemnification", "page": 18}
        ),
        Document(
            page_content="DEFINITIONS: 'Agreement' means this document and all exhibits. 'Confidential Information' means non-public information marked as confidential or reasonably understood to be confidential.",
            metadata={"section": "Definitions", "page": 1}
        ),
        Document(
            page_content="MINIMUM COMMITMENT: The client commits to a minimum monthly payment of $10,000 for the duration of the term. If usage falls below this, the difference is billed as a minimum commitment.",
            metadata={"section": "Commitment", "page": 8}
        ),
    ]
    
    try:
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
    except Exception:
        from langchain_openai import OpenAIEmbeddings
        embeddings = OpenAIEmbeddings()
    
    # Create vector store
    vector_store = Chroma.from_documents(
        contract_chunks,
        embeddings,
        collection_name="contract_analysis",
    )
    
    return vector_store


def create_agentic_workflow(
    vector_store=None,
    max_iterations: int = 5,
) -> AgentWorkflow:
    """
    Create and initialize an agentic workflow.
    
    Args:
        vector_store: Optional vector store (creates sample if None)
        max_iterations: Maximum iterations for agent loop
        
    Returns:
        Initialized AgentWorkflow
    """
    if vector_store is None:
        vector_store = create_sample_vector_store()
    
    workflow = AgentWorkflow(
        vector_store=vector_store,
        max_iterations=max_iterations,
        max_search_results=5,
    )
    
    return workflow


def demo_contract_analysis():
    """Demonstrate agentic workflow on contract analysis task."""
    print("=" * 80)
    print("DEMO: Agentic Workflow for Contract Analysis")
    print("=" * 80)
    
    workflow = create_agentic_workflow(max_iterations=5)
    
    task = (
        "Summarize the key terms of this service contract. "
        "Specifically identify: termination conditions, payment obligations, "
        "liability limitations, and any force majeure clauses."
    )
    
    print(f"\n📋 TASK:\n{task}\n")
    print("-" * 80)
    
    # Execute workflow
    result = workflow.execute_task(task)
    
    # Display results
    print(f"\n🤖 AGENT WORKFLOW RESULTS:")
    print(f"  Iterations: {result['iterations']}")
    print(f"  Stop Reason: {result['stop_reason']}")
    print(f"  Duration: {result['duration_seconds']:.2f}s")
    print(f"  Searches: {len(result['searches'])}")
    
    print(f"\n🔍 SEARCH TRAIL:")
    for i, search in enumerate(result["searches"], 1):
        print(f"  {i}. Query: '{search['query']}' ({search['result_count']} results)")
    
    print(f"\n💭 REASONING TRAIL:")
    for i, step in enumerate(result["reasoning_trail"], 1):
        print(f"  {i}. {step['step']}")
        print(f"     → {step['decision']}")
    
    print(f"\n📊 FINDINGS:")
    for key, findings in result["findings"].items():
        print(f"  {key}:")
        for i, finding in enumerate(findings[:1], 1):  # Show first
            preview = finding["value"][:100]
            print(f"    - {preview}...")
    
    print(f"\n✅ SYNTHESIS:\n")
    print(result["answer"])
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demo_contract_analysis()
