"""
Comprehensive Security Tests for SecurePDFProcessor

This test suite validates:
- Path traversal attack prevention
- File type validation
- Sandbox directory security
- Secure temporary file handling
- File size limits
- Security logging
- Error handling without information disclosure
"""

import pytest
import tempfile
import os
from pathlib import Path
from io import BytesIO
from unittest.mock import patch, MagicMock
import sys

# Add the backend directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_processor import SecurePDFProcessor, SecurityError
from services.security_validator import SecurityValidator


class TestSecurePDFProcessor:
    """Test suite for SecurePDFProcessor security features."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.user_id = "test_user_123"
        
        # Create a valid PDF file for testing
        self.valid_pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000106 00000 n 
0000000189 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
280
%%EOF"""
        
        # Create malicious file contents for testing
        self.malicious_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(../../../etc/passwd) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000106 00000 n 
0000000189 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
280
%%EOF"""
    
    def teardown_method(self):
        """Cleanup after each test method."""
        # Clean up test directory
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def create_test_file(self, filename: str, content: bytes) -> BytesIO:
        """Create a test file object with specified filename and content."""
        file_obj = BytesIO(content)
        file_obj.name = filename
        return file_obj
    
    def test_path_traversal_protection(self):
        """Test protection against various path traversal attacks."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "/../../../etc/passwd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "normal_file../../../malicious_file",
            "file..\\..\\..\\system32",
        ]
        
        for malicious_filename in traversal_attempts:
            with pytest.raises(SecurityError, match="Potentially malicious filename pattern detected"):
                file_obj = self.create_test_file(malicious_filename, self.valid_pdf_content)
                processor = SecurePDFProcessor(file_obj, user_id=self.user_id)
                processor.cleanup()
    
    def test_suspicious_filename_patterns(self):
        """Test protection against suspicious filename patterns."""
        suspicious_filenames = [
            "file\x00name.pdf",  # Null byte
            "file<test>.pdf",    # Angle brackets
            "file:test.pdf",     # Colon
            "file\"test\".pdf",   # Quote
            "file|test.pdf",     # Pipe
            "file?test.pdf",     # Question mark
            "file*test.pdf",     # Asterisk
            "con.pdf",           # Windows reserved name
            "prn.pdf",           # Windows reserved name
            "file   .pdf",       # Trailing spaces
            "   file.pdf",       # Leading spaces
            "file...pdf",        # Multiple dots
            "file\x01test.pdf",  # Control character
        ]
        
        for suspicious_filename in suspicious_filenames:
            with pytest.raises(SecurityError, match="Suspicious filename pattern detected"):
                file_obj = self.create_test_file(suspicious_filename, self.valid_pdf_content)
                processor = SecurePDFProcessor(file_obj, user_id=self.user_id)
                processor.cleanup()
    
    def test_file_type_validation(self):
        """Test file type validation by magic bytes."""
        # Test with non-PDF content
        non_pdf_content = b"This is not a PDF file"
        with pytest.raises(SecurityError, match="Invalid file type"):
            file_obj = self.create_test_file("test.txt", non_pdf_content)
            processor = SecurePDFProcessor(file_obj, user_id=self.user_id)
            processor.cleanup()
        
        # Test with corrupted PDF header
        corrupted_content = b"%NOTPDF-1.4\ncorrupted content"
        with pytest.raises(SecurityError, match="Invalid file type"):
            file_obj = self.create_test_file("test.pdf", corrupted_content)
            processor = SecurePDFProcessor(file_obj, user_id=self.user_id)
            processor.cleanup()
    
    def test_file_size_limits(self):
        """Test file size limit enforcement."""
        # Create a file larger than MAX_FILE_SIZE (10MB)
        large_content = b"A" * (11 * 1024 * 1024)  # 11MB
        with pytest.raises(ValueError, match="File size.*exceeds maximum allowed size"):
            file_obj = self.create_test_file("large_file.pdf", large_content)
            processor = SecurePDFProcessor(file_obj, user_id=self.user_id)
            processor.cleanup()
    
    def test_sandbox_directory_security(self):
        """Test sandbox directory creation and security."""
        file_obj = self.create_test_file("valid_file.pdf", self.valid_pdf_content)
        
        with SecurePDFProcessor(file_obj, user_id=self.user_id) as processor:
            # Verify sandbox directory was created
            assert processor.SANDBOX_BASE_DIR.exists()
            assert processor.SANDBOX_BASE_DIR.is_dir()
            
            # Verify secure file was created in sandbox
            assert processor.secure_file_path.exists()
            assert processor.secure_file_path.parent == processor.SANDBOX_BASE_DIR
            
            # Verify file has secure permissions (owner read/write only)
            file_stat = os.stat(processor.secure_file_path)
            file_mode = oct(file_stat.st_mode)[-3:]
            assert file_mode == "600"  # Read/write for owner only
            
            # Verify directory has secure permissions
            dir_stat = os.stat(processor.SANDBOX_BASE_DIR)
            dir_mode = oct(dir_stat.st_mode)[-3:]
            assert dir_mode == "700"  # Read/write/execute for owner only
    
    def test_secure_temporary_file_handling(self):
        """Test secure temporary file name generation."""
        file_obj = self.create_test_file("test.pdf", self.valid_pdf_content)
        
        with SecurePDFProcessor(file_obj, user_id=self.user_id) as processor:
            # Verify secure filename format
            assert processor.secure_file_path.name.startswith("secure_")
            assert processor.secure_file_path.name.endswith(".pdf")
            assert len(processor.secure_file_path.name) > 20  # UUID hex length
            
            # Verify the filename doesn't contain user input
            assert "test" not in processor.secure_file_path.name
    
    def test_secure_file_deletion(self):
        """Test secure file deletion with data overwriting."""
        file_obj = self.create_test_file("test.pdf", self.valid_pdf_content)
        
        with SecurePDFProcessor(file_obj, user_id=self.user_id) as processor:
            secure_path = processor.secure_file_path
            original_content = secure_path.read_bytes()
            
        # File should be securely deleted
        assert not secure_path.exists()
        
        # Verify the original content is no longer accessible
        # (In a real scenario, the content would be overwritten with random data)
        # For testing purposes, we just verify the file is gone
        assert not secure_path.exists()
    
    def test_security_logging(self):
        """Test that security events are properly logged."""
        # Mock the security logger
        with patch('services.pdf_processor.SecurePDFProcessor._log_security_event') as mock_log:
            file_obj = self.create_test_file("test.pdf", self.valid_pdf_content)
            
            with SecurePDFProcessor(file_obj, user_id=self.user_id) as processor:
                # Verify security events were logged
                assert mock_log.called
                
                # Check for specific security events
                logged_events = [call[0][0] for call in mock_log.call_args_list]
                assert "filename_validation" in logged_events
                assert "file_type_validated" in logged_events
                assert "secure_file_created" in logged_events
                assert "sandbox_directory_setup" in logged_events
    
    def test_error_handling_without_information_disclosure(self):
        """Test that errors don't expose sensitive information."""
        # Test with various error conditions
        error_cases = [
            (self.create_test_file("../../../etc/passwd", self.valid_pdf_content), "path traversal"),
            (self.create_test_file("large_file.pdf", b"A" * (11 * 1024 * 1024)), "file size"),
            (self.create_test_file("test.txt", b"Not a PDF"), "file type"),
        ]
        
        for file_obj, description in error_cases:
            with pytest.raises((SecurityError, ValueError)) as exc_info:
                with SecurePDFProcessor(file_obj, user_id=self.user_id) as processor:
                    pass
            
            # Verify error messages don't expose filesystem information
            error_msg = str(exc_info.value)
            assert "/etc/passwd" not in error_msg  # No sensitive path exposure
            assert "C:\\" not in error_msg  # No Windows path exposure
            assert "/tmp/" not in error_msg  # No temp directory exposure
            assert "sandbox" not in error_msg.lower() or "directory" in error_msg.lower()
    
    def test_valid_pdf_processing(self):
        """Test that valid PDFs are processed correctly."""
        file_obj = self.create_test_file("valid_infraction.pdf", self.valid_pdf_content)
        
        with SecurePDFProcessor(file_obj, user_id=self.user_id) as processor:
            # Test text extraction (should work for our test PDF)
            text = processor.extract_text()
            assert isinstance(text, str)
            
            # Test parsing
            data = processor.parse_text("Date: 2025-01-15\nLocation: Lisbon\nInfraction: CE-ART-121\nAmount: 150.00 EUR")
            assert isinstance(data, dict)
            
            # Test validation
            validated_data = processor.validate_data()
            assert isinstance(validated_data, dict)
    
    def test_context_manager_functionality(self):
        """Test context manager properly handles cleanup."""
        file_obj = self.create_test_file("test.pdf", self.valid_pdf_content)
        
        # Test successful processing
        with SecurePDFProcessor(file_obj, user_id=self.user_id) as processor:
            assert processor.secure_file_path.exists()
        
        # File should be cleaned up after context exit
        assert not processor.secure_file_path.exists()
        
        # Test exception handling in context
        with pytest.raises(SecurityError):
            with SecurePDFProcessor(self.create_test_file("../../../etc/passwd", self.valid_pdf_content), user_id=self.user_id):
                pass  # Exception should be raised
        
        # Even with exception, cleanup should happen (if processor was created)
        # Note: In this case, the processor won't be created due to early validation failure
    
    def test_file_hash_tracking(self):
        """Test that file hashes are tracked for integrity."""
        file_obj = self.create_test_file("test.pdf", self.valid_pdf_content)
        
        with SecurePDFProcessor(file_obj, user_id=self.user_id) as processor:
            # Verify file hash is computed and stored
            assert hasattr(processor, 'file_hash')
            assert isinstance(processor.file_hash, str)
            assert len(processor.file_hash) == 64  # SHA256 hex digest length
            assert processor.file_hash.isalnum()  # Should be hex
    
    def test_backward_compatibility(self):
        """Test that the old PDFProcessor name still works."""
        from services.pdf_processor import PDFProcessor
        
        file_obj = self.create_test_file("test.pdf", self.valid_pdf_content)
        
        # Should be able to use the old class name
        assert PDFProcessor is SecurePDFProcessor
        
        # Should work the same way
        with PDFProcessor(file_obj, user_id=self.user_id) as processor:
            assert processor.secure_file_path.exists()


class TestSecurityValidatorIntegration:
    """Test integration with SecurityValidator."""
    
    def test_security_validator_usage(self):
        """Test that SecurityValidator is properly used for data sanitization."""
        file_obj = BytesIO(b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
72 720 Td
(Date: <script>alert('xss')</script>) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000106 00000 n 
0000000189 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
280
%%EOF""")
        file_obj.name = "test.pdf"
        
        with SecurePDFProcessor(file_obj, user_id="test_user") as processor:
            # Parse text with potentially malicious content
            data = processor.parse_text("Date: <script>alert('xss')</script>\nLocation: Test\nAmount: 100 EUR")
            
            # Verify data was sanitized by SecurityValidator
            assert "Date" in data
            # The script tags should be sanitized
            assert "<script>" not in data["Date"]
            assert "alert" not in data["Date"]


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])