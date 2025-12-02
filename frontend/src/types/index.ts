export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isTyping?: boolean;
  metadata?: MessageMetadata;
}

export interface MessageMetadata {
  timeline?: TimelineEvent[];
  metrics_summary?: MetricsSummary;
  sla_status?: SLAStatus;
  root_causes?: RootCause[];
  failure_logs?: FailureLogs;
}

export interface FailureLogs {
  available: boolean;
  file_path: string | null;
  error_contexts: ErrorContext[];
  summary: string | null;
  total_errors_found: number;
}

export interface ErrorContext {
  error_line_number: number;
  error_message: string;
  context: LogLine[];
  error_type: string;
}

export interface LogLine {
  line_number: number;
  content: string;
  is_error_line: boolean;
}

export interface TimelineEvent {
  timestamp: string;
  event: string;
  severity: 'critical' | 'warning' | 'info';
  details: string;
  impact: string;
}

export interface MetricsSummary {
  marker_event: string;
  dag_processing: string;
  eks_status: string;
  rds_status: string;
  sqs_status: string;
}

export interface SLAStatus {
  breached: boolean;
  duration_hours: number;
  expected_hours: number;
  excess_hours: number;
  arrival_time: string;
  completion_time: string;
}

export interface RootCause {
  category: string;
  severity: string;
  cause: string;
  impact: string;
  evidence: string;
  contribution_percentage: number;
}

export interface ChatResponse {
  analysis: string;
  timeline: TimelineEvent[];
  metrics_summary: MetricsSummary;
  sla_status: SLAStatus;
  root_causes: RootCause[];
  failure_logs?: FailureLogs;
  timestamp: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  services: {
    metric_loader: string;
    rca_analyzer: string;
    azure_ai: boolean;
  };
}