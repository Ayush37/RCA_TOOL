import os
import json
import traceback
from typing import Dict, List, Any
import logging
from openai import AzureOpenAI
from azure.identity import CertificateCredential
from datetime import datetime

logger = logging.getLogger(__name__)

class AzureAIServiceCert:
    def __init__(self):
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
        self.deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-2024-08-06')
        self.client_id = os.getenv('AZURE_SPN_CLIENT_ID')
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.user_sid = os.getenv('USER_SID', '1792420')
        
        # Certificate path - can be absolute or relative to backend directory
        cert_path_env = os.getenv('AZURE_CERT_PATH', 'cert/apim-exp.pem')
        if os.path.isabs(cert_path_env):
            self.cert_path = cert_path_env
        else:
            # Make it relative to backend directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.cert_path = os.path.join(backend_dir, cert_path_env)
        
        self.client = None
        self.access_token = None
        
        if self.endpoint and self.client_id and self.tenant_id:
            try:
                self._initialize_client()
                logger.info("Azure OpenAI client with certificate auth initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
    
    def get_access_token(self):
        """Get Azure AD access token using certificate authentication"""
        try:
            logger.debug("Getting access token...")
            logger.debug(f"Certificate path: {self.cert_path}")
            
            if not os.path.exists(self.cert_path):
                logger.error(f"Certificate file does not exist at: {self.cert_path}")
                raise FileNotFoundError(f"Certificate file not found: {self.cert_path}")
            
            scope = "https://cognitiveservices.azure.com/.default"
            
            # Check environment variables
            for env_var in ["AZURE_SPN_CLIENT_ID", "AZURE_TENANT_ID"]:
                if not os.getenv(env_var):
                    logger.error(f"Environment variable {env_var} is not set")
                    raise ValueError(f"Environment variable {env_var} is not set")
            
            credential = CertificateCredential(
                client_id=self.client_id,
                certificate_path=self.cert_path,
                tenant_id=self.tenant_id,
                logging_enable=True  # Enable Azure SDK logging
            )
            
            access_token = credential.get_token(scope).token
            logger.debug("Access token obtained successfully")
            
            return access_token
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def _initialize_client(self):
        """Initialize the Azure OpenAI client with certificate authentication"""
        try:
            # Get access token
            self.access_token = self.get_access_token()
            
            # Initialize Azure OpenAI client
            # Note: API key is still required even with certificate auth (as per sample)
            logger.debug("Initializing OpenAI client...")
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY", "placeholder-api-key"),
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
                default_headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "user_sid": self.user_sid
                }
            )
        except Exception as e:
            logger.error(f"Failed to initialize client: {str(e)}")
            raise
    
    def is_configured(self) -> bool:
        return self.client is not None
    
    def generate_response(self, analysis: Dict, user_query: str, metrics: Dict) -> str:
        if not self.client:
            logger.warning("Azure OpenAI client not configured, using fallback response")
            return self._generate_fallback_response(analysis, user_query)
        
        try:
            # Refresh token if needed (tokens expire after ~1 hour)
            self._refresh_token_if_needed()
            
            context = self._prepare_context(analysis, metrics)
            prompt = self._create_prompt(context, user_query, analysis)
            
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            logger.debug("Calling Azure OpenAI API...")
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {str(e)}")
            logger.error(traceback.format_exc())
            # Try to refresh token and retry once
            try:
                logger.info("Attempting to refresh token and retry...")
                self._initialize_client()
                response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1500
                )
                return response.choices[0].message.content
            except:
                return self._generate_fallback_response(analysis, user_query)
    
    def _refresh_token_if_needed(self):
        """Refresh the access token if needed (implement token expiry check if required)"""
        # For now, we'll get a fresh token for each request
        # In production, you'd want to cache and check expiry
        try:
            self.access_token = self.get_access_token()
            self.client.default_headers["Authorization"] = f"Bearer {self.access_token}"
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
    
    def _prepare_context(self, analysis: Dict, metrics: Dict) -> Dict:
        context = {
            'sla_breach': analysis['sla_status']['breached'] if analysis['sla_status'] else False,
            'processing_duration': analysis['processing_duration'],
            'root_causes': [],
            'timeline_events': [],
            'critical_metrics': [],
            'processing_window': {
                'start': analysis['sla_status'].get('arrival_time') if analysis.get('sla_status') else None,
                'end': analysis['sla_status'].get('completion_time') if analysis.get('sla_status') else None
            }
        }
        
        for cause in analysis.get('root_causes', []):
            context['root_causes'].append({
                'category': cause['category'],
                'cause': cause['cause'],
                'impact': cause['impact']
            })
        
        # Use filtered timeline events which already contain only relevant time-window data
        critical_events = [e for e in analysis.get('timeline', []) if e['severity'] in ['critical', 'warning']]
        for event in critical_events[:10]:  # Include more events for better context
            context['timeline_events'].append({
                'time': self._format_time(event['timestamp']),
                'event': event['event'],
                'details': event['details'],
                'severity': event['severity']
            })
        
        # Extract critical metrics from the timeline (already filtered by time window)
        for event in analysis.get('timeline', []):
            if 'RDS' in event.get('event', '') and event['severity'] == 'critical':
                if 'latency' in event['details'].lower():
                    context['critical_metrics'].append({
                        'service': 'RDS',
                        'issue': event['details'],
                        'time': self._format_time(event['timestamp'])
                    })
            elif 'SQS' in event.get('event', '') and event['severity'] == 'critical':
                if 'queue' in event['details'].lower():
                    context['critical_metrics'].append({
                        'service': 'SQS', 
                        'issue': event['details'],
                        'time': self._format_time(event['timestamp'])
                    })
            elif 'EKS' in event.get('event', '') and event['severity'] == 'critical':
                context['critical_metrics'].append({
                    'service': 'EKS',
                    'issue': event['details'],
                    'time': self._format_time(event['timestamp'])
                })
        
        return context
    
    def _create_prompt(self, context: Dict, user_query: str, analysis: Dict) -> str:
        prompt = f"""
The user is asking: "{user_query}"

Please answer their specific question using the following context about derivatives batch processing:

ANALYSIS RESULTS:
- SLA Status: {'BREACHED' if context['sla_breach'] else 'MET'}
- Processing Duration: {context['processing_duration']} hours (SLA: 3 hours)
- Date: {analysis.get('date', 'Unknown')}
- Processing Window: {self._format_time(context['processing_window']['start']) if context['processing_window']['start'] else 'N/A'} to {self._format_time(context['processing_window']['end']) if context['processing_window']['end'] else 'N/A'}

ROOT CAUSES IDENTIFIED:
{self._format_root_causes(context['root_causes'])}

CRITICAL TIMELINE EVENTS (within processing window):
{self._format_timeline_events(context['timeline_events'])}

INFRASTRUCTURE ISSUES (detected during processing):
{self._format_critical_metrics(context['critical_metrics'])}

RECOMMENDATIONS:
{self._format_recommendations(analysis.get('recommendations', []))}

Remember: Focus on answering the user's specific question. Don't always provide the full RCA unless they're asking for it.
"""
        return prompt
    
    def _get_system_prompt(self) -> str:
        return """You are an expert Site Reliability Engineer specializing in batch processing systems and root cause analysis.
        You analyze complex distributed system failures involving AWS services (RDS, EKS, SQS) and provide clear, actionable insights.
        
        IMPORTANT: 
        - Answer the user's specific question directly
        - If they ask about something other than RCA/processing, respond appropriately
        - Don't always provide full RCA analysis unless specifically asked
        - Be conversational and helpful, not repetitive
        - Focus on what the user actually wants to know"""
    
    def _generate_fallback_response(self, analysis: Dict, user_query: str) -> str:
        if not analysis or not analysis.get('sla_status'):
            return "Unable to perform analysis. Please check if metrics are available for the specified date."
        
        response = f"## Root Cause Analysis for Derivatives Processing\n\n"
        
        if analysis['sla_status'].get('breached'):
            response += f"**SLA Status:** ⚠️ BREACHED\n"
            response += f"**Processing Duration:** {analysis['processing_duration']} hours (exceeded 3-hour SLA by {analysis['sla_status']['excess_hours']} hours)\n\n"
            
            response += "### Primary Root Causes:\n"
            for i, cause in enumerate(analysis.get('root_causes', []), 1):
                response += f"{i}. **{cause['category']}**: {cause['cause']}\n"
                response += f"   - Impact: {cause['impact']}\n"
                if cause.get('evidence'):
                    response += f"   - Evidence: {cause['evidence']}\n"
            
            response += "\n### Critical Timeline:\n"
            critical_events = [e for e in analysis.get('timeline', []) if e['severity'] in ['critical', 'warning']]
            for event in critical_events[:5]:
                time = self._format_time(event['timestamp'])
                response += f"- **{time}** | {event['event']}: {event['details']}\n"
            
            response += "\n### Recommendations:\n"
            for rec in analysis.get('recommendations', [])[:5]:
                response += f"- {rec}\n"
        else:
            response += f"**SLA Status:** ✅ MET\n"
            response += f"**Processing Duration:** {analysis['processing_duration']} hours (within 3-hour SLA)\n\n"
            response += "Processing completed successfully within SLA requirements.\n"
        
        return response
    
    def _format_time(self, timestamp: str) -> str:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%I:%M %p')
        except:
            return timestamp
    
    def _format_root_causes(self, causes: List[Dict]) -> str:
        if not causes:
            return "No specific root causes identified"
        
        formatted = []
        for cause in causes:
            formatted.append(f"- {cause['category']}: {cause['cause']} ({cause['impact']})")
        return '\n'.join(formatted)
    
    def _format_timeline_events(self, events: List[Dict]) -> str:
        if not events:
            return "No critical events recorded"
        
        formatted = []
        for event in events:
            formatted.append(f"- {event['time']}: {event['event']} - {event['details']}")
        return '\n'.join(formatted)
    
    def _format_critical_metrics(self, metrics: List[Dict]) -> str:
        if not metrics:
            return "No critical infrastructure issues detected"
        
        formatted = []
        for metric in metrics:
            formatted.append(f"- {metric['service']} at {metric['time']}: {metric['issue']}")
        return '\n'.join(formatted)
    
    def _format_recommendations(self, recommendations: List[str]) -> str:
        if not recommendations:
            return "No specific recommendations"
        
        formatted = []
        for i, rec in enumerate(recommendations[:5], 1):
            formatted.append(f"{i}. {rec}")
        return '\n'.join(formatted)