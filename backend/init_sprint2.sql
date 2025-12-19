-- CSA AIaaS Platform - Sprint 2 Database Schema
-- Sprint 2: The Memory Implantation (ETL & Vector DB)
--
-- This script creates the knowledge base tables for vector storage and retrieval.
-- Execute this script AFTER init.sql in your Supabase SQL Editor.
--
-- Prerequisites:
-- - init.sql must be executed first
-- - pgvector extension must be enabled (already done in init.sql)

-- =============================================================================
-- DOCUMENTS TABLE
-- =============================================================================
-- Stores metadata about source documents ingested into the knowledge base
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    file_path TEXT,
    document_type VARCHAR(100) NOT NULL,  -- 'DESIGN_CODE', 'PROJECT_FILE', 'COMPANY_MANUAL', 'LESSON_LEARNED'
    discipline VARCHAR(50),  -- 'CIVIL', 'STRUCTURAL', 'ARCHITECTURAL', 'GENERAL'
    file_format VARCHAR(20),  -- 'PDF', 'DOCX', 'DWG', 'TXT'
    file_size_bytes BIGINT,
    page_count INTEGER,
    author VARCHAR(255),
    version VARCHAR(50),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,  -- NULL for non-project-specific documents
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_processed TIMESTAMP WITH TIME ZONE,
    processing_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    chunk_count INTEGER DEFAULT 0,  -- Number of chunks created from this document
    metadata JSONB DEFAULT '{}'::jsonb,  -- Additional document metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_discipline ON documents(discipline);
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date);

-- Add trigger to update updated_at timestamp
-- Drop trigger if it exists (for idempotent execution)
DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- KNOWLEDGE_CHUNKS TABLE
-- =============================================================================
-- Stores text chunks with vector embeddings for semantic search
-- This is the core of the Enterprise Knowledge Base (EKB)
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Text content
    chunk_text TEXT NOT NULL,  -- The actual text snippet (self-contained information)

    -- Vector embedding (1536 dimensions for text-embedding-3-large model)
    -- Alternative: 3072 for text-embedding-3-large high-dim, 1024 for ada-002
    embedding VECTOR(1536),

    -- Source document reference
    source_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,

    -- Rich metadata for hybrid searching and filtering
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Expected metadata structure:
    -- {
    --   "source_document_name": "IS_456_2000.pdf",
    --   "document_type": "DESIGN_CODE",
    --   "discipline": "CIVIL",
    --   "deliverable_context": "CIVIL_FOUNDATION_ISOLATED",
    --   "project_id": "uuid-of-project-abc",
    --   "author": "John Doe",
    --   "section": "Clause 8.2.1 - Concrete Grade",
    --   "project_context": "GENERAL",
    --   "tags": ["reinforced_concrete", "coastal_area", "M30_concrete"],
    --   "page_number": 45,
    --   "chunk_sequence": 3,
    --   "confidence_score": 0.95
    -- }

    -- Chunk metadata
    chunk_index INTEGER,  -- Position in the source document
    chunk_length INTEGER,  -- Length of chunk in characters

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- VECTOR INDEXES FOR FAST SIMILARITY SEARCH
-- =============================================================================
-- IVFFlat Index (good for ~100K-1M vectors)
-- Uses Inverted File with Flat (IVF-Flat) algorithm for approximate nearest neighbor search
-- The 'lists' parameter controls the number of clusters (100 is good for 10K-100K vectors)
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_ivfflat
ON knowledge_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Alternative: HNSW Index (better for millions of vectors, higher memory usage)
-- Uncomment below if you need faster search with larger dataset:
-- CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_hnsw
-- ON knowledge_chunks
-- USING hnsw (embedding vector_cosine_ops);

-- =============================================================================
-- METADATA INDEXES FOR HYBRID SEARCH
-- =============================================================================
-- These indexes enable fast filtering by metadata fields combined with vector search
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_metadata_document_type
ON knowledge_chunks USING GIN ((metadata->'document_type'));

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_metadata_discipline
ON knowledge_chunks USING GIN ((metadata->'discipline'));

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_metadata_tags
ON knowledge_chunks USING GIN ((metadata->'tags'));

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source_document_id
ON knowledge_chunks(source_document_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_created_at
ON knowledge_chunks(created_at);


-- =============================================================================
-- VECTOR SEARCH HELPER FUNCTIONS
-- =============================================================================

-- Function to search for similar chunks with metadata filtering
-- Usage: SELECT * FROM search_knowledge_chunks('[0.1, 0.2, ...]'::vector, 5, '{"document_type": "DESIGN_CODE"}');
CREATE OR REPLACE FUNCTION search_knowledge_chunks(
    query_embedding VECTOR(1536),
    match_limit INT DEFAULT 10,
    filter_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS TABLE (
    id UUID,
    chunk_text TEXT,
    similarity FLOAT,
    metadata JSONB,
    source_document_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        kc.id,
        kc.chunk_text,
        1 - (kc.embedding <=> query_embedding) AS similarity,
        kc.metadata,
        kc.source_document_id
    FROM knowledge_chunks kc
    WHERE
        -- Apply metadata filters if provided
        (filter_metadata = '{}'::jsonb OR kc.metadata @> filter_metadata)
    ORDER BY kc.embedding <=> query_embedding
    LIMIT match_limit;
END;
$$ LANGUAGE plpgsql;


-- Function to get document statistics
CREATE OR REPLACE FUNCTION get_document_stats()
RETURNS TABLE (
    total_documents BIGINT,
    total_chunks BIGINT,
    avg_chunks_per_document NUMERIC,
    documents_by_type JSONB,
    documents_by_discipline JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM documents) AS total_documents,
        (SELECT COUNT(*) FROM knowledge_chunks) AS total_chunks,
        (SELECT ROUND(AVG(chunk_count), 2) FROM documents WHERE chunk_count > 0) AS avg_chunks_per_document,
        (SELECT jsonb_object_agg(document_type, count)
         FROM (SELECT document_type, COUNT(*) as count FROM documents GROUP BY document_type) t
        ) AS documents_by_type,
        (SELECT jsonb_object_agg(discipline, count)
         FROM (SELECT discipline, COUNT(*) as count FROM documents GROUP BY discipline) t
        ) AS documents_by_discipline;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- SAMPLE DATA FOR TESTING (Optional)
-- =============================================================================
-- Uncomment to insert sample documents for testing

-- INSERT INTO documents (name, document_type, discipline, file_format, author, metadata) VALUES
-- ('IS 456:2000 - Plain and Reinforced Concrete', 'DESIGN_CODE', 'CIVIL', 'PDF', 'Bureau of Indian Standards',
--  '{"standard": "IS 456", "year": 2000, "revision": "Fourth Revision"}'::jsonb),
-- ('IS 800:2007 - General Construction in Steel', 'DESIGN_CODE', 'STRUCTURAL', 'PDF', 'Bureau of Indian Standards',
--  '{"standard": "IS 800", "year": 2007, "revision": "Third Revision"}'::jsonb),
-- ('SES Quality Assurance Plan', 'COMPANY_MANUAL', 'GENERAL', 'PDF', 'Shiva Engineering Services',
--  '{"manual_type": "QAP", "version": "2.1"}'::jsonb);


-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these queries after executing the script to verify setup:

-- Check if all Sprint 2 tables exist:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public' AND table_name IN ('documents', 'knowledge_chunks')
-- ORDER BY table_name;

-- Check if pgvector extension is enabled and indexes exist:
-- SELECT indexname, indexdef FROM pg_indexes
-- WHERE tablename = 'knowledge_chunks'
-- ORDER BY indexname;

-- Check vector column:
-- SELECT column_name, data_type, udt_name
-- FROM information_schema.columns
-- WHERE table_name = 'knowledge_chunks' AND column_name = 'embedding';

-- Get document statistics:
-- SELECT * FROM get_document_stats();

-- Test vector search function (with dummy embedding):
-- SELECT * FROM search_knowledge_chunks(
--     array_fill(0.1, ARRAY[1536])::vector,
--     5,
--     '{"document_type": "DESIGN_CODE"}'::jsonb
-- );


-- =============================================================================
-- NOTES
-- =============================================================================
-- 1. Vector Dimensions: Using 1536 dimensions for OpenAI text-embedding-3-large
--    - For text-embedding-3-small: Use VECTOR(512)
--    - For text-embedding-ada-002: Use VECTOR(1024)
--    - For high-dimensional embeddings: Use VECTOR(3072)
--
-- 2. Distance Metrics:
--    - <=>  : Cosine distance (1 - cosine similarity) - RECOMMENDED for semantic search
--    - <->  : Euclidean distance (L2)
--    - <#>  : Inner product (dot product)
--
-- 3. Index Types:
--    - IVFFlat: Good for 10K-1M vectors, lower memory usage
--    - HNSW: Better for >1M vectors, faster queries, higher memory usage
--
-- 4. Metadata Filtering:
--    - Use JSONB operators for flexible filtering
--    - @> : Contains (e.g., metadata @> '{"discipline": "CIVIL"}')
--    - ? : Key exists (e.g., metadata ? 'tags')
--    - ?& : All keys exist
--    - ?| : Any key exists
--
-- 5. Performance Tuning:
--    - Increase 'lists' parameter for larger datasets (e.g., 200 for 500K vectors)
--    - Use HNSW for production with millions of vectors
--    - Create composite indexes for common filter combinations
