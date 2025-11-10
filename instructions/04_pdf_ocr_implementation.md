# PDF OCR Implementation Instructions

## Objective
Replace the placeholder PDF text extraction in `backend/services/pdf_processor.py` with actual OCR functionality using the available libraries (pdfplumber, pytesseract, easyocr).

## Current Status
The PDF processor currently uses hardcoded dummy data instead of real text extraction. The `extract_text()` method returns placeholder text, and `parse_text()` performs simple string splitting.

## Requirements
- Implement real PDF text extraction using pdfplumber for structured PDFs
- Add OCR fallback using pytesseract and easyocr for scanned/image-based PDFs
- Maintain the existing interface and data validation logic
- Handle different PDF types (text-based vs. image-based)
- Add proper error handling and logging

## Implementation Steps

### 1. Install and Configure OCR Dependencies
- Ensure pytesseract and tesseract-ocr are installed on the system
- Configure easyocr model loading (consider lazy loading for performance)

### 2. Enhance PDFProcessor Class
- Modify `extract_text()` to use pdfplumber first
- Add OCR methods for fallback scenarios
- Implement PDF type detection (text vs. image)

### 3. Improve Text Parsing
- Replace simple string splitting with more robust parsing
- Handle different date formats, currency symbols, and text variations
- Add regex patterns for key field extraction

### 4. Error Handling and Validation
- Add try-catch blocks for OCR operations
- Implement graceful degradation (try multiple extraction methods)
- Maintain existing user prompt logic for missing fields

## Expected Outcomes
- Real text extraction from actual PDF files
- Support for both digital and scanned PDFs
- Improved accuracy in data extraction
- Better error handling and user feedback

## Testing
- Test with sample PDFs containing different layouts
- Verify extraction accuracy for key fields (date, amount, location, etc.)
- Ensure backward compatibility with existing CLI interface

## Dependencies
- pdfplumber (already in requirements.txt)
- pytesseract (already in requirements.txt)
- easyocr (already in requirements.txt)
- System-level tesseract installation may be required (refer to pytesseract documentation for details).
- EasyOCR will download language models on first use.

## Constraints
- Maintain existing method signatures and return formats
- Keep the validation and user prompt logic intact
- Ensure performance is acceptable for typical PDF sizes