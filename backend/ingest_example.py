#!/usr/bin/env python3
"""
CSA AIaaS Platform - Document Ingestion Example
Sprint 2: The Memory Implantation

This script demonstrates how to ingest engineering documents into the knowledge base.

Usage:
    python ingest_example.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.etl.pipeline import (
    ETLPipeline,
    ingest_design_code,
    ingest_company_manual
)


def example_1_ingest_single_design_code():
    """
    Example 1: Ingest a single design code PDF.

    This is the most common use case - ingesting design standards
    like IS 456, IS 800, ACI, Eurocode, etc.
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Ingest Single Design Code")
    print("="*80)

    # Replace with your actual file path
    file_path = "/path/to/IS_456_2000.pdf"

    print(f"\nIngesting: {file_path}")
    print("This will:")
    print("  1. Extract text from PDF")
    print("  2. Chunk into semantic sections")
    print("  3. Generate vector embeddings")
    print("  4. Store in database")

    # Check if file exists
    if not Path(file_path).exists():
        print(f"\n⚠ File not found: {file_path}")
        print("Please update the file_path variable with your actual PDF location")
        return

    # Ingest the document
    result = ingest_design_code(
        file_path=file_path,
        code_name="IS 456:2000",  # Name of the design code
        discipline="CIVIL"         # CIVIL, STRUCTURAL, or ARCHITECTURAL
    )

    if result['success']:
        print(f"\n✅ SUCCESS!")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Chunks created: {result['chunks_created']}")
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")


def example_2_ingest_company_manual():
    """
    Example 2: Ingest a company manual or QAP document.

    Use this for internal company documents like:
    - Quality Assurance Plans
    - Design Checklists
    - Standard Operating Procedures
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Ingest Company Manual")
    print("="*80)

    file_path = "/path/to/QAP_Manual.pdf"

    print(f"\nIngesting: {file_path}")

    if not Path(file_path).exists():
        print(f"\n⚠ File not found: {file_path}")
        print("Please update the file_path variable with your actual PDF location")
        return

    result = ingest_company_manual(
        file_path=file_path,
        manual_name="Quality Assurance Plan",
        manual_type="QAP"  # QAP, CHECKLIST, PROCEDURE, etc.
    )

    if result['success']:
        print(f"\n✅ SUCCESS!")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Chunks created: {result['chunks_created']}")
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")


def example_3_batch_ingest_directory():
    """
    Example 3: Batch ingest all PDFs from a directory.

    Use this when you have a folder full of design codes or manuals
    and want to ingest them all at once.
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Batch Ingest from Directory")
    print("="*80)

    directory_path = "/path/to/design_codes"

    print(f"\nIngesting all PDFs from: {directory_path}")
    print("This will process all PDF files in the directory and subdirectories")

    if not Path(directory_path).exists():
        print(f"\n⚠ Directory not found: {directory_path}")
        print("Please update the directory_path variable")
        return

    # Initialize pipeline
    pipeline = ETLPipeline()

    # Ingest all PDFs from directory
    result = pipeline.ingest_directory(
        directory_path=directory_path,
        document_type="DESIGN_CODE",  # Type for all documents in this folder
        discipline="CIVIL",            # Discipline for all documents
        recursive=True,                # Search subdirectories
        file_pattern="*.pdf"           # Only process PDF files
    )

    if result['success']:
        print(f"\n✅ BATCH INGESTION COMPLETE!")
        print(f"   Total documents processed: {result['documents_processed']}")
        print(f"   Successful: {result['successful']}")
        print(f"   Failed: {result['failed']}")
        print(f"   Total chunks created: {result['stats']['chunks_created']}")
    else:
        print(f"\n❌ BATCH INGESTION FAILED: {result.get('error', 'Unknown error')}")


def example_4_custom_ingestion():
    """
    Example 4: Custom ingestion with full control.

    Use this when you need fine-grained control over the ingestion
    process with custom metadata and tags.
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Custom Ingestion with Metadata")
    print("="*80)

    file_path = "/path/to/your_document.pdf"

    if not Path(file_path).exists():
        print(f"\n⚠ File not found: {file_path}")
        print("Please update the file_path variable")
        return

    # Initialize pipeline
    pipeline = ETLPipeline()

    # Ingest with custom metadata
    result = pipeline.ingest_document(
        file_path=file_path,
        document_type="DESIGN_CODE",  # DESIGN_CODE, COMPANY_MANUAL, PROJECT_FILE, etc.
        discipline="STRUCTURAL",       # CIVIL, STRUCTURAL, ARCHITECTURAL, GENERAL
        author="Bureau of Indian Standards",
        tags=["steel", "design", "IS_800", "structural_analysis"],  # Custom tags
        custom_metadata={
            "standard": "IS 800",
            "year": 2007,
            "revision": "Third Revision",
            "applicable_region": "India",
            "supersedes": "IS 800:1984"
        }
    )

    if result['success']:
        print(f"\n✅ SUCCESS!")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Chunks created: {result['chunks_created']}")
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")


def example_5_ingest_text_file():
    """
    Example 5: Ingest a plain text file.

    Use this for markdown files, text documents, or extracted text.
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: Ingest Plain Text File")
    print("="*80)

    # Create a sample text file for demonstration
    sample_file = Path("sample_design_notes.txt")
    sample_content = """
Design Notes - Foundation Design

Section 1: Soil Investigation
The soil investigation report indicates clayey soil with following properties:
- Safe Bearing Capacity (SBC): 150 kN/m²
- Soil Type: Medium clay
- Depth of foundation: 1.5m minimum

Section 2: Foundation Design Criteria
For coastal areas, following additional considerations apply:
- Minimum concrete grade: M30
- Increased cover: 75mm for durability
- Use of marine-grade cement recommended

Section 3: Design Loads
Column loads are as follows:
- Dead Load: 600 kN
- Live Load: 400 kN
- Total: 1000 kN

Section 4: Design Calculations
Foundation area required = Total Load / SBC
= 1000 / 150
= 6.67 m²

Provide 2.6m x 2.6m footing (Area = 6.76 m²)
    """.strip()

    sample_file.write_text(sample_content)
    print(f"\n✓ Created sample file: {sample_file}")

    # Initialize pipeline
    pipeline = ETLPipeline()

    # Ingest the text file
    result = pipeline.ingest_document(
        file_path=str(sample_file),
        document_type="DESIGN_CODE",
        discipline="CIVIL",
        author="Design Engineer",
        tags=["foundation", "coastal", "design_notes"],
        custom_metadata={
            "project": "Sample Project",
            "location": "Coastal Area"
        }
    )

    if result['success']:
        print(f"\n✅ SUCCESS!")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Chunks created: {result['chunks_created']}")

        # Clean up sample file
        sample_file.unlink()
        print(f"\n✓ Cleaned up sample file")
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
        sample_file.unlink()


def main():
    """
    Main function - Run the examples.

    Uncomment the example you want to run.
    """
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║            CSA AIaaS Platform - Document Ingestion Examples              ║
║                    Sprint 2: The Memory Implantation                     ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

This script demonstrates various ways to ingest documents into the knowledge base.

BEFORE RUNNING:
1. Ensure Supabase is configured in .env
2. Run init_sprint2.sql in Supabase SQL Editor
3. Install dependencies: pip install -r requirements.txt
4. Update file paths in the examples below
    """)

    # Uncomment the example you want to run:

    # Example 1: Ingest a single design code (most common)
    # example_1_ingest_single_design_code()

    # Example 2: Ingest a company manual
    # example_2_ingest_company_manual()

    # Example 3: Batch ingest from directory
    # example_3_batch_ingest_directory()

    # Example 4: Custom ingestion with metadata
    # example_4_custom_ingestion()

    # Example 5: Ingest text file (this one works without setup!)
    example_5_ingest_text_file()

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("""
After ingesting documents, you can:

1. Search the knowledge base:
   python -c "from app.nodes.retrieval import search_knowledge_base; \\
              results = search_knowledge_base('your query here', top_k=5); \\
              print(results)"

2. Check database statistics:
   Run in Supabase SQL Editor:
   SELECT * FROM get_document_stats();

3. View all documents:
   SELECT id, name, document_type, discipline, chunk_count
   FROM documents
   ORDER BY created_at DESC;

4. View recent chunks:
   SELECT id, chunk_text, metadata->>'source_document_name' as source
   FROM knowledge_chunks
   ORDER BY created_at DESC
   LIMIT 10;

For more examples, see: SPRINT2_README.md
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
