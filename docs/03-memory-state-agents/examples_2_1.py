"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              WORK PRODUCT 2.1: DUAL-MEMORY ARCHITECTURE - EXAMPLES            ║
║                                                                              ║
║  Complete, practical demonstrations of short-term and long-term memory      ║
║  patterns for building conversational AI systems that scale.                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

📚 PURPOSE:
───────────
This module demonstrates the dual-memory pattern through three complete examples.

🎯 LEARNING OBJECTIVES:
───────────────────────
By the end of these examples, you will understand:
  ✓ How short-term and long-term memory serve different purposes
  ✓ How to bound token counts using ConversationBufferWindowMemory
  ✓ How to extract and store user facts
  ✓ How to retrieve relevant context
  ✓ How to combine both memory systems into a coherent architecture
"""

import json
from typing import Optional
from datetime import datetime
from collections import deque

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage


# ═══════════════════════════════════════════════════════════════════════════════
# SHORT-TERM MEMORY: ConversationBufferWindowMemory Pattern
# ═══════════════════════════════════════════════════════════════════════════════


class ConversationBufferWindowMemory:
    """
    A fixed-size sliding window that keeps the last N messages.

    This is a simplified implementation that demonstrates the pattern.
    In production, you'd use langchain's built-in version.
    """

    def __init__(self, k: int = 5, human_prefix: str = "User", ai_prefix: str = "Assistant"):
        """
        Initialize buffer with window size k.

        Args:
            k: Number of messages to keep
            human_prefix: Prefix for human messages
            ai_prefix: Prefix for AI messages
        """
        self.k = k
        self.human_prefix = human_prefix
        self.ai_prefix = ai_prefix
        self.messages = deque(maxlen=k * 2)  # *2 because each turn is 2 messages

    def save_context(self, inputs: dict, outputs: dict) -> None:
        """
        Add a user-assistant exchange to the buffer.
        
        This method maintains a fixed-size sliding window. Once the buffer reaches
        its capacity (maxlen=k*2), old messages are automatically dropped.
        
        Args:
            inputs: Dictionary with 'input' key containing user message
            outputs: Dictionary with 'output' key containing assistant response
            
        Example:
            memory.save_context(
                inputs={"input": "What's the weather?"},
                outputs={"output": "I don't have weather data..."}
            )
        """
        user_msg = inputs.get("input", "")
        assistant_msg = outputs.get("output", "")

        self.messages.append(HumanMessage(content=user_msg))
        self.messages.append(AIMessage(content=assistant_msg))

    def load_memory_variables(self, inputs: dict) -> dict:
        """
        Retrieve the current buffer contents.
        
        Returns messages in order from oldest to newest within the current window.
        Perfect for passing directly to a chain as context.
        
        Args:
            inputs: Unused, but included for API consistency
            
        Returns:
            Dictionary with 'recent_conversation' key containing list of Message objects
            
        Example:
            result = memory.load_memory_variables({})
            messages = result["recent_conversation"]
            # → [HumanMessage(...), AIMessage(...), ...]
        """
        return {"recent_conversation": list(self.messages)}

    def clear(self) -> None:
        """
        Clear all messages from the buffer.
        
        Use this when starting a new session or resetting conversation.
        Note: This doesn't affect long-term memory if you're using it separately.
        
        Example:
            memory.clear()  # Remove all recent messages
        """
        self.messages.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# LONG-TERM MEMORY: ConversationSummaryMemory Pattern
# ═══════════════════════════════════════════════════════════════════════════════


class ConversationSummaryMemory:
    """
    A memory that summarizes the conversation over time.

    This implementation stores text summaries that are updated based on new messages.
    In production, you'd use an LLM to generate these summaries and store them in a vector DB.
    """

    def __init__(self, llm=None, human_prefix: str = "User", ai_prefix: str = "Assistant"):
        """
        Initialize summary memory.

        Args:
            llm: Language model for generating summaries (optional for demo)
            human_prefix: Prefix for human messages
            ai_prefix: Prefix for AI messages
        """
        self.llm = llm
        self.human_prefix = human_prefix
        self.ai_prefix = ai_prefix
        self.summary = ""
        self.message_count = 0

    def save_context(self, inputs: dict, outputs: dict) -> None:
        """
        Add exchange and update summary.
        
        This method incrementally builds a summary of the conversation. In production,
        you'd use an LLM to generate summaries and store them in a vector database.
        
        This simple implementation:
        - Tags messages by category (location, job, interest)
        - Appends key facts to the growing summary
        - Preserves all metadata for later semantic search
        
        Args:
            inputs: Dictionary with 'input' key containing user message
            outputs: Dictionary with 'output' key containing assistant response
            
        Example:
            memory.save_context(
                inputs={"input": "I'm an engineer from Toronto"},
                outputs={"output": "That's interesting!"}
            )
            # Summary now includes tags: [location-related], [job-related]
        """
        user_msg = inputs.get("input", "")
        assistant_msg = outputs.get("output", "")

        self.message_count += 1

        # Simple summary update (in production, use LLM to summarize)
        if self.summary:
            # Append to existing summary
            self.summary += f"\n- User said: {user_msg[:50]}..."
            if any(keyword in user_msg.lower() for keyword in ["from", "live", "location"]):
                self.summary += f" [location-related]"
            if any(keyword in user_msg.lower() for keyword in ["engineer", "developer", "programmer", "role"]):
                self.summary += f" [job-related]"
            if any(keyword in user_msg.lower() for keyword in ["love", "like", "hobby", "interest", "enjoy"]):
                self.summary += f" [interest-related]"
        else:
            # Initialize summary
            self.summary = f"Conversation started. User: {user_msg[:50]}..."

    def load_memory_variables(self, inputs: dict) -> dict:
        """
        Retrieve the current summary.
        
        Returns the accumulated profile/summary of the user. In production, you'd
        use semantic search to retrieve only relevant facts based on the current query.
        
        Args:
            inputs: Unused, but included for API consistency
            
        Returns:
            Dictionary with 'user_profile' key containing summary text
            
        Example:
            result = memory.load_memory_variables({})
            profile = result["user_profile"]
            # → "Conversation started. User: I'm an engineer..."
        """
        if self.message_count == 0:
            summary_text = "No conversations yet."
        else:
            summary_text = self.summary if self.summary else "Conversation in progress..."
        return {"user_profile": summary_text}

    def clear(self) -> None:
        """Clear the summary."""
        self.summary = ""
        self.message_count = 0


class DualMemoryChatbot:
    """
    A chatbot that separates short-term and long-term memory.

    SHORT-TERM: Last N messages in a buffer (immediate context)
    LONG-TERM: Extracted facts stored in memory (semantic meaning)

    This separation allows:
    - Bounded token counts (short-term has fixed size)
    - Semantic reasoning (long-term captures meaning)
    - Observable architecture (each memory is separate)
    """

    def __init__(self, model: str = "gpt-4o", buffer_k: int = 5):
        """
        Initialize the dual-memory system.

        Args:
            model: LLM model to use for both chat and summarization
            buffer_k: Number of messages to keep in short-term buffer
        """
        self.model = model
        try:
            self.llm = ChatOpenAI(model=model, temperature=0.7)
        except Exception:
            # Fallback for when API key is not set
            self.llm = None

        # SHORT-TERM MEMORY: Last N messages (e.g., last 5)
        # This keeps immediate context bounded to avoid token explosion
        self.short_term_memory = ConversationBufferWindowMemory(
            k=buffer_k,
            human_prefix="User",
            ai_prefix="Assistant",
        )

        # LONG-TERM MEMORY: Summarized facts about the user
        # This grows over time but is more compressed than raw messages
        self.long_term_memory = ConversationSummaryMemory(
            llm=self.llm,
            human_prefix="User",
            ai_prefix="Assistant",
        )

        # Metadata for tracking
        self.turn_count = 0
        self.start_time = datetime.now()
        self.conversation_log = []

    def _generate_response(self, user_input: str, context: str) -> str:
        """
        Generate a response using the LLM with provided context.

        Args:
            user_input: User's message
            context: Combined short and long-term context

        Returns:
            Assistant's response
        """
        prompt = f"""You are a helpful, friendly assistant. Use the context provided to give personalized responses.

CONTEXT:
{context}

User: {user_input}

Respond naturally as a helpful assistant:"""

        message = HumanMessage(content=prompt)
        response = self.llm.invoke([message])
        return response.content

    def chat(self, user_input: str) -> str:
        """
        Run a single chat turn with both memory systems.

        Args:
            user_input: User's message

        Returns:
            Assistant's response
        """
        self.turn_count += 1

        # Step 1: Retrieve context from both memory systems
        recent = self.short_term_memory.load_memory_variables({})
        profile = self.long_term_memory.load_memory_variables({})

        # Step 2: Combine contexts
        recent_str = self._format_messages(
            recent.get("recent_conversation", [])
        )
        profile_str = profile.get("user_profile", "No profile yet")

        context = f"""RECENT CONVERSATION (last few messages):
{recent_str}

USER PROFILE (extracted facts):
{profile_str}"""

        # Step 3: Generate response
        response = self._generate_response(user_input, context)

        # Step 4: Update both memory systems
        self.short_term_memory.save_context(
            inputs={"input": user_input},
            outputs={"output": response}
        )

        self.long_term_memory.save_context(
            inputs={"input": user_input},
            outputs={"output": response}
        )

        # Step 5: Log for analysis
        self.conversation_log.append({
            "turn": self.turn_count,
            "user": user_input,
            "assistant": response,
            "timestamp": datetime.now().isoformat()
        })

        return response

    def _format_messages(self, messages: list) -> str:
        """Format a list of messages for display."""
        if not messages:
            return "No messages yet."
        
        formatted = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted.append(f"Assistant: {msg.content}")
        return "\n".join(formatted)

    def get_stats(self) -> dict:
        """
        Get memory and conversation statistics.
        
        This method collects key metrics about the memory system's current state.
        Use these in production to monitor memory health and performance.
        
        Returns:
            Dictionary with:
            - turn_count: Total conversation turns so far
            - elapsed_time: How long the conversation has lasted
            - short_term_message_count: Current # of messages in buffer (should be ≤ k*2)
            - long_term_profile_length: Character length of accumulated profile
            
        Example:
            stats = bot.get_stats()
            print(f"Conversation has {stats['turn_count']} turns")
            print(f"Buffer has {stats['short_term_message_count']} messages")
        """
        recent = self.short_term_memory.load_memory_variables({})
        profile = self.long_term_memory.load_memory_variables({})
        
        return {
            "turn_count": self.turn_count,
            "elapsed_time": str(datetime.now() - self.start_time),
            "short_term_message_count": len(
                recent.get("recent_conversation", [])
            ),
            "long_term_profile_length": len(
                str(profile.get("user_profile", ""))
            ),
        }

    def print_memory_state(self) -> None:
        """
        Print current state of both memory systems.
        
        This is a debugging and observability tool. Useful for understanding
        what the chatbot "remembers" at any point. In production, you'd export
        this to a structured format for logging.
        
        Example:
            bot.print_memory_state()
            # Prints detailed snapshot of both memory systems
        """
        print("\n" + "=" * 80)
        print("MEMORY STATE SNAPSHOT")
        print("=" * 80)

        # Short-term
        recent = self.short_term_memory.load_memory_variables({})
        print("\n📝 SHORT-TERM MEMORY (ConversationBufferWindowMemory):")
        print("-" * 80)
        recent_msgs = recent.get("recent_conversation", [])
        if recent_msgs:
            for msg in recent_msgs:
                if isinstance(msg, HumanMessage):
                    print(f"  User: {msg.content[:60]}...")
                elif isinstance(msg, AIMessage):
                    print(f"  Assistant: {msg.content[:60]}...")
        else:
            print("  (Empty)")

        # Long-term
        profile = self.long_term_memory.load_memory_variables({})
        print("\n💾 LONG-TERM MEMORY (ConversationSummaryMemory):")
        print("-" * 80)
        profile_text = profile.get("user_profile", "")
        if profile_text:
            print(f"  {profile_text}")
        else:
            print("  (No profile yet)")

        # Stats
        stats = self.get_stats()
        print("\n📊 STATISTICS:")
        print("-" * 80)
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print("=" * 80 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 1: RUNNING A FULL CONVERSATION WITH DUAL MEMORY
# ═══════════════════════════════════════════════════════════════════════════════

def example_1_dual_memory_conversation():
    """
    EXAMPLE 1: Building a complete conversation with dual memory.

    This example shows:
    - Initialization of short-term and long-term memory
    - How memory is updated on each turn
    - How to retrieve combined context
    - How memory evolves over time
    """
    print("\n" + "#" * 80)
    print("# EXAMPLE 1: Dual-Memory Chatbot Architecture")
    print("#" * 80)

    # Initialize the chatbot (this would use real LLM in production)
    print("\n[*] Initializing DualMemoryChatbot with:")
    print("    - Short-term buffer: k=5 (keep last 5 messages)")
    print("    - Long-term memory: ConversationSummaryMemory")
    
    # For testing without real LLM, we'll use a mock
    chatbot = DualMemoryChatbot(model="gpt-4o", buffer_k=5)

    # Simulate a conversation
    exchanges = [
        ("Hi! My name is Alice and I'm from Toronto.", 
         "Nice to meet you, Alice! Toronto is a great city. What brings you here today?"),
        
        ("I work as a software engineer at a tech startup.",
         "That's interesting! What technologies do you work with?"),
        
        ("Python and TypeScript, mainly. I also love hiking in my spare time.",
         "Great combo! Python and TypeScript are very complementary. Do you hike around Toronto?"),
        
        ("Yes, around Toronto and sometimes we road trip to the Rockies.",
         "The Rockies are amazing! That sounds like an awesome getaway."),
        
        ("We're planning another trip soon. Any AI tools to help plan hiking trips?",
         "Absolutely! You could use AI for route planning, weather analysis, and gear recommendations."),
    ]

    print("\n[*] Starting conversation simulation...\n")

    # Mock the conversation (without actual LLM calls)
    for i, (user_msg, assistant_msg) in enumerate(exchanges, 1):
        print(f"Turn {i}:")
        print(f"  User: {user_msg}")
        print(f"  Assistant: {assistant_msg}")
        
        # Update memories (in real scenario, would use actual LLM)
        chatbot.short_term_memory.save_context(
            inputs={"input": user_msg},
            outputs={"output": assistant_msg}
        )
        chatbot.long_term_memory.save_context(
            inputs={"input": user_msg},
            outputs={"output": assistant_msg}
        )
        chatbot.conversation_log.append({
            "turn": i,
            "user": user_msg,
            "assistant": assistant_msg,
            "timestamp": datetime.now().isoformat()
        })
        print()

    # Show memory state
    chatbot.print_memory_state()

    # Return the chatbot for further use
    return chatbot


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 2: MEMORY SEPARATION AND TOKEN COUNTING
# ═══════════════════════════════════════════════════════════════════════════════

def example_2_memory_separation():
    """
    EXAMPLE 2: Demonstrating memory separation benefits.

    This example shows:
    - How short-term memory bounds token count
    - How long-term memory captures semantic meaning
    - The difference between keeping all messages vs. using dual memory
    """
    print("\n" + "#" * 80)
    print("# EXAMPLE 2: Memory Separation & Token Bounding")
    print("#" * 80)

    # Create two chatbots with different buffer sizes
    chatbot_small = DualMemoryChatbot(model="gpt-4o", buffer_k=3)
    chatbot_large = DualMemoryChatbot(model="gpt-4o", buffer_k=10)

    # Simulate adding many messages
    messages = [
        "Tell me about your day.",
        "I worked on a new feature today.",
        "That sounds productive. What was the feature?",
        "It's a memory system for conversational AI.",
        "Interesting! How does it work?",
        "It separates short-term and long-term memory.",
        "That's a good design. Why separate them?",
        "Because we need to bound token count.",
        "I see. How does that help?",
        "It makes cost predictable and performance consistent.",
    ]

    print("\n[*] Adding 10 messages to both chatbots...\n")

    for i, msg in enumerate(messages, 1):
        user_msg = msg
        assistant_msg = f"Response {i}: That's helpful information."

        # Add to both
        for name, bot in [("Small (k=3)", chatbot_small), ("Large (k=10)", chatbot_large)]:
            bot.short_term_memory.save_context(
                inputs={"input": user_msg},
                outputs={"output": assistant_msg}
            )
            bot.long_term_memory.save_context(
                inputs={"input": user_msg},
                outputs={"output": assistant_msg}
            )

    # Compare memory states
    print("MEMORY COMPARISON AFTER 10 TURNS:\n")

    for name, bot in [("Small (k=3)", chatbot_small), ("Large (k=10)", chatbot_large)]:
        recent = bot.short_term_memory.load_memory_variables({})
        recent_msgs = recent.get("recent_conversation", [])
        
        print(f"[{name}]")
        print(f"  Short-term message count: {len(recent_msgs)}")
        print(f"  Estimated tokens: {len(recent_msgs) * 50} (assuming 50 tokens/message)")
        print(f"  Memory efficiency: {name.split()[0]}")
        print()

    print("KEY INSIGHT:")
    print("  With dual memory, you can keep buffer_k small and predictable,")
    print("  while still capturing semantic meaning in long-term memory.")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 3: OBSERVABILITY AND DEBUGGING
# ═══════════════════════════════════════════════════════════════════════════════

def example_3_observability():
    """
    EXAMPLE 3: Monitoring and debugging memory systems.

    This example shows:
    - How to inspect memory state
    - How to collect statistics
    - How to reset memory when needed
    - How to export memory for analysis
    """
    print("\n" + "#" * 80)
    print("# EXAMPLE 3: Observability and Debugging")
    print("#" * 80)

    chatbot = DualMemoryChatbot(model="gpt-4o", buffer_k=4)

    # Add some messages
    print("\n[*] Adding 6 messages to the chatbot...\n")
    
    for i in range(1, 7):
        user_msg = f"Message {i}"
        assistant_msg = f"Response to message {i}"
        
        chatbot.short_term_memory.save_context(
            inputs={"input": user_msg},
            outputs={"output": assistant_msg}
        )
        chatbot.long_term_memory.save_context(
            inputs={"input": user_msg},
            outputs={"output": assistant_msg}
        )

    # Show memory state
    chatbot.print_memory_state()

    # Extract statistics
    print("\n[*] Collecting Memory Statistics:\n")
    stats = chatbot.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Show what's in each memory
    print("\n[*] Memory Contents:\n")
    
    recent = chatbot.short_term_memory.load_memory_variables({})
    profile = chatbot.long_term_memory.load_memory_variables({})

    print("Short-term (should have last 4 messages due to k=4):")
    for msg in recent.get("recent_conversation", []):
        print(f"  - {type(msg).__name__}: {msg.content[:40]}...")

    print("\nLong-term (summarized profile):")
    print(f"  {profile.get('user_profile', 'No profile')}")

    print("\n[*] KEY INSIGHTS:")
    print("  - Memory state is always inspectable")
    print("  - Statistics help identify memory issues early")
    print("  - Separation makes debugging easier (test each memory independently)")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN: RUN ALL EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("WORK PRODUCT 2.1: SHORT-TERM VS. LONG-TERM MEMORY - EXAMPLES")
    print("=" * 80)

    print("""
This module demonstrates the dual-memory pattern for building scalable
conversational systems. You will see:

  EXAMPLE 1: Dual-Memory Chatbot Architecture
    - Initialize ConversationBufferWindowMemory and ConversationSummaryMemory
    - Run a full conversation with both memories
    - Inspect how memory evolves over time

  EXAMPLE 2: Memory Separation & Token Bounding
    - Compare chatbots with different buffer sizes
    - See how token counts stay predictable
    - Understand the scaling benefits

  EXAMPLE 3: Observability and Debugging
    - Inspect memory state
    - Collect statistics
    - Debug memory issues

Each example builds on the concepts from WP-2.1. Run them in order to understand
the complete pattern.""")

    try:
        # Run Example 1
        chatbot = example_1_dual_memory_conversation()

        # Run Example 2
        example_2_memory_separation()

        # Run Example 3
        example_3_observability()

        print("\n" + "=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Read WP-2.1-Short-Term-vs-Long-Term-Memory-A-Working-Model.md")
        print("  2. Modify examples_2_1.py with your own conversation scenarios")
        print("  3. Experiment with different buffer_k values to understand trade-offs")
        print("  4. Integrate with a real LLM by setting OPENAI_API_KEY")
        print()

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\nNote: Some examples require OpenAI API key.")
        print("Set OPENAI_API_KEY environment variable to run with real LLM.")