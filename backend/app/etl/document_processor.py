"""
CSA AIaaS Platform - Document Processor
Sprint 2: The Memory Implantation

This module handles extraction of text from various document formats (PDF, DOCX, TXT).
Uses PyPDF2 for PDF extraction as a lightweight alternative to unstructured.io.

For production, consider upgrading to unstructured.io for better handling of:
- Tables and figures
- Complex layouts
- DWG files (CAD drawings)
"""

from typing import Dict, Optional, List
import os
from pathlib import Path
from datetime import datetime
import io


class DocumentProcessor:
    """
    Processes documents and extracts text content.

    Supports:
    - PDF files (via PyPDF2)
    - TXT files (plain text)
    - DOCX files (via python-docx) - optional

    For production, consider:
    - unstructured.io for advanced extraction
    - Apache Tika for multi-format support
    - pdfplumber for tables in PDFs
    """

    SUPPORTED_FORMATS = ['.pdf', '.txt', '.md']

    def __init__(self):
        """Initialize the document processor."""
        self.processed_count = 0

    def extract_text(self, file_path: str) -> Dict:
        """
        Extract text from a document file.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary containing:
            - text: Extracted text content
            - metadata: File metadata (name, size, format, page_count)
            - success: Boolean indicating success/failure
            - error: Error message if failed

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "text": "",
                "metadata": {}
            }

        file_ext = file_path_obj.suffix.lower()

        if file_ext not in self.SUPPORTED_FORMATS:
            return {
                "success": False,
                "error": f"Unsupported format: {file_ext}. Supported: {self.SUPPORTED_FORMATS}",
                "text": "",
                "metadata": {}
            }

        # Extract text based on format
        try:
            if file_ext == '.pdf':
                result = self._extract_from_pdf(file_path_obj)
            elif file_ext in ['.txt', '.md']:
                result = self._extract_from_text(file_path_obj)
            else:
                result = {
                    "success": False,
                    "error": f"No extraction method for {file_ext}",
                    "text": "",
                    "metadata": {}
                }

            # Add common metadata
            if result['success']:
                result['metadata'].update({
                    'file_name': file_path_obj.name,
                    'file_path': str(file_path_obj.absolute()),
                    'file_format': file_ext.upper().replace('.', ''),
                    'file_size_bytes': file_path_obj.stat().st_size,
                    'extraction_date': datetime.now().isoformat()
                })

            self.processed_count += 1
            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Extraction failed: {str(e)}",
                "text": "",
                "metadata": {}
            }

    def _extract_from_pdf(self, file_path: Path) -> Dict:
        """
        Extract text from PDF file using PyPDF2.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with extraction results
        """
        try:
            import PyPDF2

            text_content = []
            page_count = 0

            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)

                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content.append(page_text)
                    except Exception as e:
                        print(f"Warning: Failed to extract page {page_num}: {e}")
                        continue

            full_text = '\n\n'.join(text_content)

            return {
                "success": True,
                "text": full_text,
                "metadata": {
                    'page_count': page_count,
                    'extraction_method': 'PyPDF2'
                },
                "error": None
            }

        except ImportError:
            return {
                "success": False,
                "text": "",
                "metadata": {},
                "error": "PyPDF2 not installed. Run: pip install PyPDF2"
            }
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "metadata": {},
                "error": f"PDF extraction failed: {str(e)}"
            }

    def _extract_from_text(self, file_path: Path) -> Dict:
        """
        Extract text from plain text file.

        Args:
            file_path: Path to text file

        Returns:
            Dictionary with extraction results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

            return {
                "success": True,
                "text": text,
                "metadata": {
                    'extraction_method': 'direct_read',
                    'encoding': 'utf-8'
                },
                "error": None
            }

        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read()

                return {
                    "success": True,
                    "text": text,
                    "metadata": {
                        'extraction_method': 'direct_read',
                        'encoding': 'latin-1'
                    },
                    "error": None
                }
            except Exception as e:
                return {
                    "success": False,
                    "text": "",
                    "metadata": {},
                    "error": f"Text extraction failed: {str(e)}"
                }

    def extract_from_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        file_pattern: Optional[str] = None
    ) -> List[Dict]:
        """
        Extract text from all supported documents in a directory.

        Args:
            directory_path: Path to directory containing documents
            recursive: Whether to search subdirectories
            file_pattern: Optional glob pattern to filter files (e.g., "*.pdf")

        Returns:
            List of extraction results (one per file)
        """
        directory = Path(directory_path)

        if not directory.exists() or not directory.is_dir():
            print(f"Error: Directory not found: {directory_path}")
            return []

        # Find all supported files
        files_to_process = []

        if file_pattern:
            if recursive:
                files_to_process = list(directory.rglob(file_pattern))
            else:
                files_to_process = list(directory.glob(file_pattern))
        else:
            for ext in self.SUPPORTED_FORMATS:
                pattern = f"*{ext}"
                if recursive:
                    files_to_process.extend(directory.rglob(pattern))
                else:
                    files_to_process.extend(directory.glob(pattern))

        print(f"Found {len(files_to_process)} documents to process")

        # Process each file
        results = []
        for file_path in files_to_process:
            print(f"Processing: {file_path.name}...")
            result = self.extract_text(str(file_path))
            results.append(result)

            if result['success']:
                print(f"  ✓ Extracted {len(result['text'])} characters")
            else:
                print(f"  ✗ Failed: {result['error']}")

        return results

    def get_stats(self) -> Dict:
        """
        Get processing statistics.

        Returns:
            Dictionary with processing stats
        """
        return {
            'processed_count': self.processed_count,
            'supported_formats': self.SUPPORTED_FORMATS
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def extract_text_from_file(file_path: str) -> str:
    """
    Convenience function to extract text from a single file.

    Args:
        file_path: Path to the document

    Returns:
        Extracted text (empty string if failed)
    """
    processor = DocumentProcessor()
    result = processor.extract_text(file_path)
    return result['text'] if result['success'] else ""


def extract_with_metadata(file_path: str) -> Dict:
    """
    Convenience function to extract text and metadata from a file.

    Args:
        file_path: Path to the document

    Returns:
        Dictionary with text and metadata
    """
    processor = DocumentProcessor()
    return processor.extract_text(file_path)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    print("Document Processor Example")
    print("=" * 80)

    processor = DocumentProcessor()

    # Example 1: Extract from a single file
    # file_path = "/path/to/your/document.pdf"
    # result = processor.extract_text(file_path)
    # if result['success']:
    #     print(f"\nExtracted {len(result['text'])} characters")
    #     print(f"Metadata: {result['metadata']}")
    #     print(f"\nFirst 500 characters:\n{result['text'][:500]}")
    # else:
    #     print(f"\nExtraction failed: {result['error']}")

    # Example 2: Extract from directory
    # directory_path = "/path/to/documents"
    # results = processor.extract_from_directory(directory_path, recursive=True, file_pattern="*.pdf")
    # print(f"\nProcessed {len(results)} documents")
    # successful = sum(1 for r in results if r['success'])
    # print(f"Successful: {successful}/{len(results)}")

    print("\n" + "=" * 80)
    print("To use this module:")
    print("1. Uncomment the examples above")
    print("2. Update the file/directory paths")
    print("3. Run: python -m app.etl.document_processor")
    print("\nOr import and use in your ETL pipeline:")
    print("  from app.etl.document_processor import DocumentProcessor")
    print("  processor = DocumentProcessor()")
    print("  result = processor.extract_text('document.pdf')")
