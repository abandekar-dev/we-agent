# Work Engineering Agent

A RAG-powered AI assistant for Work Design Engineering. Built on the Work Engineering framework, this agent helps organizations redesign how they work with AI — across work architecture, org design, decision flows, talent models, learning systems, and institutional knowledge.

## Features

- **5 Specialist Agent Modes** — each with deep domain expertise:
  - **Orchestrator** — General assistant that routes to the right expertise
  - **Work Architect** — Designs future-state work across six interdependent architectures
  - **Work Economist** — Models ROI, task-level economics, metabolic gap, and business cases
  - **Work Ethnographer** — Maps how work actually happens (not how process docs say it does)
  - **Change Engineer** — Designs organizational change using systems dynamics and Meadows' leverage points

- **Multi-Model Support (BYOK)** — Bring your own API key for:
  - Anthropic (Claude Sonnet 4, Claude Opus 4)
  - OpenAI (GPT-4o, GPT-4o Mini, o3 Mini)
  - Google (Gemini 2.5 Flash, Gemini 2.5 Pro)

- **RAG Knowledge Base** — 3,800+ chunks from the full Work Engineering corpus:
  - Resource Hub (landing page, canvas, frameworks, templates)
  - Implementation Playbooks (assess, design, activate, governance)
  - Pattern Libraries (14 transformation patterns)
  - Discernment Framework
  - Work Design Pod (7 agents, 17 skills, engagement examples)

## Quick Start

### Prerequisites

- Python 3.10+
- An API key from Anthropic, OpenAI, or Google

### Setup

```bash
# Clone the repo
git clone https://github.com/abandekar-dev/we-agent.git
cd we-agent/backend

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build the knowledge base index
# Update paths in ingest.py to point to your local content directories
python ingest.py

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in your browser.

### Usage

1. Select a provider and model from the sidebar
2. Enter your API key
3. Choose an agent mode (or leave on Orchestrator for auto-routing)
4. Ask a question or click a starter prompt

## Architecture

```
Frontend (Vanilla JS)          Backend (FastAPI)
┌─────────────────┐           ┌──────────────────────────┐
│  Chat UI        │    API    │  /api/chat               │
│  Model Selector ├──────────>│    ├─ Agent Personas      │
│  Agent Picker   │           │    ├─ RAG Retrieval       │
│  Source Viewer  │<──────────┤    └─ LLM Router          │
└─────────────────┘           │        ├─ Anthropic       │
                              │        ├─ OpenAI          │
                              │        └─ Google          │
                              │                          │
                              │  Knowledge Base (FAISS)  │
                              │    3,800+ embedded chunks │
                              └──────────────────────────┘
```

## Project Structure

```
we-agent/
├── backend/
│   ├── main.py           # FastAPI server, chat endpoint, static file serving
│   ├── agents.py          # 5 agent mode definitions with system prompts
│   ├── llm_router.py      # Routes requests to Anthropic/OpenAI/Google
│   ├── knowledge.py       # FAISS + fastembed RAG system
│   ├── ingest.py          # Knowledge base builder (processes .md and .html files)
│   └── requirements.txt
├── frontend/
│   ├── index.html         # Single-page chat application
│   ├── style.css          # Dark theme UI
│   └── app.js             # Client-side chat logic, markdown rendering
└── README.md
```

## Knowledge Base Sources

The agent's knowledge base is built from two repositories:

| Source | Content |
|--------|---------|
| **Work Engineering Hub** | Landing page, interactive canvas, task allocation framework, metrics translation template, gap analysis, platform strategy, skills & competencies |
| **Implementation Playbooks** | Phase 1 (Assess), Phase 2 (Design), Phases 3-4 (Activate), Governance & Operating Model |
| **Pattern Libraries** | 14 transformation patterns (Working Capital Optimization, Decision Velocity, Predictive Intelligence, Strategic Resource Allocation, etc.) |
| **Discernment Framework** | Strategic executive summary, synthesis session notes |
| **Work Design Pod** | 7 agent definitions, 17 skill files, engagement lifecycle, quality gates, deliverable templates |
| **Engagement Examples** | FNB Chicago (complete), Meridian Advisory (complete), Amazon (scoping) — full deliverable chains across all phases |

## Key Concepts

The agent is grounded in these Work Engineering principles:

- **Six Architectures**: Work, Org, Decision, Learning, Talent, Knowledge — designed as an interdependent system
- **Task-Level Economics**: Roles are bundles of tasks with different automation profiles (Level A-E)
- **Metabolic Gap**: An organization's capacity to absorb change is the binding constraint, not AI capability
- **Friction-First Learning**: Deliberate developmental difficulty before AI augmentation
- **Systems Dynamics**: Meadows' leverage points over generic change management
- **Specs, Not Slides**: Output is actionable specifications, not PowerPoint recommendations
