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

    def load_failure_logs(self, date: str) -> Dict:
        """
        Load and analyze stderr.gz log file for a given date.
        Returns extracted error context with surrounding lines.
        """
        result = {
            'available': False,
            'file_path': None,
            'error_contexts': [],
            'summary': None,
            'total_errors_found': 0
        }

        log_file_path = os.path.join(self.base_path, self.log_folder, f"{date}_stderr.gz")
        result['file_path'] = log_file_path

        logger.info(f"Looking for log file: {log_file_path}")

        if not os.path.exists(log_file_path):
            logger.warning(f"Log file not found: {log_file_path}")
            result['summary'] = "No error logs available for this failure"
            return result

        try:
            lines = self._read_gzip_file(log_file_path)
            if not lines:
                result['summary'] = "Log file is empty"
                return result

            result['available'] = True
            error_contexts = self._extract_error_contexts(lines)
            result['error_contexts'] = error_contexts
            result['total_errors_found'] = len(error_contexts)

            if error_contexts:
                result['summary'] = self._generate_summary(error_contexts)
            else:
                result['summary'] = "No ERROR or EXCEPTION patterns found in log file"

            logger.info(f"Found {len(error_contexts)} error contexts in log file")
            return result

        except Exception as e:
            logger.error(f"Error reading log file {log_file_path}: {str(e)}")
            result['summary'] = f"Error reading log file: {str(e)}"
            return result

    def _read_gzip_file(self, file_path: str) -> List[str]:
        """Read and decompress a gzip file, returning lines."""
        lines = []
        try:
            with gzip.open(file_path, 'rt', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"Error decompressing file: {str(e)}")
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
