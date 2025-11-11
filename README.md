# FineHero - Legal Service for Traffic Fine Contestation 🚀

## Project Overview

FineHero is a SaaS legal service that helps people contest Portuguese traffic fines by generating professional defense letters using AI. Instead of paying €100+ for a lawyer, users pay €10-30 for expertly crafted defense letters that can actually win cases.

**Key Value**: Professional legal defense at 70-90% lower cost than traditional lawyers.

The system processes fine documents, analyzes the circumstances, and generates legally robust defense letters using Portuguese legal knowledge and AI.

## Mission

- Make professional legal defense accessible to everyone who receives a traffic fine.
- Generate lawyer-quality defense letters at a fraction of traditional costs.
- Help Portuguese drivers successfully contest unfair or incorrect fines.
- Scale affordable legal services across Portugal and beyond.

## Core Features

- **Document Upload**: Upload PDF/photo of traffic fine with drag-and-drop interface
- **AI Analysis**: Advanced OCR and legal analysis of fine details and circumstances
- **Professional Letters**: Generate legally robust defense letters with proper citations
- **User Accounts**: Secure user dashboard to track cases and payment history
- **Payment Processing**: Stripe integration for subscription and one-time payments
- **Legal Accuracy**: Portuguese legal knowledge base with 7 traffic law articles
- **Multiple Pricing**: €15-50/month subscriptions or €25-35 per defense letter
- **Mobile Ready**: Responsive web design and future iOS app support

## Tech Stack

- **Backend**: Python (FastAPI) with comprehensive legal document processing
- **Frontend**: React/Next.js with TypeScript for modern web application
- **PDF/OCR**: Multi-tier OCR pipeline (pdfplumber → pytesseract → EasyOCR)
- **AI/ML**: RAG system with FAISS + HuggingFace embeddings for legal knowledge
- **Database**: PostgreSQL with optimized legal document storage
- **Payments**: Stripe integration for subscriptions and one-time payments
- **Authentication**: JWT-based user authentication and session management
- **Storage**: Cloud storage for uploaded documents and generated letters

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 16+ and npm for frontend
- PostgreSQL database (or SQLite for development)
- Stripe account for payment processing
- AI API keys (Gemini/OpenAI) for defense generation

### Current Development Status

**Phase**: Foundation Development (75% Complete)
- ✅ Portuguese legal knowledge base (7 articles)
- ✅ Core defense generation framework
- ✅ Test infrastructure
- ⏳ RAG vector store completion
- ❌ No database, frontend, or payment processing

### Testing the Current System

1. **Test Defense Generation**
   ```bash
   # Navigate to backend directory
   cd backend
   
   # Run comprehensive test
   python test_defense_simple_fixed.py
   
   # Test individual components
   python -c "from services.defense_generator import DefenseGenerator; print('DefenseGenerator imports successfully')"
   ```

2. **Knowledge Base Testing**
   ```bash
   # List Portuguese legal documents
   ls knowledge_base/legal_articles/
   
   # Check legal content
   head -20 knowledge_base/legal_articles/artigo_48_parking.txt
   ```

3. **RAG System (Pending)**
   ```bash
   # Complete vector store indexing (WEDNESDAY TASK)
   python rag/ingest.py --ingest
   
   # Test legal document retrieval
   python -c "from rag.retriever import RAGRetriever; r = RAGRetriever(); print(r.retrieve('estacionamento proibido', k=2))"
   ```

### Development Roadmap

**Current Status**: Foundation Phase (75% Complete)

**✅ Completed (Tuesday)**:
- Portuguese legal knowledge base (7 articles)
- DefenseGenerator import fixes
- Test framework establishment
- Core AI integration framework

**⏳ Wednesday Tasks**:
- Complete RAG vector store indexing
- End-to-end testing with Portuguese legal context
- Performance validation

**❌ Remaining Work**:
- Database models and migrations
- Frontend React/Next.js application
- Stripe payment integration
- User authentication system
- API endpoint development
- Production deployment

**Next Phases**: See `docs/frontend_integration_guide.md` for planned frontend development.

## Roadmap

### Phase 1 – Foundation Development (Current)
- ✅ **Legal Knowledge Base**: 7 Portuguese traffic law articles (Articles 48, 85, 105, 121, 137, 49, 135)
- ✅ **Defense Generator**: Core AI integration and fine processing framework
- ✅ **Import System**: Fixed DefenseGenerator import structure issues
- 🎯 **Current Focus**: Complete RAG vector store indexing and end-to-end testing
- ⏳ **Pending**: Full OCR pipeline, database models, frontend, Stripe integration

### Phase 2 – SaaS Launch & User Acquisition (Next)
- Launch live SaaS with payment processing
- Get first 50 paying customers
- Collect user feedback and iterate
- Optimize conversion and letter quality
- Implement lawyer review option for complex cases

### Phase 3 – Scale & Expand (Later)
- Expand to other fine categories and jurisdictions
- Add mobile app (iOS/Android)
- Implement lawyer network integration
- Consider expansion to other Portuguese-speaking countries
- Enterprise B2B services for fleet management

## Documentation

- **`docs/tuesday_implementation_report.md`** - Tuesday system transformation progress report
- **`docs/system_health_assessment_report.md`** - Monday technical assessment findings
- **`docs/portuguese_legal_sources_research.md`** - Portuguese legal sources research
- **`docs/frontend_integration_guide.md`** - Frontend integration guide (planned)
- **`docs/portugal_mvp_strategy.md`** - Portugal market entry strategy (planned)
- **`docs/one_week_action_plan.md`** - Implementation roadmap (planned)

## Business Model

### Pricing Structure
- **Single Defense**: €25 per letter
- **Premium Defense**: €35 (with lawyer review option)
- **Basic Subscription**: €15/month (2 defenses)
- **Professional**: €30/month (5 defenses)
- **Premium**: €50/month (unlimited + priority support)

### Target Market
- Portuguese drivers who receive traffic fines
- People who want to contest but can't afford lawyers
- Fleet managers and businesses with multiple vehicles
- Legal clinics and pro bono services

## Contributing

Contributions welcome! Focus on:
- Portuguese legal accuracy and knowledge base expansion
- Frontend user experience improvements
- Payment and subscription features
- Mobile app development

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For questions about the SaaS service or technical implementation:
- Create an issue for bugs or feature requests
- Check documentation in `docs/` folder
- Review existing issues and discussions

## Acknowledgments

- Portuguese legal system and traffic laws for providing the framework
- Open-source community for excellent tools (FastAPI, React, FAISS, etc.)
- Early beta users who will provide valuable feedback
- Portuguese legal professionals who help validate accuracy