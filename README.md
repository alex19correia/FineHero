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
- **Legal Accuracy**: Portuguese legal knowledge base with 200+ relevant articles
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

### Installation

1. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r backend/requirements.txt
   
   # Setup database
   python backend/database_migrations.py
   
   # Ingest Portuguese legal knowledge
   python rag/ingest.py --ingest
   
   # Start FastAPI backend
   uvicorn backend.app.main:app --reload --port 8000
   ```

2. **Frontend Setup**
   ```bash
   # Navigate to frontend directory
   cd frontend
   
   # Install dependencies
   npm install
   
   # Start development server
   npm run dev
   ```

3. **Environment Configuration**
   ```bash
   # Backend (.env)
   DATABASE_URL=postgresql://user:pass@localhost/finehero
   STRIPE_SECRET_KEY=sk_test_...
   GEMINI_API_KEY=...
   
   # Frontend (.env.local)
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
   ```

### SaaS Deployment

The system is designed as a full SaaS application with:
- User registration and authentication
- Payment processing and subscriptions
- Document upload and processing
- Professional letter generation
- User dashboard and case management

See `docs/frontend_integration_guide.md` for complete frontend setup.

## Roadmap

### Phase 1 – Portugal SaaS Launch (Current)
- ✅ **Backend Foundation**: Complete OCR, RAG, and defense generation
- ✅ **Database Models**: User accounts, fines, payments, subscriptions
- ✅ **API Structure**: FastAPI with authentication and payment endpoints
- 🎯 **Current Focus**: Frontend development + Stripe integration

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

- **`docs/saas_assessment_and_strategy.md`** - Complete SaaS business strategy and technical assessment
- **`docs/frontend_integration_guide.md`** - Detailed guide for React/Next.js frontend integration
- **`docs/portugal_mvp_strategy.md`** - Portugal market entry and user acquisition strategy
- **`docs/one_week_action_plan.md`** - Detailed implementation roadmap

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