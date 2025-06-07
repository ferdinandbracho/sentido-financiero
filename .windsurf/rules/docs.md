---
trigger: always_on
---


## 📋 Project Overview

StatementSense is a complete full-stack application that uses artificial intelligence to automatically categorize and analyze bank statement transactions. Upload PDF statements and get intelligent insights about your spending patterns using local AI processing.

## 🏗 Architecture

**Stack**: React + FastAPI + PostgreSQL + Ollama (Local LLM)

```
Frontend (React)     ←→     Backend (FastAPI)     ←→     Database (PostgreSQL)
                                     ↓
                             Ollama LLM Service
                           (Llama 3.2 1B Model)
```
## 🤖 AI Categorization System

**3-Tier Hybrid Classification**:

1. **Tier 1: Exact Keyword Matching** (80% of transactions, <1ms)
   ```python
   "OXXO ROMA" → "alimentacion" (Confidence: 1.0)
   "PEMEX 1234" → "gasolineras" (Confidence: 1.0)
   ```

2. **Tier 2: Pattern Recognition** (15% of transactions, ~1ms)
   ```python
   "REST BRAVA" → regex: r'\brest\b' → "alimentacion" (Confidence: 0.8)
   "DR MARTINEZ" → regex: r'\bdr\s+[a-z]+' → "salud" (Confidence: 0.8)
   ```

3. **Tier 3: LLM Analysis** (5% of transactions, 100-500ms)
   ```python
   "POINTMP*VONDYMEXICO" → Llama 3.2 1B → "servicios" (Confidence: 0.7)
   ```

**Supported Categories**: Alimentación, Gasolineras, Servicios, Salud, Transporte, Entretenimiento, Ropa, Educación, Transferencias, Seguros, Intereses/Comisiones, Otros

## 🔌 API Endpoints

### Core Endpoints
- `POST /api/v1/statements/upload` - Upload PDF statement
- `POST /api/v1/statements/{id}/process` - Process with AI
- `GET /api/v1/statements` - List all statements
- `GET /api/v1/statements/{id}` - Get statement details
- `GET /api/v1/statements/{id}/transactions` - Get transactions
- `GET /api/v1/statements/{id}/analysis` - Get spending analysis
- `PUT /api/v1/transactions/{id}` - Update transaction category
- `DELETE /api/v1/statements/{id}` - Delete statement

## 🛠 Tech Stack Details

### Frontend
- **React 18** with hooks and modern patterns
- **Vite** for fast development and builds
- **Tailwind CSS** for utility-first styling
- **React Router** for client-side routing
- **React Query** for server state management
- **Chart.js** for interactive data visualizations
- **React Dropzone** for file upload
- **Axios** for HTTP requests
- **Lucide React** for beautiful icons

### Backend
- **FastAPI** with async/await support
- **SQLAlchemy** for database ORM
- **Alemb