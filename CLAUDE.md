# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **documentation-only repository** containing technical specifications for a CSA (Civil & Structural Architecture) Engineering AI Automation System. It does not contain executable code, but rather comprehensive markdown documentation describing the architecture, workflows, and requirements for building an AI-powered platform for engineering automation.

## Project Structure

The repository contains 46 markdown files organized into several categories:

### Core Specification Documents
- [CSA.md](CSA.md) - Comprehensive overview of CSA Department operations, workflows, and interfaces
- [CSA2.md](CSA2.md) - AI Automation Master Specification detailing universal workflows for Civil, Structural, and Architectural modules

### Architecture Documents
- [MarkdownFile1.md](MarkdownFile1.md) - Enhanced Spec Part 1: Comparative Architecture Analysis (General AI vs. Specialized CSA AI)
- [Final_MarkdownFile.md](Final_MarkdownFile.md) - AIaaS Platform architecture and tech stack blueprint
- [CSA_AIaaS_Platform_Implementation_Guide.md](CSA_AIaaS_Platform_Implementation_Guide.md) - Sprint 1 implementation guide for the CSA AIaaS Platform, including detailed technical setup, database schema, and LangGraph orchestration

### Project Context
- [MOM_Engineering_Automation_Kickoff_Dec02_2025.md](MOM_Engineering_Automation_Kickoff_Dec02_2025.md) - Meeting minutes from the December 2025 kickoff meeting with Shiva Engineering Services, detailing project scope, timeline, and implementation roadmap

### Additional Specifications
- MarkdownFile2-21.md - Various detailed specification documents
- Markdown1-15.md - Supporting documentation
- Final1-7_MarkdownFile.md - Finalized specification segments

## Domain Context

This system is designed for **CSA Engineering** which includes:

**Core Disciplines:**
- Civil Engineering (foundations, earthworks, underground structures)
- Structural Engineering (RCC design, steel structures, PEB)
- Architectural Engineering (layouts, finishes, walls, lintels)

**Key Workflows:**
1. FEED-Level CSA (preliminary design, feasibility)
2. Basic Engineering (Design Basis Reports, architectural conceptualization, structural analysis)
3. Detailed Engineering (foundation design, RCC/steel superstructure, BOQ/MTO generation)
4. Tendering and Quality Control

**Critical Technical Concepts:**
- **STAAD/ETABS**: Structural analysis software for calculating member forces and reactions
- **BOQ/MTO**: Bill of Quantities / Material Take-Off - quantity extraction from drawings for tendering
- **DBR**: Design Basis Report - document that fixes all engineering assumptions
- **RCC**: Reinforced Cement Concrete
- **SBC**: Safe Bearing Capacity (soil parameter)
- **HITL**: Human-in-the-Loop review for high-risk decisions

## Architectural Paradigm

The documentation describes a shift from traditional AI automation to **cognitive augmentation**:

**Target Architecture:**
- Unified reasoning core with domain specialization in CSA engineering
- Deep, curated knowledge base (Vector DB) with CSA-specific data
- Dynamic, continuous learning from every project
- Proactive, goal-oriented task handling with risk-based autonomy
- Schema-based extensibility without new code

**Confirmed Tech Stack (from Implementation Guide):**
- **Backend**: Python 3.11+, FastAPI, LangGraph (StateGraph), LangChain
- **Database**: Supabase (PostgreSQL + pgvector for vector search)
- **Validation**: Pydantic V2 (strict typing)
- **LLM Integration**: OpenAI API / Anthropic API (Claude 3.5 Sonnet / GPT-4)
- **Orchestration**: LangGraph + Apache Airflow (for workflow automation)
- **Infrastructure**: Kubernetes with auto-scaling
- **Frontend**: Next.js + TypeScript + TailwindCSS
- **Configuration**: python-dotenv for environment management

## Working with This Repository

### Understanding the Specifications

When asked to explain or work with these documents:
1. Recognize this describes an AI system for **Civil & Structural engineering automation**
2. The specifications detail both business workflows (what engineers do) and technical architecture (how to build the AI system)
3. Documents are interdependent - [CSA.md](CSA.md) provides domain context, [CSA2.md](CSA2.md) provides calculation workflows, [MarkdownFile1.md](MarkdownFile1.md) provides architectural philosophy

### Document Relationships

The documentation follows a logical progression:

1. **Domain Understanding**: Start with [CSA.md](CSA.md) for business context and workflows
2. **Calculation Logic**: Review [CSA2.md](CSA2.md) for detailed engineering calculation workflows
3. **Architectural Vision**: Read [MarkdownFile1.md](MarkdownFile1.md) for the shift from automation to cognitive augmentation
4. **Platform Architecture**: Study [Final_MarkdownFile.md](Final_MarkdownFile.md) for AIaaS platform design
5. **Implementation Details**: Follow [CSA_AIaaS_Platform_Implementation_Guide.md](CSA_AIaaS_Platform_Implementation_Guide.md) for sprint-based development
6. **Project Context**: Reference [MOM_Engineering_Automation_Kickoff_Dec02_2025.md](MOM_Engineering_Automation_Kickoff_Dec02_2025.md) for scope, stakeholders, and timeline

### Key Bottlenecks Described

The system aims to solve:
- Manual RCC foundation grouping (70-80% time reduction potential)
- BOQ extraction from drawings (manual counting takes 15-20 days)
- Late multi-discipline coordination causing site rework
- Tender documentation cycle time
- Drawing validation and quality control

### Implementation Context

Per the kickoff meeting minutes:
- **Timeline**: 12-month implementation roadmap
- **Client**: Shiva Engineering Services (SES)
- **Development Team**: TheLinkAI
- **First Deliverables**: Beginning of Month 3 (February 2026)
- **Development Completion**: Months 8-9 (latest)
- **Go-Live**: Month 12 (December 2026)

**Scope Inclusions:**
- Complete engineering operation automation across all EPCM disciplines
- Procurement and construction management documentation
- Automated document generation (specifications, reports, BOQs)
- Cross-discipline review automation

**Scope Exclusions (Phase 1):**
- 2D/3D drafting/modeling (AutoCAD, Revit, BIM)
- Full ERP integration
- Mobile applications
- Fully autonomous agents without human validation

### Implementation Roadmap (Sprint-Based)

The [CSA_AIaaS_Platform_Implementation_Guide.md](CSA_AIaaS_Platform_Implementation_Guide.md) contains the detailed technical implementation plan broken into sprints:

**Phase 1: "The Knowledgeable Assistant" (3 Sprints)**
- **Sprint 1**: Infrastructure & Core Logic (Supabase, LangGraph, Ambiguity Detection)
- **Sprint 2**: ETL & Vector DB (Knowledge ingestion, embeddings, chunking)
- **Sprint 3**: RAG Agent & Conversational UI (Chat interface, retrieval-augmented generation)

**Critical Components:**
- **Ambiguity Detection Node**: Core safety mechanism that prevents the AI from guessing when data is missing. Uses strict JSON output format and must be implemented from Day 1.
- **AgentState Schema**: Backbone of LangGraph orchestration with required fields:
  - `task_id`: str
  - `input_data`: Dict
  - `retrieved_context`: Optional[str]
  - `ambiguity_flag`: bool
  - `clarification_question`: Optional[str]
  - `risk_score`: Optional[float]
- **Audit Log**: Zero-trust security logging for all actions in the system
- **Database Schema**: Foundation tables include `projects`, `deliverables`, `audit_log`, and `knowledge_chunks` (Sprint 2)

**Development Philosophy:**
- "Safety First" - baked into architecture from Day 1
- Never guess when data is missing
- Risk-based autonomy with Human-in-the-Loop (HITL) for high-risk decisions
- Strict typing throughout (Pydantic V2)
- Modular file structure for maintainability

### Making Changes

When editing or creating new documentation:
- Maintain technical accuracy regarding engineering calculations and code compliance (IS 456, IS 800, ACI, AISC)
- Preserve the architectural vision of "cognitive augmentation" vs simple automation
- Keep domain terminology consistent (use industry-standard CSA terms)
- Reference relevant existing documents when adding new specifications

### Documentation Standards

The documents follow these conventions:
- Technical specifications use numbered sections and subsections
- Engineering calculations are presented as step-by-step iteration logic
- Interdisciplinary interfaces are explicitly mapped
- Risk factors and bottlenecks are clearly identified
- Automation suggestions include expected benefits and challenges

## Notes

- This is **not a git repository** - no version control is currently configured
- No build, test, or deployment commands exist (documentation only)
- The content describes a system to be built, not an implemented system
- When referencing file paths, use the format: [filename.md](filename.md)
