"""
CSA AIaaS Platform - ETL Pipeline
Sprint 2: The Memory Implantation

This module orchestrates the complete ETL (Extract, Transform, Load) pipeline
for ingesting engineering documents into the knowledge base.

Pipeline Steps:
1. Extract: Extract text from documents (PDF, TXT, DOCX)
2. Transform: Chunk text semantically and enrich with metadata
3. Load: Generate embeddings and store in Supabase vector database
"""

from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import uuid

from app.etl.document_processor import DocumentProcessor
from app.utils.text_chunker import TextChunker, TextChunk, chunk_design_code, chunk_company_manual
from app.services.embedding_service import EmbeddingService
from app.core.database import get_db


class ETLPipeline:
    """
    Complete ETL pipeline for document ingestion into knowledge base.

    Handles the full workflow:
    - Document extraction
    - Semantic chunking
    - Metadata enrichment
    - Embedding generation
    - Database storage
    """

    def __init__(
        self,
        embedding_model: str = "text-embedding-3-large",
        chunk_size: int = 400,
        batch_size: int = 100
    ):
        """
        Initialize the ETL pipeline.

        Args:
            embedding_model: Model to use for embeddings
            chunk_size: Target size for text chunks (in words)
            batch_size: Batch size for embedding generation
        """
        self.document_processor = DocumentProcessor()
        self.text_chunker = TextChunker(target_chunk_size=chunk_size)
        self.embedding_service = EmbeddingService(model=embedding_model, batch_size=batch_size)
        self.db = get_db()

        self.stats = {
            'documents_processed': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'db_inserts': 0,
            'errors': []
        }

    def ingest_document(
        self,
        file_path: str,
        document_type: str = "GENERAL",
        discipline: str = "GENERAL",
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Ingest a single document through the complete ETL pipeline.

        Args:
            file_path: Path to the document file
            document_type: Type of document (e.g., "DESIGN_CODE", "COMPANY_MANUAL")
            discipline: Engineering discipline (e.g., "CIVIL", "STRUCTURAL")
            author: Document author
            tags: List of tags for categorization
            custom_metadata: Additional metadata to attach

        Returns:
            Dictionary with ingestion results and statistics
        """
        print(f"\n{'='*80}")
        print(f"Ingesting document: {Path(file_path).name}")
        print(f"{'='*80}")

        result = {
            'success': False,
            'document_id': None,
            'chunks_created': 0,
            'error': None
        }

        try:
            # Step 1: Extract text from document
            print("Step 1: Extracting text...")
            extraction_result = self.document_processor.extract_text(file_path)

            if not extraction_result['success']:
                result['error'] = f"Extraction failed: {extraction_result['error']}"
                self.stats['errors'].append(result['error'])
                return result

            extracted_text = extraction_result['text']
            file_metadata = extraction_result['metadata']
            print(f"  ✓ Extracted {len(extracted_text)} characters from {file_metadata.get('page_count', '?')} pages")

            # Step 2: Create document record in database
            print("Step 2: Creating document record...")
            document_id = self._create_document_record(
                file_metadata=file_metadata,
                document_type=document_type,
                discipline=discipline,
                author=author,
                custom_metadata=custom_metadata or {}
            )
            result['document_id'] = document_id
            print(f"  ✓ Document record created: {document_id}")

            # Step 3: Chunk the text
            print("Step 3: Chunking text semantically...")
            base_metadata = {
                "source_document_name": file_metadata['file_name'],
                "document_type": document_type,
                "discipline": discipline,
                "author": author,
                "tags": tags or [],
                "project_context": "GENERAL"
            }

            if custom_metadata:
                base_metadata.update(custom_metadata)

            chunks = self.text_chunker.chunk_text(extracted_text, base_metadata)
            print(f"  ✓ Created {len(chunks)} chunks")

            # Step 4: Generate embeddings
            print("Step 4: Generating embeddings...")
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_service.generate_embeddings_batch(
                chunk_texts,
                show_progress=True
            )
            print(f"  ✓ Generated {len(embeddings)} embeddings")

            # Step 5: Store chunks in database
            print("Step 5: Storing chunks in database...")
            stored_count = self._store_chunks(
                chunks=chunks,
                embeddings=embeddings,
                document_id=document_id
            )
            print(f"  ✓ Stored {stored_count} chunks in database")

            # Step 6: Update document record with chunk count
            self._update_document_chunk_count(document_id, stored_count)

            # Update stats
            self.stats['documents_processed'] += 1
            self.stats['chunks_created'] += len(chunks)
            self.stats['embeddings_generated'] += len(embeddings)
            self.stats['db_inserts'] += stored_count

            result['success'] = True
            result['chunks_created'] = stored_count

            print(f"\n✅ Document ingestion complete!")
            print(f"   Document ID: {document_id}")
            print(f"   Chunks created: {stored_count}")

            return result

        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            result['error'] = error_msg
            self.stats['errors'].append(error_msg)
            print(f"\n❌ Error: {error_msg}")
            return result

    def ingest_directory(
        self,
        directory_path: str,
        document_type: str = "GENERAL",
        discipline: str = "GENERAL",
        recursive: bool = True,
        file_pattern: Optional[str] = None
    ) -> Dict:
        """
        Ingest all supported documents from a directory.

        Args:
            directory_path: Path to directory containing documents
            document_type: Default document type for all files
            discipline: Default discipline for all files
            recursive: Whether to search subdirectories
            file_pattern: Optional glob pattern to filter files

        Returns:
            Dictionary with batch ingestion results
        """
        print(f"\n{'='*80}")
        print(f"Batch Ingestion from: {directory_path}")
        print(f"{'='*80}")

        directory = Path(directory_path)
        if not directory.exists():
            return {
                'success': False,
                'error': f"Directory not found: {directory_path}",
                'documents_processed': 0
            }

        # Find all supported files
        files_to_process = []
        if file_pattern:
            if recursive:
                files_to_process = list(directory.rglob(file_pattern))
            else:
                files_to_process = list(directory.glob(file_pattern))
        else:
            for ext in self.document_processor.SUPPORTED_FORMATS:
                pattern = f"*{ext}"
                if recursive:
                    files_to_process.extend(directory.rglob(pattern))
                else:
                    files_to_process.extend(directory.glob(pattern))

        print(f"Found {len(files_to_process)} documents to process\n")

        # Process each file
        results = []
        for file_path in files_to_process:
            result = self.ingest_document(
                file_path=str(file_path),
                document_type=document_type,
                discipline=discipline
            )
            results.append(result)

        # Summarize results
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful

        print(f"\n{'='*80}")
        print(f"Batch Ingestion Complete")
        print(f"{'='*80}")
        print(f"Total documents: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total chunks created: {self.stats['chunks_created']}")

        return {
            'success': True,
            'documents_processed': len(results),
            'successful': successful,
            'failed': failed,
            'results': results,
            'stats': self.stats
        }

    def _create_document_record(
        self,
        file_metadata: Dict,
        document_type: str,
        discipline: str,
        author: Optional[str],
        custom_metadata: Dict
    ) -> str:
        """
        Create a document record in the database.

        Args:
            file_metadata: Metadata extracted from file
            document_type: Type of document
            discipline: Engineering discipline
            author: Document author
            custom_metadata: Additional metadata

        Returns:
            UUID of created document record
        """
        document_id = str(uuid.uuid4())

        metadata = {
            **file_metadata,
            **custom_metadata
        }

        try:
            self.db.table("documents").insert({
                "id": document_id,
                "name": file_metadata.get('file_name', 'Unknown'),
                "file_path": file_metadata.get('file_path'),
                "document_type": document_type,
                "discipline": discipline,
                "file_format": file_metadata.get('file_format'),
                "file_size_bytes": file_metadata.get('file_size_bytes'),
                "page_count": file_metadata.get('page_count'),
                "author": author,
                "processing_status": "processing",
                "metadata": metadata
            }).execute()

            return document_id
        except Exception as e:
            print(f"Warning: Failed to create document record: {e}")
            # Return generated UUID anyway so pipeline can continue
            return document_id

    def _store_chunks(
        self,
        chunks: List[TextChunk],
        embeddings: List[List[float]],
        document_id: str
    ) -> int:
        """
        Store chunks and embeddings in the database.

        Args:
            chunks: List of text chunks
            embeddings: List of embedding vectors
            document_id: UUID of source document

        Returns:
            Number of chunks successfully stored
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunk count ({len(chunks)}) != embedding count ({len(embeddings)})")

        stored_count = 0

        for chunk, embedding in zip(chunks, embeddings):
            try:
                self.db.table("knowledge_chunks").insert({
                    "chunk_text": chunk.text,
                    "embedding": embedding,
                    "source_document_id": document_id,
                    "metadata": chunk.metadata,
                    "chunk_index": chunk.index,
                    "chunk_length": chunk.char_length
                }).execute()

                stored_count += 1
            except Exception as e:
                print(f"Warning: Failed to store chunk {chunk.index}: {e}")
                continue

        return stored_count

    def _update_document_chunk_count(self, document_id: str, chunk_count: int):
        """
        Update the document record with chunk count and completion status.

        Args:
            document_id: UUID of document
            chunk_count: Number of chunks created
        """
        try:
            self.db.table("documents").update({
                "chunk_count": chunk_count,
                "processing_status": "completed",
                "last_processed": datetime.now().isoformat()
            }).eq("id", document_id).execute()
        except Exception as e:
            print(f"Warning: Failed to update document record: {e}")

    def get_stats(self) -> Dict:
        """
        Get pipeline statistics.

        Returns:
            Dictionary with processing statistics
        """
        return self.stats


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def ingest_design_code(
    file_path: str,
    code_name: str,
    discipline: str = "CIVIL"
) -> Dict:
    """
    Convenience function to ingest a design code document.

    Args:
        file_path: Path to the design code PDF
        code_name: Name of the code (e.g., "IS 456:2000")
        discipline: Engineering discipline

    Returns:
        Ingestion result dictionary
    """
    pipeline = ETLPipeline()
    return pipeline.ingest_document(
        file_path=file_path,
        document_type="DESIGN_CODE",
        discipline=discipline,
        tags=["design_code", "standard"],
        custom_metadata={"code_name": code_name}
    )


def ingest_company_manual(
    file_path: str,
    manual_name: str,
    manual_type: str = "QAP"
) -> Dict:
    """
    Convenience function to ingest a company manual.

    Args:
        file_path: Path to the manual PDF
        manual_name: Name of the manual
        manual_type: Type of manual (e.g., "QAP", "CHECKLIST")

    Returns:
        Ingestion result dictionary
    """
    pipeline = ETLPipeline()
    return pipeline.ingest_document(
        file_path=file_path,
        document_type="COMPANY_MANUAL",
        discipline="GENERAL",
        tags=["manual", manual_type.lower()],
        custom_metadata={"manual_type": manual_type, "manual_name": manual_name}
    )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    print("ETL Pipeline Example")
    print("=" * 80)

    # Example 1: Ingest a single design code
    # result = ingest_design_code(
    #     file_path="/path/to/IS_456_2000.pdf",
    #     code_name="IS 456:2000",
    #     discipline="CIVIL"
    # )
    # print(f"Result: {result}")

    # Example 2: Ingest a company manual
    # result = ingest_company_manual(
    #     file_path="/path/to/QAP_Manual.pdf",
    #     manual_name="Quality Assurance Plan",
    #     manual_type="QAP"
    # )
    # print(f"Result: {result}")

    # Example 3: Batch ingest from directory
    # pipeline = ETLPipeline()
    # result = pipeline.ingest_directory(
    #     directory_path="/path/to/documents",
    #     document_type="DESIGN_CODE",
    #     discipline="CIVIL",
    #     recursive=True,
    #     file_pattern="*.pdf"
    # )
    # print(f"Batch result: {result}")

    print("\n" + "=" * 80)
    print("To use this pipeline:")
    print("1. Uncomment the examples above")
    print("2. Update the file/directory paths")
    print("3. Ensure Supabase is configured and init_sprint2.sql is executed")
    print("4. Run: python -m app.etl.pipeline")
