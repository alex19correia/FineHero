# Documentation Style Guide - FineHero/Multas AI

## Overview
This style guide establishes consistent formatting, structure, and presentation standards for all project documentation to ensure clarity, maintainability, and professional quality.

## 1. Document Structure Standards

### 1.1 Standard Document Header
```markdown
# Document Title - FineHero/Multas AI

## Overview
[Brief 2-3 sentence description of the document's purpose and scope]

## Prerequisites
- List any required knowledge, tools, or setup steps
- Link to relevant setup documentation

## Document Information
- **Last Updated**: [Date]
- **Version**: [Version number]
- **Maintained By**: [Team/Role]
- **Review Cycle**: [Frequency]
```

### 1.2 Standard Section Hierarchy
```markdown
# H1 - Document Title
## H2 - Major Sections (Installation, Configuration, Usage)
### H3 - Subsections (specific features or procedures)
#### H4 - Detailed procedures or specific configurations
##### H5 - Minor details or variations
###### H6 - Rarely used, only for very specific items
```

### 1.3 Table of Contents Format
```markdown
## Table of Contents
1. [Section 1](#section-1)
2. [Section 2](#section-2)
   2.1. [Subsection](#subsection)
3. [Section 3](#section-3)
```

## 2. Code Documentation Standards

### 2.1 Code Block Formatting
```markdown
**Python Example:**
```python
def example_function(parameter: str) -> dict:
    \"\"\"
    Brief description of what the function does.
    
    Args:
        parameter (str): Description of the parameter
        
    Returns:
        dict: Description of the return value
        
    Raises:
        ValueError: When parameter is invalid
    \"\"\"
    # Function implementation
    pass
```
```

### 2.2 Command-Line Examples
```markdown
**Install Dependencies:**
```bash
pip install -r backend/requirements.txt
```

**Run Application:**
```bash
uvicorn backend.app.main:app --reload --port 8000
```
```

### 2.3 Configuration Examples
```markdown
**Environment Configuration:**
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/finehero
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
```
```

## 3. Visual Elements Standards

### 3.1 Mermaid Diagrams
```markdown
```mermaid
graph TD
    A[User Upload PDF] --> B[PDF Processing]
    B --> C[OCR Text Extraction]
    C --> D[Data Validation]
    D --> E[AI Defense Generation]
    E --> F[PDF Output]
```
```

### 3.2 Alert Boxes and Callouts
```markdown
> **Note**: Important information that requires special attention

> **Warning**: Critical information that could cause issues if ignored

> **Tip**: Helpful suggestions for better results

> **Info**: Additional contextual information

> **Success**: Confirmation of successful operations

> **Error**: Error conditions and troubleshooting steps
```

### 3.3 Tables
```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |

**Table Caption**: Brief description of the table content
```

## 4. Content Guidelines

### 4.1 Writing Style
- **Active Voice**: Use active voice for clearer instructions
- **Present Tense**: Use present tense for ongoing processes
- **Second Person**: Address readers directly ("you", "your")
- **Concise Language**: Avoid unnecessary words and redundancy

### 4.2 Technical Terminology
- **Consistent Terms**: Use the same terms throughout the document
- **Acronyms**: Define acronyms on first use, then use consistently
  - Example: "Application Programming Interface (API)" then "API" throughout
- **File Paths**: Use backslashes for Windows, forward slashes for URLs
- **Code Elements**: Use backticks for code, file paths, and technical terms

### 4.3 Links and References
```markdown
**Internal References:**
- [Setup Guide](getting-started/installation.md)
- [API Reference](api/openapi-spec.yaml)
- [Database Schema](architecture/database-design.md)

**External References:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
```

## 5. File Organization Standards

### 5.1 File Naming Conventions
```markdown
**Documentation Files:**
- kebab-case: `getting-started-guide.md`
- descriptive: `api-endpoint-reference.md`
- versioned: `deployment-guide-v2.md`

**Image Files:**
- descriptive: `system-architecture-diagram.png`
- timestamped: `api-flow-2025-11-11.png`

**Configuration Files:**
- standard extensions: `docker-compose.yml`, `.env.example`
```

### 5.2 Directory Structure
```markdown
docs/
├── README.md                           # Main documentation index
├── getting-started/                     # Installation and setup
├── architecture/                        # System design documents
├── development/                         # Developer guidelines
├── operations/                          # Deployment and maintenance
├── api/                                # API documentation
├── business/                           # User and business docs
└── templates/                          # Reusable templates
```

## 6. Version Control Integration

### 6.1 Document Versioning
```markdown
## Document Information
- **Version**: 1.0.0
- **Last Updated**: 2025-11-11
- **Changes**: 
  - 1.0.0 (2025-11-11): Initial version
  - 0.9.0 (2025-10-15): Beta release with feedback integration
```

### 6.2 Change Tracking
```markdown
## Revision History
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-11 | 1.0.0 | Initial documentation | Development Team |
| 2025-10-15 | 0.9.0 | Added API examples | Technical Writer |
```

## 7. Quality Assurance Standards

### 7.1 Review Checklist
- [ ] All code examples tested and working
- [ ] All links and references verified
- [ ] Consistent terminology throughout
- [ ] Proper formatting and structure
- [ ] Clear and actionable instructions
- [ ] Complete prerequisites and requirements listed

### 7.2 Accessibility Standards
- Descriptive alt text for all images
- Proper heading hierarchy for screen readers
- Sufficient color contrast for text and backgrounds
- Keyboard navigation support for interactive elements

### 7.3 SEO and Discoverability
- Descriptive document titles
- Clear meta descriptions
- Proper heading structure for search indexing
- Consistent keyword usage
- Internal linking for related content

## 8. Template Integration

### 8.1 Required Elements Checklist
- [ ] Document header with title and overview
- [ ] Table of contents for documents > 500 words
- [ ] Prerequisites and requirements section
- [ ] Clear step-by-step instructions
- [ ] Code examples with proper formatting
- [ ] Cross-references to related documentation
- [ ] Version information and revision history

### 8.2 Quality Gates
1. **Technical Review**: All technical content verified for accuracy
2. **Editorial Review**: Writing style, grammar, and clarity checked
3. **User Testing**: Instructions tested by new users
4. **Update Integration**: Changes reflected in related documents

This style guide ensures that all documentation maintains professional quality, consistency, and usability across the entire FineHero/Multas AI project.