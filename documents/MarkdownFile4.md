**To the World-Class AI Development Team:** This document is **Part 4 of 12** of the definitive specification. It details the architecture of the **Enterprise Knowledge Base (EKB)**, the system's long-term memory. This includes the Vector Database design and the Retrieval-Augmented Generation (RAG) strategy that will fuel the AI's reasoning core with expert, context-aware knowledge.

# Enhanced Spec Part 4: Vector DB & RAG-Based Knowledge Management

**Version:** 6.0 (Strategic Blueprint) **Audience:** AI/ML Engineers, Data Architects

## 4.1. The EKB Philosophy: "Corporate Memory, Instantly Accessible"

The Enterprise Knowledge Base (EKB) is designed to solve one of the biggest challenges in large engineering firms: knowledge silos and the loss of institutional memory. The EKB will be the single, authoritative source of all CSA knowledge, both explicit (design codes) and tacit (lessons learned from past projects). The AI will consult this memory before every single decision.

## 4.2. Vector Database Architecture

We will use **Supabase's pgvector extension** for our Vector Database. This provides a seamless, integrated solution within our existing PostgreSQL environment, simplifying the tech stack.

### 4.2.1. The knowledge\_chunks Table

A single, powerful table will store all the embedded knowledge.

\-- Table to store all text chunks and their vector embeddings

CREATE TABLE csa.knowledge\_chunks (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

chunk\_text TEXT NOT NULL, -- The actual text snippet

embedding VECTOR(1536), -- The vector embedding (size depends on the model, e.g., 1536 for text-embedding-3-large)

metadata JSONB, -- Rich metadata for filtering

source\_document\_id UUID REFERENCES csa.documents(id), -- Link to the source document

created\_at TIMESTAMPTZ DEFAULT now()

);

\-- Create an IVFFlat index for fast approximate nearest neighbor search

CREATE INDEX ON csa.knowledge\_chunks USING ivfflat (embedding vector\_cosine\_ops) WITH (lists = 100);

### 4.2.2. The Power of Metadata

As detailed in Part 3, the metadata JSONB field is critical. It will allow us to perform **hybrid searches**: a combination of semantic vector search and precise metadata filtering.

**Example Metadata Structure:**

{

"source\_document\_name": "Project\_ABC\_Lessons\_Learned.docx",

"document\_type": "LESSON\_LEARNED",

"discipline": "CIVIL",

"deliverable\_context": "CIVIL\_FOUNDATION\_ISOLATED",

"project\_id": "uuid-of-project-abc",

"author": "John Doe",

"tags": \["corrosion", "coastal\_area", "M30\_concrete"\]

}

## 4.3. The Retrieval-Augmented Generation (RAG) Strategy

The RAG agent is the bridge between the EKB and the Unified Reasoning Core. It follows a sophisticated, multi-step retrieval process to gather the most relevant context.

### The RAG Workflow:

1.  **Initial Query:** The reasoning core generates an initial query. Example: Designing an isolated footing for a column with P=800kN in a coastal area.
2.  **Query Expansion (LLM-Step):** The initial query is sent to the reasoning core LLM with a prompt: You are a search expert. Expand the following query to cover all relevant aspects for a comprehensive knowledge base search. Query: \[Initial Query\] **Expanded Queries:**
    *   Isolated footing design for heavy loads
    *   Reinforced concrete design in corrosive coastal environments
    *   IS 456 guidelines for concrete grade in marine exposure
    *   Past project examples of foundations in coastal areas
3.  **Multi-Vector Search:** The RAG agent performs a separate vector search for **each** of the expanded queries.
4.  **Metadata Filtering:** The search results are then filtered based on the current project's context.
    *   **Example:** The system will prioritize results where metadata.project\_context matches the current project's standards or where metadata.tags are relevant.
5.  **Re-ranking (LLM-Step):** The filtered results (a collection of text chunks) are passed back to the reasoning core LLM with a final prompt: You are a lead engineer. Here are several pieces of information related to the current design task. Rank them in order of importance and relevance from 1 to 10. Discard any that are irrelevant.
6.  **Context Assembly:** The top-ranked, most relevant text chunks are assembled into a final, concise context block.
7.  **Final Prompt:** This context block is prepended to the final prompt that is sent to the reasoning core to perform the actual design task.

### Example Final Prompt:

SYSTEM

You are a CSA Engineer AI. Your task is to design an isolated footing. Before you begin, review the following critical context retrieved from the Enterprise Knowledge Base.

\--- CONTEXT START ---

\*\*From IS 456, Clause 8.2.1:\*\* "For structures located in coastal areas, the minimum grade of concrete shall be M30."

\*\*From Project ABC (similar project):\*\* "Initial designs used M25 concrete, which showed signs of spalling after 5 years. All subsequent designs were revised to use M30 with a minimum cover of 50mm."

\*\*From Lessons Learned DB:\*\* "In the Mumbai coastal region, always specify galvanized or epoxy-coated rebar for foundations to mitigate chloride-induced corrosion."

\--- CONTEXT END ---

USER

\*\*Task:\*\* Design Isolated Footing

\*\*Inputs:\*\*

\- DBR: { "SBC\_VALUE": 150, "CONCRETE\_GRADE": "M25" } <-- Note the conflict!

\- Support Reaction: { "P": 800 }

\*\*Action:\*\* Proceed with the design.

In this example, the AI, armed with the retrieved context, would immediately detect the conflict between the DBR's M25 grade and the best practices from the EKB. This would trigger the **Ambiguity Detection Framework** (Part 6), causing the AI to proactively ask for clarification: The DBR specifies M25 concrete, but best practices and IS 456 strongly recommend M30 for this coastal location. Please clarify which grade to use.

This RAG strategy transforms the AI from a simple calculator into a wise, experienced engineer that leverages the company's entire history of collective intelligence.