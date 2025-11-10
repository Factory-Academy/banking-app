# Transaction Monitoring System

A banking transaction monitoring and fraud detection system designed to showcase Factory Droid capabilities across various software engineering scenarios.

![CI Status](https://github.com/yourusername/finance-research-app/workflows/CI%20Pipeline/badge.svg)

## 🎯 Purpose

This application demonstrates how Factory Droids can assist with:

- **Codebase Research**: Understanding complex systems
- **Feature Development**: Adding new functionality end-to-end
- **Test Implementation**: Writing comprehensive test suites
- **Code Review Automation**: Setting up CI/CD pipelines
- **Incident Response**: Debugging and fixing production issues

## 📋 Overview

### The Scenario

You're a fraud analyst at a major bank. Transactions flagged as high-risk by our automated system are **held** (frozen) and placed in your review queue. Your job is to review each one and decide:

- ✅ **Approve & Release** - Legitimate transaction, process it
- ❌ **Reject & Block** - Confirmed fraud, cancel it
- ⬆️ **Escalate** - Needs senior review

### Fraud Detection Rules

The system automatically analyzes transactions using 6 rules:

1. **High Amount Rule** (30 points): Transactions over $10,000
2. **Velocity Rule** (40 points): More than 5 transactions in 1 hour
3. **Geographic Anomaly Rule** (50 points): Different country within 4 hours
4. **Unusual Time Rule** (20 points): Transactions between 2-5 AM
5. **First International Rule** (25 points): First international transaction
6. **Amount Deviation Rule** (35 points): Amount >3x account average

**Risk Scoring:**
- **LOW** (<40 points): Auto-approved, cleared immediately
- **MEDIUM** (40-69 points): Logged for review, but cleared
- **HIGH** (≥70 points): **Auto-held**, requires analyst approval

## 🚀 Quick Start

### Prerequisites

- Python 3.10+ (3.14 recommended)
- Node.js 18+ (20 recommended)  
- Git

### Installation

**1. Clone the repository:**
```bash
git clone <repository-url>
cd finance-research-app
```

**2. Backend setup:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

**3. Start the backend:**
```bash
uvicorn app.main:app --reload
```

**4. Seed the database (in a new terminal):**
```bash
# The seed script sends transactions via API (backend must be running)
python -m app.utils.seed_data
```

**5. Frontend setup (new terminal):**
```bash
cd frontend
npm install
npm run dev
```

**6. Open the app:**

Navigate to **http://localhost:5173**

You should see 12-15 transactions in the "Held Transactions" queue ready for review!

## 📖 Documentation

- **[Demo Guide](docs/demo.md)**: Complete walkthrough with 6 testing scenarios for Factory Droids
- **[Architecture](docs/architecture.md)**: Technical architecture and design decisions
- **[API Documentation](docs/api.md)**: REST API endpoints and schemas

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest --cov=app --cov-report=term
```

Coverage target: **>80%**

### Frontend Tests

```bash
cd frontend
npm test
```

Coverage target: **>70%**

### Run All Quality Checks

**Backend:**
```bash
cd backend
ruff check .                    # Linting
mypy app --ignore-missing-imports  # Type checking
pytest --cov=app --cov-fail-under=80  # Tests
bandit -r app                   # Security scan
```

**Frontend:**
```bash
cd frontend
npm run lint                    # ESLint
npm run type-check              # TypeScript
npm run build                   # Build check
```

## 🏗️ Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- SQLite (database)
- Pydantic (validation)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- React Query (data fetching)
- React Router (navigation)

**Testing:**
- pytest, pytest-cov (backend)
- vitest (frontend)

**Code Quality:**
- Ruff, mypy (Python)
- ESLint, TypeScript (frontend)
- Bandit (security)

## 📁 Project Structure

```
finance-research-app/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app
│   │   ├── database.py             # DB setup
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── routes/                 # API endpoints
│   │   ├── services/               # Business logic
│   │   │   └── fraud_detection.py  # Fraud rules
│   │   └── utils/
│   │       └── seed_data.py        # Mock data generator
│   ├── tests/                      # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/             # React components
│   │   ├── pages/                  # Page components
│   │   ├── hooks/                  # React Query hooks
│   │   ├── api/                    # API client
│   │   └── types/                  # TypeScript types
│   └── package.json
├── docs/
│   ├── demo.md                     # Demo guide
│   ├── architecture.md             # Architecture docs
│   └── api.md                      # API documentation
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions
└── README.md
```

## 🎓 Demo Scenarios

The [demo.md](docs/demo.md) file includes 6 comprehensive scenarios:

1. **Codebase Research** (15 min): Understand the fraud detection system
2. **Add Feature - Merchant Blacklist** (30 min): Implement new functionality
3. **Implement Tests** (20 min): Achieve >90% test coverage
4. **Code Review Automation** (25 min): Set up GitHub Actions
5. **Incident Response - DB Connection** (20 min): Fix timeout issues
6. **Incident Response - Null Bug** (15 min): Debug crashes

**Total time: ~2 hours**

Each scenario tests different Factory Droid capabilities in a realistic banking context.

## 🤖 Using with Factory Droids

This project is designed for testing Factory Droids.

Ask the droid to:
- Explain how fraud detection works
- Add a new fraud rule
- Write tests for edge cases
- Debug production issues
- Set up CI/CD pipelines
- Add new features

See [demo.md](docs/demo.md) for detailed scenarios and prompts.

## 🔒 Security Notes

This is a **demo application** for testing purposes. Do not use in production without:

- Adding authentication/authorization
- Using environment variables for secrets
- Implementing rate limiting
- Adding input sanitization
- Using a production database (PostgreSQL)
- Setting up proper monitoring/logging
- Conducting security audit

## 🐛 Known Limitations

- Uses SQLite (not suitable for production)
- No authentication system
- Mock data only
- Simplified fraud detection (real systems use ML)
- No rate limiting
- No real-time notifications

## 📊 Database Schema

**Transaction Model:**
```sql
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    account_number TEXT NOT NULL,
    account_holder_name TEXT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    merchant_name TEXT NOT NULL,
    merchant_category TEXT,
    transaction_type TEXT,
    location_city TEXT,
    location_country TEXT,
    latitude FLOAT,
    longitude FLOAT,
    timestamp DATETIME NOT NULL,
    status TEXT NOT NULL,  -- CLEARED, HELD, APPROVED, REJECTED, ESCALATED
    risk_level TEXT NOT NULL,  -- LOW, MEDIUM, HIGH
    risk_score INTEGER DEFAULT 0,
    fraud_flags JSON,
    reviewed_by TEXT,
    reviewed_at DATETIME,
    review_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);
```

## 🛣️ API Endpoints

### Transactions

- `POST /api/v1/transactions` - **NEW!** Create transaction with real-time fraud detection
- `GET /api/v1/transactions` - List transactions with filters (supports pagination & search)
- `GET /api/v1/transactions/{id}` - Get single transaction
- `GET /api/v1/transactions/{id}/history` - Get account history
- `POST /api/v1/transactions/{id}/review` - Review a transaction

### Stats

- `GET /api/v1/stats/dashboard` - Get dashboard statistics

See [api.md](docs/api.md) for detailed endpoint documentation.

## 🤝 Contributing

This is a demo project for Factory Droid testing. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📝 License

MIT License - feel free to use this for learning and demos.

## 🙏 Acknowledgments

Built to demonstrate Factory Droid capabilities for financial institutions.

## 📞 Support

For questions or issues:
- Open a GitHub issue
- Check the [demo.md](docs/demo.md) troubleshooting section
- Review [architecture.md](docs/architecture.md) for technical details

---

**Ready to test Factory Droids?** Start with the [Demo Guide](docs/demo.md)!
