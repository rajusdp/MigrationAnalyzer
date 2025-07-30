# Slack-to-Teams Migration Estimator

Enterprise-grade, secure, and scalable web application for estimating Slack-to-Teams migration costs and effort.

## 🚀 Features

### Core Functionality
- **Two-step Form Process**: Customer Info → Technical Details → Review → Results
- **Real-time Validation**: Auto-save every 250ms, completeness gauge, conditional field rendering
- **Precise Cost Algorithms**: Based on message volume with $35,000 baseline + $6,500 per additional 3M messages
- **Interactive Results**: Cost breakdown charts, effort timeline, project plan tabs
- **PDF Generation**: Server-side rendering with Azure Blob Storage integration

### Role-Based Access
- **End User**: Submit forms, view results, download PDFs
- **Sales**: View all submissions, update status, add comments, manage leads
- **Admin**: User management, role assignments, audit logs, system monitoring

### Enterprise Security
- **Azure AD B2C Integration**: Single sign-on and multi-factor authentication
- **Role-Based Authorization**: Granular permissions and access control
- **Audit Logging**: Complete compliance trail for all user actions
- **OWASP Security Headers**: Rate limiting, CORS, CSP, and security best practices
- **Data Encryption**: At rest and in transit with Azure-managed keys

## 🏗️ Architecture

### Technology Stack
**Frontend**: Next.js 14, TailwindCSS, Redux Toolkit, React Hook Form, Zod, Recharts, MSAL React  
**Backend**: FastAPI, PostgreSQL, SQLAlchemy, Redis, Azure Blob Storage, Puppeteer  
**Infrastructure**: Azure App Service, PostgreSQL Flexible Server, Azure Front Door, Key Vault  
**DevOps**: GitHub Actions, Docker, Azure Developer CLI (azd)

### Repository Structure
```
/
├── frontend/                 # Next.js 14 application
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # Reusable UI components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API service layer
│   │   ├── store/           # Redux store and slices
│   │   ├── types/           # TypeScript definitions
│   │   └── utils/           # Utility functions
│   ├── Dockerfile
│   └── package.json
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/             # API routes and endpoints
│   │   ├── models/          # Database models and schemas
│   │   ├── services/        # Business logic services
│   │   └── utils/           # Configuration and utilities
│   ├── tests/               # Test suite
│   ├── Dockerfile
│   └── requirements.txt
├── infrastructure/           # Azure Bicep templates
│   ├── modules/             # Modular Bicep components
│   ├── main.bicep           # Main infrastructure template
│   └── main.parameters.json # Environment parameters
├── .github/
│   └── workflows/
│       └── ci-cd.yml        # CI/CD pipeline
├── docs/                     # Documentation
├── docker-compose.yml        # Local development
├── azure.yaml               # Azure Developer CLI config
├── .env.sample              # Environment variables template
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose**: For local development
- **Node.js 18+**: For frontend development
- **Python 3.11+**: For backend development
- **Azure CLI**: For cloud deployment
- **Azure Developer CLI (azd)**: For streamlined Azure deployment

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/migration-estimator.git
cd migration-estimator
```

2. **Set up environment variables**
```bash
cp .env.sample .env
# Edit .env with your configuration
```

3. **Start all services**
```bash
docker-compose up --build
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs

### Development Workflow

#### Frontend Development
```bash
cd frontend
npm install
npm run dev        # Start development server
npm run test       # Run tests
npm run lint       # Lint code
npm run type-check # TypeScript validation
```

#### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload  # Start development server
pytest                     # Run tests
black .                    # Format code
isort .                    # Sort imports
flake8 .                   # Lint code
```

## ☁️ Azure Deployment

### Using Azure Developer CLI (Recommended)

1. **Install Azure Developer CLI**
```bash
# Windows (via winget)
winget install microsoft.azd

# macOS (via Homebrew)
brew tap azure/azd && brew install azd

# Linux
curl -fsSL https://aka.ms/install-azd.sh | bash
```

2. **Initialize the project**
```bash
azd init
```

3. **Deploy to Azure**
```bash
azd up
```

This command will:
- Provision all Azure resources using Bicep templates
- Build and deploy both frontend and backend applications
- Configure environment variables and secrets
- Set up monitoring and logging

## 📊 Cost Estimation Algorithms

### Base Pricing
- **First 3 million messages**: $35,000 (8 weeks)
- **Each additional 3M messages**: +$6,500 (+1 week)

### Calculation Logic
```python
def calculate_cost(message_volume):
    base_cost = 35000
    if message_volume <= 3_000_000:
        return base_cost
    
    excess = message_volume - 3_000_000
    additional_tiers = math.ceil(excess / 3_000_000)
    return base_cost + (additional_tiers * 6500)
```

### Add-on Services (per week)
- **Hypercare Support**: $4,000/week
- **Adoption & Change Management**: $2,000/week
- **Application Integration Development**: $4,000/week

## 🛠️ Local Development

```bash
docker-compose up --build
```

## 📚 API Documentation

- **OpenAPI Specification**: `/api/docs` (Swagger UI)
- **ReDoc Documentation**: `/api/redoc`
- **Schema Downloads**: `/api/openapi.json`

---

**Built with ❤️ using Azure, Next.js, and FastAPI**
