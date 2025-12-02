import os
from typing import Dict, List, Any
import logging
from openai import AzureOpenAI
from datetime import datetime

logger = logging.getLogger(__name__)

class AzureAIService:
    def __init__(self):
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
        self.deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
        
        self.client = None
        if self.api_key and self.endpoint:
            try:
                self.client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint
                )
                logger.info("Azure OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
    
    def is_configured(self) -> bool:
        return self.client is not None
    
    def generate_response(self, analysis: Dict, user_query: str, metrics: Dict) -> str:
        if not self.client:
            return self._generate_fallback_response(analysis, user_query)
        
        try:
            context = self._prepare_context(analysis, metrics)
            prompt = self._create_prompt(context, user_query, analysis)
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {str(e)}")
            return self._generate_fallback_response(analysis, user_query)
    
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
            formatted.append(f"- {metric['service']}: {metric['issue']}")
        return '\n'.join(formatted)

    def analyze_failure_logs(self, log_content: str) -> Dict:
        """
        Use LLM to analyze failure logs and provide insights.
        Returns a structured analysis with root cause, suggestions, and patterns.
        """
        if not self.client:
            return self._generate_fallback_log_analysis(log_content)

        try:
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