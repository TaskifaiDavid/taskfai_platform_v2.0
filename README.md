# TaskifAI - Sales Data Analytics Platform

A comprehensive sales data analytics platform that ingests, cleans, normalizes, and analyzes multi-channel sales data from various reseller partners, powered by AI-driven insights.

## 🎯 Features

- **Multi-Vendor Data Ingestion**: Automatic format detection and processing for 9+ vendor formats
- **AI-Powered Chat**: Natural language querying using OpenAI GPT-4 + LangChain
- **Multi-Channel Analytics**: Unified view of offline (B2B) and online (D2C) sales
- **External Dashboard Integration**: Embed dashboards from Looker, Tableau, Power BI, etc.
- **Email Notifications**: Automated upload status and scheduled reports
- **Row-Level Security**: User data isolation via Supabase RLS

## 🏗️ Architecture

```
Frontend (React 19 + Vite 6 + TypeScript)
    ↕ HTTPS/JSON
Backend (FastAPI + Python 3.11)
    ↕
Background Worker (Celery + Redis)
    ↕
Database (Supabase PostgreSQL 17)
```

## 📚 Complete Documentation

**Choose your guide based on your needs:**

| I want to... | Read this guide |
|--------------|-----------------|
| **Understand what TaskifAI does and how it works** | [Platform Guide](claudedocs/PLATFORM_GUIDE.md) - Complete overview of the platform, features, and architecture |
| **Use TaskifAI as an analyst or manager** | [User Guide](claudedocs/USER_GUIDE.md) - How to upload files, create dashboards, and use AI chat |
| **Develop features or add vendor processors** | [Developer Guide](claudedocs/DEVELOPER_GUIDE.md) - Development workflows, patterns, and best practices |
| **Understand multi-tenant architecture** | [Architecture Clarity](claudedocs/architecture_clarity.md) - Multi-tenant design decisions and rationale |
| **Add a new vendor processor** | [Adding Vendor Processors](claudedocs/adding_vendor_processors.md) - Step-by-step guide |
| **Review recent refactoring** | [Refactoring Summary](claudedocs/refactoring_summary.md) - DRY refactoring details and impact |

**Technical Documentation**:
- [System Architecture](docs/architecture/SYSTEM_OVERVIEW.md) - Detailed technical architecture
- [API Reference](docs/api/README.md) - Complete REST API documentation
- [Data Model](docs/architecture/04_Data_Model.md) - Database schema and relationships

## 📋 Prerequisites

- **Node.js** 20+ (for frontend)
- **Python** 3.11+ (for backend)
- **Docker** & Docker Compose (recommended for local development)
- **Supabase Account** (or local PostgreSQL 17)
- **OpenAI API Key** (for AI chat features)
- **SendGrid Account** (for email notifications)

## 🚀 Quick Start with Docker

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd TaskifAI_platform_v2.0
```

### 2. Set Up Environment Variables

**Backend:**
```bash
cd backend
cp .env.example .env
# Edit .env with your actual credentials
```

**Frontend:**
```bash
cd ../frontend
cp .env.example .env
# Edit .env if needed
```

### 3. Start All Services

```bash
cd ..
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- Celery worker (background tasks)
- Frontend app (port 3000)

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

## 💻 Manual Setup (Without Docker)

### Backend Setup

1. **Create Virtual Environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set Up Environment Variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Set Up Database:**
```bash
# If using local PostgreSQL:
psql -U postgres -d taskifai -f db/schema.sql

# If using Supabase:
# Copy contents of db/schema.sql to Supabase SQL Editor and run
```

5. **Start Backend Server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Start Celery Worker (in new terminal):**
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

### Frontend Setup

1. **Install Dependencies:**
```bash
cd frontend
npm install
```

2. **Set Up Environment Variables:**
```bash
cp .env.example .env
# Edit .env if needed
```

3. **Start Development Server:**
```bash
npm run dev
```

## 🗄️ Database Setup

### Option 1: Supabase (Recommended)

1. Create a new Supabase project at https://supabase.com
2. Go to **SQL Editor**
3. Copy and paste the contents of `backend/db/schema.sql`
4. Run the SQL script
5. Copy your **Project URL** and **Anon Key** to `backend/.env`

### Option 2: Local PostgreSQL

1. Install PostgreSQL 17
2. Create database:
```bash
createdb taskifai
```
3. Run schema:
```bash
psql -U postgres -d taskifai -f backend/db/schema.sql
```

## 🔑 Environment Variables

### Backend Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key (min 32 chars) | `your-super-secret-key` |
| `SUPABASE_URL` | Supabase project URL | `https://xyz.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase anon public key | `eyJhbG...` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | `eyJhbG...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `SENDGRID_API_KEY` | SendGrid API key | `SG....` |
| `SENDGRID_FROM_EMAIL` | Sender email address | `noreply@company.com` |

### Frontend Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000/api` |

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📦 Project Structure

```
TaskifAI_platform_v2.0/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # Config, security, dependencies
│   │   ├── models/           # Pydantic models
│   │   ├── db/               # Database models & migrations
│   │   ├── services/         # Business logic
│   │   │   ├── vendors/      # Vendor-specific processors
│   │   │   ├── ai_chat/      # LangChain agents
│   │   │   └── email/        # Email service
│   │   └── workers/          # Celery tasks
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom hooks
│   │   ├── lib/              # Utilities
│   │   ├── stores/           # Zustand stores
│   │   └── api/              # API client
│   ├── package.json
│   └── Dockerfile
├── Project_docs/             # Comprehensive documentation
├── docker-compose.yml
└── README.md
```

## 🔐 Security

- JWT-based authentication
- Row Level Security (RLS) for user data isolation
- SQL injection prevention in AI chat
- Password hashing with bcrypt
- HTTPS enforced in production
- Encrypted sensitive dashboard credentials

## 🚢 Deployment

### Production Deployment Options

1. **Vercel (Frontend) + Railway (Backend)** - Recommended for MVP
2. **Render** - All-in-one platform
3. **AWS** - Maximum scalability (ECS + RDS + S3 + CloudFront)

See `Project_docs/12_Technology_Stack_Recommendations.md` for detailed deployment guides.

## 📖 Documentation

Comprehensive documentation is available in the `Project_docs/` directory:

- **[01_System_Overview.md](Project_docs/01_System_Overview.md)** - System purpose and features
- **[02_Architecture.md](Project_docs/02_Architecture.md)** - Technical architecture
- **[04_Data_Model.md](Project_docs/04_Data_Model.md)** - Database schema
- **[05_Data_Processing_Pipeline.md](Project_docs/05_Data_Processing_Pipeline.md)** - Vendor processing
- **[07_AI_Chat_System.md](Project_docs/07_AI_Chat_System.md)** - AI chat implementation
- **[10_Security_Architecture.md](Project_docs/10_Security_Architecture.md)** - Security patterns
- **[11_Customer_Detail_Views.md](Project_docs/11_Customer_Detail_Views.md)** - User guide
- **[12_Technology_Stack_Recommendations.md](Project_docs/12_Technology_Stack_Recommendations.md)** - Tech stack details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

[Your License Here]

## 🆘 Support

For issues and questions:
- Check the [documentation](Project_docs/)
- Open an issue on GitHub
- Contact: your-email@company.com

---

**Built with:** React 19, FastAPI, Supabase, OpenAI GPT-4, LangChain, Tailwind CSS v4
