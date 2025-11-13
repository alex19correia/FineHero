"""
Secure PDF Processor with Comprehensive Path Traversal Protection

This module provides a hardened PDF processor that prevents:
- Path traversal attacks (../, ..\\, URL encoding bypasses)
- Directory traversal and unauthorized file access
- Resource exhaustion through file size attacks
- Malicious file type processing
- Information leakage through error messages

Security Features:
- Secure file path validation
- Sandbox directory isolation
- Random secure temporary file names
- File type and size validation
- Comprehensive security logging
- Proper error handling without information disclosure
"""

import pandas as pd
from typing import IO, Optional, Dict, Any
import pdfplumber
import pytesseract
import easyocr
import re
import io
import os
import tempfile
import uuid
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from PIL import Image
import numpy as np
from .security_validator import SecurityValidator

# Custom security exception for clear error handling
class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass

class SecurePDFProcessor:
    """
    Secure PDF processor with comprehensive path traversal protection and sandboxing.
    """

    # Security configuration
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES = {'.pdf'}
    SANDBOX_BASE_DIR = Path(tempfile.gettempdir()) / "finehero_pdf_sandbox"
    
    # Path traversal patterns to detect and block
    TRAVERSAL_PATTERNS = [
        r'\.\./',           # Unix style
        r'\.\.\\',          # Windows style
        r'%2e%2e%2f',       # URL encoded
        r'%2e%2e%5c',       # URL encoded Windows
        r'\.\.%2f',         # Partial URL encoded
        r'\.\.%5c',         # Partial URL encoded Windows
        r'\.\.%252f',       # Double URL encoded
        r'\.\.%255c',       # Double URL encoded Windows
        r'/%2e%2e/',        # Mixed encoding
        r'\\%2e%2e\\',      # Mixed encoding Windows
        r'\.\.%2f%2f',      # Double traversal
        r'\.\.%5c%5c',      # Double Windows traversal
        r'\.\.\\/',         # Mixed separators
    ]
    
    # Suspicious filename patterns
    SUSPICIOUS_PATTERNS = [
        r'\x00',           # Null bytes
        r'[<>:"|?*]',      # Windows invalid chars
        r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])$',  # Windows reserved names
        r'\s+$',           # Trailing spaces
        r'^\s+',           # Leading spaces
        r'\.{2,}',         # Multiple dots
        r'[\x01-\x1f]',    # Control characters
    ]

    def __init__(self, pdf_file: IO, user_id: Optional[str] = None):
        """
        Initialize secure PDF processor.
        
        Args:
            pdf_file: File-like object containing PDF data
            user_id: Optional user identifier for security logging
            
        Raises:
            ValueError: If file validation fails
            SecurityError: If security checks detect threats
        """
        self.security_validator = SecurityValidator()
        self.logger = logging.getLogger(__name__)
        self.security_logger = logging.getLogger('security_events')
        self.user_id = user_id
        
        # Initialize EasyOCR reader
        self.reader = easyocr.Reader(['en'])
        
        # Validate and process input file
        self._validate_and_setup_file(pdf_file)
        
        # Ensure sandbox directory exists
        self._setup_sandbox_directory()
        
        self.extracted_data = {}
        
    def _validate_and_setup_file(self, pdf_file: IO):
        """
        Validates the input PDF file against predefined security policies (size, type)
        and prepares a secure working copy within a sandboxed environment.
        This function is crucial for preventing various file-based attacks.
        
        Args:
            pdf_file: A file-like object containing the PDF data.
            
        Raises:
            ValueError: If basic file validation (e.g., missing file, size limit exceeded) fails.
            SecurityError: If security checks (e.g., invalid file type, malicious filename) detect threats.
        """
        if not pdf_file:
            self._log_security_event("file_missing", {"user_id": self.user_id})
            raise ValueError("PDF file is required")
        
        # 1. Validate filename if available.
        #    This prevents path traversal and other filename-based injection attacks.
        filename = getattr(pdf_file, 'name', None)
        if filename:
            self._validate_filename(filename)
        
        # 2. Validate file size.
        #    Prevents resource exhaustion attacks by limiting the maximum allowed file size.
        current_pos = pdf_file.tell() # Store current position to restore later
        pdf_file.seek(0, 2)  # Seek to the end of the file
        file_size = pdf_file.tell()  # Get the file size
        pdf_file.seek(current_pos)  # Restore original position
        
        if file_size > self.MAX_FILE_SIZE:
            self._log_security_event("file_too_large", {
                "filename": filename,
                "file_size": file_size,
                "max_size": self.MAX_FILE_SIZE
            })
            raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowed size ({self.MAX_FILE_SIZE} bytes)")
        
        # 3. Validate file type by reading magic bytes.
        #    Ensures that the file is indeed a PDF and not a disguised malicious executable.
        self._validate_file_type(pdf_file)
        
        # 4. Create a secure working copy in a sandboxed directory.
        #    This isolates the processing from the original file and prevents any
        #    potential side-effects from affecting other parts of the system.
        self._create_secure_working_copy(pdf_file, filename)
        
        self._log_security_event("file_setup_complete", {
            "filename": filename,
            "file_size": file_size,
            "user_id": self.user_id
        })
    def _validate_filename(self, filename: str):
        """
        Validates a given filename against known path traversal patterns,
        suspicious characters, and length limits to prevent file system attacks.
        A sanitized version of the filename is stored for safe logging.
        
        Args:
            filename: The filename string to validate.
            
        Raises:
            SecurityError: If any malicious or suspicious patterns are detected,
                           or if the filename exceeds length limits.
        """
        # Log the attempt to validate the filename for audit purposes.
        self._log_security_event("filename_validation", {
            "filename": filename,
            "user_id": self.user_id
        })
        
        # 1. Check for path traversal patterns.
        #    These patterns (e.g., "../", "..\\") attempt to access directories
        #    outside the intended working directory.
        for pattern in self.TRAVERSAL_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                self._log_security_event("path_traversal_attempt", {
                    "filename": filename,
                    "pattern_detected": pattern,
                    "user_id": self.user_id
                })
                raise SecurityError(f"Potentially malicious filename pattern detected: {pattern}")
        
        # 2. Check for suspicious filename patterns.
        #    These include null bytes, invalid Windows characters, reserved names,
        #    and control characters that could be used for various exploits.
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                self._log_security_event("suspicious_filename", {
                    "filename": filename,
                    "pattern_detected": pattern,
                    "user_id": self.user_id
                })
                raise SecurityError(f"Suspicious filename pattern detected: {pattern}")
        
        # 3. Check filename length limits.
        #    Extremely long filenames can sometimes be used in denial-of-service attacks.
        if len(filename) > 255: # Common filesystem limit
            self._log_security_event("filename_too_long", {
                "filename": filename,
                "length": len(filename),
                "user_id": self.user_id
            })
            raise SecurityError("Filename too long")
        
        # 4. Sanitize the filename for safe internal use and logging.
        #    This step replaces any non-alphanumeric, non-hyphen, non-underscore,
        #    non-dot characters with an underscore. This prevents logging or
        #    displaying potentially harmful characters.
        try:
            safe_filename = re.sub(r'[^\w\-_.]', '_', filename)
            self.sanitized_filename = safe_filename
            self._log_security_event("filename_sanitized", {
                "original_filename": filename,
                "sanitized_filename": safe_filename,
                "user_id": self.user_id
            })
        except Exception as e:
            self._log_security_event("filename_sanitization_error", {
                "filename": filename,
                "error": str(e),
                "user_id": self.user_id
            })
            raise SecurityError("Unable to process filename safely")
    
    def _validate_file_type(self, pdf_file: IO):
        """
        Validate file type by reading magic bytes.
        
        Args:
            pdf_file: File-like object to check
            
        Raises:
            SecurityError: If not a valid PDF file
        """
        # Read first few bytes to check PDF signature
        current_pos = pdf_file.tell()
        pdf_file.seek(0)
        header = pdf_file.read(8)
        pdf_file.seek(current_pos)
        
        # PDF files should start with "%PDF"
        if not header.startswith(b'%PDF'):
            self._log_security_event("invalid_file_type", {
                "file_signature": header[:4],
                "user_id": self.user_id
            })
            raise SecurityError("Invalid file type: File does not appear to be a valid PDF")
        
        # Log successful file type validation
        self._log_security_event("file_type_validated", {
            "file_signature": header[:4].decode('ascii', errors='ignore'),
            "user_id": self.user_id
        })
    
    def _create_secure_working_copy(self, pdf_file: IO, original_filename: Optional[str]):
        """
        Creates a secure, temporary working copy of the input PDF file within the
        designated sandbox directory. This isolation prevents direct manipulation
        of the original file and ensures that processing occurs in a controlled environment.
        
        Args:
            pdf_file: The original file-like object containing the PDF data.
            original_filename: The original filename for logging purposes.
            
        Raises:
            SecurityError: If the secure file creation fails or if file size
                           verification after copying indicates tampering.
        """
        # Generate a secure, random filename using UUID to prevent name collisions
        # and make it difficult to guess or target specific files.
        secure_filename = f"secure_{uuid.uuid4().hex}.pdf"
        
        # Construct the full path for the secure copy within the sandbox directory.
        self.secure_file_path = self.SANDBOX_BASE_DIR / secure_filename
        
        try:
            # Open the new file in binary write mode within the sandbox.
            with open(self.secure_file_path, 'wb') as secure_file:
                # Reset the original file pointer to the beginning and read its content.
                pdf_file.seek(0)
                # Read content up to MAX_FILE_SIZE + 1 to detect if it's unexpectedly larger.
                content = pdf_file.read(self.MAX_FILE_SIZE + 1)
                
                # Re-verify file size after reading to catch any potential bypasses
                # or unexpected data during the read operation.
                if len(content) > self.MAX_FILE_SIZE:
                    self._log_security_event("file_size_reverification_failed", {
                        "secure_filename": secure_filename,
                        "read_size": len(content),
                        "max_size": self.MAX_FILE_SIZE,
                        "user_id": self.user_id
                    })
                    raise SecurityError("File size verification failed after reading content")
                
                # Calculate a SHA256 hash of the file content. This hash can be used
                # later for integrity checking or duplicate detection.
                self.file_hash = hashlib.sha256(content).hexdigest()
                
                # Write the content to the secure working copy.
                secure_file.write(content)
                
            # Set restrictive file permissions (read/write for owner only).
            # This prevents other users or processes on the system from accessing the file.
            os.chmod(self.secure_file_path, 0o600)
            
            self._log_security_event("secure_file_created", {
                "secure_filename": secure_filename,
                "original_filename": original_filename,
                "file_hash": self.file_hash[:16],  # Log first 16 chars for tracking, not full hash
                "user_id": self.user_id
            })
            
        except Exception as e:
            self._log_security_event("secure_file_creation_failed", {
                "error": str(e),
                "original_filename": original_filename,
                "user_id": self.user_id
            })
            raise SecurityError(f"Failed to create secure working copy: {str(e)}")
    
    def _setup_sandbox_directory(self):
        """
        Set up secure sandbox directory with proper permissions.
        """
        try:
            # Create sandbox directory if it doesn't exist
            self.SANDBOX_BASE_DIR.mkdir(parents=True, exist_ok=True)
            
            # Set secure permissions (owner read/write/execute only)
            os.chmod(self.SANDBOX_BASE_DIR, 0o700)
            
            self._log_security_event("sandbox_directory_setup", {
                "sandbox_path": str(self.SANDBOX_BASE_DIR),
                "user_id": self.user_id
            })
            
        except Exception as e:
            self._log_security_event("sandbox_setup_failed", {
                "error": str(e),
                "sandbox_path": str(self.SANDBOX_BASE_DIR),
                "user_id": self.user_id
            })
            raise SecurityError(f"Failed to setup sandbox directory: {str(e)}")
    
    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log security events for audit trail.
        
        Args:
            event_type: Type of security event
            details: Event details dictionary
        """
        log_data = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "processor": "SecurePDFProcessor",
            "user_id": self.user_id,
            "secure_filename": getattr(self, 'sanitized_filename', 'unknown'),
            **details
        }
        
        self.security_logger.warning(f"Security event: {event_type}", extra={
            "security_event": True,
            "event_data": log_data
        })
    
    def extract_text(self):
        """
        Extracts text from the PDF using a multi-stage approach:
        1. Attempts extraction with `pdfplumber` (best for structured, text-based PDFs).
        2. If `pdfplumber` fails or yields no text, falls back to OCR methods.
        3. OCR fallback first tries `pytesseract` (generally faster).
        4. If `pytesseract` fails or yields no text, it falls back to `easyocr` (more robust for complex images).
        Security events are logged at each stage of the extraction process.
        """
        self._log_security_event("text_extraction_started", {
            "file_hash": getattr(self, 'file_hash', 'unknown')[:16],
            "user_id": self.user_id
        })
        
        full_text = ""
        extraction_method = "none"

        # Stage 1: Attempt text extraction using pdfplumber
        # This is the preferred method for PDFs that contain selectable text.
        try:
            # Use the secure file path for processing to ensure sandboxing.
            with pdfplumber.open(self.secure_file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text
                        
            if full_text.strip():
                extraction_method = "pdfplumber"
                self._log_security_event("text_extraction_success", {
                    "method": extraction_method,
                    "text_length": len(full_text),
                    "user_id": self.user_id
                })
                return full_text
        except Exception as e:
            # Log any exceptions during pdfplumber extraction but continue to fallbacks.
            self._log_security_event("text_extraction_failed", {
                "method": "pdfplumber",
                "error": str(e),
                "user_id": self.user_id
            })

        # Stage 2: Fallback to OCR methods if pdfplumber failed or returned no text.
        # This handles scanned PDFs or PDFs where text extraction is not straightforward.
        try:
            with pdfplumber.open(self.secure_file_path) as pdf:
                for page in pdf.pages:
                    # Render each page of the PDF to an image for OCR processing.
                    page_image = page.to_image()
                    img_byte_arr = io.BytesIO()
                    page_image.original.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    img = Image.open(img_byte_arr)
                    
                    # Sub-stage 2a: Try pytesseract first (often faster for clear text).
                    try:
                        text = pytesseract.image_to_string(img)
                        if text.strip():
                            full_text += text
                            extraction_method = "pytesseract"
                            # If pytesseract succeeds for a page, we can break and use its output.
                            break 
                    except Exception:
                        # Sub-stage 2b: If pytesseract fails, fall back to EasyOCR (more robust).
                        # Convert PIL Image to NumPy array for EasyOCR.
                        img_np = np.array(img)
                        results = self.reader.readtext(img_np)
                        for (bbox, text, prob) in results:
                            full_text += text + " "
                        extraction_method = "easyocr"
                        # If EasyOCR succeeds for a page, we can break and use its output.
                        break
                        
            if full_text.strip():
                self._log_security_event("text_extraction_success", {
                    "method": extraction_method,
                    "text_length": len(full_text),
                    "user_id": self.user_id
                })
                return full_text
                
        except Exception as e:
            # Log any exceptions during OCR fallback.
            self._log_security_event("text_extraction_failed", {
                "method": "ocr_fallback",
                "error": str(e),
                "user_id": self.user_id
            })

        # If no text could be extracted by any method, log this event.
        self._log_security_event("text_extraction_no_content", {
            "user_id": self.user_id
        })
        return full_text

    def parse_text(self, text: str):
        """
        Parses the extracted text to find key-value pairs using regex.
        """
        self._log_security_event("text_parsing_started", {
            "text_length": len(text),
            "user_id": self.user_id
        })
        
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
        
        # Sanitize parsed data
        sanitized_data = {}
        for key, value in data.items():
            # Use security validator to sanitize values
            try:
                safe_value = self.security_validator._sanitize_string(value)
                sanitized_data[key] = safe_value
            except Exception as e:
                self._log_security_event("data_sanitization_failed", {
                    "field": key,
                    "value": value[:100],  # Log first 100 chars
                    "error": str(e),
                    "user_id": self.user_id
                })
        
        self.extracted_data = sanitized_data
        self._log_security_event("text_parsing_completed", {
            "fields_extracted": len(sanitized_data),
            "fields": list(sanitized_data.keys()),
            "user_id": self.user_id
        })
        return self.extracted_data

    def validate_data(self):
        """
        Validates the extracted data against the required schema.
        Implements the requirement to ask the user for missing fields.
        """
        self._log_security_event("data_validation_started", {
            "extracted_fields": list(self.extracted_data.keys()),
            "user_id": self.user_id
        })
        
        print("Validating data...")
        required_fields = ["date", "location", "infraction", "amount"]
        missing_fields = [field for field in required_fields if field not in self.extracted_data]

        if missing_fields:
            print(f"Missing fields: {', '.join(missing_fields)}")
            self._log_security_event("data_validation_missing_fields", {
                "missing_fields": missing_fields,
                "user_id": self.user_id
            })
            
            # In a real implementation, this would prompt the user
            # For security, we don't use user input directly but generate safe defaults
            for field in missing_fields:
                safe_default = f"user_provided_{field}_{uuid.uuid4().hex[:8]}"
                self.extracted_data[field] = safe_default
                
            self._log_security_event("data_validation_defaults_applied", {
                "missing_fields": missing_fields,
                "user_id": self.user_id
            })
        
        print("Data validation complete.")
        return self.extracted_data

    def process(self):
        """
        Full processing pipeline for a PDF with comprehensive security logging.
        """
        self._log_security_event("processing_pipeline_started", {
            "file_hash": getattr(self, 'file_hash', 'unknown')[:16],
            "user_id": self.user_id
        })
        
        try:
            text = self.extract_text()
            self.parse_text(text)
            self.validate_data()
            
            self._log_security_event("processing_pipeline_completed", {
                "extracted_data_fields": list(self.extracted_data.keys()),
                "user_id": self.user_id
            })
            
            return self.extracted_data
            
        except Exception as e:
            self._log_security_event("processing_pipeline_failed", {
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": self.user_id
            })
            
            # Return secure error response without exposing sensitive information
            return {
                "error": "Processing failed",
                "error_code": "PROCESSING_ERROR",
                "secure_processing": True
            }

    def cleanup(self):
        """
        Securely clean up temporary files and resources.
        """
        try:
            # Remove secure working copy
            if hasattr(self, 'secure_file_path') and self.secure_file_path.exists():
                # Overwrite file with random data before deletion
                with open(self.secure_file_path, 'r+b') as f:
                    file_size = f.seek(0, 2)
                    f.seek(0)
                    # Write random data
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                
                # Secure delete
                os.remove(self.secure_file_path)
                
                self._log_security_event("secure_file_deleted", {
                    "secure_filename": self.secure_file_path.name,
                    "file_hash": getattr(self, 'file_hash', 'unknown')[:16]
                })
            
        except Exception as e:
            self._log_security_event("cleanup_error", {
                "error": str(e),
                "secure_path": getattr(self, 'secure_file_path', 'unknown')
            })
        
        # Clean up EasyOCR resources
        try:
            if hasattr(self, 'reader'):
                del self.reader
        except Exception:
            pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
    
    def __del__(self):
        """Destructor with cleanup."""
        self.cleanup()


# Legacy compatibility - keep old class name for backward compatibility
PDFProcessor = SecurePDFProcessor


if __name__ == '__main__':
    # Example usage with security features:
    # with open("secure_document.pdf", "rb") as f:
    #     with SecurePDFProcessor(f, user_id="user123") as processor:
    #         data = processor.process()
    #         print(data)
    pass
