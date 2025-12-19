**To the World-Class AI Development Team:** This document is **Part 3 of 12** of the definitive specification. It outlines the crucial strategy for selecting, fine-tuning, and preparing the Large Language Models (LLMs) that will power the CSA AI's reasoning core. This strategy is designed for a hybrid approach that maximizes both performance and cost-effectiveness.

# Enhanced Spec Part 3: LLM Selection, Fine-tuning & Knowledge Prep

**Version:** 6.0 (Strategic Blueprint) **Audience:** AI/ML Engineers, Data Scientists

## 3.1. The Hybrid Model Philosophy

A single LLM is not optimal for a system this complex. We will adopt a hybrid, multi-model strategy:

1.  **A powerful, state-of-the-art model** for the central **Unified Reasoning Core**. This model will handle complex reasoning, strategic decision-making, and dynamic persona adoption. Performance is the priority here, not cost.
2.  **Smaller, specialized, fine-tuned models** for high-volume, repetitive tasks like data extraction and classification. These models are faster, cheaper, and can be optimized for near-perfect accuracy on a narrow task.

This approach is analogous to a human engineering firm: you have senior partners (the reasoning core) for strategic decisions and a team of junior engineers and drafters (the specialized models) for production work.

## 3.2. Model Selection

| Role | Recommended Model | Justification |
| --- | --- | --- |
| Unified Reasoning Core | gemini-2.5-flash (or equivalent state-of-the-art model like GPT-4.1-mini) | Superior Reasoning & Function Calling: Required for the complex logic of the cognitive workflow, risk assessment, and adopting different personas. <br> Large Context Window: Essential for processing large RAG-retrieved contexts from the knowledge base. <br> Cost/Performance Balance: Provides top-tier performance at a more efficient cost than the largest flagship models. |
| Specialized Extraction | Fine-tuned Llama-3-8B or Mixtral-8x7B (Self-hosted) | High Accuracy on Narrow Tasks: Fine-tuning allows these models to achieve >99% accuracy on specific extraction tasks (e.g., pulling data from a DBR). <br> Cost-Effective & Fast: Significantly cheaper and faster to run for high-volume, repetitive API calls. <br> Data Privacy: Self-hosting these models ensures that sensitive project data never leaves the company's secure environment. |
| Knowledge Embedding | text-embedding-3-large (or similar high-performance embedding model) | High-Dimensional Embeddings: Crucial for the RAG system to find nuanced and semantically relevant information in the Vector Database. The quality of the RAG output is directly tied to the quality of the embeddings. |

## 3.3. The Fine-Tuning Strategy

Fine-tuning the specialized models is the key to achieving world-class accuracy and efficiency. This process will be automated by the **Continuous Learning Loop (CLL)**.

### 3.3.1. Data Preparation

The CLL automatically generates a high-quality training dataset. The Training Dataset table in Supabase will store records in the following format:

{

"input\_context": "Text snippet from the source document...",

"instruction": "Extract the Safe Bearing Capacity value.",

"expected\_output": { "sbc\_kn\_m2": 150 }

}

This dataset is built from every human correction and every validated AI output, creating a perfect, ever-growing source of training data.

### 3.3.2. The Fine-Tuning Process (Automated Weekly)

An automated script will run weekly:

1.  **Export Data:** Export the latest records from the Training Dataset table.
2.  **Select Model:** Start with the latest self-hosted Llama-3-8B checkpoint.
3.  **Fine-Tuning with LoRA:** Use **LoRA (Low-Rank Adaptation)** to fine-tune the model. LoRA is highly efficient, allowing us to update the model's knowledge without retraining the entire network. This saves significant time and computational cost.
4.  **Evaluation:** The newly fine-tuned model is evaluated against a "golden" benchmark dataset (a set of hand-verified, complex extraction tasks). The model is only promoted to production if its accuracy improves by a statistically significant margin.
5.  **Deploy:** The new model checkpoint is deployed, replacing the previous week's version.

## 3.4. Domain Knowledge Preparation

This is the process of preparing the company's existing knowledge for ingestion into the **Enterprise Knowledge Base (EKB)**.

### The ETL (Extract, Transform, Load) Pipeline:

An n8n workflow will be created to process all existing documents (manuals, QAP, checklists, past project files):

1.  **Extract:** Use tools like unstructured.io to extract raw text and tables from various file formats (PDF, DOCX, DWG).
2.  **Transform (Chunking & Metadata):** This is the most critical step.
    *   **Chunking:** The raw text is broken down into smaller, semantically meaningful chunks (e.g., paragraphs, sections of a design code). A chunk should be a self-contained piece of information.
    *   **Metadata Enrichment:** Each chunk is tagged with rich metadata. This is vital for accurate retrieval.
3.  **Example Chunk with Metadata:**

{

"text": "The minimum grade of concrete for reinforced concrete shall be M20. For structures located in coastal areas, the minimum grade shall be M30.",

"metadata": {

"source\_document": "IS\_456\_2000.pdf",

"document\_type": "DESIGN\_CODE",

"discipline": "CIVIL",

"section": "Clause 8.2.1 - Concrete Grade",

"project\_context": "GENERAL"

}

}

1.  **Load:**
    *   The text chunk is passed to the embedding model (text-embedding-3-large) to create a vector.
    *   The vector, along with the text and its rich metadata, is loaded into the **Vector Database**.

This meticulous preparation ensures that when the RAG agent queries the EKB, it can retrieve highly relevant, context-rich information, enabling the reasoning core to make expert-level decisions.