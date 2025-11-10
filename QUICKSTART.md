# Quick Start Guide

## 5-Minute Setup

### Prerequisites
- Python 3.11-3.13 (3.14 works but has some compatibility issues)
- Node.js 18+

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Start Backend

```bash
uvicorn app.main:app --reload
```

### Seed Database (New Terminal)

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python -m app.utils.seed_data
```

**Note:** Backend must be running before seeding!

Backend will run at **http://localhost:8000**

### Frontend Setup (New Terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at **http://localhost:5173**

### Open the App

Navigate to **http://localhost:5173** in your browser.

You should see:
- ✅ Dashboard with stats
- ✅ 10-15 transactions in "Held" queue
- ✅ Alert banner at top

## Next Steps

1. **Review a transaction** - Click "Review Transaction" on any held item
2. **Make a decision** - Approve, Reject, or Escalate
3. **Check the demo guide** - See `docs/demo.md` for 6 Factory Droid scenarios

## Common Issues

**Port already in use?**
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

**Database not seeded?**
```bash
cd backend
python -m app.utils.seed_data
```

**Frontend won't start?**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Documentation

- 📖 [Full Demo Guide](docs/demo.md) - 6 Factory Droid testing scenarios
- 🏗️ [Architecture](docs/architecture.md) - Technical details
- 📚 [API Documentation](docs/api.md) - REST API endpoints
- 📝 [README](README.md) - Complete project overview
