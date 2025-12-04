import os
import json
import traceback
from typing import Dict, List, Any
import logging
from openai import AzureOpenAI
from azure.identity import CertificateCredential
from datetime import datetime, timedelta

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
        self.token_expiry = None
        self.credential = None
        
        if self.endpoint and self.client_id and self.tenant_id:
            try:
                self._initialize_client()
                logger.info("Azure OpenAI client with certificate auth initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
    
    def _initialize_credential(self):
        """Initialize the credential object once"""
        if not self.credential:
            logger.debug("Initializing certificate credential...")
            logger.debug(f"Certificate path: {self.cert_path}")
            
            if not os.path.exists(self.cert_path):
                logger.error(f"Certificate file does not exist at: {self.cert_path}")
                raise FileNotFoundError(f"Certificate file not found: {self.cert_path}")
            
            # Check environment variables
            for env_var in ["AZURE_SPN_CLIENT_ID", "AZURE_TENANT_ID"]:
                if not os.getenv(env_var):
                    logger.error(f"Environment variable {env_var} is not set")
                    raise ValueError(f"Environment variable {env_var} is not set")
            
            self.credential = CertificateCredential(
                client_id=self.client_id,
                certificate_path=self.cert_path,
                tenant_id=self.tenant_id,
                logging_enable=True  # Enable Azure SDK logging
            )
            logger.debug("Certificate credential initialized successfully")

    def get_access_token(self):
        """Get Azure AD access token using certificate authentication"""
        try:
            logger.debug("Getting access token...")
            
            # Initialize credential if not already done
            self._initialize_credential()
            
            scope = "https://cognitiveservices.azure.com/.default"
            
            token_response = self.credential.get_token(scope)
            self.access_token = token_response.token
            
            # Azure tokens typically expire in 1 hour, we'll refresh 5 minutes before expiry
            self.token_expiry = datetime.now() + timedelta(minutes=55)
            
            logger.debug(f"Access token obtained successfully, expires at: {self.token_expiry}")
            
            return self.access_token
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def _initialize_client(self):
        """Initialize the Azure OpenAI client with certificate authentication"""
        try:
            # Reset credential if needed to ensure fresh start
            if not self.credential:
                self._initialize_credential()
            
            # Get fresh access token
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
            logger.info("Azure OpenAI client initialized successfully with fresh token")
        except Exception as e:
            logger.error(f"Failed to initialize client: {str(e)}")
            logger.error(traceback.format_exc())
            # Reset credential for next attempt
            self.credential = None
            self.access_token = None
            self.token_expiry = None
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
        """Refresh the access token if it's expired or about to expire"""
        try:
            # Check if token is missing or expired
            if not self.access_token or not self.token_expiry or datetime.now() >= self.token_expiry:
                logger.info("Token expired or missing, refreshing...")
                self.access_token = self.get_access_token()
                
                # Update the client headers with the new token
                if self.client:
                    self.client.default_headers["Authorization"] = f"Bearer {self.access_token}"
                    logger.info("Token refreshed successfully")
            else:
                logger.debug(f"Token still valid, expires at: {self.token_expiry}")
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
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
        # Count infrastructure issues for better context
        infra_summary = {}
        for metric in context['critical_metrics']:
            service = metric.get('service', 'Unknown')
            if service not in infra_summary:
                infra_summary[service] = 0
            infra_summary[service] += 1
        
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

DETAILED TIMELINE ANALYSIS FOR DERIVATIVES:
{self._format_timeline_events(context['timeline_events'])}

INFRASTRUCTURE ISSUES (detected during processing):
{self._format_critical_metrics(context['critical_metrics'])}
Summary: {', '.join([f'{service}: {count} issues' for service, count in infra_summary.items()]) if infra_summary else 'No critical infrastructure issues detected'}

RECOMMENDATIONS:
{self._format_recommendations(analysis.get('recommendations', []))}

Remember: 
- Focus on answering the user's specific question
- ALWAYS include the Detailed Timeline Analysis when discussing processing issues
- Show the cascading failure pattern with proper formatting
- When discussing infrastructure issues, be specific about which services had problems and when they occurred
- Use the timeline format with visual hierarchy (|, ├, └) to show relationships
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
        - Focus on what the user actually wants to know
        - When showing timelines, use the formatted timeline provided in the context
        - Explain the cascading failure pattern when relevant"""
    
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
            
            response += "\n### Detailed Timeline Analysis for Derivatives:\n\n"
            response += "The Cascading Failure Pattern:\n\n"
            all_timeline = analysis.get('timeline', [])
            # Sort timeline events in ascending order
            sorted_timeline = sorted(all_timeline, key=lambda x: x.get('timestamp', ''))
            critical_events = [e for e in sorted_timeline if e['severity'] in ['critical', 'warning']]
            for event in critical_events[:10]:
                time = self._format_time(event['timestamp'])
                event_name = event['event']
                details = event['details']
                
                response += f"**{time}** | {event_name}\n"
                if 'marker' in event_name.lower():
                    response += f"        | {details}\n"
                    response += f"        └ Upstream system delay\n"
                elif 'rds' in event_name.upper() or 'database' in event_name.lower():
                    response += f"        ├ {details}\n"
                    if event['severity'] == 'critical':
                        response += f"        └ Database bottleneck from concurrent processing\n"
                elif 'sqs' in event_name.upper():
                    response += f"        ├ {details}\n"
                    response += f"        └ Queue backup from slow processing\n"
                else:
                    response += f"        └ {details}\n"
                response += "\n"
            
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
        
        formatted = ["\nThe Cascading Failure Pattern:\n"]
        
        # Sort events by timestamp in ascending order
        sorted_events = sorted(events, key=lambda x: x.get('timestamp', ''))
        
        for i, event in enumerate(sorted_events):
            time_str = event['time']
            event_name = event['event']
            details = event['details']
            severity = event.get('severity', 'info')
            
            # Main event line
            if severity == 'critical':
                formatted.append(f"{time_str} | {event_name} (Critical Issue)")
            elif severity == 'warning':
                formatted.append(f"{time_str} | {event_name}")
            else:
                formatted.append(f"{time_str} | {event_name}")
            
            # Details with proper indentation
            if 'marker' in event_name.lower() and 'delayed' in details.lower():
                formatted.append(f"        | {details}")
                formatted.append(f"        └ Upstream system issue")
            elif 'dag' in event_name.lower() and 'start' in event_name.lower():
                formatted.append(f"        └ {details}")
            elif 'rds' in event_name.upper() or 'database' in event_name.lower():
                formatted.append(f"        ├ {details}")
                if 'critical' in str(severity):
                    formatted.append(f"        └ Caused by: High concurrent queries + delayed processing")
            elif 'sqs' in event_name.upper() or 'queue' in event_name.lower():
                formatted.append(f"        ├ {details}")
                formatted.append(f"        └ Queue backup caused by slow processing")
            elif 'eks' in event_name.upper():
                formatted.append(f"        ├ {details}")
                formatted.append(f"        └ Resource strain from delayed batch processing")
            elif 'complete' in event_name.lower():
                formatted.append(f"        └ {details}")
            else:
                formatted.append(f"        └ {details}")
            
            formatted.append("")  # Empty line between events
        
        return '\n'.join(formatted)
    
    def _format_critical_metrics(self, metrics: List[Dict]) -> str:
        if not metrics:
            return "No critical infrastructure issues detected"

        formatted = []
        for metric in metrics:
            formatted.append(f"- {metric['service']} at {metric['time']}: {metric['issue']}")
        return '\n'.join(formatted)

    def analyze_failure_logs(self, log_content: str) -> Dict:
        """
        Use LLM to analyze failure logs and provide insights.
        Returns a structured analysis with root cause, suggestions, and patterns.
        """
        if not self.client:
            return self._generate_fallback_log_analysis(log_content)

        try:
            # Refresh token if needed before making the API call
            self._refresh_token_if_needed()
            
            prompt = f"""Analyze the following application failure logs and provide a detailed technical analysis.

{log_content}

Please provide your analysis in the following JSON format (respond ONLY with valid JSON, no markdown):
{{
    "root_cause": "A clear, concise explanation of the root cause of the failure",
    "error_chain": ["Step 1 of how the error propagated", "Step 2...", "Step 3..."],
    "affected_components": ["component1", "component2"],
    "suggested_fixes": [
        {{
            "priority": "high|medium|low",
            "action": "Specific action to take",
            "rationale": "Why this fix will help"
        }}
    ],
    "patterns_detected": ["Pattern 1 noticed in the logs", "Pattern 2..."],
    "severity_assessment": "critical|high|medium|low",
    "summary": "A 2-3 sentence executive summary of the failure and recommended immediate action"
}}
"""

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": """You are an expert DevOps engineer and log analyst.
Analyze application logs to identify root causes, patterns, and provide actionable recommendations.
Focus on:
1. Identifying the primary root cause
2. Understanding the error propagation chain
3. Suggesting specific, actionable fixes
4. Detecting patterns that might indicate systemic issues
Always respond with valid JSON only, no markdown formatting."""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            response_text = response.choices[0].message.content.strip()

            # Try to parse JSON response
            import json
            try:
                # Remove markdown code blocks if present
                if response_text.startswith('```'):
                    response_text = response_text.split('```')[1]
                    if response_text.startswith('json'):
                        response_text = response_text[4:]
                analysis = json.loads(response_text)
                return analysis
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON, returning as summary")
                return {
                    "root_cause": "Analysis completed",
                    "summary": response_text,
                    "error_chain": [],
                    "affected_components": [],
                    "suggested_fixes": [],
                    "patterns_detected": [],
                    "severity_assessment": "medium"
                }

        except Exception as e:
            logger.error(f"Error analyzing logs with LLM: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Try to reinitialize the client and retry once
            if "401" in str(e) or "unauthorized" in str(e).lower() or "token" in str(e).lower():
                try:
                    logger.info("Token error detected, reinitializing client and retrying...")
                    self._initialize_client()
                    
                    response = self.client.chat.completions.create(
                        model=self.deployment,
                        messages=[
                            {"role": "system", "content": """You are an expert DevOps engineer and log analyst.
Analyze application logs to identify root causes, patterns, and provide actionable recommendations.
Focus on:
1. Identifying the primary root cause
2. Understanding the error propagation chain
3. Suggesting specific, actionable fixes
4. Detecting patterns that might indicate systemic issues
Always respond with valid JSON only, no markdown formatting."""},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1500
                    )
                    
                    response_text = response.choices[0].message.content.strip()
                    
                    # Try to parse JSON response
                    import json
                    try:
                        if response_text.startswith('```'):
                            response_text = response_text.split('```')[1]
                            if response_text.startswith('json'):
                                response_text = response_text[4:]
                        analysis = json.loads(response_text)
                        return analysis
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse LLM response as JSON on retry, returning as summary")
                        return {
                            "root_cause": "Analysis completed",
                            "summary": response_text,
                            "error_chain": [],
                            "affected_components": [],
                            "suggested_fixes": [],
                            "patterns_detected": [],
                            "severity_assessment": "medium"
                        }
                except Exception as retry_error:
                    logger.error(f"Retry also failed: {str(retry_error)}")
            
            return self._generate_fallback_log_analysis(log_content)

    def _generate_fallback_log_analysis(self, log_content: str) -> Dict:
        """Generate a basic analysis when LLM is not available."""
        # Count errors and warnings from content
        error_count = log_content.lower().count('error')
        warning_count = log_content.lower().count('warn')

        severity = "critical" if error_count > 5 else "high" if error_count > 2 else "medium"

        return {
            "root_cause": "Unable to perform AI analysis - LLM service unavailable",
            "summary": f"Log file contains {error_count} error(s) and {warning_count} warning(s). Manual review recommended.",
            "error_chain": [],
            "affected_components": [],
            "suggested_fixes": [
                {
                    "priority": "high",
                    "action": "Review the error contexts manually",
                    "rationale": "AI analysis unavailable, manual investigation required"
                }
            ],
            "patterns_detected": [],
            "severity_assessment": severity
        }

    def _format_recommendations(self, recommendations: List[str]) -> str:
        if not recommendations:
            return "No specific recommendations"
        
        formatted = []
        for i, rec in enumerate(recommendations[:5], 1):
            formatted.append(f"{i}. {rec}")
        return '\n'.join(formatted)