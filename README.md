# RCA Analysis Chatbot for Derivatives Processing

An AI-powered chatbot that performs automated Root Cause Analysis for failures and delays in derivatives batch job processing. The system monitors a strict 3-hour SLA and identifies infrastructure bottlenecks across AWS services.

## Features

- **Intelligent RCA Analysis**: Automatically identifies root causes for processing delays and failures
- **Real-time Timeline Visualization**: Interactive timeline showing cascade of events
- **Infrastructure Monitoring**: Analyzes metrics from AWS RDS, EKS, and SQS
- **SLA Tracking**: Monitors 3-hour processing SLA with breach detection
- **Natural Language Interface**: Chat-based interaction powered by Azure OpenAI
- **Professional UI**: Modern, sleek design with dark/light mode support

## Architecture

```
Frontend (React + TypeScript + Material-UI)
    ↓
Backend (Flask + Python)
    ↓
Azure OpenAI API + Local Metric Processing
```

## Prerequisites

- Python 3.8+
- Node.js 16+
- Azure OpenAI API credentials

## Quick Start

### 1. Clone and Setup

```bash
# Run the setup script
./setup.sh
```

### 2. Configure Azure OpenAI

The system supports two authentication methods:

#### Option A: Certificate-based Authentication (Recommended for Production)

1. Place your certificate file in `backend/cert/apim-exp.pem`
2. Edit `backend/.env`:

```env
AUTH_METHOD=certificate
AZURE_SPN_CLIENT_ID=your_service_principal_client_id
AZURE_TENANT_ID=your_tenant_id  
AZURE_CERT_PATH=cert/apim-exp.pem
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-2024-08-06
USER_SID=1792420  # Optional
```

#### Option B: API Key Authentication (Simple Setup)

Edit `backend/.env`:

```env
AUTH_METHOD=api_key
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### 3. Start the Application

```bash
# Terminal 1: Start backend
./run-backend.sh

# Terminal 2: Start frontend
./run-frontend.sh
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## Project Structure

```
RCA_TOOL/
├── backend/
│   ├── app.py                 # Flask application
│   ├── services/
│   │   ├── metric_loader.py   # Loads and parses metrics
│   │   ├── rca_analyzer.py    # Core RCA analysis logic
│   │   └── azure_ai_service.py # Azure OpenAI integration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── Timeline.tsx
│   │   │   └── MetricsPanel.tsx
│   │   ├── services/          # API services
│   │   └── types/             # TypeScript types
│   └── package.json
└── metrics/                    # Sample data files
    ├── markerEvent/
    ├── dagDetails/
    ├── eksMetrics/
    ├── sqsMetrics/
    └── rdsMetrics/
```

## Key Features

### 1. Intelligent Analysis
- Preprocesses metrics locally before sending to Azure OpenAI
- Identifies threshold breaches and correlates failures
- Creates concise summaries focusing on critical issues

### 2. Timeline Visualization
- Chronological event display with severity indicators
- Shows cascade effects from root cause to final impact
- Color-coded by severity (critical, warning, info)

### 3. Metrics Dashboard
- Real-time SLA status tracking
- Infrastructure health monitoring
- Root cause contribution analysis

### 4. Chat Interface
- Natural language queries
- Suggested query chips
- Markdown-formatted responses
- Typing indicators

## Sample Queries

- "Why did derivatives processing fail on August 1st?"
- "What caused the SLA breach for derivatives today?"
- "Show me the RCA timeline for derivatives processing"
- "Analyze the derivatives delay on August 1st"

## Threshold Configuration

### EKS Metrics
- CPU: Warning at 80%, Critical at 90%
- Memory: Warning at 80%, Critical at 90%
- Pod Restarts: Warning at 5, Critical at 10

### RDS Metrics
- CPU: Warning at 90%, Critical at 95%
- Connections: Warning at 200, Critical at 250
- Commit Latency: Warning at 25ms, Critical at 50ms

### SQS Metrics
- Message Age: Warning at 300s, Critical at 600s
- Visible Messages: Warning at 500, Critical at 1000

## API Endpoints

- `POST /api/chat` - Process chat messages
- `GET /api/health` - Health check
- `GET /api/metrics/{date}` - Get metrics for a date
- `GET /api/available-dates` - List available dates

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate
python app.py
```

### Frontend Development
```bash
cd frontend
npm start
```

### Testing
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## Troubleshooting

1. **Backend not connecting**: Ensure Flask is running on port 5000
2. **Azure OpenAI errors**: Verify credentials in `.env` file
3. **Missing metrics**: Check that metric JSON files exist in correct folders
4. **CORS issues**: Frontend proxy is configured for localhost:5000

## Future Enhancements

- Export RCA reports to PDF
- Historical trend analysis
- Predictive failure detection
- Multi-date comparison
- Real-time metric streaming
- Slack/Teams integration

## License

MIT

## Support

For issues or questions, please create an issue in the repository.