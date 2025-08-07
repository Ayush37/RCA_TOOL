import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MetricLoader:
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.metric_folders = {
            'markerEvent': 'marker_event',
            'dagDetails': 'dag_metrics',
            'eksMetrics': 'eks_metrics',
            'sqsMetrics': 'sqs_metrics',
            'rdsMetrics': 'rds_metrics'
        }
    
    def load_all_metrics(self, date: str) -> Dict[str, Any]:
        metrics = {}
        
        for folder, file_suffix in self.metric_folders.items():
            file_path = os.path.join(self.base_path, folder, f"{date}_{file_suffix}.json")
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        metrics[folder] = json.load(f)
                        logger.info(f"Loaded {folder} metrics for {date}")
                except Exception as e:
                    logger.error(f"Error loading {folder} metrics: {str(e)}")
                    metrics[folder] = None
            else:
                logger.warning(f"File not found: {file_path}")
                metrics[folder] = None
        
        return metrics if any(v is not None for v in metrics.values()) else None
    
    def get_available_dates(self) -> List[str]:
        dates = set()
        
        for folder in self.metric_folders.keys():
            folder_path = os.path.join(self.base_path, folder)
            if os.path.exists(folder_path):
                for filename in os.listdir(folder_path):
                    if filename.endswith('.json'):
                        date = filename.split('_')[0]
                        dates.add(date)
        
        return sorted(list(dates), reverse=True)
    
    def extract_key_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        extracted = {
            'marker_event': None,
            'dag_processing': [],
            'infrastructure': {
                'eks': [],
                'rds': [],
                'sqs': []
            }
        }
        
        if metrics.get('markerEvent'):
            marker = metrics['markerEvent']
            extracted['marker_event'] = {
                'arrival_time': marker.get('actual_arrival_time'),
                'expected_time': marker.get('expected_arrival_time'),
                'delay_minutes': marker.get('delay_in_minutes', 0),
                'product': marker.get('product'),
                'type': marker.get('type')
            }
        
        if metrics.get('dagDetails'):
            dag_data = metrics['dagDetails']
            if 'readings' in dag_data:
                for reading in dag_data['readings']:
                    if 'entries' in reading:
                        for entry in reading['entries']:
                            # Calculate duration from start and end times
                            duration = None
                            if entry.get('start_date') and entry.get('end_date'):
                                try:
                                    start = datetime.fromisoformat(entry['start_date'].replace('Z', '+00:00'))
                                    end = datetime.fromisoformat(entry['end_date'].replace('Z', '+00:00'))
                                    duration = (end - start).total_seconds()
                                except:
                                    pass
                            
                            extracted['dag_processing'].append({
                                'dag_id': entry.get('dag_id'),
                                'run_id': entry.get('run_id'),
                                'start_time': entry.get('start_date'),
                                'end_time': entry.get('end_date'),
                                'duration_seconds': duration,
                                'state': entry.get('state')
                            })
        
        if metrics.get('eksMetrics'):
            eks = metrics['eksMetrics']
            extracted['infrastructure']['eks'] = self._extract_eks_issues(eks)
        
        if metrics.get('rdsMetrics'):
            rds = metrics['rdsMetrics']
            extracted['infrastructure']['rds'] = self._extract_rds_issues(rds)
        
        if metrics.get('sqsMetrics'):
            sqs = metrics['sqsMetrics']
            extracted['infrastructure']['sqs'] = self._extract_sqs_issues(sqs)
        
        return extracted
    
    def _extract_eks_issues(self, eks_data: Dict) -> List[Dict]:
        issues = []
        thresholds = {
            'cpu_critical': 90,
            'cpu_warning': 80,
            'memory_critical': 90,
            'memory_warning': 80,
            'restarts_critical': 10,
            'restarts_warning': 5
        }
        
        for pod in eks_data.get('pods', []):
            cpu = pod.get('cpu_usage_percentage', 0)
            memory = pod.get('memory_usage_percentage', 0)
            restarts = pod.get('restart_count', 0)
            
            if cpu > thresholds['cpu_critical'] or memory > thresholds['memory_critical'] or restarts > thresholds['restarts_critical']:
                issues.append({
                    'timestamp': pod.get('timestamp'),
                    'pod_name': pod.get('pod_name'),
                    'severity': 'critical',
                    'cpu': cpu,
                    'memory': memory,
                    'restarts': restarts,
                    'details': f"CPU: {cpu}%, Memory: {memory}%, Restarts: {restarts}"
                })
            elif cpu > thresholds['cpu_warning'] or memory > thresholds['memory_warning'] or restarts > thresholds['restarts_warning']:
                issues.append({
                    'timestamp': pod.get('timestamp'),
                    'pod_name': pod.get('pod_name'),
                    'severity': 'warning',
                    'cpu': cpu,
                    'memory': memory,
                    'restarts': restarts,
                    'details': f"CPU: {cpu}%, Memory: {memory}%, Restarts: {restarts}"
                })
        
        return issues
    
    def _extract_rds_issues(self, rds_data: Dict) -> List[Dict]:
        issues = []
        thresholds = {
            'cpu_critical': 95,
            'cpu_warning': 90,
            'connections_critical': 250,
            'connections_warning': 200,
            'commit_latency_critical': 50,
            'commit_latency_warning': 25,
            'select_latency_critical': 100,
            'select_latency_warning': 50
        }
        
        for metric in rds_data.get('database_metrics', []):
            cpu = metric.get('cpu_utilization', 0)
            connections = metric.get('database_connections', 0)
            commit_latency = metric.get('commit_latency', 0)
            select_latency = metric.get('select_latency', 0)
            
            severity = None
            if (cpu > thresholds['cpu_critical'] or 
                connections > thresholds['connections_critical'] or
                commit_latency > thresholds['commit_latency_critical'] or
                select_latency > thresholds['select_latency_critical']):
                severity = 'critical'
            elif (cpu > thresholds['cpu_warning'] or 
                  connections > thresholds['connections_warning'] or
                  commit_latency > thresholds['commit_latency_warning'] or
                  select_latency > thresholds['select_latency_warning']):
                severity = 'warning'
            
            if severity:
                issues.append({
                    'timestamp': metric.get('timestamp'),
                    'severity': severity,
                    'cpu': cpu,
                    'connections': connections,
                    'commit_latency': commit_latency,
                    'select_latency': select_latency,
                    'details': f"CPU: {cpu}%, Connections: {connections}, Commit: {commit_latency}ms, Select: {select_latency}ms"
                })
        
        return issues
    
    def _extract_sqs_issues(self, sqs_data: Dict) -> List[Dict]:
        issues = []
        thresholds = {
            'age_critical': 600,
            'age_warning': 300,
            'visible_critical': 1000,
            'visible_warning': 500,
            'received_critical': 4500,
            'received_warning': 1800
        }
        
        for metric in sqs_data.get('queue_metrics', []):
            age = metric.get('approximate_age_of_oldest_message', 0)
            visible = metric.get('approximate_number_of_messages_visible', 0)
            received = metric.get('number_of_messages_received', 0)
            
            severity = None
            if (age > thresholds['age_critical'] or 
                visible > thresholds['visible_critical'] or
                received > thresholds['received_critical']):
                severity = 'critical'
            elif (age > thresholds['age_warning'] or 
                  visible > thresholds['visible_warning'] or
                  received > thresholds['received_warning']):
                severity = 'warning'
            
            if severity:
                issues.append({
                    'timestamp': metric.get('timestamp'),
                    'queue_name': metric.get('queue_name'),
                    'severity': severity,
                    'message_age': age,
                    'visible_messages': visible,
                    'messages_received': received,
                    'details': f"Age: {age}s, Visible: {visible}, Received: {received}"
                })
        
        return issues