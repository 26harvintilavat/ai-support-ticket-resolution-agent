# AI Support Ticket Resolution Agent

## Project Overview

The **AI Support Ticket Resolution Agent** is an Agentic AI and RAG-based system designed to help support teams resolve customer issues faster and more consistently.

Support teams often receive repetitive questions, troubleshooting requests, configuration issues, and product-related problems. In many cases, the information required to solve a new ticket already exists somewhere inside product documentation, FAQs, knowledge bases, or previously resolved support tickets.

However, support engineers still have to manually search through these sources before writing a response.

This project aims to automate a large part of that process.

The system will analyze an incoming support ticket, retrieve relevant information from trusted sources, reason over the retrieved evidence, and generate a suggested resolution with citations. If the system cannot find enough reliable evidence, it should avoid inventing an answer and instead recommend escalation to a human support engineer.

---

## Problem Statement

Support teams commonly face the following problems:

- Large numbers of repetitive customer tickets.
- Time spent manually searching documentation.
- Useful solutions hidden inside historical resolved tickets.
- Inconsistent responses between different support engineers.
- Slow response times.
- Knowledge being dependent on experienced support staff.
- LLM-generated responses potentially hallucinating unsupported solutions.

The goal of this project is to build an AI assistant that can intelligently search existing support knowledge and produce evidence-based resolution suggestions.

---

## Example Scenario

A customer submits the following ticket:

> "After rotating my API key, all of my requests are returning HTTP 401 Unauthorized."

The system should not immediately ask an LLM to generate an answer.

Instead, it should execute a workflow similar to:

```text
Incoming Support Ticket
        ↓
Understand / Classify Ticket
        ↓
Search Product Documentation
        ↓
Search Similar Historical Tickets
        ↓
Retrieve Relevant Evidence
        ↓
Analyze Possible Resolution
        ↓
Check Whether Evidence Is Sufficient
       / \
      /   \
    Yes    No
     ↓      ↓
Generate   Escalate
Response   to Human
     ↓
Validate Citations
     ↓
Final Suggested Resolution
```

The final response could contain:

```text
Suggested Resolution

The 401 error is likely caused by the application still using the
previous API key.

Recommended steps:

1. Verify that the new API key has been updated in the application.
2. Restart services that cache environment variables.
3. Confirm that the Authorization header uses the expected format.

Evidence:

- API Authentication Documentation
- API Key Rotation Guide
- Similar resolved ticket #1842
```

---

# Core Goal

The core goal of the system is:

> Generate reliable support resolution suggestions using company documentation and historical support knowledge while minimizing hallucinations and escalating uncertain cases to humans.

This is not intended to be a generic chatbot.

It is an **evidence-driven support resolution workflow**.

---

# Main AI Concepts

The project will primarily explore:

- Generative AI
- Retrieval-Augmented Generation (RAG)
- Agentic AI
- LLM tool calling
- Structured LLM outputs
- Stateful AI workflows
- Semantic search
- Vector databases
- Reranking
- AI observability
- LLM evaluation
- Hallucination reduction
- Human-in-the-loop workflows

---

# Proposed Technology Stack

## Backend

- Python
- FastAPI
- Pydantic

FastAPI will expose APIs for ticket submission, retrieval, resolution generation, and evaluation.

---

## AI Framework

### LangChain

LangChain will provide reusable AI components such as:

- LLM integrations
- Embedding models
- Document loaders
- Text splitters
- Retrievers
- Vector store integrations
- Tool definitions
- Structured output
- Prompt management

---

### LangGraph

LangGraph will manage the agentic workflow.

Possible workflow:

```text
START
  ↓
classify_ticket
  ↓
retrieve_documentation
  ↓
retrieve_similar_tickets
  ↓
rerank_evidence
  ↓
analyze_ticket
  ↓
check_evidence
  ↓
 ┌─────────────────────┐
 │                     │
Enough Evidence     Insufficient Evidence
 │                     │
 ↓                     ↓
generate_response    escalate_ticket
 │
 ↓
validate_response
 │
 ↓
END
```

LangGraph will allow the system to maintain state and conditionally route execution between different steps.

---

## RAG Layer

The knowledge base may contain:

- Product documentation
- Troubleshooting guides
- FAQs
- API documentation
- Configuration guides
- Historical resolved support tickets
- Known issues
- Internal support knowledge

Documents will be converted into embeddings and stored in a vector database.

---

## Vector Database

Recommended initial implementation:

```text
PostgreSQL
+
pgvector
```

This provides both relational storage and semantic vector search.

Alternative vector stores may be explored later if required.

---

## Observability and Evaluation

### Langfuse

Langfuse will be used to observe and evaluate the AI workflow.

It should capture:

- Incoming ticket
- Retrieved documents
- Retrieved historical tickets
- LLM prompts
- LLM responses
- Agent decisions
- Tool calls
- Latency
- Token usage
- Model cost
- Errors
- Evaluation results

This will make it possible to understand why the system generated a particular resolution.

---

# High-Level Architecture

```text
                    ┌─────────────────────┐
                    │      Frontend       │
                    │ Ticket Resolution UI│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       FastAPI       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      LangGraph      │
                    │ Agentic Workflow    │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼───────────────┐
                │              │               │
                ▼              ▼               ▼
        Documentation      Historical      LLM / Tools
            RAG              Tickets
                │              │
                └──────┬───────┘
                       ▼
                PostgreSQL + pgvector

                       │
                       ▼
                   Langfuse
             Tracing + Evaluation
```

---

# Main System Components

## 1. Knowledge Ingestion

Responsible for processing support knowledge.

It will:

- Load documents.
- Clean text.
- Split documents into chunks.
- Generate embeddings.
- Store chunks in the vector database.
- Preserve metadata about each source.

Example metadata:

```json
{
  "source": "api-authentication-guide.md",
  "document_type": "documentation",
  "section": "API Key Rotation"
}
```

---

## 2. Historical Ticket Ingestion

Resolved support tickets will also become part of the knowledge base.

Example ticket:

```text
Issue:
API started returning 401 after credential rotation.

Resolution:
Application was still using the old API key stored in the deployment
environment. Updating the environment variable and restarting the
application resolved the issue.
```

These tickets can help the system identify previously solved problems that resemble the new ticket.

---

## 3. Ticket Classification

The incoming ticket will first be analyzed.

Possible categories could include:

- Authentication
- Billing
- API
- Configuration
- Deployment
- Performance
- Database
- Account
- Integration
- Unknown

Structured output could look like:

```json
{
  "category": "authentication",
  "priority": "medium",
  "summary": "API returns 401 after API key rotation"
}
```

---

## 4. Documentation Retrieval

The system searches the product knowledge base for documentation relevant to the problem.

Example:

```text
Query:
401 unauthorized after rotating API key

Retrieved:

1. API Key Rotation Guide
2. Authentication Troubleshooting
3. Authorization Header Documentation
```

---

## 5. Similar Ticket Retrieval

The system independently searches historical resolved tickets.

Example:

```text
New Ticket
   ↓
Embedding
   ↓
Vector Similarity Search
   ↓
Top Similar Historical Tickets
```

This gives the model access to solutions that previously worked for similar incidents.

---

## 6. Retrieval Reranking

Initial vector search may return partially relevant results.

A reranking step can evaluate which retrieved documents are actually useful for the current support request.

Example:

```text
Initial Retrieval

Document A
Document B
Document C
Document D
Document E

        ↓

Reranker

        ↓

Document D
Document A
Document C
```

Only the strongest evidence should be passed into the reasoning stage.

---

## 7. Resolution Analysis

The system analyzes:

- Customer ticket
- Product documentation
- Historical ticket resolutions
- Retrieved evidence

It then determines a possible resolution.

The model should be instructed to reason only from available evidence rather than invent unsupported product behavior.

---

## 8. Evidence Sufficiency Check

Before generating the final response, the system decides whether enough evidence exists.

Possible structured output:

```json
{
  "evidence_sufficient": true,
  "confidence": 0.88,
  "reason": "Documentation and two historical tickets support the same resolution."
}
```

If evidence is insufficient:

```text
Ticket
 ↓
Unable to establish reliable solution
 ↓
Human escalation
```

The system should not fabricate a resolution.

---

## 9. Response Generation

When sufficient evidence exists, the system produces a structured support response.

Example:

```text
Issue Summary

The customer receives HTTP 401 responses after rotating the API key.

Likely Cause

The application may still be using the previous API credential.

Recommended Resolution

1. Verify the new key is configured in the application.
2. Restart services that cache environment variables.
3. Verify the Authorization header format.
4. Retry the API request.

Sources

- API Key Rotation Guide
- Authentication Troubleshooting Guide
- Resolved Ticket #1842
```

---

## 10. Citation Validation

The system should verify that claims in the generated response are supported by retrieved evidence.

The objective is to reduce hallucination.

Example:

```text
Generated Claim
      ↓
Find Supporting Evidence
      ↓
Supported?
  /        \
Yes        No
 ↓          ↓
Keep      Remove / Regenerate
```

---

## 11. Human Escalation

Certain situations should automatically require human review.

Examples:

- Insufficient documentation
- Conflicting retrieved sources
- Very low retrieval relevance
- Potential security issue
- Unknown product behavior
- Multiple possible causes without enough evidence

Example response:

```text
Escalation Recommended

Reason:
The available documentation does not contain enough evidence to safely
recommend a resolution.

Relevant findings:
- Similar ticket found, but resolution does not match current product version.
- No supporting product documentation was retrieved.
```

---

# LangGraph State

A possible workflow state could contain:

```python
{
    "ticket_id": "...",
    "ticket_text": "...",
    "category": "...",

    "documentation_results": [],
    "similar_tickets": [],
    "reranked_evidence": [],

    "analysis": "...",

    "evidence_sufficient": False,
    "confidence": 0.0,

    "draft_response": "...",
    "citations": [],

    "requires_human_review": False
}
```

Each LangGraph node will read or modify this shared state.

---

# Example Agent Tools

The agent may eventually have tools such as:

```text
search_documentation()

search_historical_tickets()

get_document()

get_ticket()

retrieve_known_issue()

search_faq()

escalate_ticket()
```

The model should only receive tools that are necessary for the workflow.

---

# Evaluation

A key part of the project is evaluating whether the AI system actually improves when different RAG techniques are introduced.

A small evaluation dataset can contain around:

```text
30–50 support tickets
```

with expected answers or reference resolutions.

Experiments can compare:

```text
Baseline LLM

vs

Simple RAG

vs

RAG + Historical Tickets

vs

RAG + Reranking

vs

Agentic RAG
```

Important metrics may include:

- Answer correctness
- Retrieval relevance
- Citation correctness
- Hallucination rate
- Escalation accuracy
- Response latency
- Token usage
- Cost per ticket

Langfuse will be used to record and compare these experiments.

---

# Initial Scope

The project should remain intentionally small.

The first version should NOT attempt to become a complete customer support platform.

The initial system only needs to support:

```text
Support ticket
      ↓
Retrieve relevant knowledge
      ↓
Analyze evidence
      ↓
Generate supported resolution
      OR
Escalate
```

The focus is AI engineering rather than building a full SaaS application.

---

# Out of Scope for Initial Version

The following features should not be included unless the core system is already complete:

- Full help-desk platform
- CRM integration
- Email integration
- Slack integration
- Multi-tenant SaaS architecture
- Complex authentication system
- Enterprise RBAC
- Voice support
- Autonomous customer communication
- Large administrative dashboard
- Billing
- Mobile application

Keeping these out of scope prevents the project from becoming unnecessarily large.

---

# Suggested Development Phases

## Phase 1 — Project Foundation

Build:

- FastAPI backend
- PostgreSQL
- pgvector
- basic project structure
- Docker environment
- configuration management

---

## Phase 2 — Knowledge Ingestion

Build:

- document loader
- chunking
- embeddings
- vector storage
- metadata handling

---

## Phase 3 — Basic RAG

Build:

```text
Question
 ↓
Retrieve documents
 ↓
Generate answer
```

This establishes the baseline.

---

## Phase 4 — Support Ticket Retrieval

Add:

- historical ticket storage
- similar-ticket retrieval
- combined documentation + ticket context

---

## Phase 5 — LangGraph Agentic Workflow

Implement:

```text
classify
 ↓
retrieve
 ↓
analyze
 ↓
check evidence
 ↓
respond / escalate
```

---

## Phase 6 — Reranking and Citation Validation

Add:

- retrieval reranking
- citation generation
- evidence verification
- hallucination controls

---

## Phase 7 — Langfuse Observability

Add:

- traces
- LLM call monitoring
- retrieval traces
- latency
- token usage
- cost tracking

---

## Phase 8 — Evaluation

Create an evaluation dataset and compare different system versions.

Example:

```text
Simple RAG
      ↓
RAG + Reranking
      ↓
Agentic RAG
```

The goal is to provide measurable evidence that architectural improvements actually improve system quality.

---

# Success Criteria

The project can be considered successful when it can:

1. Accept a realistic support ticket.
2. Understand the ticket category and problem.
3. Retrieve relevant product documentation.
4. Retrieve similar historical tickets.
5. Select the strongest evidence.
6. Generate a useful resolution based on that evidence.
7. Cite the sources used to generate the answer.
8. Detect when the available evidence is insufficient.
9. Escalate uncertain tickets rather than hallucinating.
10. Provide full Langfuse traces showing how the answer was produced.
11. Run against a small evaluation dataset with measurable results.

---

# Project Philosophy

The purpose of this project is not to demonstrate that an LLM can answer questions.

The purpose is to demonstrate how to build a **reliable AI system around an LLM**.

The project should emphasize:

```text
Retrieval
+
Agentic Workflow
+
Evidence
+
State
+
Tool Use
+
Observability
+
Evaluation
```

rather than simply:

```text
User → LLM → Answer
```

The final system should demonstrate practical skills relevant to modern **Generative AI, RAG, Agentic AI, and AI Engineering** roles.
