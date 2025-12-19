#!/usr/bin/env python3
"""
CSA AIaaS Platform - Ingest All Documents
Sprint 2: The Memory Implantation

This script ingests ALL markdown documents from the documents folder
into the knowledge base.

Usage:
    python ingest_all_documents.py
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.etl.pipeline import ETLPipeline
from app.core.config import settings


def ingest_all_documents():
    """
    Ingest all markdown documents from the documents folder.
    """
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║          CSA AIaaS Platform - Batch Document Ingestion                   ║
║                Sprint 2: The Memory Implantation                         ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    # Check configuration
    print("Checking configuration...")
    if not settings.OPENROUTER_API_KEY:
        print("❌ ERROR: OPENROUTER_API_KEY not found in environment")
        print("   Please add it to your .env file")
        return

    if not (settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY):
        print("⚠ WARNING: Supabase not configured")
        print("   Documents will be processed but not stored in database")
        proceed = input("   Continue anyway? (y/n): ")
        if proceed.lower() != 'y':
            return

    print("✓ Configuration OK\n")

    # Get documents directory path
    backend_dir = Path(__file__).parent
    project_dir = backend_dir.parent
    documents_dir = project_dir / "documents"

    if not documents_dir.exists():
        print(f"❌ ERROR: Documents directory not found: {documents_dir}")
        return

    # Find all markdown files
    markdown_files = list(documents_dir.glob("*.md"))

    print(f"Found {len(markdown_files)} markdown documents in: {documents_dir}")
    print(f"\nDocuments to be ingested:")
    for i, file in enumerate(markdown_files[:10], 1):
        print(f"  {i}. {file.name}")
    if len(markdown_files) > 10:
        print(f"  ... and {len(markdown_files) - 10} more")

    # Confirm before proceeding
    print(f"\n{'='*80}")
    print(f"This will ingest {len(markdown_files)} documents into the knowledge base.")
    print(f"Estimated time: ~{len(markdown_files) * 5} seconds ({len(markdown_files) * 5 // 60} minutes)")
    print(f"Estimated cost: ~${len(markdown_files) * 0.01:.2f} (with text-embedding-3-large)")
    print(f"{'='*80}")

    confirm = input("\nProceed with ingestion? (y/n): ")
    if confirm.lower() != 'y':
        print("Ingestion cancelled.")
        return

    # Initialize ETL pipeline
    print("\nInitializing ETL pipeline...")
    pipeline = ETLPipeline()

    # Track statistics
    stats = {
        'start_time': datetime.now(),
        'total_files': len(markdown_files),
        'successful': 0,
        'failed': 0,
        'total_chunks': 0,
        'errors': []
    }

    # Process each document
    print(f"\n{'='*80}")
    print("Starting batch ingestion...")
    print(f"{'='*80}\n")

    for i, file_path in enumerate(markdown_files, 1):
        print(f"[{i}/{len(markdown_files)}] Processing: {file_path.name}")

        # Determine document type and discipline based on filename
        file_name = file_path.name.lower()

        # Categorize documents
        if "implementation" in file_name or "guide" in file_name:
            doc_type = "IMPLEMENTATION_GUIDE"
            discipline = "GENERAL"
            tags = ["implementation", "guide", "technical_spec"]
        elif "csa" in file_name:
            doc_type = "CSA_SPECIFICATION"
            discipline = "CIVIL"
            tags = ["csa", "specification", "workflow"]
        elif "markdown" in file_name or "final" in file_name:
            doc_type = "ARCHITECTURE_SPEC"
            discipline = "GENERAL"
            tags = ["architecture", "design", "technical_spec"]
        else:
            doc_type = "TECHNICAL_DOCUMENT"
            discipline = "GENERAL"
            tags = ["technical", "documentation"]

        try:
            # Ingest the document
            result = pipeline.ingest_document(
                file_path=str(file_path),
                document_type=doc_type,
                discipline=discipline,
                author="CSA AIaaS Platform",
                tags=tags,
                custom_metadata={
                    "original_filename": file_path.name,
                    "source_directory": "documents",
                    "batch_ingestion": True,
                    "ingestion_date": datetime.now().isoformat()
                }
            )

            if result['success']:
                stats['successful'] += 1
                stats['total_chunks'] += result.get('chunks_created', 0)
                print(f"  ✓ SUCCESS - Created {result['chunks_created']} chunks")
            else:
                stats['failed'] += 1
                error_msg = result.get('error', 'Unknown error')
                stats['errors'].append({
                    'file': file_path.name,
                    'error': error_msg
                })
                print(f"  ✗ FAILED - {error_msg}")

        except Exception as e:
            stats['failed'] += 1
            stats['errors'].append({
                'file': file_path.name,
                'error': str(e)
            })
            print(f"  ✗ ERROR - {str(e)}")

        print()  # Blank line between files

    # Calculate final statistics
    stats['end_time'] = datetime.now()
    stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()

    # Print final summary
    print(f"\n{'='*80}")
    print("BATCH INGESTION COMPLETE")
    print(f"{'='*80}")
    print(f"\nResults:")
    print(f"  Total documents processed: {stats['total_files']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total chunks created: {stats['total_chunks']}")
    print(f"  Average chunks per document: {stats['total_chunks'] / stats['successful'] if stats['successful'] > 0 else 0:.1f}")
    print(f"\nTime:")
    print(f"  Duration: {stats['duration']:.1f} seconds ({stats['duration'] / 60:.1f} minutes)")
    print(f"  Average per document: {stats['duration'] / stats['total_files']:.1f} seconds")

    if stats['errors']:
        print(f"\nErrors ({len(stats['errors'])}):")
        for error in stats['errors'][:5]:
            print(f"  - {error['file']}: {error['error']}")
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more errors")

    # Save detailed report
    report_file = f"ingestion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_data = {
        **stats,
        'start_time': stats['start_time'].isoformat(),
        'end_time': stats['end_time'].isoformat()
    }

    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

    # Next steps
    print(f"\n{'='*80}")
    print("NEXT STEPS")
    print(f"{'='*80}")
    print("""
Your knowledge base is now populated! You can:

1. Check database statistics:
   In Supabase SQL Editor, run:
   SELECT * FROM get_document_stats();

2. Search the knowledge base:
   python -c "from app.nodes.retrieval import search_knowledge_base; \\
              results = search_knowledge_base('LangGraph workflow', top_k=5); \\
              print(f'Found {len(results)} results')"

3. View all documents:
   In Supabase SQL Editor:
   SELECT id, name, document_type, discipline, chunk_count
   FROM documents
   ORDER BY created_at DESC;

4. Test the retrieval node:
   python test_sprint2.py

5. Start using the AI with knowledge context:
   python main.py
   # Then make API calls to /api/v1/execute

For more information, see: SPRINT2_README.md
    """)


def main():
    try:
        ingest_all_documents()
    except KeyboardInterrupt:
        print("\n\n⚠ Ingestion interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
