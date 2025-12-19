#!/usr/bin/env python3
"""
CSA AIaaS Platform - Sprint 2 Testing Script
Sprint 2: The Memory Implantation

This script tests all Sprint 2 components:
- Document extraction (PDF, TXT)
- Text chunking
- Embedding generation
- ETL pipeline
- Vector similarity search
- Retrieval node

Usage:
    python test_sprint2.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.etl.document_processor import DocumentProcessor
from app.utils.text_chunker import TextChunker
from app.services.embedding_service import EmbeddingService
from app.etl.pipeline import ETLPipeline
from app.nodes.retrieval import search_knowledge_base
from app.core.config import settings


class Sprint2Tester:
    """
    Comprehensive tester for Sprint 2 functionality.
    """

    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }

    def run_all_tests(self):
        """Run all Sprint 2 tests."""
        print("\n" + "="*80)
        print("CSA AIaaS Platform - Sprint 2 Testing Suite")
        print("Sprint 2: The Memory Implantation")
        print("="*80)

        # Test 1: Configuration
        self.test_configuration()

        # Test 2: Document Processor
        self.test_document_processor()

        # Test 3: Text Chunker
        self.test_text_chunker()

        # Test 4: Embedding Service
        self.test_embedding_service()

        # Test 5: ETL Pipeline (requires test documents)
        self.test_etl_pipeline()

        # Test 6: Vector Search (requires data in database)
        self.test_vector_search()

        # Generate summary
        self.generate_summary()

        # Save results
        self.save_results()

    def test_configuration(self):
        """Test Sprint 2 configuration."""
        print("\n" + "-"*80)
        print("TEST 1: Configuration Check")
        print("-"*80)

        test_result = {
            'name': 'Configuration Check',
            'success': False,
            'details': {}
        }

        try:
            # Check required environment variables
            checks = {
                'OPENROUTER_API_KEY': settings.OPENROUTER_API_KEY is not None,
                'OPENROUTER_MODEL': settings.OPENROUTER_MODEL is not None,
            }

            print(f"OpenRouter API Key: {'✓ Set' if checks['OPENROUTER_API_KEY'] else '✗ Missing'}")
            print(f"OpenRouter Model: {settings.OPENROUTER_MODEL if checks['OPENROUTER_MODEL'] else '✗ Missing'}")

            # Supabase is optional
            has_supabase = settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY
            print(f"Supabase: {'✓ Configured' if has_supabase else '⚠ Not configured (optional)'}")

            test_result['success'] = all(checks.values())
            test_result['details'] = checks

            if test_result['success']:
                print("\n✅ Configuration test PASSED")
            else:
                print("\n❌ Configuration test FAILED")

        except Exception as e:
            print(f"\n❌ Configuration test ERROR: {e}")
            test_result['error'] = str(e)

        self.results['tests'].append(test_result)

    def test_document_processor(self):
        """Test document extraction."""
        print("\n" + "-"*80)
        print("TEST 2: Document Processor")
        print("-"*80)

        test_result = {
            'name': 'Document Processor',
            'success': False,
            'details': {}
        }

        try:
            processor = DocumentProcessor()

            # Create a test text file
            test_file = Path("test_document.txt")
            test_content = """
This is a test document for the CSA AIaaS Platform.

The minimum grade of concrete for reinforced concrete shall be M20.
For structures located in coastal areas, the minimum grade shall be M30
to ensure adequate durability against corrosive environments.

This is the second paragraph with different content.
            """.strip()

            test_file.write_text(test_content)

            # Extract text
            result = processor.extract_text(str(test_file))

            print(f"Extraction Status: {'✓ Success' if result['success'] else '✗ Failed'}")
            if result['success']:
                print(f"Extracted Characters: {len(result['text'])}")
                print(f"File Format: {result['metadata'].get('file_format', 'Unknown')}")
                test_result['success'] = True
                test_result['details'] = {
                    'chars_extracted': len(result['text']),
                    'metadata': result['metadata']
                }
            else:
                print(f"Error: {result['error']}")
                test_result['details']['error'] = result['error']

            # Cleanup
            test_file.unlink()

            if test_result['success']:
                print("\n✅ Document Processor test PASSED")
            else:
                print("\n❌ Document Processor test FAILED")

        except Exception as e:
            print(f"\n❌ Document Processor test ERROR: {e}")
            test_result['error'] = str(e)

        self.results['tests'].append(test_result)

    def test_text_chunker(self):
        """Test text chunking."""
        print("\n" + "-"*80)
        print("TEST 3: Text Chunker")
        print("-"*80)

        test_result = {
            'name': 'Text Chunker',
            'success': False,
            'details': {}
        }

        try:
            chunker = TextChunker(target_chunk_size=100, min_chunk_size=30, max_chunk_size=150)

            test_text = """
The minimum grade of concrete for reinforced concrete shall be M20.
For structures located in coastal areas, the minimum grade shall be M30.

Design Basis Report (DBR) is a critical document that establishes all engineering assumptions.
It must be reviewed and approved before detailed design begins.

The safe bearing capacity of soil must be determined through soil investigation.
Laboratory tests shall be conducted as per IS 1888 standards.
            """.strip()

            metadata = {
                "source_document_name": "Test Document",
                "document_type": "DESIGN_CODE",
                "discipline": "CIVIL"
            }

            chunks = chunker.chunk_text(test_text, metadata)

            print(f"Input Text Length: {len(test_text)} characters")
            print(f"Chunks Created: {len(chunks)}")

            for i, chunk in enumerate(chunks, 1):
                print(f"\nChunk {i}:")
                print(f"  Length: {chunk.char_length} characters")
                print(f"  Word Count: {chunk.metadata.get('word_count', 0)} words")
                print(f"  Preview: {chunk.text[:80]}...")

            test_result['success'] = len(chunks) > 0
            test_result['details'] = {
                'chunks_created': len(chunks),
                'avg_chunk_length': sum(c.char_length for c in chunks) / len(chunks) if chunks else 0
            }

            if test_result['success']:
                print("\n✅ Text Chunker test PASSED")
            else:
                print("\n❌ Text Chunker test FAILED")

        except Exception as e:
            print(f"\n❌ Text Chunker test ERROR: {e}")
            test_result['error'] = str(e)

        self.results['tests'].append(test_result)

    def test_embedding_service(self):
        """Test embedding generation."""
        print("\n" + "-"*80)
        print("TEST 4: Embedding Service")
        print("-"*80)

        test_result = {
            'name': 'Embedding Service',
            'success': False,
            'details': {}
        }

        try:
            if not settings.OPENROUTER_API_KEY:
                print("⚠ Skipping test - OPENROUTER_API_KEY not configured")
                test_result['skipped'] = True
                self.results['tests'].append(test_result)
                return

            service = EmbeddingService()
            print(f"Model: {service.model}")
            print(f"Dimensions: {service.dimensions}")

            test_text = "Design isolated footing for column load 500 kN with M25 concrete"

            print(f"\nGenerating embedding for: '{test_text}'")
            embedding = service.generate_embedding(test_text)

            print(f"Embedding Generated: ✓")
            print(f"Dimensions: {len(embedding)}")
            print(f"First 5 values: {embedding[:5]}")

            test_result['success'] = len(embedding) == service.dimensions
            test_result['details'] = {
                'model': service.model,
                'dimensions': len(embedding),
                'expected_dimensions': service.dimensions
            }

            if test_result['success']:
                print("\n✅ Embedding Service test PASSED")
            else:
                print(f"\n❌ Embedding Service test FAILED - Dimension mismatch")

        except Exception as e:
            print(f"\n❌ Embedding Service test ERROR: {e}")
            test_result['error'] = str(e)

        self.results['tests'].append(test_result)

    def test_etl_pipeline(self):
        """Test ETL pipeline."""
        print("\n" + "-"*80)
        print("TEST 5: ETL Pipeline")
        print("-"*80)

        test_result = {
            'name': 'ETL Pipeline',
            'success': False,
            'details': {}
        }

        try:
            if not settings.OPENROUTER_API_KEY:
                print("⚠ Skipping test - OPENROUTER_API_KEY not configured")
                test_result['skipped'] = True
                self.results['tests'].append(test_result)
                return

            if not (settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY):
                print("⚠ Skipping test - Supabase not configured")
                test_result['skipped'] = True
                self.results['tests'].append(test_result)
                return

            # Create test document
            test_file = Path("test_design_code.txt")
            test_content = """
Clause 8.2: Concrete Grade

The minimum grade of concrete for reinforced concrete shall be M20.

For structures exposed to severe environmental conditions:
- Coastal areas: M30 minimum
- Industrial atmosphere: M25 minimum
- Moderate conditions: M20 minimum

The concrete grade must be specified in the Design Basis Report.
            """.strip()

            test_file.write_text(test_content)

            # Run ETL pipeline
            pipeline = ETLPipeline()
            print("Starting document ingestion...")

            result = pipeline.ingest_document(
                file_path=str(test_file),
                document_type="DESIGN_CODE",
                discipline="CIVIL",
                author="Test Author",
                tags=["concrete", "grade", "test"]
            )

            print(f"\nIngestion Status: {'✓ Success' if result['success'] else '✗ Failed'}")
            if result['success']:
                print(f"Document ID: {result['document_id']}")
                print(f"Chunks Created: {result['chunks_created']}")
                test_result['success'] = True
                test_result['details'] = result
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                test_result['details']['error'] = result.get('error')

            # Cleanup
            test_file.unlink()

            if test_result['success']:
                print("\n✅ ETL Pipeline test PASSED")
            else:
                print("\n❌ ETL Pipeline test FAILED")

        except Exception as e:
            print(f"\n❌ ETL Pipeline test ERROR: {e}")
            test_result['error'] = str(e)

        self.results['tests'].append(test_result)

    def test_vector_search(self):
        """Test vector similarity search."""
        print("\n" + "-"*80)
        print("TEST 6: Vector Search & Retrieval")
        print("-"*80)

        test_result = {
            'name': 'Vector Search',
            'success': False,
            'details': {}
        }

        try:
            if not settings.OPENROUTER_API_KEY:
                print("⚠ Skipping test - OPENROUTER_API_KEY not configured")
                test_result['skipped'] = True
                self.results['tests'].append(test_result)
                return

            if not (settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY):
                print("⚠ Skipping test - Supabase not configured")
                test_result['skipped'] = True
                self.results['tests'].append(test_result)
                return

            query = "What is the minimum concrete grade for coastal areas?"
            print(f"Search Query: '{query}'")

            results = search_knowledge_base(
                query=query,
                top_k=3,
                discipline="CIVIL"
            )

            print(f"\nResults Found: {len(results)}")

            for i, chunk in enumerate(results, 1):
                similarity = chunk.get('similarity', 0)
                source = chunk.get('metadata', {}).get('source_document_name', 'Unknown')
                text_preview = chunk.get('chunk_text', '')[:100]

                print(f"\nResult {i}:")
                print(f"  Source: {source}")
                print(f"  Similarity: {similarity:.3f}")
                print(f"  Text: {text_preview}...")

            test_result['success'] = True  # Success even if no results (empty DB is ok)
            test_result['details'] = {
                'query': query,
                'results_count': len(results)
            }

            if len(results) > 0:
                print("\n✅ Vector Search test PASSED (results found)")
            else:
                print("\n✅ Vector Search test PASSED (no results - database may be empty)")

        except Exception as e:
            print(f"\n❌ Vector Search test ERROR: {e}")
            test_result['error'] = str(e)

        self.results['tests'].append(test_result)

    def generate_summary(self):
        """Generate test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        total_tests = len(self.results['tests'])
        passed = sum(1 for t in self.results['tests'] if t.get('success', False))
        failed = sum(1 for t in self.results['tests'] if not t.get('success', False) and not t.get('skipped', False))
        skipped = sum(1 for t in self.results['tests'] if t.get('skipped', False))

        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")

        self.results['summary'] = {
            'total': total_tests,
            'passed': passed,
            'failed': failed,
            'skipped': skipped
        }

        if failed == 0:
            print("\n✅ All tests PASSED!")
        else:
            print(f"\n⚠ {failed} test(s) FAILED")

    def save_results(self):
        """Save test results to JSON file."""
        report_file = f"sprint2_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Test report saved to: {report_file}")


def main():
    """Main test execution."""
    tester = Sprint2Tester()
    tester.run_all_tests()

    print("\n" + "="*80)
    print("Sprint 2 Testing Complete!")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()
