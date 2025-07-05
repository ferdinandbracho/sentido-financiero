"""
Table Extraction Testing Utility

This utility helps test and debug table extraction methods on PDF statements.
Use this to quickly test which extraction method works best for your specific PDFs.

Usage:
    python -m app.utils.table_extraction_test path/to/your/statement.pdf

Author: StatementSense
Created: July 2025
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

from app.services.table_extractor import table_extractor, TableExtractionResult
from app.services.pdf_parser import pdf_processor
from app.config import settings

logger = settings.get_logger(__name__)


class TableExtractionTester:
    """Testing utility for table extraction methods."""
    
    def __init__(self):
        self.logger = logger
    
    def test_extraction_methods(self, pdf_path: str, page_number: int = 0) -> Dict[str, Any]:
        """
        Test all available extraction methods on a PDF.
        
        Args:
            pdf_path: Path to PDF file
            page_number: Page to test (0-indexed)
            
        Returns:
            Dictionary with test results from each method
        """
        try:
            # Read PDF file
            with open(pdf_path, 'rb') as file:
                pdf_content = file.read()
            
            print(f"Testing extraction methods on: {pdf_path}")
            print(f"PDF size: {len(pdf_content)} bytes")
            print(f"Testing page: {page_number + 1}")
            print("-" * 60)
            
            # Test all extraction methods
            results = table_extractor.extract_tables_from_pdf(pdf_content, page_number)
            
            # Sort results by confidence (best first)
            results.sort(key=lambda x: x.confidence, reverse=True)
            
            test_results = {
                "pdf_path": pdf_path,
                "page_number": page_number,
                "results": []
            }
            
            for i, result in enumerate(results):
                print(f"\n{i+1}. Method: {result.method.value}")
                print(f"   Success: {result.success}")
                print(f"   Confidence: {result.confidence:.2f}")
                print(f"   Tables found: {len(result.tables)}")
                
                if result.error_message:
                    print(f"   Error: {result.error_message}")
                
                if result.success and result.tables:
                    print(f"   Table dimensions: {[f'{len(t)}x{len(t.columns)}' for t in result.tables]}")
                    
                    # Show first few rows of first table
                    first_table = result.tables[0]
                    if len(first_table) > 0:
                        print(f"   Sample data (first 3 rows):")
                        print(first_table.head(3).to_string(index=False))
                
                test_results["results"].append({
                    "method": result.method.value,
                    "success": result.success,
                    "confidence": result.confidence,
                    "tables_count": len(result.tables),
                    "error": result.error_message
                })
            
            return test_results
            
        except Exception as e:
            self.logger.error(f"Testing failed: {e}", exc_info=True)
            return {"error": str(e)}
    
    def test_transaction_detection(self, pdf_path: str) -> Dict[str, Any]:
        """
        Test transaction table detection specifically.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with transaction detection results
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_content = file.read()
            
            print(f"\nTesting transaction detection on: {pdf_path}")
            print("-" * 60)
            
            # Test transaction table detection
            transaction_tables = table_extractor.find_transaction_tables(pdf_content)
            
            print(f"Transaction tables found: {len(transaction_tables)}")
            
            if transaction_tables:
                for i, table in enumerate(transaction_tables):
                    print(f"\nTransaction Table {i+1}:")
                    print(f"  Dimensions: {len(table)} rows x {len(table.columns)} columns")
                    print(f"  Sample data:")
                    print(table.head(5).to_string(index=False))
            
            return {
                "pdf_path": pdf_path,
                "transaction_tables_count": len(transaction_tables),
                "transaction_tables": [table.to_dict() for table in transaction_tables]
            }
            
        except Exception as e:
            self.logger.error(f"Transaction detection test failed: {e}", exc_info=True)
            return {"error": str(e)}
    
    def test_full_processing_pipeline(self, pdf_path: str) -> Dict[str, Any]:
        """
        Test the full processing pipeline including Mexican parser integration.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with full pipeline results
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_content = file.read()
            
            print(f"\nTesting full processing pipeline on: {pdf_path}")
            print("-" * 60)
            
            # Test full processing
            result = pdf_processor.process_statement(pdf_content)
            
            print(f"Processing result:")
            print(f"  Success: {result['success']}")
            print(f"  Confidence: {result['confidence']:.2f}")
            print(f"  Extraction method: {result.get('extraction_method', 'N/A')}")
            print(f"  Transactions found: {len(result.get('transactions', []))}")
            
            if result.get('error'):
                print(f"  Error: {result['error']}")
            
            if result.get('metadata'):
                metadata = result['metadata']
                print(f"  Metadata:")
                for key, value in metadata.items():
                    if value is not None:
                        print(f"    {key}: {value}")
            
            # Show sample transactions
            if result.get('transactions'):
                print(f"\n  Sample transactions (first 5):")
                for i, tx in enumerate(result['transactions'][:5]):
                    print(f"    {i+1}. {tx.get('date')} - {tx.get('description')} - ${tx.get('amount')}")
            
            return {
                "pdf_path": pdf_path,
                "processing_result": result
            }
            
        except Exception as e:
            self.logger.error(f"Full pipeline test failed: {e}", exc_info=True)
            return {"error": str(e)}
    
    def run_comprehensive_test(self, pdf_path: str, page_number: int = 0) -> Dict[str, Any]:
        """
        Run all tests on a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            page_number: Page to test (0-indexed)
            
        Returns:
            Dictionary with all test results
        """
        print("=" * 80)
        print("COMPREHENSIVE TABLE EXTRACTION TEST")
        print("=" * 80)
        
        results = {
            "pdf_path": pdf_path,
            "page_number": page_number,
            "extraction_methods": None,
            "transaction_detection": None,
            "full_pipeline": None
        }
        
        try:
            # Test 1: Extraction methods
            print("\n1. TESTING EXTRACTION METHODS")
            results["extraction_methods"] = self.test_extraction_methods(pdf_path, page_number)
            
            # Test 2: Transaction detection
            print("\n2. TESTING TRANSACTION DETECTION")
            results["transaction_detection"] = self.test_transaction_detection(pdf_path)
            
            # Test 3: Full pipeline
            print("\n3. TESTING FULL PROCESSING PIPELINE")
            results["full_pipeline"] = self.test_full_processing_pipeline(pdf_path)
            
            print("\n" + "=" * 80)
            print("TEST SUMMARY")
            print("=" * 80)
            
            # Summary
            extraction_success = any(r.get("success", False) for r in results["extraction_methods"].get("results", []))
            transaction_success = results["transaction_detection"].get("transaction_tables_count", 0) > 0
            pipeline_success = results["full_pipeline"].get("processing_result", {}).get("success", False)
            
            print(f"Extraction Methods: {'✓' if extraction_success else '✗'}")
            print(f"Transaction Detection: {'✓' if transaction_success else '✗'}")
            print(f"Full Pipeline: {'✓' if pipeline_success else '✗'}")
            
            if extraction_success:
                best_method = max(results["extraction_methods"]["results"], key=lambda x: x.get("confidence", 0))
                print(f"Best Method: {best_method['method']} (confidence: {best_method['confidence']:.2f})")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Comprehensive test failed: {e}", exc_info=True)
            results["error"] = str(e)
            return results


def main():
    """Command line interface for testing table extraction."""
    parser = argparse.ArgumentParser(description='Test table extraction methods on PDF statements')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('--page', type=int, default=0, help='Page number to test (0-indexed)')
    parser.add_argument('--methods-only', action='store_true', help='Test extraction methods only')
    parser.add_argument('--transactions-only', action='store_true', help='Test transaction detection only')
    parser.add_argument('--pipeline-only', action='store_true', help='Test full pipeline only')
    
    args = parser.parse_args()
    
    # Validate PDF path
    if not Path(args.pdf_path).exists():
        print(f"Error: PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    tester = TableExtractionTester()
    
    try:
        if args.methods_only:
            tester.test_extraction_methods(args.pdf_path, args.page)
        elif args.transactions_only:
            tester.test_transaction_detection(args.pdf_path)
        elif args.pipeline_only:
            tester.test_full_processing_pipeline(args.pdf_path)
        else:
            tester.run_comprehensive_test(args.pdf_path, args.page)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()