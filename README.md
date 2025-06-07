# 🚀 StatementSense - AI-Powered Bank Statement Analyzer

A modern, full-stack application that uses artificial intelligence to automatically categorize and analyze bank statement transactions. Upload PDF statements and get intelligent insights about your spending patterns.

![StatementSense Demo](https://via.placeholder.com/800x400/3B82F6/FFFFFF?text=StatementSense+Demo)

## ✨ Features

### 🤖 **Smart AI Categorization**
- **Hybrid Classification**: Combines exact matching, pattern recognition, and LLM intelligence
- **Local LLM**: Uses Llama 3.2 1B model running locally via Ollama
- **Multi-Bank Support**: Works with Mexican bank statements (BBVA, Banamex, Santander, etc.)
- **Learning System**: Improves accuracy over time

### 📊 **Comprehensive Analysis**
- **Spending Insights**: Detailed breakdown by categories
- **Interactive Charts**: Beautiful visualizations with Chart.js
- **Transaction Management**: Edit categories and add notes
- **Export Data**: Download analyses and reports

### 🎨 **Modern Interface**
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Real-time Updates**: Live processing status and notifications
- **Drag & Drop Upload**: Intuitive file upload experience
- **Dark/Light Themes**: Comfortable viewing in any environment

### 🔒 **Privacy & Security**
- **Local Processing**: All data stays on your machine
- **No External APIs**: Bank data never leaves your infrastructure
- **Secure Storage**: Encrypted file handling and secure database

## 🏗 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │  PostgreSQL DB  │
│                 │    │                 │    │                 │
│  • File Upload  │◄──►│  • PDF Parser   │◄──►│  • Statements   │
│  • Charts       │    │  • AI Categorizer│    │  • Transactions │
│  • Transaction  │    │  • Analysis     │    │  • Categories   │
│    Management   │    │  • REST API     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Ollama LLM    │
                       │                 │
                       │ • Llama 3.2 1B  │
                       │ • Local Inference│
                       │ • Smart Categoriz│
                       └─────────────────┘
```

## 🚀 Quick Start

### Option 1: Docker Development (Recommended)

```bash
git clone <repository-url>
cd statement-sense

# Start development environment (includes hot reload)
make docker-dev
# OR
docker-compose up --build

# Download AI model (in another terminal)
docker-compose exec ollama ollama pull llama3.2:1b
```

### Option 2: Docker Production

```bash
# Clone and enter directory
git clone <repository-url>
cd statement-sense

# Start production environment
make docker-prod
# OR
docker-compose -f docker-compose.yml up --build
```

### Option 3: Local Development

```bash
# Copy environment file
cp .env.local .env

# Backend setup
python -m venv .venv
source .venv/bin/activate
pip install uv
uv pip install -e ".[dev]"

# Start local database (or use Docker only for db)
docker-compose -f docker-compose.dev.yml up postgres ollama

# Run backend
make run
# OR
uvicorn app.main:app --reload

# Frontend setup (in another terminal)
cd frontend
npm install
npm run dev
```

### Option 4: One-Command Setup

```bash
git clone <repository-url>
cd statement-sense
./setup.sh
```

The setup script will:
1. Check system requirements
2. Set up Docker services
3. Download AI models
4. Initialize the database
5. Start all services

## 📋 Requirements

### System Requirements
- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for development)
- **Node.js 18+** (for frontend development)
- **PostgreSQL 15+** (if running locally)

### Hardware Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 5GB for Docker images and models
- **CPU**: Multi-core recommended for AI processing

## 🔧 Configuration

### Environment Files

The project supports multiple environment configurations:

- **`.env`** - Default (Docker development)
- **`.env.local`** - Local development (no Docker)
- **`.env.docker`** - Docker development (explicit)
- **`.env.production`** - Production environment

#### Backend Environment Variables

```env
# Database Configuration
DB_HOST=postgres          # Use 'localhost' for local dev
DB_PORT=5432
DB_USER=statement_user
DB_PASS=statement_password
DB_NAME=statement_sense

# AI Service
OLLAMA_URL=http://ollama:11434  # Use 'http://localhost:11434' for local

# Application Settings
PROJECT_NAME=StatementSense
LOG_LEVEL=INFO
DEBUG=true
UPLOAD_DIR=/app/uploads    # Use './uploads' for local dev
```

#### Frontend Environment Variables

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=StatementSense
VITE_APP_DESCRIPTION=AI-Powered Bank Statement Analyzer
```

### Deployment Modes

#### Development Mode (with hot reload)
```bash
# Uses docker-compose.yml + docker-compose.override.yml automatically
docker-compose up
# OR
make docker-dev
```

#### Production Mode
```bash
# Uses only docker-compose.yml (no overrides)
docker-compose -f docker-compose.yml up
# OR  
make docker-prod
```

#### Services-only Mode (for local development)
```bash
# Only start database and AI services
docker-compose -f docker-compose.dev.yml up
```

## 📚 Usage Guide

### 1. Upload Statement
1. Navigate to **Upload** page
2. Drag & drop PDF file or click to select
3. Wait for upload confirmation
4. Click "Process" to analyze

### 2. View Analysis
1. Go to **Statements** page
2. Click on processed statement
3. Explore different tabs:
   - **Overview**: Charts and summaries
   - **Transactions**: Detailed transaction list
   - **Analysis**: In-depth spending analysis

### 3. Manage Categories
1. Click on any transaction
2. Edit category if needed
3. Add notes for future reference
4. Export data for external use

## 🧠 AI Categorization How It Works

### 3-Tier Classification System

```python
# Tier 1: Exact Keyword Matching (Fastest)
"OXXO ROMA" → "alimentacion" (Confidence: 1.0)

# Tier 2: Pattern Recognition (Fast + Smart)
"REST BRAVA" → regex: r'\brest\b' → "alimentacion" (Confidence: 0.8)

# Tier 3: LLM Analysis (Smart + Context-Aware)
"POINTMP*VONDYMEXICO" → LLM → "servicios" (Confidence: 0.7)
```

### Performance Stats
- **80%** of transactions classified by Tiers 1-2 (< 1ms)
- **15%** require LLM analysis (~100-500ms)
- **5%** fall back to "otros" category

### Supported Categories
- 🍽️ **Alimentación** - Restaurants, groceries, convenience stores
- ⛽ **Gasolineras** - Gas stations, fuel
- 🔧 **Servicios** - Utilities, subscriptions, streaming
- 🏥 **Salud** - Healthcare, pharmacies, medical
- 🚗 **Transporte** - Uber, taxi, parking, public transport
- 🎬 **Entretenimiento** - Movies, bars, entertainment
- 👕 **Ropa** - Clothing, fashion, department stores
- 📚 **Educación** - Schools, books, courses
- 💸 **Transferencias** - Bank transfers, payments
- 🛡️ **Seguros** - Insurance, policies
- 📊 **Intereses/Comisiones** - Bank fees, interest
- 📋 **Otros** - Miscellaneous

## 🔌 API Documentation

### Core Endpoints

#### Statements
- `POST /api/v1/statements/upload` - Upload PDF file
- `GET /api/v1/statements` - List all statements
- `GET /api/v1/statements/{id}` - Get statement details
- `POST /api/v1/statements/{id}/process` - Process statement
- `DELETE /api/v1/statements/{id}` - Delete statement

#### Transactions
- `GET /api/v1/statements/{id}/transactions` - Get transactions
- `PUT /api/v1/transactions/{id}` - Update transaction
- `DELETE /api/v1/transactions/{id}` - Delete transaction

#### Analysis
- `GET /api/v1/statements/{id}/analysis` - Get spending analysis

### Example Request
```bash
# Upload a statement
curl -X POST "http://localhost:8000/api/v1/statements/upload" \
     -F "file=@statement.pdf"

# Get analysis
curl "http://localhost:8000/api/v1/statements/{id}/analysis"
```

Full API documentation available at: `http://localhost:8000/docs`

## 🛠 Development

### Project Structure
```
statement-sense/
├── app/                    # FastAPI Backend
│   ├── api/               # API routes
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   │   ├── pdf_parser.py  # PDF processing
│   │   └── smart_categorizer.py # AI categorization
│   └── main.py           # FastAPI app
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom hooks
│   │   ├── services/      # API services
│   │   └── utils/         # Utilities
│   └── package.json
├── migrations/            # Database migrations
├── docker-compose.yml     # Docker services
├── setup.sh              # Setup script
└── README.md
```

### Adding New Features

#### Backend
1. Add model in `app/models/`
2. Create schema in `app/schemas/`
3. Add API endpoint in `app/api/`
4. Generate migration: `alembic revision --autogenerate`

#### Frontend
1. Create component in `src/components/`
2. Add route in `src/App.jsx`
3. Create API service in `src/services/`
4. Add hook in `src/hooks/`

### Running Tests
```bash
# Backend tests
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | React development server |
| Backend | 8000 | FastAPI application |
| Database | 5432 | PostgreSQL database |
| Ollama | 11434 | LLM inference server |

### Docker Commands
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Restart service
docker-compose restart [service-name]

# Stop all services
docker-compose down

# Rebuild and start
docker-compose up --build
```

## 🔍 Troubleshooting

### Common Issues

#### Upload Fails
- Check file is PDF format
- Ensure file size < 50MB
- Verify backend is running

#### Processing Stuck
- Check Ollama service status
- Restart Ollama: `docker-compose restart ollama`
- Download model: `docker-compose exec ollama ollama pull llama3.2:1b`

#### Database Errors
- Check PostgreSQL is running
- Run migrations: `alembic upgrade head`
- Reset database: `python init_db.py`

#### Frontend Issues
- Clear browser cache
- Check console for errors
- Restart frontend: `docker-compose restart frontend`

### Logs and Debugging
```bash
# View all logs
docker-compose logs -f

# Backend logs only
docker-compose logs -f backend

# Database logs
docker-compose logs -f postgres

# Check service status
docker-compose ps
```

## 🚀 Production Deployment

### Environment Setup
1. Use production database (not SQLite)
2. Set secure environment variables
3. Enable HTTPS
4. Configure proper CORS settings
5. Set up monitoring and logging

### Docker Production
```bash
# Production compose file
docker-compose -f docker-compose.prod.yml up -d

# With SSL termination
docker-compose -f docker-compose.prod.yml -f docker-compose.ssl.yml up -d
```

### Performance Optimization
- Enable PostgreSQL connection pooling
- Use Redis for caching
- Configure CDN for static assets
- Optimize Docker images
- Set up load balancing

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use Prettier for JavaScript formatting
- Write tests for new features
- Update documentation
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** - Local LLM inference
- **Meta** - Llama 3.2 model
- **FastAPI** - Modern Python web framework
- **React** - Frontend framework
- **Tailwind CSS** - Utility-first CSS
- **Chart.js** - Data visualization
- **PostgreSQL** - Database system

## 📞 Support

- **Documentation**: Check the `/docs` endpoints
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Email**: [contact@statementsense.com](mailto:contact@statementsense.com)

---

<div align="center">

**Built with ❤️ for better financial insights**

[⭐ Star this repo](https://github.com/your-username/statement-sense) • [🐛 Report Bug](https://github.com/your-username/statement-sense/issues) • [💡 Request Feature](https://github.com/your-username/statement-sense/issues)

</div>