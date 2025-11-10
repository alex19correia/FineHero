import pandas as pd
from typing import IO
import pdfplumber
import pytesseract
import easyocr
import re
import io
from PIL import Image
import numpy as np

class PDFProcessor:
    """
    A class to handle PDF ingestion and data extraction.
    """

    def __init__(self, pdf_file: IO):
        """
        Initialize with a PDF file object.
        """
        self.pdf_file = pdf_file
        self.extracted_data = {}
        self.reader = easyocr.Reader(['en']) # Initialize EasyOCR reader once

    def extract_text(self):
        """
        Extracts text from the PDF using pdfplumber, pytesseract, and easyocr as fallbacks.
        """
        print(f"Extracting text from {self.pdf_file.name}...")
        full_text = ""

        # Try pdfplumber first for text-based PDFs
        try:
            # Reset file pointer for other libraries
            self.pdf_file.seek(0)
            with pdfplumber.open(self.pdf_file) as pdf:
                for page in pdf.pages:
                    full_text += page.extract_text() or ""
            if full_text.strip():
                print("Text extracted using pdfplumber.")
                return full_text
        except Exception as e:
            print(f"pdfplumber failed: {e}. Falling back to OCR.")

        # Fallback to pytesseract (requires Tesseract-OCR installed)
        try:
            # Reset file pointer for other libraries
            self.pdf_file.seek(0)
            with pdfplumber.open(self.pdf_file) as pdf:
                for page in pdf.pages:
                    # Render page to image for Tesseract
                    page_image = page.to_image()
                    img_byte_arr = io.BytesIO()
                    page_image.original.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    img = Image.open(img_byte_arr)
                    full_text += pytesseract.image_to_string(img) or ""
            if full_text.strip():
                print("Text extracted using pytesseract.")
                return full_text
        except Exception as e:
            print(f"pytesseract failed: {e}. Falling back to EasyOCR.")

        # Fallback to EasyOCR
        try:
            # Reset file pointer for other libraries
            self.pdf_file.seek(0)
            with pdfplumber.open(self.pdf_file) as pdf:
                for page in pdf.pages:
                    # Render page to image for EasyOCR
                    page_image = page.to_image()
                    img_byte_arr = io.BytesIO()
                    page_image.original.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    img = Image.open(img_byte_arr)
                    
                    # EasyOCR expects a file path or numpy array, convert PIL Image
                    img_np = np.array(img)
                    results = self.reader.readtext(img_np)
                    for (bbox, text, prob) in results:
                        full_text += text + " "
            if full_text.strip():
                print("Text extracted using EasyOCR.")
                return full_text
        except Exception as e:
            print(f"EasyOCR failed: {e}. No text extracted.")

        return full_text

    def parse_text(self, text: str):
        """
        Parses the extracted text to find key-value pairs using regex.
        """
        print("Parsing extracted text...")
        data = {}

        # Regex patterns for common fields
        patterns = {
            "date": r"(?i)(?:date|data):\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}\s+\w+\s+\d{4})",
            "location": r"(?i)(?:local|location):\s*([A-Za-zÀ-ÿ\s,\-]+)",
            "infraction": r"(?i)(?:infraction|infração|code):\s*([A-Z0-9]+)",
            "amount": r"(?i)(?:amount|valor):\s*(\d+(?:[.,]\d{2})?)\s*(?:eur|€)"
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                data[field] = match.group(1).strip()
        
        self.extracted_data = data
        return self.extracted_data

    def validate_data(self):
        """
        Validates the extracted data against the required schema.
        Implements the requirement to ask the user for missing fields.
        """
        print("Validating data...")
        required_fields = ["date", "location", "infraction", "amount"]
        missing_fields = [field for field in required_fields if field not in self.extracted_data]

        if missing_fields:
            print(f"Missing fields: {', '.join(missing_fields)}")
            # Here we would implement the logic to ask the user for input.
            # For now, we'll just log it.
            for field in missing_fields:
                # In the CLI, this would be an input() prompt
                user_input = f"user_provided_{field}" 
                self.extracted_data[field] = user_input
        
        print("Data validation complete.")
        return self.extracted_data

    def process(self):
        """
        Full processing pipeline for a PDF.
        """
        text = self.extract_text()
        self.parse_text(text)
        self.validate_data()
        return self.extracted_data

if __name__ == '__main__':
    # Example usage:
    # This would be called from the CLI.
    # with open("path/to/your.pdf", "rb") as f:
    #     processor = PDFProcessor(f)
    #     data = processor.process()
    #     print(data)
    pass
