import os
import sys
import pdfplumber
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_pdf(file_path):
    """Analyze a PDF file and extract relevant information"""
    logger.info(f"Analyzing PDF: {file_path}")
    
    try:
        with pdfplumber.open(file_path) as pdf:
            # Extract basic info
            num_pages = len(pdf.pages)
            logger.info(f"Number of pages: {num_pages}")
            
            # Extract text from first few pages
            full_text = ""
            for i, page in enumerate(pdf.pages[:min(3, num_pages)]):
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
                    logger.info(f"Page {i+1} text length: {len(page_text)} characters")
            
            # Look for bank indicators
            bank_indicators = {
                'bbva': ['bbva', 'bancomer', 'tarjeta platinum bbva', 'bbva méxico', 'bbva bancomer'],
                'banamex': ['banamex', 'citibanamex', 'banco nacional de méxico'],
                'santander': ['santander', 'banco santander', 'santander like', 'santander méxico', 'tarjeta de crédito santander'],
                'hsbc': ['hsbc', 'hsbc méxico', 'hsbc bank'],
                'scotiabank': ['scotiabank', 'scotia', 'scotiabank inverlat'],
                'banorte': ['banorte', 'banco mercantil del norte']
            }
            
            text_lower = full_text.lower()
            detected_banks = []
            
            for bank, indicators in bank_indicators.items():
                for indicator in indicators:
                    if indicator in text_lower:
                        detected_banks.append((bank, indicator))
            
            if detected_banks:
                logger.info(f"Detected banks: {detected_banks}")
            else:
                logger.warning("No bank indicators found")
            
            # Look for transaction patterns
            transaction_patterns = [
                r'\d{2}[-/]\w{3}[-/]\d{4}\s+\d{2}[-/]\w{3}[-/]\d{4}\s+.+?\s+[\+\-]?\s*\$[\d,]+\.\d{2}',  # BBVA
                r'\d{2}/\d{2}\s+.+?\s+[\+\-]?\$[\d,]+\.\d{2}',  # Banamex
                r'\d{2}/\d{2}/\d{4}\s+.+?\s+[\+\-]?\$[\d,]+\.\d{2}',  # Generic
            ]
            
            import re
            for i, pattern in enumerate(transaction_patterns):
                matches = re.findall(pattern, full_text)
                if matches:
                    logger.info(f"Found {len(matches)} transactions with pattern {i+1}")
                    for j, match in enumerate(matches[:3]):
                        logger.info(f"Sample transaction {j+1}: {match[:100]}")
            
            # Print sample of text for manual inspection
            logger.info("Sample text from document:")
            print("=" * 80)
            print(full_text[:1000])
            print("=" * 80)
            
            return {
                "file_name": os.path.basename(file_path),
                "num_pages": num_pages,
                "detected_banks": detected_banks,
                "text_sample": full_text[:1000]
            }
            
    except Exception as e:
        logger.error(f"Error analyzing PDF: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_pdfs.py <pdf_file1> [<pdf_file2> ...]")
        sys.exit(1)
    
    results = []
    for file_path in sys.argv[1:]:
        if os.path.exists(file_path):
            results.append(analyze_pdf(file_path))
        else:
            logger.error(f"File not found: {file_path}")
    
    logger.info(f"Analyzed {len(results)} PDF files")
