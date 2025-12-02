import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Collapse,
  IconButton,
  Chip,
  Divider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { FailureLogs } from '../types';

interface FailureLogAnalysisProps {
  failureLogs: FailureLogs;
}

const FailureLogAnalysis: React.FC<FailureLogAnalysisProps> = ({ failureLogs }) => {
  const [expanded, setExpanded] = useState(false);
  const [expandedContexts, setExpandedContexts] = useState<Set<number>>(new Set());

  const toggleContext = (index: number) => {
    const newExpanded = new Set(expandedContexts);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedContexts(newExpanded);
  };

  if (!failureLogs) {
    return null;
  }

  return (
    <Paper
      elevation={0}
      sx={{
        mt: 2,
        border: '1px solid',
        borderColor: failureLogs.available ? 'error.light' : 'grey.300',
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 2,
          backgroundColor: failureLogs.available ? 'error.50' : 'grey.50',
          cursor: 'pointer',
          '&:hover': {
            backgroundColor: failureLogs.available ? 'error.100' : 'grey.100',
          },
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Box display="flex" alignItems="center" gap={1.5}>
          {failureLogs.available ? (
            <ErrorIcon sx={{ color: 'error.main' }} />
          ) : (
            <WarningIcon sx={{ color: 'grey.500' }} />
          )}
          <Typography variant="subtitle1" fontWeight={600}>
            Failure Log Analysis
          </Typography>
          {failureLogs.available && failureLogs.total_errors_found > 0 && (
            <Chip
              label={`${failureLogs.total_errors_found} error${failureLogs.total_errors_found > 1 ? 's' : ''}`}
              size="small"
              color="error"
              sx={{ height: 24 }}
            />
          )}
        </Box>
        <IconButton size="small">
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>

      {/* Content */}
      <Collapse in={expanded}>
        <Box sx={{ p: 2 }}>
          {/* Summary */}
          <Typography
            variant="body2"
            sx={{
              mb: 2,
              p: 1.5,
              backgroundColor: 'grey.50',
              borderRadius: 1,
              color: 'text.secondary',
            }}
          >
            {failureLogs.summary}
          </Typography>

          {/* Error Contexts */}
          {failureLogs.available && failureLogs.error_contexts.length > 0 && (
            <Box>
              {failureLogs.error_contexts.map((context, index) => (
                <Box key={index} sx={{ mb: 2 }}>
                  {/* Error Header */}
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      p: 1,
                      backgroundColor: 'error.50',
                      borderRadius: '4px 4px 0 0',
                      cursor: 'pointer',
                    }}
                    onClick={() => toggleContext(index)}
                  >
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        label={context.error_type}
                        size="small"
                        color="error"
                        variant="outlined"
                        sx={{ height: 22, fontSize: '0.75rem' }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        Line {context.error_line_number}
                      </Typography>
                    </Box>
                    <IconButton size="small">
                      {expandedContexts.has(index) ? (
                        <ExpandLessIcon fontSize="small" />
                      ) : (
                        <ExpandMoreIcon fontSize="small" />
                      )}
                    </IconButton>
                  </Box>

                  {/* Error Message Preview */}
                  <Box
                    sx={{
                      p: 1.5,
                      backgroundColor: 'grey.900',
                      color: 'error.light',
                      fontFamily: 'monospace',
                      fontSize: '0.8rem',
                      borderRadius: expandedContexts.has(index) ? 0 : '0 0 4px 4px',
                      overflowX: 'auto',
                    }}
                  >
                    <Typography
                      component="pre"
                      sx={{
                        margin: 0,
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        fontSize: 'inherit',
                        fontFamily: 'inherit',
                      }}
                    >
                      {context.error_message}
                    </Typography>
                  </Box>

                  {/* Expanded Context */}
                  <Collapse in={expandedContexts.has(index)}>
                    <Box
                      sx={{
                        backgroundColor: 'grey.900',
                        borderRadius: '0 0 4px 4px',
                        overflow: 'hidden',
                      }}
                    >
                      <Divider sx={{ borderColor: 'grey.700' }} />
                      <Box sx={{ p: 1 }}>
                        <Typography
                          variant="caption"
                          sx={{ color: 'grey.400', mb: 1, display: 'block' }}
                        >
                          Context (±10 lines):
                        </Typography>
                        {context.context.map((line, lineIndex) => (
                          <Box
                            key={lineIndex}
                            sx={{
                              display: 'flex',
                              fontFamily: 'monospace',
                              fontSize: '0.75rem',
                              backgroundColor: line.is_error_line
                                ? 'rgba(244, 67, 54, 0.2)'
                                : 'transparent',
                              borderLeft: line.is_error_line
                                ? '3px solid'
                                : '3px solid transparent',
                              borderColor: 'error.main',
                              py: 0.25,
                              px: 1,
                            }}
                          >
                            <Typography
                              component="span"
                              sx={{
                                color: 'grey.500',
                                minWidth: 50,
                                textAlign: 'right',
                                mr: 2,
                                fontFamily: 'inherit',
                                fontSize: 'inherit',
                                userSelect: 'none',
                              }}
                            >
                              {line.line_number}
                            </Typography>
                            <Typography
                              component="pre"
                              sx={{
                                color: line.is_error_line ? 'error.light' : 'grey.300',
                                margin: 0,
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-all',
                                fontFamily: 'inherit',
                                fontSize: 'inherit',
                              }}
                            >
                              {line.content}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    </Box>
                  </Collapse>
                </Box>
              ))}
            </Box>
          )}
        </Box>
      </Collapse>
    </Paper>
  );
};

export default FailureLogAnalysis;
