# RCA (Root Cause Analysis) Chatbot for Derivatives Processing

## Project Overview
Build an AI-powered chatbot that performs automated Root Cause Analysis for failures or delays in derivatives batch job processing. The system monitors a strict 3-hour SLA from marker event arrival to completion and identifies infrastructure bottlenecks across AWS services (RDS, EKS, SQS).

## Technical Stack
- **Frontend**: React with modern AI chatbot UI design principles
- **Backend**: Flask (Python)
- **AI Service**: Azure OpenAI API
- **Infrastructure Monitored**: AWS RDS, EKS, SQS
- **Data Format**: JSON metrics stored locally

## Architecture

### System Components
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  Flask Backend   │────▶│ Azure OpenAI    │
│    (Chatbot UI) │◀────│  (RCA Engine)    │◀────│     API         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Local Metric Files │
                    │  ├── markerEvent/    │
                    │  ├── dagDetails/     │
                    │  ├── eksMetrics/     │
                    │  ├── sqsMetrics/     │
                    │  └── rdsMetrics/     │
                    └──────────────────────┘
```

## Data Structure

### Directory Structure
```
/metrics
  /markerEvent
    └── 2025-08-01_marker_event.json
  /dagDetails
    └── 2025-08-01_dag_metrics.json
  /eksMetrics
    └── 2025-08-01_eks_metrics.json
  /sqsMetrics
    └── 2025-08-01_sqs_metrics.json
  /rdsMetrics
    └── 2025-08-01_rds_metrics.json
```

### File Naming Convention
- Pattern: `YYYY-MM-DD_<metric_type>.json`
- Example: `2025-08-01_marker_event.json`

## Business Logic

### SLA Definition
- **Trigger**: Marker event arrival (from `markerEvent` JSON)
- **SLA Duration**: 3 hours maximum for complete derivatives processing
- **Completion**: Last DAG execution end time (from `dagDetails` JSON)

### RCA Decision Flow
```
1. Check Marker Event
   └── Extract actual_arrival_time
   
2. Check DAG Processing
   ├── Find first DAG start_date for derivatives
   └── Find last DAG end_date for derivatives
   
3. Calculate Processing Duration
   └── If duration > 3 hours → SLA BREACH
   
4. If SLA Breached:
   ├── Analyze EKS metrics during processing window
   ├── Analyze RDS metrics during processing window
   └── Analyze SQS metrics during processing window
   
5. Generate Root Cause Analysis
   └── Create timeline with cascading failure pattern
```

## Metric Thresholds (Auto-detected from JSON)

### EKS Metrics
- **CPU Utilization**: Warning at 80%, Critical at 90%
- **Memory Utilization**: Warning at 80%, Critical at 90%
- **Pod Restarts**: Warning at 5, Critical at 10
- **DAG Processing Time**: Warning at 30s, Critical at 60s

### RDS Metrics
- **CPU Utilization**: Warning at 90%, Critical at 95%
- **Database Connections**: Warning at 200, Critical at 250
- **Commit Latency**: Warning at 25ms, Critical at 50ms
- **Select Latency**: Warning at 50ms, Critical at 100ms

### SQS Metrics
- **Message Age**: Warning at 300s, Critical at 600s
- **Visible Messages**: Warning at 500, Critical at 1000
- **Messages Received**: Warning at 1800, Critical at 4500

## API Configuration

### Azure OpenAI Credentials (Environment Variables)
```env
AZURE_OPENAI_API_KEY=<your_key>
AZURE_OPENAI_ENDPOINT=<your_endpoint>
AZURE_OPENAI_API_VERSION=<api_version>
AZURE_TENANT_ID=<tenant_id>
AZURE_SPN_CLIENT_ID=<client_id>
AZURE_OPENAI_DEPLOYMENT=<deployment_name>  # e.g., gpt-4
```

## Frontend Requirements

### React Chatbot UI Features
1. **Modern AI Chat Interface**
   - Message bubbles with user/AI distinction
   - Typing indicators
   - Timestamp display
   - Dark/Light mode support
   - Smooth animations and transitions

2. **Interactive Elements**
   - Query input with auto-suggestions
   - Date picker for historical analysis
   - Collapsible timeline view
   - Metric charts and visualizations

3. **Visualization Components**
   - Timeline chart showing cascading failures
   - Metric graphs (line/area charts) for:
     - CPU/Memory utilization
     - Database latency
     - Queue depth
   - Color-coded severity indicators

### Sample User Queries
- "Why did derivatives processing fail on August 1st?"
- "What caused the SLA breach for derivatives today?"
- "Show me the RCA for derivatives processing on 2025-08-01"
- "Analyze the derivatives delay on August 1st"

## Backend Requirements

### Flask API Endpoints

```python
# Main endpoints
POST /api/chat
  - Body: { "query": "user question", "date": "2025-08-01" }
  - Response: { "analysis": "...", "timeline": [...], "charts": [...] }

GET /api/metrics/{date}
  - Returns all metrics for a specific date

GET /api/health
  - Health check endpoint
```

### Core Functions

```python
1. load_metrics(date: str) -> dict
   - Load all metric files for given date
   
2. analyze_sla_breach(metrics: dict) -> dict
   - Calculate processing duration
   - Identify SLA breach
   
3. identify_root_causes(metrics: dict, time_window: tuple) -> list
   - Check threshold breaches
   - Correlate failures across services
   
4. generate_timeline(events: list) -> list
   - Create chronological event sequence
   
5. call_azure_openai(context: dict, query: str) -> str
   - Format technical analysis in natural language
```

## RCA Analysis Output Format

### Timeline Structure (Similar to provided image)
```
06:45 AM | Marker Delay (Root Cause)
         | └─ GLOBAL-OTCDerivatives-EOD_Close arrives 30 minutes late
         | └─ Upstream OTC system issue

09:00 AM | Derivatives Process Starts
         | └─ Starts with incomplete/delayed data dependency

10:15 AM | Database Performance Degradation Begins
         | └─ 125.6ms latency (25.6% over SLA)
         | └─ Caused by: Processing delayed marker data + normal workload

10:30 AM | Infrastructure Crisis Peak
         | └─ DB: 192ms latency (92% over SLA), 90% CPU
         | └─ SQS: 1,250 messages (25% over capacity), 890sec aging
         |     └─ Queue backup caused by slow DB queries

10:45 AM | Continued Degradation
         | └─ DB: Still critical (118ms latency)
         | └─ SQS: Peak queue size (1,456 messages)

11:00 AM | Infrastructure Recovery Begins
         | └─ DB: Latency improves to 95ms (warning level)
         | └─ SQS: Queue starts draining (1,123 messages)

11:20 AM | Derivatives Completes (20 minutes late)
         | └─ Late due to: Initial marker delay + infrastructure slowdown
```

## Implementation Notes

### Phase 1: Core Functionality
1. Set up Flask backend with metric loading
2. Implement SLA breach detection
3. Create basic RCA logic
4. Integrate Azure OpenAI for natural language generation

### Phase 2: Frontend Development
1. Build React chatbot interface
2. Implement chat interaction flow
3. Add date selection capability
4. Create basic metric display

### Phase 3: Visualizations
1. Add timeline visualization component
2. Implement metric charts (Chart.js/Recharts)
3. Add severity color coding
4. Create interactive drill-down features

### Phase 4: Enhancements
1. Add export functionality for RCA reports
2. Implement metric comparison across dates
3. Add remediation recommendations
4. Create alerting mechanisms

## Error Handling

### Common Scenarios
1. **Missing metric files**: Gracefully handle and inform user
2. **Incomplete data**: Process available metrics, note gaps
3. **Azure OpenAI failures**: Fallback to rule-based analysis
4. **Invalid date queries**: Provide clear error messages

## Testing Requirements

### Test Cases
1. Normal processing within SLA
2. SLA breach due to marker delay
3. SLA breach due to infrastructure issues
4. Multiple cascading failures
5. Missing metric files
6. API error scenarios

## Security Considerations

1. Store Azure credentials in environment variables
2. Validate and sanitize all user inputs
3. Implement rate limiting on API endpoints
4. Add CORS configuration for frontend-backend communication
5. Use HTTPS in production

## Performance Optimization

1. Cache loaded metrics in memory
2. Implement pagination for historical data
3. Use async processing for Azure OpenAI calls
4. Optimize metric file parsing
5. Implement frontend lazy loading

## Deployment Configuration

### Docker Support
- Containerize Flask backend
- Containerize React frontend
- Use docker-compose for local development

### Environment Setup
```bash
# Backend
python -m venv venv
pip install flask flask-cors openai pandas numpy

# Frontend
npx create-react-app rca-chatbot
npm install axios recharts date-fns @mui/material
```

## Success Criteria

1. Accurately identify root causes for SLA breaches
2. Generate clear, technical timeline analysis
3. Provide actionable insights through natural language
4. Response time < 3 seconds for analysis
5. Support for historical date queries
6. Interactive and intuitive UI/UX

## Sample Azure OpenAI Prompt Template

```
You are an expert in analyzing batch job processing failures. Given the following metrics:

Marker Event: {marker_details}
Processing Duration: {duration}
Infrastructure Metrics During Processing:
- EKS: {eks_metrics}
- RDS: {rds_metrics}  
- SQS: {sqs_metrics}

Threshold Breaches: {breaches}

User Query: {user_query}

Provide a detailed root cause analysis explaining:
1. The primary cause of the delay/failure
2. The cascade effect on other systems
3. Specific metrics that exceeded thresholds
4. Remediation recommendations

Format the response as a clear, technical narrative suitable for operations teams.
```

## Next Steps for Implementation

1. Create project structure with Flask backend and React frontend
2. Implement metric file loading and parsing
3. Build SLA breach detection logic
4. Set up Azure OpenAI integration
5. Develop React chatbot UI components
6. Implement timeline and chart visualizations
7. Test with provided sample data
8. Iterate based on user feedback
