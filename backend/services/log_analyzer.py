import gzip
import os
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LogAnalyzer:
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.log_folder = 'failed_dag_log'
        self.context_lines = 10  # Lines before and after ERROR/EXCEPTION
        self.error_patterns = [
            re.compile(r'\bERROR\b', re.IGNORECASE),
            re.compile(r'\bEXCEPTION\b', re.IGNORECASE),
        ]
        self.warning_patterns = [
            re.compile(r'\bWARN(?:ING)?\b', re.IGNORECASE),
            re.compile(r'\bCRITICAL\b', re.IGNORECASE),
            re.compile(r'\bFATAL\b', re.IGNORECASE),
        ]
        self.stack_trace_patterns = [
            re.compile(r'^\s+at\s+', re.IGNORECASE),
            re.compile(r'Traceback', re.IGNORECASE),
            re.compile(r'File ".*", line \d+', re.IGNORECASE),
        ]

    def load_failure_logs(self, date: str) -> Dict:
        """
        Load and analyze stderr.gz or stderr.txt log file for a given date.
        Returns extracted error context with surrounding lines.
        """
        result = {
            'available': False,
            'file_path': None,
            'error_contexts': [],
            'summary': None,
            'total_errors_found': 0,
            'warnings_found': 0,
            'stack_traces': [],
            'log_metadata': {
                'total_lines': 0,
                'first_timestamp': None,
                'last_timestamp': None,
                'error_timeline': []
            },
            'ai_analysis': None  # Will be populated by LLM
        }

        # Try .gz first, then .txt
        gz_path = os.path.join(self.base_path, self.log_folder, f"{date}_stderr.gz")
        txt_path = os.path.join(self.base_path, self.log_folder, f"{date}_stderr.txt")

        log_file_path = None
        is_gzip = False

        if os.path.exists(gz_path):
            log_file_path = gz_path
            is_gzip = True
            logger.info(f"Found gzip log file: {log_file_path}")
        elif os.path.exists(txt_path):
            log_file_path = txt_path
            is_gzip = False
            logger.info(f"Found text log file: {log_file_path}")
        else:
            logger.warning(f"Log file not found: {gz_path} or {txt_path}")
            result['summary'] = "No error logs available for this failure"
            return result

        result['file_path'] = log_file_path

        try:
            lines = self._read_log_file(log_file_path, is_gzip)
            if not lines:
                result['summary'] = "Log file is empty"
                return result

            result['available'] = True
            result['log_metadata']['total_lines'] = len(lines)

            # Extract timestamps from first and last lines
            result['log_metadata']['first_timestamp'] = self._extract_timestamp(lines[0]) if lines else None
            result['log_metadata']['last_timestamp'] = self._extract_timestamp(lines[-1]) if lines else None

            # Extract error contexts
            error_contexts = self._extract_error_contexts(lines)
            result['error_contexts'] = error_contexts
            result['total_errors_found'] = len(error_contexts)

            # Extract warnings count
            result['warnings_found'] = self._count_warnings(lines)

            # Extract stack traces
            result['stack_traces'] = self._extract_stack_traces(lines)

            # Build error timeline
            result['log_metadata']['error_timeline'] = self._build_error_timeline(lines)

            if error_contexts:
                result['summary'] = self._generate_summary(error_contexts)
            else:
                result['summary'] = "No ERROR or EXCEPTION patterns found in log file"

            logger.info(f"Found {len(error_contexts)} error contexts, {result['warnings_found']} warnings in log file")
            return result

        except Exception as e:
            logger.error(f"Error reading log file {log_file_path}: {str(e)}")
            result['summary'] = f"Error reading log file: {str(e)}"
            return result

    def _read_log_file(self, file_path: str, is_gzip: bool = False) -> List[str]:
        """Read a log file (gzip or plain text), returning lines."""
        lines = []
        try:
            if is_gzip:
                with gzip.open(file_path, 'rt', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
            else:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            raise
        return lines

    def _extract_error_contexts(self, lines: List[str]) -> List[Dict]:
        """
        Find ERROR/EXCEPTION patterns and extract surrounding context.
        Returns list of error contexts with line numbers and content.
        """
        error_contexts = []
        total_lines = len(lines)
        processed_ranges = set()  # Track processed line ranges to avoid duplicates

        for i, line in enumerate(lines):
            # Check if line matches any error pattern
            is_error_line = any(pattern.search(line) for pattern in self.error_patterns)

            if is_error_line:
                # Calculate context range
                start_idx = max(0, i - self.context_lines)
                end_idx = min(total_lines, i + self.context_lines + 1)

                # Create a key for this range to avoid duplicates
                range_key = (start_idx, end_idx)

                # Check if this range overlaps with already processed ranges
                is_overlap = False
                for processed_start, processed_end in processed_ranges:
                    if start_idx <= processed_end and end_idx >= processed_start:
                        is_overlap = True
                        break

                if not is_overlap:
                    processed_ranges.add(range_key)

                    context_lines = []
                    for j in range(start_idx, end_idx):
                        context_lines.append({
                            'line_number': j + 1,
                            'content': lines[j].rstrip(),
                            'is_error_line': j == i
                        })

                    # Extract the main error message
                    error_message = self._extract_error_message(line)

                    error_contexts.append({
                        'error_line_number': i + 1,
                        'error_message': error_message,
                        'context': context_lines,
                        'error_type': self._classify_error(line)
                    })

        # Limit to most relevant errors (first 5 unique contexts)
        return error_contexts[:5]

    def _extract_error_message(self, line: str) -> str:
        """Extract the main error message from a log line."""
        # Remove timestamp patterns at the beginning
        cleaned = re.sub(r'^\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[.,]?\d*\s*', '', line)
        # Remove common log prefixes
        cleaned = re.sub(r'^(INFO|DEBUG|WARN|WARNING|ERROR|CRITICAL|FATAL)\s*[-:]\s*', '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()[:500]  # Limit length

    def _classify_error(self, line: str) -> str:
        """Classify the type of error based on common patterns."""
        line_lower = line.lower()

        if 'connection' in line_lower or 'timeout' in line_lower:
            return 'Connection/Timeout Error'
        elif 'memory' in line_lower or 'oom' in line_lower:
            return 'Memory Error'
        elif 'permission' in line_lower or 'access denied' in line_lower:
            return 'Permission Error'
        elif 'null' in line_lower or 'none' in line_lower:
            return 'Null Reference Error'
        elif 'database' in line_lower or 'sql' in line_lower:
            return 'Database Error'
        elif 'file' in line_lower and ('not found' in line_lower or 'missing' in line_lower):
            return 'File Not Found Error'
        elif 'exception' in line_lower:
            return 'Exception'
        else:
            return 'Error'

    def _generate_summary(self, error_contexts: List[Dict]) -> str:
        """Generate a human-readable summary of the errors found."""
        if not error_contexts:
            return "No errors found in log file"

        error_types = {}
        for ctx in error_contexts:
            error_type = ctx['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1

        summary_parts = []
        summary_parts.append(f"Found {len(error_contexts)} error(s) in the log file")

        type_descriptions = []
        for error_type, count in error_types.items():
            type_descriptions.append(f"{count} {error_type}(s)")

        if type_descriptions:
            summary_parts.append(f"Types: {', '.join(type_descriptions)}")

        # Add the first error message as the primary cause
        if error_contexts:
            primary_error = error_contexts[0]['error_message']
            if len(primary_error) > 200:
                primary_error = primary_error[:200] + "..."
            summary_parts.append(f"Primary error: {primary_error}")

        return " | ".join(summary_parts)

    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from a log line."""
        # Match common timestamp formats
        patterns = [
            r'(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[.,]?\d*)',
            r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})',
        ]
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return None

    def _count_warnings(self, lines: List[str]) -> int:
        """Count warning lines in the log."""
        count = 0
        for line in lines:
            if any(pattern.search(line) for pattern in self.warning_patterns):
                count += 1
        return count

    def _extract_stack_traces(self, lines: List[str]) -> List[Dict]:
        """Extract stack trace blocks from the log."""
        stack_traces = []
        current_trace = []
        in_trace = False

        for i, line in enumerate(lines):
            is_trace_line = any(pattern.search(line) for pattern in self.stack_trace_patterns)
            is_error_line = any(pattern.search(line) for pattern in self.error_patterns)

            if is_error_line or (is_trace_line and not in_trace):
                if current_trace:
                    stack_traces.append({
                        'start_line': current_trace[0]['line_number'],
                        'lines': current_trace
                    })
                current_trace = []
                in_trace = True

            if in_trace:
                if is_trace_line or is_error_line or line.strip().startswith('at '):
                    current_trace.append({
                        'line_number': i + 1,
                        'content': line.rstrip()
                    })
                elif current_trace and not line.strip():
                    # Empty line might continue trace
                    pass
                else:
                    # End of trace
                    if current_trace:
                        stack_traces.append({
                            'start_line': current_trace[0]['line_number'],
                            'lines': current_trace
                        })
                    current_trace = []
                    in_trace = False

        # Don't forget the last trace
        if current_trace:
            stack_traces.append({
                'start_line': current_trace[0]['line_number'],
                'lines': current_trace
            })

        return stack_traces[:3]  # Limit to first 3 stack traces

    def _build_error_timeline(self, lines: List[str]) -> List[Dict]:
        """Build a timeline of errors and warnings."""
        timeline = []

        for i, line in enumerate(lines):
            timestamp = self._extract_timestamp(line)
            is_error = any(pattern.search(line) for pattern in self.error_patterns)
            is_warning = any(pattern.search(line) for pattern in self.warning_patterns)

            if is_error or is_warning:
                timeline.append({
                    'line_number': i + 1,
                    'timestamp': timestamp,
                    'level': 'error' if is_error else 'warning',
                    'message': self._extract_error_message(line)[:200]
                })

        return timeline[:20]  # Limit to first 20 events

    def get_log_content_for_llm(self, failure_logs: Dict) -> str:
        """
        Prepare log content for LLM analysis.
        Returns a condensed version of the logs suitable for AI analysis.
        """
        if not failure_logs.get('available'):
            return "No log file available for analysis."

        parts = []

        # Add metadata
        metadata = failure_logs.get('log_metadata', {})
        parts.append(f"=== LOG FILE ANALYSIS ===")
        parts.append(f"Total lines: {metadata.get('total_lines', 'N/A')}")
        parts.append(f"Time range: {metadata.get('first_timestamp', 'N/A')} to {metadata.get('last_timestamp', 'N/A')}")
        parts.append(f"Errors found: {failure_logs.get('total_errors_found', 0)}")
        parts.append(f"Warnings found: {failure_logs.get('warnings_found', 0)}")
        parts.append("")

        # Add error timeline
        error_timeline = metadata.get('error_timeline', [])
        if error_timeline:
            parts.append("=== ERROR/WARNING TIMELINE ===")
            for event in error_timeline:
                level = event.get('level', 'unknown').upper()
                ts = event.get('timestamp', 'N/A')
                msg = event.get('message', '')
                parts.append(f"[{ts}] {level}: {msg}")
            parts.append("")

        # Add error contexts with surrounding lines
        error_contexts = failure_logs.get('error_contexts', [])
        if error_contexts:
            parts.append("=== DETAILED ERROR CONTEXTS ===")
            for i, ctx in enumerate(error_contexts, 1):
                parts.append(f"\n--- Error #{i}: {ctx.get('error_type', 'Unknown')} (Line {ctx.get('error_line_number', 'N/A')}) ---")
                parts.append(f"Error message: {ctx.get('error_message', 'N/A')}")
                parts.append("\nContext (surrounding lines):")
                for line_info in ctx.get('context', []):
                    prefix = ">>>" if line_info.get('is_error_line') else "   "
                    parts.append(f"{prefix} {line_info.get('line_number', '')}: {line_info.get('content', '')}")
            parts.append("")

        # Add stack traces
        stack_traces = failure_logs.get('stack_traces', [])
        if stack_traces:
            parts.append("=== STACK TRACES ===")
            for i, trace in enumerate(stack_traces, 1):
                parts.append(f"\n--- Stack Trace #{i} ---")
                for line_info in trace.get('lines', []):
                    parts.append(f"  {line_info.get('content', '')}")
            parts.append("")

        return "\n".join(parts)
