# Sprint 2: Quick Start Guide
## Get Started with the Knowledge Base in 5 Minutes

---

## Prerequisites

✅ Sprint 1 completed and working
✅ Supabase account configured
✅ OpenRouter API key set

---

## Step 1: Update Database (2 minutes)

```bash
# 1. Open Supabase SQL Editor
# 2. Copy contents of init_sprint2.sql
# 3. Click "Run"
```

**Verify**:
```sql
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('documents', 'knowledge_chunks');
```

Expected: 2 rows returned

---

## Step 2: Install Dependencies (1 minute)

```bash
cd backend
pip install PyPDF2>=3.0.0
```

---

## Step 3: Test Sprint 2 (2 minutes)

```bash
python test_sprint2.py
```

**Expected Output**:
```
TEST 1: Configuration Check          ✅ PASSED
TEST 2: Document Processor            ✅ PASSED
TEST 3: Text Chunker                  ✅ PASSED
TEST 4: Embedding Service             ✅ PASSED
TEST 5: ETL Pipeline                  ✅ PASSED (or ⚠ SKIPPED if no DB)
TEST 6: Vector Search                 ✅ PASSED (or ⚠ SKIPPED if no DB)
```

---

## Step-4 : StartDocumentIngestion

### Option A: Use Python Script

Create `ingest_example.py`:

```python
from app.etl.pipeline import ingest_design_code

# Ingest a design code PDF
result = ingest_design_code(
    file_path="/path/to/your/design_code.pdf",
    code_name="IS 456:2000",  # Or your code name
    discipline="CIVIL"
)

print(f"✅ Ingested: {result['document_id']}")
print(f"📊 Created {result['chunks_created']} chunks")
```

Run it:
```bash
python ingest_example.py
```

### Option B: Use Interactive Python

```bash
python
```

```python
from app.etl.pipeline import ETLPipeline

pipeline = ETLPipeline()
result = pipeline.ingest_document(
    file_path="/path/to/document.pdf",
    document_type="DESIGN_CODE",
    discipline="CIVIL"
)

print(result)
```

---

## Step 5: Search Your Knowledge Base

```python
from app.nodes.retrieval import search_knowledge_base

results = search_knowledge_base(
    query="minimum concrete grade for coastal areas",
    top_k=5,
    discipline="CIVIL"
)

for i, chunk in enumerate(results, 1):
    print(f"\n{i}. {chunk['metadata']['source_document_name']}")
    print(f"   Similarity: {chunk['similarity']:.3f}")
    print(f"   {chunk['chunk_text'][:200]}...")
```

---

## Common Commands

### Ingest Single Document
```python
from app.etl.pipeline import ingest_design_code

ingest_design_code("IS_456.pdf", "IS 456:2000", "CIVIL")
```

### Ingest Directory
```python
from app.etl.pipeline import ETLPipeline

ETLPipeline().ingest_directory(
    "/path/to/documents",
    document_type="DESIGN_CODE",
    discipline="CIVIL",
    file_pattern="*.pdf"
)
```

### Search Knowledge Base
```python
from app.nodes.retrieval import search_knowledge_base

search_knowledge_base("your query here", top_k=5)
```

### Check Statistics
```sql
-- In Supabase SQL Editor
SELECT * FROM get_document_stats();
```

---

## Troubleshooting

### "Table does not exist"
→ Run `init_sprint2.sql` in Supabase SQL Editor

### "PyPDF2 not found"
→ Run `pip install PyPDF2>=3.0.0`

### "OPENROUTER_API_KEY not found"
→ Add to `.env`: `OPENROUTER_API_KEY=sk-or-v1-your-key`

### "No results found"
→ Ingest some documents first using ETL pipeline

---

## What's in the Box

Sprint 2 gives you:

📄 **Document Processing**: PDF, TXT, Markdown
🔪 **Smart Chunking**: Semantic boundaries, not arbitrary splits
🧠 **Vector Embeddings**: 1536-dimensional vectors (OpenRouter)
🔍 **Hybrid Search**: Semantic + metadata filtering
⚡ **Fast Retrieval**: <500ms vector search
💰 **Cost-Effective**: ~$0.13 per 1M tokens

---

## Next Steps

1. **Ingest your documents** using the ETL pipeline
2. **Test retrieval** with engineering queries
3. **Check the full guide**: [SPRINT2_README.md](SPRINT2_README.md)
4. **Wait for Sprint 3**: Conversational UI

---

## Quick Reference

| Task | Command |
|------|---------|
| Test Sprint 2 | `python test_sprint2.py` |
| Ingest PDF | `ingest_design_code("file.pdf", "Name", "CIVIL")` |
| Search | `search_knowledge_base("query", top_k=5)` |
| DB Stats | `SELECT * FROM get_document_stats();` |

---

**Ready to use Sprint 2!** 🚀

For detailed documentation, see [SPRINT2_README.md](SPRINT2_README.md).
