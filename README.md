# FineHero / Multas AI 🚀

## Project Overview

FineHero is an AI-powered system designed to automate the contestation of traffic fines in Portugal. It offers a faster, more affordable, and scalable alternative to traditional legal services, combining automated document processing with human oversight and legal compliance.

The system is modular and extensible, enabling expansion to other markets and integration with multi-lingual legal frameworks in the future.

## Mission

- Build a modular, AI-driven system for contesting fines.
- Enable rapid, accurate, and legally sound defenses.
- Scale efficiently to new regions while preserving human verification and compliance.
- Deliver affordable, accessible solutions for both B2C and B2B markets.

## Core Features

- **PDF Ingestion**: Automated ingestion of fine notifications in PDF format.
- **Data Extraction**: OCR-based structured data extraction (pytesseract, easyocr).
- **AI Defense Generation**: Generate administrative defenses with AI, using a continuous learning loop for improvement.
- **CLI Interface**: Initial command-line interface for testing and advanced users.
- **History & Logging**: Maintain user history and robust process logging for auditability.
- **Multi-Language Ready**: Designed with future international expansion in mind.
- **Scalable Architecture**: From SQLite prototypes to PostgreSQL/PostGIS for full-scale deployment.

## Tech Stack

- **Backend**: Python (FastAPI)
- **CLI**: Python
- **PDF/OCR**: pdfplumber, pytesseract, easyocr
- **AI/ML**: Gemini CLI, transformers, google-generativeai
- **Database**: SQLite (initial), PostgreSQL (production-ready)
- **Optional Frontend / MVP**: Lovable, React / Next.js for landing pages and user interaction

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Install Python dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Run the CLI**
   ```bash
   python cli/main.py
   ```

### Next Steps (Recommended)

- Configure database: PostgreSQL recommended for production.
- Setup AI API keys (OpenAI, Google Generative AI, or Gemini CLI).
- Prepare PDF samples for testing ingestion and extraction.
- Review prompts and templates for AI-generated defenses.

## Roadmap

### Phase 1 – MVP (Portugal)
- PDF ingestion + OCR extraction
- AI-generated defense letters (manual validation)
- CLI interface + basic logging

### Phase 1.5 – Knowledge Base Foundation (Current Focus)
- **Automated Data Collection**: Implemented web scraping infrastructure (`backend/services/web_scraper.py`) for Portuguese legal databases (ANSR, with placeholders for Diario da Republica and DGSI.pt).
- **RAG Enhancement**: Expanded knowledge base with metadata tagging and quality scoring in `rag/ingest.py`.
- **Metadata System**: Implemented database models (`backend/app/models.py`) for document metadata and quality tracking.
- **CLI Commands**: Added CLI commands (`cli/main.py`) for web scraping and knowledge base ingestion (directory and single document).
- **Quality Control**: Automated document scoring and filtering for legal relevance (initial implementation in `rag/ingest.py`).
- **Continuous Updates**: Scheduled monitoring for new legal developments and precedents (planned).

### Phase 2 – Beta
- Launch landing page / subscription model
- Automate end-to-end generation & PDF delivery
- Collect user feedback

### Phase 3 – Scale
- Internationalization (Brazil, Spanish markets)
- Multi-language RAG integration
- Human-in-the-loop optional validation
- Analytics & KPI dashboards

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repo
2. Create a new branch for features/bugfixes
3. Run tests locally before submitting a PR

## License

[Specify the license here, e.g., MIT License]

## Contact

For questions or support, please [add contact information or link to issues].

## Acknowledgments

- Thanks to the open-source community for the tools and libraries used.
- Special mention to contributors and early adopters.