**To the World-Class AI Development Team:** This document details the architecture of the **Enterprise Knowledge Base (EKB)** and the **Continuous Learning Loop (CLL)**. These two components form the soul of our AIaaS platform, providing it with a perfect memory and the ability to learn from experience, transforming it from a static tool into a dynamic, evolving intelligence.

## 1\. The Enterprise Knowledge Base (EKB): The Corporate Memory

The EKB is the single source of truth for all CSA knowledge. It combines a Vector Database for semantic understanding and a Relational Database for structured data.

### 1.1. Vector Database (Weaviate)

This stores the unstructured and semi-structured knowledge of the entire organization.

*   **Content:**
    *   All past project files (drawings, reports, calculations).
    *   All design codes and standards (IS, ACI, Eurocode).
    *   All internal company checklists, QAPs, and best practice manuals.
    *   All lessons learned and human corrections captured by the CLL.
*   **Process:** An automated ETL pipeline (using n8n and unstructured.io) will continuously process new documents, break them into meaningful chunks, enrich them with detailed metadata, and load them into Weaviate.

### 1.2. Relational Database (Supabase PostgreSQL)

This stores the structured, transactional data for all active and past projects, as defined in the previous specifications (projects, deliverables, tasks, reviews, users, audit logs).

### 1.3. Retrieval-Augmented Generation (RAG): The Bridge to Knowledge

The RAG agent is the sophisticated mechanism the AI uses to query the EKB. It follows a multi-step process:

1.  **Query Expansion:** Expands a simple user query into multiple, nuanced search vectors.
2.  **Hybrid Search:** Performs a combination of semantic vector search and precise metadata filtering to find the most relevant knowledge chunks.
3.  **Re-ranking:** Uses an LLM to rank the retrieved chunks for relevance and importance.
4.  **Context Assembly:** Assembles the top-ranked chunks into a concise, context-rich block that is fed to the reasoning core.

This ensures every AI decision is informed by the full weight of the company's collective experience.

## 2\. The Continuous Learning Loop (CLL): The Engine of Improvement

The CLL is what makes our AIaaS a true learning machine. It is an automated n8n workflow that captures the value from every human interaction.

### 2.1. The Learning Trigger

The CLL is triggered every time a human engineer approves, rejects, or overrides an AI-generated output. This action provides a clear signal of success or failure.

### 2.2. The Learning Process

1.  **Capture Data:** The workflow captures the AI's input, its output, and the human's action (including comments and data overrides).
2.  **Generate Learning Record:** It creates a structured "learning record." If the AI was wrong, this is a "mistake-correction" pair. If the AI was right, it's a "positive reinforcement" example.
3.  **Instant Knowledge Update:** The learning record is immediately converted into a "Lesson Learned" text, embedded, and stored in the Vector Database. The AI's knowledge grows in real-time.
4.  **Curate Training Data:** The structured record is also saved to a dedicated fine\_tuning\_dataset table.
5.  **Automated Fine-Tuning:** On a regular schedule, an automated process uses this curated dataset to fine-tune our self-hosted Llama 3.1 models. This improves the AI's baseline performance over time.

### 2.3. The Flywheel Effect

This creates a powerful virtuous cycle:

*   More projects lead to more human interactions.
*   More interactions lead to more learning records.
*   More learning records lead to a smarter EKB and better fine-tuned models.
*   A smarter system produces better results, encouraging more usage.

This learning flywheel is our most powerful competitive advantage. It ensures that our AIaaS platform doesn't just stay current; it becomes exponentially more valuable over time.