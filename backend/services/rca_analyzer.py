from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RCAAnalyzer:
    def __init__(self):
        self.sla_hours = 3
        
    def analyze(self, metrics: Dict[str, Any], target_date: str) -> Dict[str, Any]:
        analysis = {
            'date': target_date,
            'sla_status': None,
            'processing_duration': None,
            'timeline': [],
            'root_causes': [],
            'metrics_summary': {},
            'recommendations': []
        }
        
        marker_info = self._analyze_marker_event(metrics.get('markerEvent'))
        dag_info = self._analyze_dag_processing(metrics.get('dagDetails'))
        
        if marker_info and dag_info:
            sla_breach = self._check_sla_breach(marker_info, dag_info)
            analysis['sla_status'] = sla_breach
            analysis['processing_duration'] = sla_breach.get('duration_hours')
            
            if sla_breach['breached']:
                infrastructure_issues = self._analyze_infrastructure(
                    metrics,
                    marker_info['arrival_time'],
                    dag_info['end_time']
                )
                
                timeline = self._build_timeline(
                    marker_info,
                    dag_info,
                    infrastructure_issues
                )
                analysis['timeline'] = timeline
                
                root_causes = self._identify_root_causes(
                    marker_info,
                    infrastructure_issues,
                    sla_breach
                )
                analysis['root_causes'] = root_causes
                
                analysis['recommendations'] = self._generate_recommendations(root_causes)
        
        analysis['metrics_summary'] = self._create_metrics_summary(metrics)
        
        return analysis
    
    def _analyze_marker_event(self, marker_data: Optional[Dict]) -> Optional[Dict]:
        if not marker_data:
            return None
        
        return {
            'arrival_time': marker_data.get('actual_arrival_time'),
            'expected_time': marker_data.get('expected_arrival_time'),
            'delay_minutes': marker_data.get('delay_in_minutes', 0),
            'product': marker_data.get('product'),
            'type': marker_data.get('type'),
            'delayed': marker_data.get('delay_in_minutes', 0) > 0
        }
    
    def _analyze_dag_processing(self, dag_data: Optional[Dict]) -> Optional[Dict]:
        if not dag_data:
            return None
        
        # Handle nested structure with readings and entries
        derivatives_dags = []
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
                        
                        derivatives_dags.append({
                            'dag_id': entry.get('dag_id'),
                            'run_id': entry.get('run_id'),
                            'start_date': entry.get('start_date'),
                            'end_date': entry.get('end_date'),
                            'duration': duration,
                            'state': entry.get('state'),
                            'run_type': entry.get('run_type')
                        })
        
        if not derivatives_dags:
            return None
        
        sorted_dags = sorted(derivatives_dags, key=lambda x: x.get('start_date', ''))
        
        return {
            'start_time': sorted_dags[0].get('start_date'),
            'end_time': sorted_dags[-1].get('end_date'),
            'total_dags': len(derivatives_dags),
            'failed_dags': sum(1 for dag in derivatives_dags if dag.get('state') == 'failed'),
            'dag_details': derivatives_dags
        }
    
    def _check_sla_breach(self, marker_info: Dict, dag_info: Dict) -> Dict:
        try:
            arrival = datetime.fromisoformat(marker_info['arrival_time'].replace('Z', '+00:00'))
            completion = datetime.fromisoformat(dag_info['end_time'].replace('Z', '+00:00'))
            
            duration = completion - arrival
            duration_hours = duration.total_seconds() / 3600
            
            return {
                'breached': duration_hours > self.sla_hours,
                'duration_hours': round(duration_hours, 2),
                'expected_hours': self.sla_hours,
                'excess_hours': max(0, round(duration_hours - self.sla_hours, 2)),
                'arrival_time': marker_info['arrival_time'],
                'completion_time': dag_info['end_time']
            }
        except Exception as e:
            logger.error(f"Error checking SLA breach: {str(e)}")
            return {
                'breached': False,
                'duration_hours': 0,
                'error': str(e)
            }
    
    def _analyze_infrastructure(self, metrics: Dict, start_time: str, end_time: str) -> Dict:
        issues = {
            'eks': [],
            'rds': [],
            'sqs': [],
            'summary': {
                'critical_count': 0,
                'warning_count': 0,
                'peak_issue_time': None
            }
        }
        
        if metrics.get('eksMetrics'):
            issues['eks'] = self._analyze_eks_metrics(metrics['eksMetrics'], start_time, end_time)
        
        if metrics.get('rdsMetrics'):
            issues['rds'] = self._analyze_rds_metrics(metrics['rdsMetrics'], start_time, end_time)
        
        if metrics.get('sqsMetrics'):
            issues['sqs'] = self._analyze_sqs_metrics(metrics['sqsMetrics'], start_time, end_time)
        
        for service_issues in [issues['eks'], issues['rds'], issues['sqs']]:
            for issue in service_issues:
                if issue['severity'] == 'critical':
                    issues['summary']['critical_count'] += 1
                elif issue['severity'] == 'warning':
                    issues['summary']['warning_count'] += 1
        
        return issues
    
    def _analyze_eks_metrics(self, eks_data: Dict, start_time: str, end_time: str) -> List[Dict]:
        issues = []
        thresholds = {
            'cpu_critical': 90, 'cpu_warning': 80,
            'memory_critical': 90, 'memory_warning': 80,
            'restarts_critical': 10, 'restarts_warning': 5
        }
        
        for pod in eks_data.get('pods', []):
            if not self._is_within_timeframe(pod.get('timestamp'), start_time, end_time):
                continue
            
            cpu = pod.get('cpu_usage_percentage', 0)
            memory = pod.get('memory_usage_percentage', 0)
            restarts = pod.get('restart_count', 0)
            
            if cpu > thresholds['cpu_critical'] or memory > thresholds['memory_critical']:
                issues.append({
                    'timestamp': pod.get('timestamp'),
                    'service': 'EKS',
                    'severity': 'critical',
                    'type': 'resource_exhaustion',
                    'details': f"Pod {pod.get('pod_name')}: CPU {cpu}%, Memory {memory}%, Restarts {restarts}",
                    'metrics': {'cpu': cpu, 'memory': memory, 'restarts': restarts}
                })
            elif cpu > thresholds['cpu_warning'] or memory > thresholds['memory_warning']:
                issues.append({
                    'timestamp': pod.get('timestamp'),
                    'service': 'EKS',
                    'severity': 'warning',
                    'type': 'high_resource_usage',
                    'details': f"Pod {pod.get('pod_name')}: CPU {cpu}%, Memory {memory}%",
                    'metrics': {'cpu': cpu, 'memory': memory, 'restarts': restarts}
                })
        
        return issues
    
    def _analyze_rds_metrics(self, rds_data: Dict, start_time: str, end_time: str) -> List[Dict]:
        issues = []
        thresholds = {
            'cpu_critical': 95, 'cpu_warning': 90,
            'connections_critical': 250, 'connections_warning': 200,
            'commit_latency_critical': 50, 'commit_latency_warning': 25,
            'select_latency_critical': 100, 'select_latency_warning': 50
        }
        
        for metric in rds_data.get('database_metrics', []):
            if not self._is_within_timeframe(metric.get('timestamp'), start_time, end_time):
                continue
            
            cpu = metric.get('cpu_utilization', 0)
            connections = metric.get('database_connections', 0)
            commit_latency = metric.get('commit_latency', 0)
            select_latency = metric.get('select_latency', 0)
            
            critical_issues = []
            warning_issues = []
            
            if cpu > thresholds['cpu_critical']:
                critical_issues.append(f"CPU {cpu}%")
            elif cpu > thresholds['cpu_warning']:
                warning_issues.append(f"CPU {cpu}%")
            
            if commit_latency > thresholds['commit_latency_critical']:
                critical_issues.append(f"Commit latency {commit_latency}ms")
            elif commit_latency > thresholds['commit_latency_warning']:
                warning_issues.append(f"Commit latency {commit_latency}ms")
            
            if select_latency > thresholds['select_latency_critical']:
                critical_issues.append(f"Select latency {select_latency}ms")
            elif select_latency > thresholds['select_latency_warning']:
                warning_issues.append(f"Select latency {select_latency}ms")
            
            if critical_issues:
                issues.append({
                    'timestamp': metric.get('timestamp'),
                    'service': 'RDS',
                    'severity': 'critical',
                    'type': 'database_performance',
                    'details': f"Database critical: {', '.join(critical_issues)}",
                    'metrics': {
                        'cpu': cpu,
                        'connections': connections,
                        'commit_latency': commit_latency,
                        'select_latency': select_latency
                    }
                })
            elif warning_issues:
                issues.append({
                    'timestamp': metric.get('timestamp'),
                    'service': 'RDS',
                    'severity': 'warning',
                    'type': 'database_degradation',
                    'details': f"Database warning: {', '.join(warning_issues)}",
                    'metrics': {
                        'cpu': cpu,
                        'connections': connections,
                        'commit_latency': commit_latency,
                        'select_latency': select_latency
                    }
                })
        
        return issues
    
    def _analyze_sqs_metrics(self, sqs_data: Dict, start_time: str, end_time: str) -> List[Dict]:
        issues = []
        thresholds = {
            'age_critical': 600, 'age_warning': 300,
            'visible_critical': 1000, 'visible_warning': 500
        }
        
        for metric in sqs_data.get('queue_metrics', []):
            if not self._is_within_timeframe(metric.get('timestamp'), start_time, end_time):
                continue
            
            age = metric.get('approximate_age_of_oldest_message', 0)
            visible = metric.get('approximate_number_of_messages_visible', 0)
            
            if age > thresholds['age_critical'] or visible > thresholds['visible_critical']:
                issues.append({
                    'timestamp': metric.get('timestamp'),
                    'service': 'SQS',
                    'severity': 'critical',
                    'type': 'queue_backup',
                    'details': f"Queue {metric.get('queue_name')}: {visible} messages, oldest {age}s",
                    'metrics': {'message_age': age, 'visible_messages': visible}
                })
            elif age > thresholds['age_warning'] or visible > thresholds['visible_warning']:
                issues.append({
                    'timestamp': metric.get('timestamp'),
                    'service': 'SQS',
                    'severity': 'warning',
                    'type': 'queue_delay',
                    'details': f"Queue {metric.get('queue_name')}: {visible} messages, oldest {age}s",
                    'metrics': {'message_age': age, 'visible_messages': visible}
                })
        
        return issues
    
    def _build_timeline(self, marker_info: Dict, dag_info: Dict, infrastructure: Dict) -> List[Dict]:
        timeline = []
        
        if marker_info['delayed']:
            timeline.append({
                'timestamp': marker_info['expected_time'],
                'event': 'Marker Event Delay',
                'severity': 'critical',
                'details': f"{marker_info['product']} marker delayed by {marker_info['delay_minutes']} minutes",
                'impact': 'Root cause - triggers cascade of delays'
            })
        
        timeline.append({
            'timestamp': marker_info['arrival_time'],
            'event': 'Marker Event Arrival',
            'severity': 'info',
            'details': f"{marker_info['product']} marker arrives",
            'impact': 'Processing can begin'
        })
        
        timeline.append({
            'timestamp': dag_info['start_time'],
            'event': 'DAG Processing Starts',
            'severity': 'info',
            'details': f"Started processing {dag_info['total_dags']} derivatives DAG runs",
            'impact': 'Derivatives processing initiated'
        })
        
        # Add failed DAG runs to timeline if any
        for dag in dag_info.get('dag_details', []):
            if dag.get('state') == 'failed':
                timeline.append({
                    'timestamp': dag['end_date'],
                    'event': 'DAG Run Failed',
                    'severity': 'critical',
                    'details': f"Run {dag['run_id'].split('_')[-1][:20]}... failed after {dag.get('duration', 0)/60:.1f} minutes",
                    'impact': 'Processing delay due to failed DAG run'
                })
        
        all_issues = (
            infrastructure.get('eks', []) +
            infrastructure.get('rds', []) +
            infrastructure.get('sqs', [])
        )
        
        for issue in sorted(all_issues, key=lambda x: x['timestamp']):
            timeline.append({
                'timestamp': issue['timestamp'],
                'event': f"{issue['service']} {issue['type'].replace('_', ' ').title()}",
                'severity': issue['severity'],
                'details': issue['details'],
                'impact': self._determine_impact(issue)
            })
        
        timeline.append({
            'timestamp': dag_info['end_time'],
            'event': 'DAG Processing Complete',
            'severity': 'warning' if dag_info.get('failed_dags', 0) > 0 else 'info',
            'details': f"Completed {dag_info['total_dags']} DAG runs ({dag_info.get('failed_dags', 0)} failed)",
            'impact': 'Derivatives processing finished'
        })
        
        return sorted(timeline, key=lambda x: x['timestamp'])
    
    def _identify_root_causes(self, marker_info: Dict, infrastructure: Dict, sla_breach: Dict) -> List[Dict]:
        root_causes = []
        
        if marker_info['delayed']:
            root_causes.append({
                'category': 'Upstream Dependency',
                'severity': 'critical',
                'cause': f"Marker event delayed by {marker_info['delay_minutes']} minutes",
                'impact': f"Initiated processing late, contributing {marker_info['delay_minutes']/60:.1f} hours to SLA breach",
                'evidence': f"{marker_info['product']} marker arrived at {marker_info['arrival_time']}",
                'contribution_percentage': min(100, (marker_info['delay_minutes']/60) / sla_breach['excess_hours'] * 100)
            })
        
        critical_infra = []
        for service in ['eks', 'rds', 'sqs']:
            critical_issues = [i for i in infrastructure.get(service, []) if i['severity'] == 'critical']
            if critical_issues:
                critical_infra.append((service.upper(), critical_issues))
        
        if critical_infra:
            for service, issues in critical_infra:
                root_causes.append({
                    'category': 'Infrastructure Bottleneck',
                    'severity': 'critical',
                    'cause': f"{service} performance degradation",
                    'impact': f"{len(issues)} critical issues detected during processing",
                    'evidence': issues[0]['details'] if issues else '',
                    'contribution_percentage': 0
                })
        
        return root_causes
    
    def _determine_impact(self, issue: Dict) -> str:
        impacts = {
            'resource_exhaustion': 'Slows down DAG execution significantly',
            'database_performance': 'Causes query delays and transaction bottlenecks',
            'queue_backup': 'Messages not processed timely, cascading delays',
            'high_resource_usage': 'May lead to performance degradation',
            'database_degradation': 'Slower query processing',
            'queue_delay': 'Message processing delays'
        }
        return impacts.get(issue['type'], 'System performance impact')
    
    def _generate_recommendations(self, root_causes: List[Dict]) -> List[str]:
        recommendations = []
        
        for cause in root_causes:
            if 'Upstream Dependency' in cause['category']:
                recommendations.append("Implement marker event monitoring and alerting for delays > 15 minutes")
                recommendations.append("Establish SLA with upstream OTC system for marker delivery")
            elif 'Infrastructure Bottleneck' in cause['category']:
                if 'RDS' in cause['cause']:
                    recommendations.append("Scale up RDS instance or implement read replicas")
                    recommendations.append("Optimize database queries and add appropriate indexes")
                elif 'EKS' in cause['cause']:
                    recommendations.append("Implement horizontal pod autoscaling for derivatives processing")
                    recommendations.append("Review resource requests/limits for pods")
                elif 'SQS' in cause['cause']:
                    recommendations.append("Increase SQS consumer concurrency")
                    recommendations.append("Implement dead letter queue for failed messages")
        
        recommendations.append("Set up predictive monitoring to detect issues before SLA breach")
        
        return list(set(recommendations))
    
    def _create_metrics_summary(self, metrics: Dict) -> Dict:
        summary = {
            'marker_event': 'Not available',
            'dag_processing': 'Not available',
            'eks_status': 'Not available',
            'rds_status': 'Not available',
            'sqs_status': 'Not available'
        }
        
        if metrics.get('markerEvent'):
            marker = metrics['markerEvent']
            delay = marker.get('delay_in_minutes', 0)
            summary['marker_event'] = f"{'Delayed' if delay > 0 else 'On time'} ({delay} min delay)" if delay else 'On time'
        
        if metrics.get('dagDetails'):
            dags = metrics['dagDetails'].get('dags', [])
            derivatives_dags = [d for d in dags if 'derivatives' in d.get('dag_id', '').lower()]
            summary['dag_processing'] = f"{len(derivatives_dags)} DAGs processed"
        
        if metrics.get('eksMetrics'):
            pods = metrics['eksMetrics'].get('pods', [])
            high_cpu = sum(1 for p in pods if p.get('cpu_usage_percentage', 0) > 80)
            summary['eks_status'] = f"{len(pods)} pods, {high_cpu} with high CPU"
        
        if metrics.get('rdsMetrics'):
            db_metrics = metrics['rdsMetrics'].get('database_metrics', [])
            if db_metrics:
                avg_cpu = sum(m.get('cpu_utilization', 0) for m in db_metrics) / len(db_metrics)
                summary['rds_status'] = f"Avg CPU: {avg_cpu:.1f}%"
        
        if metrics.get('sqsMetrics'):
            queue_metrics = metrics['sqsMetrics'].get('queue_metrics', [])
            if queue_metrics:
                max_messages = max(m.get('approximate_number_of_messages_visible', 0) for m in queue_metrics)
                summary['sqs_status'] = f"Max queue depth: {max_messages}"
        
        return summary
    
    def _is_within_timeframe(self, timestamp: str, start_time: str, end_time: str) -> bool:
        try:
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            return start <= ts <= end
        except:
            return False