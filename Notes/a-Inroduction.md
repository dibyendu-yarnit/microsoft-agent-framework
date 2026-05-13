# **Microsoft Agent Framework (MAF)**

> **Version**: 1.0 GA (Released April 3, 2026)  
> **Language**: Python (Primary Focus)  
> **Install**: `pip install agent-framework`  
> **GitHub**: https://github.com/microsoft/agent-framework  
> **Docs**: https://learn.microsoft.com/en-us/agent-framework/

---

## Table of Contents

1. [Framework Overview](#1-framework-overview)
2. [Agents](#2-agents)
   - 2.1 Overview
   - 2.2 Running an Agent
   - 2.3 Agent Pipeline
   - 2.4 Multimodal
   - 2.5 Structured Outputs
   - 2.6 Background Response
   - 2.7 Declarative Agents
   - 2.8 Observability
   - 2.9 Agent Skills
   - 2.10 CodeAct
   - 2.11 Agent Safety
3. [Tools](#3-tools)
   - 3.1 Overview
   - 3.2 Functional Tools
   - 3.3 Tool Approval
   - 3.4 Code Interpreter
   - 3.5 File Search
   - 3.6 Web Search
   - 3.7 Hosted MCP Tools
   - 3.8 Local MCP Tools
4. [Conversations & Memory](#4-conversations--memory)
   - 4.1 Overview
   - 4.2 Session
   - 4.3 Context Provider
   - 4.4 Storage
   - 4.5 Compaction
5. [Middleware](#5-middleware)
   - 5.1 Overview
   - 5.2 Defining Middleware
   - 5.3 Chat-Level Middleware
   - 5.4 Agent & Run Scope
   - 5.5 Terminations & Guardrails
   - 5.6 Results Overrides
   - 5.7 Exception Handling
   - 5.8 Shared State
   - 5.9 Running Context
6. [Workflows](#6-workflows)
   - 6.1 Overview
   - 6.2 Functional Workflow API
   - 6.3 Graph-Based Workflows
   - 6.4 Orchestration Patterns
   - 6.5 Advanced Execution
7. [DevUI](#7-devui)
8. [Architecture Diagram](#8-architecture-diagram)
9. [Best Practices Summary](#9-best-practices-summary)

---

## 1. Framework Overview

### What is Microsoft Agent Framework?

Microsoft Agent Framework (MAF) is an **open-source, production-ready SDK and runtime** for building, orchestrating, and deploying AI agents and multi-agent workflows — in both **Python** and **.NET**.

It is the **direct successor to both AutoGen and Semantic Kernel**, combining:
- AutoGen's **simple, expressive agent abstractions**
- Semantic Kernel's **enterprise-grade features**: session state, type safety, telemetry, middleware

MAF was released as **GA v1.0 on April 3, 2026**, with a long-term support commitment.

### Why It Matters

| Problem | MAF Solution |
|---|---|
| Too many fragmented agent SDKs | Single unified SDK across .NET and Python |
| No enterprise memory management | Session-based state + pluggable context providers |
| Tool integration is ad-hoc | Type-safe function tools + hosted MCP support |
| Multi-agent orchestration is complex | Built-in Sequential, Concurrent, Handoff, Group Chat |
| Hard to debug agents | DevUI + OpenTelemetry built in |
| Vendor lock-in to one LLM | Multi-provider: Azure OpenAI, OpenAI, Anthropic, Bedrock, Gemini, Ollama |

### Two Primary Capability Pillars

```
┌─────────────────────────────────────────────────────────────────┐
│                  Microsoft Agent Framework                      │
├───────────────────────────┬─────────────────────────────────────┤
│         AGENTS            │            WORKFLOWS                │
│  Individual LLM units     │  Graph-based multi-step processes   │
│  with tools & memory      │  with agents + functions            │
│  Open-ended, autonomous   │  Deterministic, explicit control    │
└───────────────────────────┴─────────────────────────────────────┘
```

### Quick Start (5 lines)

```python
# pip install agent-framework
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="MyAgent",
        instructions="You are a helpful assistant. Keep answers brief.",
    )
    result = await agent.run("What is the capital of France?")
    print(result)  # "Paris is the capital of France."

asyncio.run(main())
```

---

## 2. Agents

### 2.1 Overview

**Description**: An Agent in MAF is a **stateful execution unit** powered by an LLM. It receives inputs (text, images, files), reasons about them using LLM capabilities, optionally calls tools, and returns a response. Agents are NOT just prompt wrappers — they maintain conversation state, use middleware pipelines, and integrate with memory systems.

**Core Properties of an Agent**:
- `name` — Agent identifier (used in multi-agent routing)
- `instructions` — System prompt that defines behavior
- `client` — LLM provider client (Azure OpenAI, Anthropic, etc.)
- `tools` — List of callable functions
- `context_providers` — Memory and context injection
- `middleware` — Request/response interceptors

**Supported Providers**: Azure OpenAI, OpenAI, Microsoft Foundry, Anthropic Claude, Amazon Bedrock, Google Gemini, Ollama, GitHub Copilot.

**Use Cases**: Customer service bots, coding assistants, research agents, document analysis, data wrangling.

**Best Practice**: Always give agents a meaningful `name` — it appears in logs, traces, and multi-agent routing tables.

---

### 2.2 Running an Agent

**Description**: MAF supports both **streaming** and **non-streaming** agent runs. Non-streaming (`agent.run()`) returns the complete response after all LLM turns are done. Streaming (`agent.run(..., stream=True)`) yields token-by-token events, essential for real-time UX.

**Architecture**:
```
User Input → Agent.run() → LLM Call → Tool Calls (if needed) → Final Response
                        ↕
                  Middleware Pipeline
                        ↕
                  Context Providers (Memory)
```

**Example — Non-Streaming vs Streaming**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

async def main():
    client = OpenAIChatClient()
    agent = Agent(
        client=client,
        name="AssistantAgent",
        instructions="You are a concise technical assistant.",
    )

    # --- Non-Streaming: complete response ---
    result = await agent.run("Explain async/await in Python in 2 sentences.")
    print(f"[Non-streaming]: {result}")

    # --- Streaming: token by token ---
    print("[Streaming]: ", end="", flush=True)
    async for event in agent.run("Write a haiku about agents.", stream=True):
        if event.type == "text_delta":
            print(event.data, end="", flush=True)
    print()

asyncio.run(main())
```

**Best Practice**: Use streaming for any user-facing interface. Use non-streaming for background pipelines where you only care about the final result.

---

### 2.3 Agent Pipeline

**Description**: The Agent Pipeline is the **internal execution lifecycle** of a single agent turn. Every run passes through: input processing → middleware chain → LLM call → tool execution (if needed) → middleware post-processing → output. This pipeline can be intercepted at every step.

**Pipeline Stages**:
```
[Input] → [Pre-Middleware] → [LLM Request] → [Tool Execution Loop]
                                                       ↓
[Output] ← [Post-Middleware] ← [Final LLM Response] ←─┘
```

**Importance**: Understanding the pipeline is critical for adding logging, safety filters, token counting, and retry logic without touching business logic.

**Example — Pipeline with Tool Loop**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

def get_current_time() -> str:
    """Returns the current UTC time."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def calculate(expression: str) -> str:
    """Safely evaluates a basic math expression."""
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error: {e}"

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="PipelineAgent",
        instructions="You are a helpful assistant. Use tools when needed.",
        tools=[get_current_time, calculate],
    )
    # The pipeline automatically loops: LLM → tool call → LLM → final answer
    result = await agent.run("What is 2^10 and what time is it now?")
    print(result)

asyncio.run(main())
```

**Best Practice**: Keep the tool execution loop bounded. Set a `max_turns` or use termination middleware to prevent infinite LLM-tool loops.

---

### 2.4 Multimodal

**Description**: MAF agents natively support **multimodal inputs** — text, images (base64 or URL), and documents (PDF). The agent passes these to the underlying LLM's vision capabilities. You can combine image analysis with tool calling in the same turn.

**Supported Input Types**: Text, Image URLs, Base64-encoded images, PDF documents.

**Use Cases**: Invoice processing, chart analysis, medical image Q&A, UI screenshot debugging.

**Example**:

```python
import asyncio, base64
from agent_framework import Agent, Message, ImageContent
from agent_framework.openai import OpenAIChatClient

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="VisionAgent",
        instructions="You are a visual analysis expert. Describe images precisely.",
    )

    # --- Multimodal message: image URL + question ---
    messages = [
        Message(
            role="user",
            content=[
                ImageContent(url="https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"),
                "What objects do you see in this image? List them briefly.",
            ]
        )
    ]
    result = await agent.run(messages)
    print(result)

asyncio.run(main())
```

**Best Practice**: Always validate image dimensions and file size before sending to the agent. Large images increase latency and token cost significantly.

---

### 2.5 Structured Outputs

**Description**: MAF supports **typed, schema-validated outputs** from agents using Python dataclasses or Pydantic models. Instead of getting a raw string, the agent returns a validated Python object. This eliminates manual JSON parsing and hallucination of schema structure.

**Why Important**: Removes brittle string parsing. The LLM is instructed to produce JSON that matches your schema, and MAF validates it automatically.

**Use Cases**: Data extraction pipelines, API response generation, form filling, classification tasks.

**Example**:

```python
import asyncio
from dataclasses import dataclass
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

@dataclass
class ProductReview:
    sentiment: str          # "positive", "negative", "neutral"
    score: int              # 1-5
    key_topics: list[str]   # main topics mentioned
    summary: str            # one-line summary

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="ReviewAnalyzer",
        instructions="You are a product review analyst. Extract structured insights.",
        response_format=ProductReview,  # Enforce structured output
    )

    review = """
    I bought this laptop last month. The battery life is fantastic — 12 hours easily.
    But the keyboard feels mushy and the fan is loud under load. Overall decent value.
    """
    result: ProductReview = await agent.run(f"Analyze this review: {review}")
    print(f"Sentiment: {result.sentiment}")
    print(f"Score: {result.score}/5")
    print(f"Topics: {', '.join(result.key_topics)}")
    print(f"Summary: {result.summary}")

asyncio.run(main())
```

**Best Practice**: Use Pydantic models with field validators for production pipelines. Add `.model_validate()` as a secondary safeguard.

---

### 2.6 Background Response

**Description**: Background Response allows agents to **run asynchronously in the background** without blocking the caller. The agent processes the request on a background task and the caller can poll or await the result later. Critical for long-running tasks in web APIs.

**Use Cases**: Webhook-triggered processing, report generation, async batch jobs, fire-and-forget pipelines.

**Example**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="BackgroundAgent",
        instructions="You are a report writer. Generate detailed analysis reports.",
    )

    # Fire the agent run in the background
    task = asyncio.create_task(
        agent.run("Write a 3-paragraph analysis of cloud computing trends in 2026.")
    )

    # Do other work while the agent processes
    print("Agent is working in background...")
    await asyncio.sleep(0)  # yield control

    # Await the result when needed
    result = await task
    print(f"Report ready:\n{result}")

asyncio.run(main())
```

**Best Practice**: In FastAPI/web contexts, use `BackgroundTasks` or a task queue (Celery, Azure Service Bus) for truly durable background runs. Wrap with try/except for timeout and error handling.

---

### 2.7 Declarative Agents

**Description**: MAF supports **YAML-defined agents** where instructions, tools, memory configuration, and provider settings are declared in a version-controlled file. You load and run the agent with a single API call. This decouples agent behavior from application code, enabling GitOps-style agent management.

**Why Important**: Declarative agents are auditable, version-controlled, and can be updated without code deployments. Perfect for enterprise environments.

**agent.yaml**:
```yaml
name: CustomerServiceAgent
provider: azure_openai
model: gpt-4o
instructions: |
  You are a friendly customer service agent for Contoso Electronics.
  Always be polite. Escalate complaints to a human supervisor.
  Never discuss competitors.
tools:
  - name: lookup_order
    description: Look up a customer order by order ID
  - name: get_product_info
    description: Get product specifications and availability
memory:
  history_provider: in_memory
  max_history_turns: 20
```

**Example**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.declarative import load_agent

# Define tools separately
def lookup_order(order_id: str) -> str:
    """Look up a customer order."""
    # Simulated lookup
    return f"Order {order_id}: Shipped on 2026-05-01. Expected delivery: 2026-05-05."

def get_product_info(product_name: str) -> str:
    """Get product specifications."""
    return f"{product_name}: 4K display, 16GB RAM, 512GB SSD. In stock."

async def main():
    # Load agent from YAML declaration
    agent = load_agent(
        "agent.yaml",
        tools=[lookup_order, get_product_info]
    )
    result = await agent.run("What's the status of my order #12345?")
    print(result)

asyncio.run(main())
```

**Best Practice**: Store agent YAML files in version control. Use environment variable substitution in YAML for secrets (API keys, endpoints).

---

### 2.8 Observability

**Description**: MAF has **built-in OpenTelemetry integration**. Every agent run, tool call, and LLM request emits spans and traces. You can export to Azure Monitor, Jaeger, Zipkin, or any OTLP-compatible backend. This gives you full visibility into agent behavior in production.

**What's Traced**:
- Agent runs (start, end, duration, token counts)
- Individual LLM requests (model, prompt tokens, completion tokens)
- Tool calls (function name, inputs, outputs, duration)
- Middleware execution
- Workflow step transitions

**Example**:

```python
import asyncio
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.telemetry import configure_tracing

# Set up OpenTelemetry with console exporter (use OTLP exporter in production)
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

# Enable MAF tracing
configure_tracing(tracer_provider=provider)

def search_database(query: str) -> str:
    """Search the product database."""
    return f"Found 3 results for '{query}': ProductA, ProductB, ProductC"

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="ObservableAgent",
        instructions="You are a product search assistant.",
        tools=[search_database],
    )
    result = await agent.run("Find me laptops under $1000")
    print(result)
    # All spans (agent run, LLM call, tool call) are printed to console

asyncio.run(main())
```

**Best Practice**: In production, export to Azure Application Insights or Grafana Tempo. Set `OTEL_SERVICE_NAME=your-agent-service` environment variable for easy filtering.

---

### 2.9 Agent Skills

Imagine you hire a new employee. Instead of explaining everything from scratch every time they start a new task, you give them a **company handbook** they can look up whenever needed.

**Agent Skills are that handbook** — but for AI agents.

Without skills, you either:
- Stuff everything into the system prompt (bloated, hits token limits fast)
- Rewrite agent instructions for every new domain (repetitive, unmaintainable)

With skills, you write knowledge **once**, store it somewhere, and any agent can **discover and query it** on demand — only pulling in what it actually needs for the current task.

---

#### The Key Insight — "Discover and Use"

Skills are **not** automatically injected into every prompt. The agent uses **semantic search** to find relevant skill content based on the current task. If the user asks about Python async code, the agent fetches the Python skills. If the user asks about API design, it fetches the API design skill. Irrelevant skills stay on the shelf.

```
User asks: "How should I handle async errors in Python?"
                    ↓
Agent searches skill library semantically
                    ↓
Finds: python-coding.md → fetches relevant section
                    ↓
Injects that section into context → answers with skill knowledge
```

---

#### Skill Type 1 — File-Based Skills: (Markdown / Text files with domain knowledge)

**What it is**: A plain `.md` or `.txt` file sitting on disk. You write domain knowledge in it once. The agent reads it when relevant.

**Real-world analogy**: A printed style guide or coding standards document that a new developer reads when they need it — not memorised upfront, just referenced when the question comes up.

**Example — skills/python-coding.md**:

```markdown
# Python Coding Best Practices

## Async / Await
- Always use `async def` for functions that call external APIs
- Never use `time.sleep()` in async code — use `await asyncio.sleep()`
- Wrap all async operations in try/except for TimeoutError

## Error Handling
- Use specific exceptions, never bare `except:`
- Always log the original exception with `raise ... from e`

## Type Hints
- All function signatures must have type hints
- Use `Optional[str]` not `str | None` for Python < 3.10
```


**Example — skills/shopify-domain.md**:

```markdown
# Shopify Domain Knowledge

## Key Concepts
- A "variant" is a specific version of a product (size, colour)
- "Metafields" store custom data not in the default Shopify schema
- Orders have 5 states: pending, open, closed, cancelled, any

## Common Pitfalls
- The Shopify API rate limit is 2 requests/second on Basic plan
- Inventory is tracked at the variant level, NOT the product level
- Discount codes are case-insensitive but stored uppercase
```

**How the agent uses it**:

```python
    from agent_framework import Agent
    from agent_framework.openai import OpenAIChatClient
    from agent_framework.skills import FileSkillProvider, SkillSet

    # Point at a folder of .md files
    skill_provider = FileSkillProvider(skills_dir="./skills/")

    agent = Agent(
        client=OpenAIChatClient(),
        name="DevAssistant",
        instructions="You are a senior developer. Use your skills to answer questions.",
        skill_set=SkillSet(providers=[skill_provider]),
    )

    # Agent searches skills/python-coding.md automatically
    result = await agent.run("What's wrong with using time.sleep() in async code?")
    # Agent pulls the relevant section and answers correctly
```

**When to use**: Domain knowledge, coding standards, company policies, brand guidelines, product documentation — anything that is reference material, not executable logic.

---

#### Skill Type 2 — Code-Based Skills: (Python functions exposed as skill endpoints)

**What it is**: A Python function that the agent can call to get dynamic, computed knowledge — not static text, but live data or calculations.

**Real-world analogy**: Instead of a printed price list (file-based), this is a live pricing calculator that always returns the current price. The "skill" is the ability to calculate, not a fixed piece of text.

**The difference from a Tool**: Tools **take actions** (send email, write to DB). Code-based skills **provide knowledge** (tell me the formula, compute this, explain this concept). Skills inform. Tools act.

```python
    # skills/pricing_skill.py

    def get_pricing_rules(product_category: str) -> str:
        """
        Skill: Returns the pricing logic for a given product category.
        Agents call this to understand HOW to price, not to set prices.
        """
        rules = {
            "electronics": (
                "Electronics are priced at cost × 1.4 (40% margin). "
                "Apply 10% discount for quantities over 50 units. "
                "Never go below cost × 1.15 — that is the floor."
            ),
            "apparel": (
                "Apparel uses cost × 2.2 (120% margin). "
                "Seasonal items get 30% discount in the last month of season. "
                "Premium lines (branded) never discount more than 15%."
            ),
        }
        return rules.get(product_category, "No specific rules. Use standard 35% margin.")


    def get_tax_guidelines(country: str) -> str:
        """
        Skill: Returns tax handling rules for a country.
        """
        guidelines = {
            "UK":  "Apply 20% VAT. Display prices inclusive of VAT on storefront.",
            "USA": "Tax is state-dependent. Never include tax in listed price.",
            "IN":  "Apply 18% GST for most goods. Food items: 5% GST.",
        }
        return guidelines.get(country, "Consult local tax regulations.")
```

```python
    from agent_framework.skills import CodeSkillProvider, SkillSet

    # Register the functions as skill endpoints
    skill_provider = CodeSkillProvider(
        skill_functions=[get_pricing_rules, get_tax_guidelines]
    )

    agent = Agent(
        client=OpenAIChatClient(),
        name="PricingAgent",
        instructions="You are a pricing specialist. Use skills to apply correct rules.",
        skill_set=SkillSet(providers=[skill_provider]),
    )

    result = await agent.run(
        "A UK customer wants to buy 60 units of electronics at £50 cost each. "
        "What should the final price be?"
    )
    # Agent calls get_pricing_rules("electronics") → gets the formula
    # Agent calls get_tax_guidelines("UK") → gets VAT rules
    # Combines both and calculates: £50 × 1.4 = £70, minus 10% bulk = £63, plus 20% VAT = £75.60
```

**When to use**: When the knowledge needs to be computed, looked up from a live source, or parameterised by input. Pricing rules, eligibility checks, formula lookups, conditional policies.

---

#### Skill Type 3 — Class-Based Skills: (Encapsulated skill providers)

**What it is**: A Python class that bundles multiple related skills together into one reusable, importable package. Think of it as a skill **library** rather than a single skill file.

**Real-world analogy**: A specialist consultant firm. Instead of hiring one person who knows one thing (file-based skill) or one calculator (code-based skill), you bring in a whole consulting firm (class-based skill) that has multiple experts, a database, and structured methodology — all bundled together.

**Why use a class**: When your skills are complex enough to need their own state, configuration, or multiple related methods that belong together logically.

```python
    # skills/ecommerce_skill_provider.py

    class EcommerceSkillProvider:
        """
        A bundled skill library covering all ecommerce domain knowledge.
        One class — multiple skills — imported anywhere.
        """

        def __init__(self, store_type: str = "shopify"):
            self.store_type = store_type
            # Could load from DB, config file, or API on init
            self._policies = self._load_policies()

        def _load_policies(self) -> dict:
            return {
                "return_window_days": 30,
                "free_shipping_threshold": 50.0,
                "max_discount_percent": 40,
            }

        def get_return_policy(self, product_type: str) -> str:
            """Skill: Explains the return policy for a product type."""
            window = self._policies["return_window_days"]
            exceptions = {
                "digital": "Digital products are non-refundable once downloaded.",
                "perishable": "Perishable goods cannot be returned.",
                "custom": "Custom/personalised items cannot be returned.",
            }
            if product_type in exceptions:
                return exceptions[product_type]
            return (
                f"Standard return window is {window} days from delivery. "
                f"Item must be unused and in original packaging. "
                f"Refund processed within 5-7 business days."
            )

        def get_shipping_rules(self, order_value: float, destination: str) -> str:
            """Skill: Returns shipping cost rules based on order and destination."""
            threshold = self._policies["free_shipping_threshold"]
            if order_value >= threshold:
                return f"Order qualifies for FREE shipping (over £{threshold})."
            rates = {"UK": "£3.99 standard (3-5 days), £7.99 express (next day)",
                    "EU": "£9.99 standard (5-10 days)",
                    "USA": "£14.99 standard (7-14 days)"}
            return rates.get(destination, "£19.99 international standard shipping.")

        def get_discount_guardrails(self) -> str:
            """Skill: Explains what discounts agents are allowed to offer."""
            max_pct = self._policies["max_discount_percent"]
            return (
                f"Maximum discount is {max_pct}%. "
                f"Never stack more than 2 discount codes. "
                f"Loyalty members get an additional 5% on top of any offer. "
                f"Flash sales require manager approval for discounts over 25%."
            )
```

```python
    from agent_framework.skills import ClassSkillProvider, SkillSet

    # Instantiate the class — it carries its own state and config
    ecommerce_skills = EcommerceSkillProvider(store_type="shopify")

    skill_provider = ClassSkillProvider(skill_class=ecommerce_skills)

    agent = Agent(
        client=OpenAIChatClient(),
        name="CustomerServiceAgent",
        instructions=(
            "You are a customer service agent for an online store. "
            "Use your skills to give accurate, policy-compliant answers."
        ),
        skill_set=SkillSet(providers=[skill_provider]),
    )

    # Test 1 — return policy question
    r1 = await agent.run("Can I return a custom-engraved watch I ordered last week?")
    # Agent fetches get_return_policy("custom") → "Custom items cannot be returned."

    # Test 2 — shipping question
    r2 = await agent.run("My order is £45. How much is shipping to the UK?")
    # Agent fetches get_shipping_rules(45.0, "UK") → shows £3.99 standard rate

    # Test 3 — discount question
    r3 = await agent.run("Can I give this customer 50% off to keep them happy?")
    # Agent fetches get_discount_guardrails() → "Max 40%. Manager approval needed over 25%."
```

**When to use**: When you have 5+ related skills that share configuration, state, or belong to the same business domain. Build a class, import it anywhere, reuse across multiple agents.

---

**All Three Types — Side by Side**

| | File-Based | Code-Based | Class-Based |
|---|---|---|---|
| **Format** | `.md` / `.txt` file | Python function | Python class |
| **Knowledge type** | Static text, reference | Dynamic, computed | Structured, stateful |
| **Best for** | Docs, standards, policies | Formulas, live lookups | Full domain bundles |
| **Reusability** | Copy the file | Import the function | Import the class |
| **Example** | `python-best-practices.md` | `get_pricing_rules()` | `EcommerceSkillProvider` |
| **Analogy** | Employee handbook | Live calculator | Consulting firm |

---

**One-Paragraph Summary:**

Agent Skills are reusable knowledge packages that agents query on demand using semantic search — they only pull in what is relevant to the current task, rather than bloating every prompt with everything upfront. File-based skills are the simplest — just Markdown files of domain knowledge that read like reference docs. Code-based skills are functions that compute or look up dynamic knowledge with parameters. Class-based skills bundle many related skills into one reusable package with shared state and config. All three serve the same goal: write your domain knowledge once, in the right form, and let any agent discover and use it without you rewriting instructions every time the domain changes.

**Skills Directory Structure**:
```
skills/
├── python-coding.md        # Python best practices
├── data-analysis.md        # Data analysis guidelines
├── api-design.md           # REST API design patterns
└── security-guidelines.md  # Security coding standards
```

**Best Practice**: Keep skill files focused and under 2000 tokens. Use clear headings — the agent uses semantic search over skill content.

---

### 2.10 CodeAct

---

#### The Problem It Solves

Imagine you ask an agent to do this:

> *"Get the sales data for Q1, compare it to Q4, calculate the growth percentage, then format it as a summary report."*

That is **four separate jobs chained together**. Each job depends on the result of the previous one.

---

#### How a Normal Agent Handles This (The Slow Way)

Without CodeAct, the agent works like a person who can only do **one thing at a time** and has to check in with their manager after every single step:

```
Step 1: Agent thinks → "I need Q1 sales" → fetches Q1 data → stops, reports back
Step 2: Agent thinks → "Now I need Q4 sales" → fetches Q4 data → stops, reports back
Step 3: Agent thinks → "Now calculate growth" → runs calculation → stops, reports back
Step 4: Agent thinks → "Now format the report" → formats it → stops, reports back
Step 5: Agent thinks → "Done" → returns final answer
```

**Every single "stop and report back" = one full round trip to the LLM.**

That means 5 separate API calls, 5 waits, and the full conversation history is re-sent to the model every single time. This is slow and expensive.

---

#### How CodeAct Handles This (The Smart Way)

CodeAct works like a manager who, instead of checking in after every step, **writes the full plan on paper first**, hands it to an assistant, and says *"Execute all of this, come back when it's done."*

```
Step 1: Agent thinks once → writes a complete plan covering all 4 jobs
        → hands the plan to a safe execution environment
        → execution environment runs all 4 jobs in sequence
        → brings back the final result
Step 2: Done.
```

**One LLM call. One wait. One result.**

The plan the agent writes is a small Python script — but you do not need to think of it as "code." Think of it as a **structured to-do list** that a machine can execute automatically, where each item on the list is a tool call and the output of one item flows automatically into the next.

---

#### The Sandbox — Why It Is Safe

When CodeAct runs the plan, it runs it inside a **completely isolated sandbox** — a sealed, temporary box that:

- Has **no access** to your real file system
- Has **no access** to your actual database
- Has **no access** to the internet directly
- Can **only call the tools you explicitly registered**
- Gets **destroyed** after the run finishes

Think of it like a locked testing room where a temp worker executes your instructions. They can use the tools you left in the room. They cannot walk out and touch anything else in your building.

---

#### The Performance Numbers — What They Actually Mean

**~50% latency reduction**

If a chained task used to take 12 seconds (because the agent was making 5 separate round trips to the LLM), it now takes around 6 seconds. The time saved is all the waiting between steps — those gaps are simply eliminated.

**~60% token reduction**

Every time a normal agent makes a new LLM call, it resends the entire conversation history as context — every message, every tool result so far. On a 5-step chain, that history gets sent 5 times. CodeAct sends it once. The savings are not just about fewer calls — they compound because the history grows with each step, making later calls increasingly expensive.

---

#### When to USE CodeAct ✅

---

**✅ Data wrangling with multiple tool calls**

This is the ideal scenario. You need to pull data from several places, process it, and combine it into something useful. Each step feeds the next. Without CodeAct, every step is a separate LLM call. With CodeAct, the agent writes the entire sequence upfront and runs it in one shot.

Real example: *"Pull last month's orders from Shopify, filter for returns only, calculate the total refund amount, and group by product category."* — That is four chained operations. Perfect for CodeAct.

---

**✅ Chained lookups (query → process → query again)**

This is when the result of one lookup determines what you look up next. The agent cannot know what to ask for in step 2 until it has seen the answer from step 1.

Real example: *"Find the customer who placed order #5892, then look up all their previous orders, then find the most expensive item they ever bought."* — Step 2 needs the customer ID from step 1. Step 3 needs the order list from step 2. CodeAct handles this dependency chain naturally because the plan is written as a flowing sequence where outputs feed directly into inputs.

---

**✅ Report generation from multiple data sources**

When a report needs data from 3 or 4 different sources — say, Shopify for sales, Google Analytics for traffic, and a spreadsheet for ad spend — a normal agent would make a separate LLM call for each source. CodeAct pulls all of them in one execution run, combines them, and formats the report without ever going back to the LLM between steps.

Real example: *"Generate an executive summary combining this week's sales, top traffic sources, and ad spend ROI."* — Three data sources, one execution, one result.

---

#### When NOT to Use CodeAct ❌

---

**❌ Single-step tasks — it is overkill**

If someone asks *"What is the weather in London right now?"* — that is one tool call. There is nothing to chain. Using CodeAct here is like hiring a project manager to make you a cup of tea. The overhead of setting up the plan, running the sandbox, and returning the result adds complexity with zero benefit.

The rule of thumb: **if the task only needs one tool call, use the tool directly.**

---

**❌ Tasks needing human approval between steps**

This is the most important limitation to understand.

CodeAct runs the entire plan **non-stop, start to finish**, inside the sandbox. It cannot pause in the middle, surface an intermediate result to a human, wait for their decision, and then continue. The whole point of CodeAct is that it runs as one uninterrupted execution.

So if your workflow looks like this:

> Draft email → **Human reviews and approves** → Send email

CodeAct **cannot** handle this. The moment it drafts the email, it would immediately move to sending it — because that is the next step in the plan and there is no mechanism to pause and wait.

For any workflow that has a mandatory human checkpoint between steps — approval gates, review steps, compliance sign-offs — you need a regular workflow with built-in Human-in-the-Loop (HITL) support instead. Those workflows are specifically designed to pause, notify a human, and resume only when cleared.

---

#### The One-Paragraph Summary

CodeAct is the agent equivalent of handing someone a complete to-do list instead of texting them one instruction at a time and waiting for them to reply before sending the next one. The agent writes the full plan in one go — covering every tool it needs to call, in what order, passing results from one step to the next — hands it to a safe execution sandbox, and gets back the final answer without any further back-and-forth with the LLM. It is best suited for chained, multi-step data tasks where each step feeds the next. It is the wrong choice for anything simple enough to need just one tool call, or anything that requires a human to review and approve an intermediate result before the work continues.


**Example**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.codeact import CodeActPlugin  # alpha package

def get_sales_data(region: str) -> dict:
    """Get sales data for a region."""
    data = {
        "north": {"q1": 120000, "q2": 145000, "q3": 132000, "q4": 178000},
        "south": {"q1": 98000,  "q2": 115000, "q3": 109000, "q4": 134000},
    }
    return data.get(region, {})

def calculate_growth(current: float, previous: float) -> float:
    """Calculate percentage growth."""
    return ((current - previous) / previous) * 100

def format_currency(amount: float) -> str:
    """Format a number as currency."""
    return f"${amount:,.0f}"

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="CodeActAgent",
        instructions="""
        You are a sales analyst. When asked to analyze data,
        write a single Python script using call_tool() to gather 
        all data and compute results in one pass.
        """,
        tools=[get_sales_data, calculate_growth, format_currency],
        plugins=[CodeActPlugin()],  # Enable CodeAct pattern
    )

    # Without CodeAct: 6 LLM turns (3 data fetches + 2 calculations + 1 format)
    # With CodeAct: 1 LLM turn (writes script that does all of it)
    result = await agent.run(
        "Compare Q4 vs Q3 sales growth for north and south regions. "
        "Show absolute amounts and growth percentages."
    )
    print(result)

asyncio.run(main())
```

**Best Practice**: CodeAct runs in an isolated sandbox (Hyperlight). Never expose file system or network tools to CodeAct — only pure computation and data retrieval tools.

---

### 2.11 Agent Safety

**Description**: MAF provides multiple layers of **safety and guardrails** for production agents. These include: content safety middleware, tool approval gates, input/output validation, prompt injection detection, and output schema enforcement. Safety is configured as composable middleware, not hardcoded into agent logic.

**Safety Layers**:
1. **Input validation** — Reject malformed or malicious inputs before the LLM sees them
2. **Content safety filters** — Block harmful content (Azure AI Content Safety integration)
3. **Tool approval** — Human-in-the-loop gates before dangerous tool calls
4. **Output validation** — Ensure responses meet schema and policy constraints
5. **Prompt injection detection** — Detect and block adversarial prompt manipulation

**Example**:

```python
import asyncio
from typing import Callable, Awaitable
from agent_framework import Agent, AgentRunContext
from agent_framework.openai import OpenAIChatClient
from agent_framework.middleware import ChatMiddlewareContext

# Custom safety middleware
async def safety_guardrail_middleware(
    context: ChatMiddlewareContext,
    next: Callable[[ChatMiddlewareContext], Awaitable[None]],
) -> None:
    """Block requests containing sensitive data patterns."""
    user_input = context.messages[-1].text if context.messages else ""

    # Block PII patterns (simplified example)
    import re
    pii_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b4[0-9]{12}(?:[0-9]{3})?\b',  # Visa card
    ]
    for pattern in pii_patterns:
        if re.search(pattern, user_input):
            context.result = "I cannot process requests containing sensitive personal data."
            return  # Short-circuit: don't call next()

    # Proceed to actual agent execution
    await next(context)

    # Post-processing: validate output doesn't leak sensitive info
    if context.result and "password" in context.result.lower():
        context.result = "[Response filtered for security compliance]"

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="SafeAgent",
        instructions="You are a helpful assistant.",
        chat_middleware=[safety_guardrail_middleware],
    )

    # This will be blocked by the guardrail
    result = await agent.run("Process payment for card 4111111111111111")
    print(result)  # "I cannot process requests containing sensitive personal data."

    # This proceeds normally
    result = await agent.run("What is the weather like in London?")
    print(result)

asyncio.run(main())
```

**Best Practice**: Layer safety middleware from broad to specific: content safety → PII detection → business rules → output validation. Use Azure AI Content Safety for production-grade moderation.

---

## 3. Tools

### 3.1 Overview

**Description**: Tools are **typed, callable functions** that extend agent capabilities beyond text generation. Tools can read databases, call APIs, execute code, search the web, or interact with any external system. MAF uses Python's type hints and docstrings to automatically generate the tool schema sent to the LLM.

**Tool Resolution Flow**:
```
LLM decides to call a tool
       ↓
MAF extracts tool name + arguments from LLM response
       ↓
MAF validates arguments against tool schema
       ↓
Tool function is called
       ↓
Result is added to conversation and LLM continues
```

**Best Practice**: Write clear docstrings — the LLM reads them to decide when and how to call the tool. Always include parameter descriptions and return value descriptions.

---

### 3.2 Functional Tools

**Description**: Any Python function can be a tool. MAF automatically extracts the schema from type hints and docstrings. Functions can be sync or async. The agent calls them automatically based on LLM reasoning.

**Example**:

```python
import asyncio
from datetime import datetime
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

# Sync tool
def get_weather(city: str, unit: str = "celsius") -> dict:
    """
    Get the current weather for a city.
    
    Args:
        city: The city name to get weather for
        unit: Temperature unit - 'celsius' or 'fahrenheit'
    
    Returns:
        A dictionary with temperature, humidity, and conditions
    """
    # In production, call a real weather API
    return {
        "city": city,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "humidity": "65%",
        "conditions": "Partly cloudy",
        "timestamp": datetime.utcnow().isoformat()
    }

# Async tool
async def fetch_stock_price(ticker: str) -> dict:
    """
    Fetch the current stock price for a ticker symbol.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'MSFT', 'AAPL')
    
    Returns:
        Current price and change information
    """
    # Simulate async API call
    await asyncio.sleep(0.1)
    prices = {"MSFT": 425.30, "AAPL": 211.15, "GOOGL": 178.45}
    price = prices.get(ticker.upper(), 0.0)
    return {"ticker": ticker.upper(), "price": price, "currency": "USD"}

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="FinancialAssistant",
        instructions="You are a financial assistant. Help users with weather and stock information.",
        tools=[get_weather, fetch_stock_price],  # Register both tools
    )

    result = await agent.run(
        "What's the weather in Seattle and what is MSFT stock price right now?"
    )
    print(result)

asyncio.run(main())
```

---

### 3.3 Tool Approval

**Description**: Tool Approval is a **Human-in-the-Loop (HITL) gate** that pauses agent execution before calling specific tools, requiring explicit human approval. Critical for tools with side effects: sending emails, making payments, deleting records.

**Use Cases**: Email sending approval, database write confirmation, financial transaction authorization, file deletion confirmation.

**Example**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.tools import requires_approval

@requires_approval  # Mark tool as requiring human approval
def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email to a recipient.
    
    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content
    """
    # In production, integrate with email service
    print(f"[EMAIL SENT] To: {to} | Subject: {subject}")
    return f"Email sent successfully to {to}"

def draft_email_content(topic: str) -> str:
    """Draft email content for a given topic."""
    return f"Subject: Update on {topic}\n\nDear Team, here is the latest update on {topic}..."

async def approval_handler(tool_name: str, arguments: dict) -> bool:
    """Custom approval handler — in production, this would show a UI prompt."""
    print(f"\n⚠️  APPROVAL REQUIRED")
    print(f"Tool: {tool_name}")
    print(f"Arguments: {arguments}")
    response = input("Approve? (y/n): ").strip().lower()
    return response == "y"

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="EmailAgent",
        instructions="You are an email assistant. Draft and send professional emails.",
        tools=[draft_email_content, send_email],
        tool_approval_handler=approval_handler,  # Register approval handler
    )

    result = await agent.run(
        "Send an email to team@company.com about the Q2 project update."
    )
    print(result)

asyncio.run(main())
```

**Best Practice**: Always use `@requires_approval` for tools that have irreversible side effects. Log all approval decisions with timestamps for audit trails.

---

### 3.4 Code Interpreter

**Description**: The Code Interpreter tool allows agents to **write and execute Python code** in a sandboxed environment. The agent can generate code, run it, see the output, and iterate. Useful for data analysis, chart generation, and mathematical computations.

**Example**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework.tools import CodeInterpreterTool
from azure.identity import AzureCliCredential

async def main():
    client = FoundryChatClient(credential=AzureCliCredential())

    agent = Agent(
        client=client,
        name="DataAnalystAgent",
        instructions="""
        You are a data analyst. When asked to analyze data or create charts,
        write Python code to do it precisely. Show your work.
        """,
        tools=[CodeInterpreterTool()],  # Enable sandboxed code execution
    )

    result = await agent.run(
        "Calculate the fibonacci sequence up to n=15 and plot a bar chart. "
        "Also compute the golden ratio from the last two numbers."
    )
    print(result)
    # Agent will write Python code, execute it in sandbox, return results + chart

asyncio.run(main())
```

**Best Practice**: Code Interpreter runs in a fully isolated sandbox. It cannot access your file system or make network calls unless explicitly enabled. Use it for pure computation tasks.

---

### 3.5 File Search

**Description**: File Search (RAG-backed tool) allows agents to **search over uploaded documents** using semantic search. The agent can query a knowledge base of PDFs, Word docs, or text files and retrieve relevant chunks to answer questions.

**Use Cases**: Document Q&A, knowledge base search, policy lookup, contract review.

**Example**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework.tools import FileSearchTool
from azure.identity import AzureCliCredential

async def main():
    client = FoundryChatClient(credential=AzureCliCredential())

    # Configure file search over a knowledge base (vector store)
    file_search = FileSearchTool(
        vector_store_id="vs_abc123",  # Pre-created vector store
        max_results=5,
        rank_threshold=0.7,
    )

    agent = Agent(
        client=client,
        name="KnowledgeBaseAgent",
        instructions="""
        You are a policy assistant. Answer questions strictly based on 
        the uploaded company policy documents. If information is not found,
        say so clearly.
        """,
        tools=[file_search],
    )

    result = await agent.run("What is the company's remote work policy?")
    print(result)

asyncio.run(main())
```

**Best Practice**: Chunk documents at 512-1024 tokens with 20% overlap for best retrieval quality. Always add a system instruction telling the agent to cite its sources.

---

### 3.6 Web Search

**Description**: Web Search gives agents **real-time internet access**. The agent can formulate search queries, retrieve current information, and synthesize answers from web results. Essential for tasks that require up-to-date knowledge beyond the LLM's training cutoff.

**Example**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework.tools import BingSearchTool
from azure.identity import AzureCliCredential

async def main():
    client = FoundryChatClient(credential=AzureCliCredential())

    agent = Agent(
        client=client,
        name="ResearchAgent",
        instructions="""
        You are a research assistant. Use web search to find current, 
        accurate information. Always cite your sources.
        """,
        tools=[
            BingSearchTool(
                subscription_key="YOUR_BING_KEY",
                max_results=5,
                freshness="Week",  # Only results from the past week
            )
        ],
    )

    result = await agent.run("What are the latest developments in quantum computing in 2026?")
    print(result)

asyncio.run(main())
```

**Best Practice**: Combine web search with file search — use file search for internal knowledge (company docs) and web search for external, time-sensitive information.

---

### 3.7 Hosted MCP Tools

**Description**: MAF supports **Model Context Protocol (MCP)** — a standard protocol for agents to discover and call tools hosted on external MCP servers. Hosted MCP tools are registered once and available to all agents. No need to write glue code for each integration.

**Architecture**:
```
Agent → MAF MCP Client → [MCP Server: GitHub]
                        → [MCP Server: Jira]
                        → [MCP Server: Salesforce]
                        → [Any MCP-compliant server]
```

**Example**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.mcp import HostedMCPClient

async def main():
    # Connect to a hosted MCP server (e.g., GitHub MCP server)
    github_mcp = HostedMCPClient(
        server_url="https://mcp.github.com/sse",
        auth_token="your_github_token",
        server_name="github-mcp",
    )

    agent = Agent(
        client=OpenAIChatClient(),
        name="GitHubAgent",
        instructions="""
        You are a GitHub assistant. Help developers manage their repositories,
        issues, and pull requests.
        """,
        mcp_clients=[github_mcp],  # Agent discovers tools from MCP server
    )

    result = await agent.run(
        "List all open issues in the microsoft/agent-framework repository "
        "and summarize the most critical ones."
    )
    print(result)

asyncio.run(main())
```

**Best Practice**: Cache MCP tool discovery results — tool schemas don't change frequently. Use connection pooling for high-throughput scenarios.

---

### 3.8 Local MCP Tools

**Description**: Local MCP Tools run an **MCP server process locally** (as a subprocess) and the agent connects to it via stdio. This is useful for development, testing, or when the MCP server needs access to local resources (file system, local databases).

**Example**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.mcp import LocalMCPClient

async def main():
    # Start a local MCP server (e.g., filesystem MCP server)
    local_fs_mcp = LocalMCPClient(
        command=["python", "-m", "mcp_filesystem_server"],
        args=["--root", "./workspace"],
        server_name="filesystem-mcp",
    )

    async with local_fs_mcp:  # Starts/stops the subprocess
        agent = Agent(
            client=OpenAIChatClient(),
            name="FilesystemAgent",
            instructions="You are a file management assistant.",
            mcp_clients=[local_fs_mcp],
        )

        result = await agent.run(
            "List all Python files in the workspace and summarize their purpose."
        )
        print(result)

asyncio.run(main())
```

**Best Practice**: Always use `async with` context manager for local MCP clients to ensure clean subprocess shutdown. Set resource limits on local MCP server processes.

---

## 4. Conversations & Memory

### 4.1 Overview

**Description**: MAF provides a **pluggable, multi-layer memory architecture**. Memory ranges from the current conversation context (short-term) to persistent vector stores (long-term). Context providers inject relevant memory into each agent turn automatically.

**Memory Layers**:
```
┌─────────────────────────────────────────────┐
│  Context Window (Active Turn)               │  ← In-memory, ephemeral
├─────────────────────────────────────────────┤
│  Session History (Multi-turn conversation)  │  ← In-memory or persistent
├─────────────────────────────────────────────┤
│  Key-Value State (Persistent facts)         │  ← Redis, Cosmos DB
├─────────────────────────────────────────────┤
│  Vector Memory (Semantic recall)            │  ← Qdrant, Pinecone, Foundry
└─────────────────────────────────────────────┘
```

---

### 4.2 Session

**Description**: A **Session** is a named, stateful container for a multi-turn conversation. It persists conversation history across multiple `agent.run()` calls. Sessions are the foundation of chatbot-style interactions.

**Example**:

```python
import asyncio
from agent_framework import Agent, Session
from agent_framework.openai import OpenAIChatClient

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="ChatAgent",
        instructions="You are a helpful personal assistant. Remember what users tell you.",
    )

    # Create a named session — history persists across turns
    session = Session(id="user_alice_session_001")

    # Turn 1
    r1 = await agent.run("My name is Alice and I love hiking.", session=session)
    print(f"Agent: {r1}")

    # Turn 2 — Agent remembers Alice's name and interest
    r2 = await agent.run("What outdoor activities would you recommend for me?", session=session)
    print(f"Agent: {r2}")

    # Turn 3 — Still in the same session context
    r3 = await agent.run("What did I tell you my name was?", session=session)
    print(f"Agent: {r3}")  # "You told me your name is Alice."

asyncio.run(main())
```

**Best Practice**: Generate session IDs from user identifiers (user_id + conversation_id) to ensure isolation. Implement session expiry (e.g., 24 hours of inactivity) to prevent unbounded growth.

---

### 4.3 Context Provider

**Description**: Context Providers **automatically inject relevant information** into the agent's context before each turn. The agent framework calls all registered providers, collects their output, and prepends it to the conversation. Examples: conversation history, user profile, retrieved documents.

**Built-in Providers**:
- `InMemoryHistoryProvider` — Stores history in RAM
- `CompactionProvider` — Compresses old history to save tokens
- `VectorMemoryProvider` — Retrieves semantically relevant past messages

**Example**:

```python
import asyncio
from agent_framework import Agent, Session
from agent_framework.openai import OpenAIChatClient
from agent_framework.memory import (
    InMemoryHistoryProvider,
    KeyValueProvider,
    VectorMemoryProvider,
)

async def main():
    # Multi-layer context provider setup
    agent = Agent(
        client=OpenAIChatClient(),
        name="MemoryAgent",
        instructions="""
        You are a personal assistant. Use the provided context about the user
        to give personalized, contextually relevant responses.
        """,
        context_providers=[
            # Layer 1: Full conversation history (last 10 turns)
            InMemoryHistoryProvider(max_turns=10),

            # Layer 2: Persistent user profile facts
            KeyValueProvider(
                initial_facts={
                    "user_name": "Alice",
                    "preferred_language": "Python",
                    "timezone": "PST",
                    "experience_level": "Senior Developer",
                }
            ),
        ],
    )

    session = Session(id="alice_dev_session")
    result = await agent.run(
        "What Python libraries should I use for building async web APIs?",
        session=session
    )
    print(result)

asyncio.run(main())
```

---

### 4.4 Storage

**Description**: MAF supports **pluggable storage backends** for persisting session history and agent state. Storage options range from in-memory (development) to Redis, Azure Cosmos DB, or Foundry Memory Service (production).

**Storage Options**:

| Backend | Use Case | Persistence |
|---|---|---|
| `InMemoryStorage` | Development, testing | None (process-scoped) |
| `RedisStorage` | High-throughput production | Yes |
| `CosmosDBStorage` | Azure-native production | Yes |
| `FoundryMemoryStorage` | Azure AI Foundry integration | Yes |

**Example**:

```python
import asyncio
from agent_framework import Agent, Session
from agent_framework.openai import OpenAIChatClient
from agent_framework.memory import InMemoryHistoryProvider, RedisStorage

async def main():
    # Use Redis for persistent session storage
    storage = RedisStorage(
        connection_string="redis://localhost:6379",
        key_prefix="maf:sessions:",
        ttl_seconds=86400,  # Sessions expire after 24 hours
    )

    agent = Agent(
        client=OpenAIChatClient(),
        name="PersistentAgent",
        instructions="You are a helpful assistant with persistent memory.",
        context_providers=[
            InMemoryHistoryProvider(storage=storage),
        ],
    )

    # Session persists to Redis — survives server restarts
    session = Session(id="user_123_conv_456")
    result = await agent.run("Remember: my project deadline is June 1st.", session=session)
    print(result)

asyncio.run(main())
```

**Best Practice**: Use Redis with LRU eviction for high-traffic scenarios. Set TTL on session keys to prevent unbounded storage growth.

---

### 4.5 Compaction

**Description**: Context Compaction **automatically summarizes or truncates old conversation history** when it grows too large for the context window. Without compaction, long conversations exceed the model's token limit and fail. MAF provides built-in compaction strategies.

**Compaction Strategies**:
- `SlidingWindowStrategy` — Keep only the N most recent turns
- `SummarizationStrategy` — Summarize old turns into a compressed block
- `TokenBudgetStrategy` — Keep history within a token budget

**Example**:

```python
import asyncio
from agent_framework import Agent, Session
from agent_framework.openai import OpenAIChatClient
from agent_framework.memory import (
    InMemoryHistoryProvider,
    CompactionProvider,
    SlidingWindowStrategy,
    SummarizationStrategy,
)

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="LongConversationAgent",
        instructions="You are a long-running project management assistant.",
        context_providers=[
            InMemoryHistoryProvider(),
            CompactionProvider(
                # When history exceeds threshold, summarize the oldest messages
                before_strategy=SummarizationStrategy(
                    max_tokens_before_compaction=8000,
                    summary_prompt="Summarize the key decisions and facts from this conversation.",
                ),
                # Alternatively: keep only last 5 conversation groups
                # before_strategy=SlidingWindowStrategy(keep_last_groups=5),
            ),
        ],
    )

    session = Session(id="project_alpha_planning")

    # Simulate a long conversation — compaction triggers automatically
    topics = [
        "We're building a microservices platform with 12 services.",
        "The tech stack is Python FastAPI, PostgreSQL, and Kubernetes.",
        "Sprint 1 goal: authentication service and user management.",
        "We decided to use JWT tokens with 1-hour expiry.",
        "The deployment target is Azure AKS with 3 replicas per service.",
    ]

    for topic in topics:
        result = await agent.run(topic, session=session)
        print(f"Agent: {result[:100]}...")

    # Even after many turns, context stays manageable
    summary = await agent.run("Give me a summary of all key technical decisions.", session=session)
    print(f"\nFinal Summary:\n{summary}")

asyncio.run(main())
```

**Best Practice**: Use `SummarizationStrategy` for conversational agents where context matters. Use `SlidingWindowStrategy` for task-oriented agents where old turns are irrelevant.

---

## 5. Middleware

### 5.1 Overview

**Description**: Middleware is MAF's **interceptor pattern** for the agent pipeline. Every request and response passes through a chain of middleware handlers. You can inject logic at any point — logging, authentication, rate limiting, content safety, retry logic — without modifying agent code.

**Middleware Execution Model**:
```
[Request] → MW1.pre → MW2.pre → MW3.pre → [Agent LLM Call] → MW3.post → MW2.post → MW1.post → [Response]
```

**Two Middleware Types**:
- **Chat Middleware** — Intercepts the full conversation (pre/post LLM call)
- **Function Middleware** — Intercepts individual tool/function calls

---

### 5.2 Defining Middleware

**Example — Full Middleware Stack**:

```python
import asyncio
import time
from typing import Callable, Awaitable
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.middleware import (
    ChatMiddlewareContext,
    FunctionInvocationContext,
)

# ---- Chat Middleware: wraps the entire agent LLM call ----
async def logging_chat_middleware(
    context: ChatMiddlewareContext,
    next: Callable[[ChatMiddlewareContext], Awaitable[None]],
) -> None:
    """Log every agent invocation with timing."""
    start = time.monotonic()
    user_msg = context.messages[-1].text if context.messages else "N/A"
    print(f"[Chat MW] → Calling agent | Input: '{user_msg[:60]}...'")

    await next(context)  # Execute the agent

    elapsed = time.monotonic() - start
    response_preview = str(context.result)[:60] if context.result else "None"
    print(f"[Chat MW] ← Agent responded in {elapsed:.2f}s | Output: '{response_preview}...'")


# ---- Function Middleware: wraps individual tool calls ----
async def logging_function_middleware(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    """Log every tool call."""
    print(f"[Tool MW] → Calling tool: {context.function.name}({context.arguments})")
    await next(context)
    print(f"[Tool MW] ← Tool returned: {str(context.result)[:80]}")


def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: 22°C, Sunny"


async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="MiddlewareAgent",
        instructions="You are a helpful assistant.",
        tools=[get_weather],
        chat_middleware=[logging_chat_middleware],
        function_middleware=[logging_function_middleware],
    )

    result = await agent.run("What's the weather in Paris?")
    print(f"\nFinal Answer: {result}")

asyncio.run(main())
```

---

### 5.3 Chat-Level Middleware

**Description**: Chat-level middleware intercepts **the complete conversation context** — all messages, before and after the LLM processes them. Used for: token counting, conversation logging, A/B testing, input transformation.

**Example — Token Counting Middleware**:

```python
async def token_counting_middleware(
    context: ChatMiddlewareContext,
    next: Callable[[ChatMiddlewareContext], Awaitable[None]],
) -> None:
    """Count tokens used per request."""
    import tiktoken
    enc = tiktoken.encoding_for_model("gpt-4o")
    
    # Count input tokens
    input_text = " ".join(m.text for m in context.messages if m.text)
    input_tokens = len(enc.encode(input_text))
    
    await next(context)
    
    # Count output tokens
    output_tokens = len(enc.encode(str(context.result))) if context.result else 0
    
    print(f"[Tokens] Input: {input_tokens} | Output: {output_tokens} | Total: {input_tokens + output_tokens}")
    # In production: emit to metrics system (Prometheus, Azure Monitor)
```

---

### 5.4 Agent & Run Scope

**Simple explanation:** Think of it like rules at two levels — house rules vs. room rules.
* **Agent-level middleware** = house rules. They apply every time anyone runs this agent, no matter what. Example: "always log every request."

* **Run-level middleware** = room rules. They apply only for one specific agent.run() call. Example: "for this one API request from user Alice, tag all logs with her user ID."

**Real-world analogy:** Imagine a hotel. Every guest gets towels (agent-level — always happens). But a VIP guest gets a fruit basket delivered specifically for their stay (run-level — only for that one check-in).


**Description**: Middleware can be scoped to the **agent level** (applies to all runs of this agent) or **run level** (applies only to a specific `agent.run()` call). Run-level middleware is useful for per-request context like user ID, request ID, or custom logging.

**Example 01**:

```python
import asyncio
from agent_framework import Agent, RunOptions
from agent_framework.openai import OpenAIChatClient

async def request_id_middleware(context, next):
    """Inject request ID into all log messages for this run."""
    request_id = context.run_context.get("request_id", "unknown")
    print(f"[ReqID: {request_id}] Starting agent run")
    await next(context)
    print(f"[ReqID: {request_id}] Agent run complete")

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="ScopedAgent",
        instructions="You are a helpful assistant.",
    )

    # Inject per-request middleware at run time
    result = await agent.run(
        "Summarize quantum computing in 2 sentences.",
        options=RunOptions(
            chat_middleware=[request_id_middleware],
            run_context={"request_id": "req_abc_789", "user_id": "user_alice"},
        )
    )
    print(result)

asyncio.run(main())
```

**Example 02:**

```python
    # Agent-level: fires on EVERY run of this agent
    agent = Agent(
        client=client,
        instructions="You are a helpful assistant.",
        chat_middleware=[always_log_middleware],  # ← always active
    )

    # Run-level: fires ONLY for this one specific call
    result = await agent.run(
        "Help me write an email.",
        options=RunOptions(
            chat_middleware=[tag_with_user_id_middleware],  # ← only for THIS call
            run_context={"user_id": "alice_42"}
        )
    )
```

---

### 5.5 Terminations & Guardrails

**Description**: Termination middleware **stops the agent loop** when a condition is met — max turns reached, specific output detected, budget exceeded, or a policy violation found. Guardrails middleware validates outputs and can reject or redirect them.

**Example**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

MAX_TURNS = 5
turn_count = 0

async def max_turns_termination_middleware(context, next):
    """Stop the agent after MAX_TURNS turns."""
    global turn_count
    turn_count += 1
    if turn_count > MAX_TURNS:
        context.result = "Maximum conversation turns reached. Please start a new session."
        return
    await next(context)

async def topic_guardrail_middleware(context, next):
    """Reject off-topic requests."""
    off_topic_keywords = ["competitor", "lawsuit", "internal_salary"]
    user_input = context.messages[-1].text.lower() if context.messages else ""
    
    for keyword in off_topic_keywords:
        if keyword in user_input:
            context.result = "I'm not able to discuss that topic. How can I help you with something else?"
            return
    
    await next(context)

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="GuardedAgent",
        instructions="You are a product support assistant.",
        chat_middleware=[
            topic_guardrail_middleware,  # Check topic first
            max_turns_termination_middleware,  # Then check turn limit
        ],
    )

    result = await agent.run("Tell me about your competitor's pricing.")
    print(result)  # Blocked by guardrail

asyncio.run(main())
```

---

### 5.6 Results Overrides

**Description**: Result Override middleware **modifies or replaces the agent's response** after it's generated. Used for: adding disclaimers, reformatting output, injecting citations, or translating responses.

**Example**:

```python
async def disclaimer_middleware(context, next):
    """Append a legal disclaimer to all agent responses."""
    await next(context)
    if context.result and isinstance(context.result, str):
        context.result += "\n\n---\n*This response is for informational purposes only and does not constitute legal or financial advice.*"
```

---

### 5.7 Exception Handling

**Description**: Exception handling middleware **catches errors in the agent pipeline** and provides graceful degradation. Without it, tool failures or LLM errors propagate as unhandled exceptions.

**Example**:

```python
async def error_handling_middleware(context, next):
    """Gracefully handle agent pipeline errors."""
    try:
        await next(context)
    except TimeoutError:
        context.result = "The request took too long. Please try a simpler question."
    except Exception as e:
        # Log the full error internally
        print(f"[ERROR] Agent pipeline error: {type(e).__name__}: {e}")
        # Return user-friendly message
        context.result = "I encountered an issue processing your request. Please try again."
```

---

### 5.8 Shared State

**Simple explanation:** Shared State is a sticky note board that all middleware in a single run can write to and read from — without touching the actual conversation messages.

Without it, if Middleware A measures something (like start time), it cannot pass that to Middleware B without hacking the conversation. Shared State solves this cleanly.

**Real-world analogy:** Think of airport check-in. The ticketing agent writes your bag weight on a paper slip. Security reads that same slip. The boarding agent reads it again. None of them need to ask you (the conversation) — they pass information to each other via the slip (shared state).

**Description**: Shared State allows **multiple middleware handlers to share data** within a single agent run, without polluting the agent's conversation context. Think of it as a request-scoped blackboard.

**Example 01**:

```python
async def timing_start_middleware(context, next):
    """Record start time in shared state."""
    context.shared_state["start_time"] = time.monotonic()
    context.shared_state["token_budget"] = 4000
    await next(context)

async def timing_end_middleware(context, next):
    """Read from shared state set by another middleware."""
    await next(context)
    start = context.shared_state.get("start_time", 0)
    elapsed = time.monotonic() - start
    budget = context.shared_state.get("token_budget", 0)
    print(f"Run completed in {elapsed:.2f}s | Token budget: {budget}")
```

**Example 02:**
```python
    async def start_timer_middleware(context, next):
    # Middleware A writes to the shared board
        context.shared_state["start_time"] = time.monotonic()
        context.shared_state["user_tier"] = "premium"
        await next(context)

    async def end_timer_middleware(context, next):
        await next(context)
        # Middleware B reads from the same board
        elapsed = time.monotonic() - context.shared_state["start_time"]
        tier = context.shared_state["user_tier"]
        print(f"[{tier}] Request took {elapsed:.2f}s")
```

Both middlewares share data (`start_time`, `user_tier`) without putting any of it into the chat messages the user sees.

---

### 5.9 Running Context

**Simple explanation:** Running Context is like a name badge that the agent wears for a single run. It carries metadata about who is making this call and why — things like user ID, request ID, feature flags. Every middleware can read the badge, but it never appears in the conversation.

**Real-world analogy:** When a doctor sees a patient, the nurse hands the doctor a clipboard with the patient's name, insurance, and visit reason. The doctor doesn't ask the patient all of that again mid-conversation — they just read the clipboard. Running Context is that clipboard.

**Key difference from Shared State:** Running Context is set before the run starts by the caller. Shared State is written during the run by middleware. Running Context = inputs. Shared State = working notes passed between middleware mid-run.


**Description**: Running Context is a **per-run metadata container** that flows through the entire middleware chain. It carries request-scoped information: user ID, request ID, feature flags, A/B test group assignments.

**Example**:

```python
async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="ContextAwareAgent",
        instructions="You are a personalized assistant.",
    )

    # Running context flows through all middleware
    result = await agent.run(
        "Help me write a professional bio.",
        options=RunOptions(
            run_context={
                "user_id": "usr_alice_42",
                "request_id": "req_20260512_001",
                "ab_test_group": "B",
                "feature_flags": {"enable_codeact": True, "use_gpt4o": True},
                "locale": "en-US",
            }
        )
    )
    print(result)
```

**Example 02:**
```python
    result = await agent.run(
        "Suggest a product for me.",
        options=RunOptions(
            run_context={
                "user_id": "usr_alice_42",       # Who is calling
                "request_id": "req_20260512",    # Audit trail ID
                "ab_test_group": "B",            # A/B testing
                "feature_flags": {
                    "show_premium_offers": True  # Feature toggle
                },
            }
        )
    )

    # Any middleware can read this without touching the conversation
    async def ab_test_middleware(context, next):
        group = context.run_context.get("ab_test_group", "A")
        if group == "B":
            print("Using variant B response style")
        await next(context)
```


**How They Relate — One-Line Summary Each**

| Concept | What it is | Set by | Read by |
|---|---|---|---|
| **Agent Scope** | Always-on middleware for all runs | Developer at agent setup | Every run |
| **Run Scope** | One-time middleware for a single call | Caller at `agent.run()` | That run only |
| **Shared State** | Working notepad between middlewares in one run | Any middleware during the run | Other middlewares |
| **Running Context** | Metadata clipboard about the caller | Caller before the run starts | All middlewares |

The simplest mental model: **Running Context** is what you bring *into* the run. **Shared State** is what middleware *creates and passes around* during the run. **Scope** controls *which* middleware even participates.

---

## 6. Workflows

### 6.1 Overview

**Description**: Workflows in MAF are **graph-based, explicit orchestration engines** for composing multiple agents and functions into deterministic, multi-step processes. Unlike a single agent (which decides its own steps autonomously), a workflow defines exactly which agents run, in what order, with what inputs and outputs.

**When to use Workflows vs Agents**:

| Use Agent | Use Workflow |
|---|---|
| Open-ended, conversational | Defined steps with clear sequence |
| Single LLM with tools | Multiple agents that need to coordinate |
| Autonomous planning | Explicit control flow needed |
| Simple Q&A | Complex business process with branching |

**Workflow Execution Model**:
```
Input → [Executor A] → [Edge (condition)] → [Executor B] → [Executor C] → Output
                    ↘  [Edge (alt path)] → [Executor D] ↗
```

---

### 6.2 Functional Workflow API

**Description**: The Functional Workflow API lets you write workflows as **plain Python async functions** using `@workflow` and `@step` decorators. Use native Python control flow (`if/else`, loops, `asyncio.gather`) instead of graph concepts. Best starting point for most developers.

**Example — Content Pipeline**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.workflows.functional import workflow, step

client = OpenAIChatClient()

researcher = Agent(
    client=client,
    name="Researcher",
    instructions="You research topics and provide factual summaries. Be concise.",
)

writer = Agent(
    client=client,
    name="Writer",
    instructions="You write engaging articles based on research. Use clear language.",
)

editor = Agent(
    client=client,
    name="Editor",
    instructions="You edit articles for clarity, grammar, and style. Return the improved version.",
)

fact_checker = Agent(
    client=client,
    name="FactChecker",
    instructions="You verify factual claims. Flag any inaccuracies clearly.",
)


@workflow
async def content_creation_pipeline(topic: str) -> str:
    """Full content creation pipeline: research → write → fact-check → edit."""

    # Step 1: Research the topic
    research = await step(researcher.run(f"Research this topic thoroughly: {topic}"))

    # Step 2: Write article based on research
    draft = await step(writer.run(f"Write a 300-word article about {topic}. Research: {research}"))

    # Step 3: Fact-check and write in parallel (concurrent step)
    fact_check, style_notes = await asyncio.gather(
        step(fact_checker.run(f"Check facts in this article: {draft}")),
        step(editor.run(f"Give style improvement notes (don't rewrite yet): {draft}")),
    )

    # Step 4: Final edit incorporating all feedback
    final = await step(
        editor.run(
            f"Rewrite this article incorporating feedback:\n"
            f"Original: {draft}\n"
            f"Fact check issues: {fact_check}\n"
            f"Style notes: {style_notes}"
        )
    )

    return final


async def main():
    result = await content_creation_pipeline("The impact of quantum computing on cybersecurity")
    print(result)

asyncio.run(main())
```

---

### 6.3 Graph-Based Workflows

**Description**: Graph-based workflows use `WorkflowBuilder` to define **directed graphs** with typed edges between executors. Each executor is a processing unit (an agent, a function, or a custom executor). Edges define valid message paths, with type-safe routing.

**Key Concepts**:
- **Executor** — A processing unit in the graph (agent, function, or custom)
- **Edge** — A directed connection between two executors
- **Event** — Data flowing along edges (type-validated)
- **Superstep** — A round of parallel execution in the graph

**Example — Graph-Based Research Workflow**:

```python
import asyncio
from dataclasses import dataclass
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.workflows import WorkflowBuilder, AgentExecutor, FunctionExecutor
from agent_framework.workflows.execution import InProcessExecution

@dataclass
class ResearchRequest:
    topic: str
    depth: str = "standard"  # "standard" or "deep"

@dataclass
class ResearchResult:
    topic: str
    summary: str
    key_points: list[str]

@dataclass
class FinalReport:
    content: str
    word_count: int

client = OpenAIChatClient()

# Define specialized agents
researcher_agent = Agent(client=client, name="researcher",
    instructions="You are a research specialist. Provide factual, structured research summaries.")

writer_agent = Agent(client=client, name="writer",
    instructions="You write clear, engaging reports from research data.")

# Define a function executor for post-processing
def format_report(result: ResearchResult) -> FinalReport:
    """Format research result into a publishable report."""
    content = f"# Report: {result.topic}\n\n{result.summary}\n\n"
    content += "## Key Points\n" + "\n".join(f"- {p}" for p in result.key_points)
    return FinalReport(content=content, word_count=len(content.split()))

async def main():
    # Build graph-based workflow
    workflow = (
        WorkflowBuilder()
        .add_executor(AgentExecutor(researcher_agent, input_type=ResearchRequest, output_type=ResearchResult))
        .add_executor(AgentExecutor(writer_agent, input_type=ResearchResult, output_type=ResearchResult))
        .add_executor(FunctionExecutor(format_report, input_type=ResearchResult, output_type=FinalReport))
        .add_edge("researcher", "writer")
        .add_edge("writer", "format_report")
        .set_entry("researcher")
        .set_exit("format_report")
        .build()
    )

    # Execute
    request = ResearchRequest(topic="AI agents in healthcare 2026", depth="deep")
    result: FinalReport = await InProcessExecution.run_async(workflow, request)
    print(result.content)
    print(f"\nWord count: {result.word_count}")

asyncio.run(main())
```

---

### 6.4 Orchestration Patterns

MAF ships with **5 built-in orchestration patterns**:

#### Sequential Orchestration

**Description**: Agents execute **one after another** in a fixed linear chain. Output of each agent becomes input for the next. Simple, predictable, easy to debug.

Agents work one after another, like an assembly line. Agent A finishes completely, hands its output to Agent B, B finishes, hands to Agent C. No agent starts until the previous one is done.

**Real-world analogy:** Think of a restaurant kitchen. The chef cooks the dish first. Only when it is plated does the waiter pick it up. Only when the waiter delivers it does the cashier generate the bill. Each person waits for the previous person to finish before they start their part.


```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.orchestrations import SequentialBuilder

async def main():
    client = OpenAIChatClient()

    planner = Agent(client=client, name="planner",
        instructions="You create detailed project plans. Output a numbered step-by-step plan.")
    
    estimator = Agent(client=client, name="estimator",
        instructions="You estimate time and cost for project plans. Be specific with numbers.")
    
    risk_analyzer = Agent(client=client, name="risk_analyzer",
        instructions="You identify and rate project risks. List top 5 risks with mitigation strategies.")

    # Build sequential workflow: planner → estimator → risk_analyzer
    workflow = SequentialBuilder(participants=[planner, estimator, risk_analyzer]).build()

    # Run entire pipeline
    outputs = []
    async for event in workflow.run("Plan a mobile app for restaurant reservations.", stream=True):
        if event.type == "output":
            outputs.append(event.data)

    # Print each agent's contribution
    agent_names = ["Planner", "Estimator", "Risk Analyzer"]
    for i, output in enumerate(outputs):
        print(f"\n--- {agent_names[i]} ---")
        for msg in output:
            print(msg.text)

asyncio.run(main())
```

**How it works step by step:**
```markdown
    User Input → [Planner Agent] → output passed as input →
    [Estimator Agent] → output passed as input →
    [Risk Analyzer Agent] → Final Result
```
1. The user gives one task to the workflow
2. The Planner receives it, thinks, produces a plan
3. That plan is automatically handed to the Estimator
4. The Estimator produces time and cost estimates
5. Those estimates are automatically handed to the Risk Analyzer
6. The Risk Analyzer produces the final risk assessment
7. You get all three outputs in sequence


**When to use it:**
Use Sequential when each agent's work genuinely depends on what the previous agent produced. When the order matters. When you need a clear, auditable chain of steps where each step builds on the last. Best for pipelines like: research → write → review → publish, or plan → estimate → approve.

**When NOT to use it:**
Do not use Sequential if the agents do not depend on each other's output. Running three independent analysts sequentially when they could all work at the same time is just wasting time.


#### Concurrent Orchestration

**Description**: All agents **execute simultaneously** on the same input, in parallel. Results are collected when all complete. Use when agents are independent and can work in parallel.

All agents receive the same input and work simultaneously, in parallel. Nobody waits for anyone else. Results are collected when everyone finishes.

**Real-world analogy:** Think of a panel of judges at a talent show. All three judges watch the same performance at the same time. Each forms their own independent opinion. Once everyone has finished scoring, all scores are collected and compared. No judge waits for another to finish before making up their mind.


```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.orchestrations import ConcurrentBuilder

async def main():
    client = OpenAIChatClient()

    # Three independent analysis agents
    technical_analyst = Agent(client=client, name="technical",
        instructions="Analyze technical feasibility. Focus on tech stack and architecture.")
    
    market_analyst = Agent(client=client, name="market",
        instructions="Analyze market opportunity. Focus on TAM, competition, and trends.")
    
    financial_analyst = Agent(client=client, name="financial",
        instructions="Analyze financial viability. Focus on revenue model and unit economics.")

    # All three run concurrently — much faster than sequential
    workflow = ConcurrentBuilder(participants=[technical_analyst, market_analyst, financial_analyst]).build()

    topic = "A SaaS platform for AI agent monitoring and observability"
    print(f"Analyzing: {topic}\n")

    async for event in workflow.run(topic, stream=True):
        if event.type == "output" and event.data:
            for msg in event.data:
                agent_name = msg.author_name or "Agent"
                print(f"[{agent_name}]: {msg.text}\n")

asyncio.run(main())
```

**How it works step by step:**
```markdown
    → [Technical Analyst] → result ─┐
    User Input ────────→ [Market Analyst]    → result ──┼→ All results collected
                        → [Financial Analyst] → result ─┘
```

1. The user gives one task to the workflow
2. All three agents receive the exact same input simultaneously
3. Each agent works completely independently of the others
4. All three run at the same time — the wall clock time is only as long as the slowest agent
5. Results are collected from all three and returned together

**When to use it**
Use Concurrent when agents are completely independent of each other — meaning Agent A's answer does not affect what Agent B needs to do. Best for multi-perspective analysis, parallel research, or any situation where you need several viewpoints on the same question at the same time. Dramatically faster than running the same agents sequentially.

**When NOT to use it:**
Do not use Concurrent if Agent B needs to see Agent A's output before it can do its job. If there is a dependency between agents, use Sequential instead.


#### Handoff Orchestration

**Description**: Agents **hand off control** to other agents based on their own reasoning. The active agent decides which specialist to transfer to next. Enables dynamic routing through a graph of specialized agents.

One agent acts as a receptionist who decides which specialist to send you to. Once you are passed to that specialist, they handle your request. Agents hand control to each other dynamically based on what they understand about the situation.

**Real-world analogy:** Think of calling a company's customer service line. The first person who picks up is not a specialist — they listen to your problem and decide whether to transfer you to billing, technical support, returns, or sales. Once they transfer you, the specialist takes over completely. The routing decision is made based on what you say, not by a fixed rule set upfront.

```python
    import asyncio
    from agent_framework import Agent
    from agent_framework.openai import OpenAIChatClient
    from agent_framework.orchestrations import HandoffBuilder

    async def main():
        client = OpenAIChatClient()

        # Customer service specialist agents
        triage_agent = Agent(client=client, name="triage",
            instructions="""
            You are a customer service triage agent. 
            Route to: 'orders' for order issues, 'returns' for return requests,
            'technical' for product technical problems, 'billing' for payment issues.
            """)
        
        orders_agent = Agent(client=client, name="orders",
            instructions="You handle order status, shipping, and delivery inquiries.")
        
        returns_agent = Agent(client=client, name="returns",
            instructions="You handle return requests, refunds, and exchange policies.")
        
        technical_agent = Agent(client=client, name="technical",
            instructions="You handle technical product support and troubleshooting.")
        
        billing_agent = Agent(client=client, name="billing",
            instructions="You handle billing disputes, payments, and subscription changes.")

        # Build handoff topology
        workflow = (
            HandoffBuilder(participants=[triage_agent, orders_agent, returns_agent, technical_agent, billing_agent])
            .with_start_agent(triage_agent)
            .add_handoff(triage_agent, [orders_agent, returns_agent, technical_agent, billing_agent])
            .add_handoff(returns_agent, [billing_agent], description="Suspected refund fraud")
            .build()
        )

        # Triage automatically routes to the right specialist
        print("Test 1: Order inquiry")
        result = await workflow.run("Where is my order #98765? It's been 2 weeks!")
        print(result)

        print("\nTest 2: Technical problem")
        result = await workflow.run("My device won't turn on after the latest firmware update.")
        print(result)

    asyncio.run(main())
```

**How it works step by step:**
```markdown
    User Input → [Triage Agent]
                 │
                 ├── "order problem?" → [Orders Agent] → Final Answer
                 ├── "return request?" → [Returns Agent] → Final Answer
                 ├── "technical issue?" → [Technical Agent] → Final Answer
                 └── "billing problem?" → [Billing Agent] → Final Answer
```

1. Every request starts at the Triage Agent
2. The Triage Agent reads the request and decides which specialist is the right fit
3. Control is handed off to that specialist
4. The specialist handles the request fully and returns the answer
5. Specialist agents can also hand off to other specialists if needed (e.g. Returns hands fraud cases to Billing)


**When to use it:**
Use Handoff when you have one entry point but many possible paths through your system — like customer service, help desks, intake forms, or any domain where different types of requests need different types of expertise. The routing decision is intelligent and context-aware, not a simple if/else rule.

**When NOT to use it:**
Do not use Handoff when every request goes through the same agents every time. If the path is always the same, Sequential is simpler and more predictable.


#### Group Chat Orchestration

**Description**: A **manager agent coordinates multiple specialist agents** in a collaborative discussion. The manager selects who speaks next, agents build on each other's responses, and all share the same conversation history.

Multiple agents have a collaborative conversation with each other, all sharing the same chat history. A manager decides who speaks next. Agents can read what others have said and build on it, disagree with it, or refine it — just like a real team meeting.

**Real-world analogy:** Think of a product design workshop. A developer, a designer, and a business analyst sit in the same room. The facilitator calls on each person in turn. The developer proposes a technical solution. The designer hears it and suggests a UX improvement. The business analyst hears both and adds a cost consideration. Everyone's contribution is shaped by what the others already said. The conversation builds collectively toward a better outcome than any one person could reach alone.


```python
    import asyncio
    from agent_framework import Agent
    from agent_framework.openai import OpenAIChatClient
    from agent_framework.orchestrations import GroupChatBuilder, RoundRobinGroupChatManager

    async def main():
        client = OpenAIChatClient()

        # Collaborative code review team
        developer = Agent(client=client, name="developer",
            instructions="You write clean, efficient Python code based on requirements. Show your implementation.")
        
        reviewer = Agent(client=client, name="reviewer",
            instructions="You review code for bugs, security issues, and best practices. Be specific and constructive.")
        
        architect = Agent(client=client, name="architect",
            instructions="You evaluate code architecture, scalability, and design patterns. Suggest improvements.")

        # Group chat with round-robin speaker selection
        workflow = (
            GroupChatBuilder(
                participants=[developer, reviewer, architect],
                manager=RoundRobinGroupChatManager(),
                max_iterations=3,  # Each agent speaks 3 times max
            )
            .build()
        )

        task = "Write a Python class for a rate limiter that supports multiple rate limit rules."
        
        async for event in workflow.run(task, stream=True):
            if event.type == "agent_response":
                print(f"\n[{event.agent_name}]:\n{event.content}\n{'─'*60}")

    asyncio.run(main())
```

**How it works step by step:**
```markdown
    Task → Manager decides: "Developer speaks first"
     → Developer responds (everyone reads it)
     → Manager decides: "Reviewer speaks next"
     → Reviewer responds, referencing developer's output
     → Manager decides: "Architect speaks next"
     → Architect responds, building on both
     → Repeat for max_iterations → Final result
```

1. The task is given to the group
2. The manager (a coordinator — not a specialist) decides which agent speaks first
3. That agent responds — their response is added to the shared conversation history
4. All other agents can see that response
5. The manager calls the next agent, who builds on what was already said
6. This continues for a set number of rounds
7. The result is the accumulated collaborative output of the whole group

**When to use It:**
Use Group Chat when the best answer requires genuine collaboration — when Agent B's contribution should be shaped by what Agent A said, and Agent C should synthesise both. Best for code review (write → review → improve), complex document drafting, multi-disciplinary analysis, or any task where the quality of the output improves when agents respond to each other rather than working in isolation.

**When NOT to use It**
Do not use Group Chat for simple tasks or when you just want independent opinions. If agents do not need to hear each other, Concurrent is faster and cleaner.


#### Magentic (Magnetic) Orchestration

**Description**: A **manager agent dynamically creates and manages a task list**, assigns sub-tasks to specialized agents, verifies results, and re-assigns if needed. Most powerful for complex, open-ended tasks requiring adaptive planning.


A manager agent receives a complex goal, breaks it down into sub-tasks on its own, assigns each sub-task to the most appropriate specialist agent, checks the results, and re-assigns or adjusts if the result is not good enough. The plan is not written by you — the manager figures it out dynamically.


**Real-world analogy:** Think of a project manager at a consulting firm who receives one big vague brief from a client: "Help us enter the Asian market." The project manager does not have a fixed playbook. They assess the brief, decide they need a market researcher, a legal expert, and a financial modeller, assign work to each one, review what comes back, send the researcher back to dig deeper on one country, ask the financial modeller to redo the numbers with new assumptions, and keep adjusting until the final deliverable is ready. No one told the project manager exactly what steps to follow — they figured it out themselves based on the goal.


```python
    import asyncio
    from agent_framework import Agent
    from agent_framework.openai import OpenAIChatClient
    from agent_framework.orchestrations import MagenticBuilder

    async def main():
        client = OpenAIChatClient()

        # Specialized sub-agents for the Magentic team
        web_surfer = Agent(client=client, name="web_surfer",
            instructions="You search the web and summarize relevant findings.")
        
        code_writer = Agent(client=client, name="code_writer",
            instructions="You write production-quality Python code.")
        
        data_analyst = Agent(client=client, name="data_analyst",
            instructions="You analyze data and extract insights.")
        
        file_manager = Agent(client=client, name="file_manager",
            instructions="You manage file operations and organize output.")

        # Magentic orchestrator — manager creates and manages tasks dynamically
        workflow = (
            MagenticBuilder(
                participants=[web_surfer, code_writer, data_analyst, file_manager],
                max_rounds=10,
            )
            .build()
        )

        complex_task = """
        Research the top 5 Python agent frameworks in 2026,
        compare their features in a structured format,
        and write a Python script that demonstrates 
        creating an agent in each framework.
        """

        result = await workflow.run(complex_task)
        print(result)

    asyncio.run(main())
```

**How it works step by step:**
```makdown
    Complex Goal → [Manager Agent]
                    │
                    ├── Creates Task 1 → assigns to [Web Surfer] → reviews result
                    ├── Creates Task 2 → assigns to [Data Analyst] → reviews result
                    ├── Creates Task 3 → assigns to [Code Writer] → reviews result
                    │        ↑
                    │   "Not good enough — redo with these changes"
                    │        │
                    └── Re-assigns → [Code Writer] → reviews again → Final Result
```

1. You give the manager one complex, open-ended goal
2. The manager reads it and decides what sub-tasks are needed — you do not specify these
3. The manager assigns each sub-task to the most suitable specialist from the available pool
4. Each specialist completes their task and returns the result to the manager
5. The manager reviews the result — if it is good enough, it moves on; if not, it re-assigns with feedback
6. This continues until the manager is satisfied that the overall goal is achieved
7. The final synthesised result is returned

**When to use It**
Use Magentic when the task is genuinely complex, open-ended, and cannot be broken down into a fixed sequence of steps in advance — because you do not know upfront exactly what steps will be needed. Best for research and synthesis tasks, building things from scratch across multiple domains, or any goal where the path to the answer needs to be discovered rather than prescribed.

**When NOT to use It:**
Do not use Magentic for simple or predictable tasks. It is the most powerful pattern but also the most expensive and least predictable in terms of exactly what steps it will take. If you know the steps upfront, use Sequential. If you need control and auditability, use Sequential or Handoff.


| Pattern | One-line summary |
|---|---|
| **Sequential** | Agents take turns in a fixed order, each building on the last |
| **Concurrent** | All agents work simultaneously on the same input, independently |
| **Handoff** | A receptionist agent routes to the right specialist based on the request |
| **Group Chat** | Agents have a shared conversation, each building on what others said |
| **Magentic** | A manager agent figures out the plan itself and coordinates specialists dynamically |

---

### 6.5 Advanced Execution

#### Human-in-the-Loop (HITL)

**Description**: Workflows can **pause execution and wait for human input** at any step. This is critical for approval gates, data correction, and supervised AI systems.

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.workflows import WorkflowBuilder, AgentExecutor
from agent_framework.workflows.hitl import HumanApprovalExecutor
from agent_framework.workflows.execution import InProcessExecution

async def main():
    client = OpenAIChatClient()
    draft_agent = Agent(client=client, name="drafter",
        instructions="Write a formal business email based on the request.")

    # Build workflow with HITL approval step
    workflow = (
        WorkflowBuilder()
        .add_executor(AgentExecutor(draft_agent, name="draft"))
        .add_executor(HumanApprovalExecutor(
            name="human_approval",
            prompt="Please review this email draft. Approve or provide feedback:",
        ))
        .add_edge("draft", "human_approval")
        .set_entry("draft")
        .set_exit("human_approval")
        .build()
    )

    result = await InProcessExecution.run_async(
        workflow,
        "Write an email to our investors about Q2 results being 15% above target."
    )
    print(result)

asyncio.run(main())
```

#### Checkpoint & Resume

**Description**: Workflows can **save their state at any step** (checkpoint) and **resume from that point** after an interruption. Critical for long-running processes that can fail or require days to complete.

```python
import asyncio
from agent_framework.workflows.execution import InProcessExecution
from agent_framework.workflows.checkpointing import RedisCheckpointStore

async def main():
    checkpoint_store = RedisCheckpointStore(connection_string="redis://localhost:6379")

    # Execution with checkpointing enabled
    run = await InProcessExecution.start_async(
        workflow=my_long_running_workflow,
        input_data={"task": "Analyze 1000 customer reviews"},
        checkpoint_store=checkpoint_store,
        checkpoint_id="review_analysis_run_001",
    )

    # If the process is interrupted, resume from last checkpoint:
    # run = await InProcessExecution.resume_async(
    #     checkpoint_id="review_analysis_run_001",
    #     checkpoint_store=checkpoint_store,
    # )

    result = await run.get_result()
    print(result)
```

---

## 7. DevUI

**Description**: DevUI is a **browser-based local debugger** for Microsoft Agent Framework. It provides a real-time visual representation of agent message flows, tool calls, workflow step transitions, and state changes. Essential for debugging complex multi-agent workflows.

**Features**:
- **Message Flow Visualization** — See all messages between agents
- **Tool Call Tracing** — Inspect tool inputs and outputs
- **Workflow Graph View** — Visual graph of executor states
- **Streaming Replay** — Replay any conversation step-by-step
- **State Inspector** — View shared state and session data at any point
- **Performance Metrics** — Token counts, latency per step

**How to Enable**:

```python
import asyncio
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from agent_framework.devui import DevUIServer  # Preview package

async def main():
    # Start DevUI server (opens browser at http://localhost:5001)
    async with DevUIServer(port=5001) as devui:
        agent = Agent(
            client=OpenAIChatClient(),
            name="DebugAgent",
            instructions="You are a helpful assistant.",
            devui=devui,  # Attach DevUI for real-time visualization
        )

        result = await agent.run("Explain the difference between TCP and UDP.")
        print(result)
        # All traces visible at http://localhost:5001

asyncio.run(main())
```

**Tracing and Observability in DevUI**:

```bash
# Install DevUI package
pip install agent-framework-devui --pre

# Set environment variables for DevUI
export MAF_DEVUI_ENABLED=true
export MAF_DEVUI_PORT=5001

# Run your agent script — DevUI opens automatically
python my_agent.py
```

**Security and Deployment**:
- DevUI is **localhost-only** in development mode
- For production observability, use OpenTelemetry export to Azure Monitor or Grafana
- DevUI traces contain full message content — never expose in production without authentication

---

## 8. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Microsoft Agent Framework (MAF)                    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      WORKFLOW LAYER                           │  │
│  │  Sequential │ Concurrent │ Handoff │ Group Chat │ Magentic   │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │ Workflow Builder │ Executors │ Edges │ State Management  │  │  │
│  │  │ Checkpointing   │ HITL      │ Sub-Workflows │ DAG Exec  │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                       AGENT LAYER                             │  │
│  │  ┌───────────────────────────────────────────────────────┐    │  │
│  │  │           MIDDLEWARE PIPELINE                         │    │  │
│  │  │  Safety │ Logging │ Guardrails │ HITL │ Token Count  │    │  │
│  │  └───────────────────────────────────────────────────────┘    │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐  │  │
│  │  │    TOOLS    │  │   MEMORY     │  │   AGENT SKILLS       │  │  │
│  │  │  Functions  │  │  Session     │  │  File-based          │  │  │
│  │  │  Code Interp│  │  Context     │  │  Code-based          │  │  │
│  │  │  File Search│  │  Compaction  │  │  Class-based         │  │  │
│  │  │  Web Search │  │  Storage     │  │  (CodeAct + Skills)  │  │  │
│  │  │  MCP Tools  │  │  Backends    │  └──────────────────────┘  │  │
│  │  └─────────────┘  └──────────────┘                            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    MODEL PROVIDER LAYER                       │  │
│  │  Azure OpenAI │ OpenAI │ Anthropic │ Bedrock │ Gemini │ Ollama│  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   OBSERVABILITY LAYER                         │  │
│  │  OpenTelemetry │ Azure Monitor │ DevUI │ Structured Logging   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Best Practices Summary

### Agent Design
- Give every agent a clear `name` — used in routing, logging, and traces
- Write sharp, focused `instructions` — one agent, one responsibility
- Set `max_turns` to prevent infinite tool-call loops
- Use Declarative YAML agents for enterprise deployments (version control, no code deploys)

### Tools
- Write docstrings — the LLM reads them to decide when to call a tool
- Always use `@requires_approval` for tools with irreversible side effects
- Keep tool functions pure (no hidden side effects)
- Use CodeAct for chained multi-tool workloads (50% latency reduction)

### Memory & Sessions
- Generate session IDs from user + conversation identifiers
- Set TTL on persistent sessions (e.g., 24 hours of inactivity)
- Use `SummarizationStrategy` for long conversations, `SlidingWindowStrategy` for task bots
- Use Redis for production session storage, not in-memory

### Middleware
- Order middleware: Safety → Logging → Business Rules → Output Validation
- Use `shared_state` to pass data between middleware without polluting conversation
- Always handle exceptions in middleware — wrap with try/except

### Workflows
- Start with Functional Workflow API (`@workflow` / `@step`) for simplicity
- Move to `WorkflowBuilder` when you need type-safe message routing
- Use Checkpointing for any workflow that takes >30 seconds
- Add HITL gates before any irreversible operation (email send, database write)
- Choose the right orchestration pattern:
  - Fixed steps → Sequential
  - Independent analysis → Concurrent
  - Dynamic routing → Handoff
  - Collaborative refinement → Group Chat
  - Complex open-ended task → Magentic

### Production
- Export OpenTelemetry traces to Azure Monitor in production
- Use `ManagedIdentityCredential` (not `AzureCliCredential`) in production
- Set meaningful `OTEL_SERVICE_NAME` environment variable
- Use DevUI only in local development — never expose in production
- Pin `agent-framework` package version in `requirements.txt` for reproducible builds

---

## Installation Reference

```bash
# Full install (recommended for development)
pip install agent-framework

# Minimal installs for production
pip install agent-framework-core              # Core + Azure OpenAI + Workflows
pip install agent-framework-foundry          # Core + Azure AI Foundry
pip install agent-framework-anthropic        # Core + Anthropic Claude
pip install agent-framework-devui --pre      # DevUI debugger (preview)
pip install agent-framework-hyperlight-codeact --pre  # CodeAct (alpha)
```

## Environment Variables

```bash
# Azure OpenAI
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"

# Azure AI Foundry
export FOUNDRY_PROJECT_ENDPOINT="https://your-project.services.ai.azure.com"
export FOUNDRY_MODEL_DEPLOYMENT_NAME="gpt-4o"

# OpenAI
export OPENAI_API_KEY="sk-..."

# Observability
export OTEL_SERVICE_NAME="my-agent-service"
export OTEL_EXPORTER_OTLP_ENDPOINT="https://your-otlp-endpoint"

# DevUI
export MAF_DEVUI_ENABLED=true
export MAF_DEVUI_PORT=5001
```

---

*Guide compiled from: [Microsoft Learn Docs](https://learn.microsoft.com/en-us/agent-framework/), [GitHub: microsoft/agent-framework](https://github.com/microsoft/agent-framework), [MAF Dev Blog](https://devblogs.microsoft.com/agent-framework/), and [PyPI: agent-framework](https://pypi.org/project/agent-framework/). Version 1.0 GA — May 2026.*