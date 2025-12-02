import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Collapse,
  IconButton,
  Chip,
  Alert,
  AlertTitle,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Psychology as AIIcon,
  BugReport as BugIcon,
  Lightbulb as LightbulbIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { FailureLogs, AILogAnalysis } from '../types';

interface AILogInsightsProps {
  failureLogs: FailureLogs;
}

const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' | 'success' => {
  switch (severity?.toLowerCase()) {
    case 'critical':
    case 'high':
      return 'error';
    case 'medium':
      return 'warning';
    case 'low':
      return 'info';
    default:
      return 'info';
  }
};

const AILogInsights: React.FC<AILogInsightsProps> = ({ failureLogs }) => {
  const [expanded, setExpanded] = useState(true);

  if (!failureLogs?.ai_analysis) {
    return null;
  }

  const analysis: AILogAnalysis = failureLogs.ai_analysis;
  const severityColor = getSeverityColor(analysis.severity_assessment);

  // Get the top priority fix
  const topFix = analysis.suggested_fixes?.[0];

  return (
    <Paper
      elevation={0}
      sx={{
        mt: 2,
        border: '1px solid',
        borderColor: 'primary.light',
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
          p: 1.5,
          bgcolor: 'grey.50',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Box display="flex" alignItems="center" gap={1}>
          <AIIcon sx={{ color: 'primary.main', fontSize: 22 }} />
          <Typography variant="subtitle2" fontWeight={600} color="primary.main">
            AI-Powered Log Analysis
          </Typography>
          <Chip
            label={analysis.severity_assessment?.toUpperCase() || 'ANALYSIS'}
            size="small"
            color={severityColor}
            sx={{ height: 20, fontSize: '0.65rem' }}
          />
        </Box>
        <IconButton size="small">
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>

      {/* Content */}
      <Collapse in={expanded}>
        <Box sx={{ p: 2 }}>
          {/* DAG Failure Summary */}
          <Alert
            severity={severityColor}
            icon={<BugIcon fontSize="small" />}
            sx={{ mb: 2, py: 0.5 }}
          >
            <AlertTitle sx={{ fontWeight: 600, fontSize: '0.875rem', mb: 0.5 }}>
              DAG Failure Summary
            </AlertTitle>
            <Typography variant="body2">{analysis.summary}</Typography>
          </Alert>

          {/* Root Cause */}
          <Box sx={{ mb: 2 }}>
            <Box display="flex" alignItems="center" gap={0.5} mb={0.5}>
              <ErrorIcon sx={{ fontSize: 18, color: 'error.main' }} />
              <Typography variant="subtitle2" fontWeight={600} fontSize="0.8rem">
                Root Cause Identified
              </Typography>
            </Box>
            <Paper
              elevation={0}
              sx={{
                p: 1.5,
                backgroundColor: 'error.50',
                borderLeft: '3px solid',
                borderColor: 'error.main',
              }}
            >
              <Typography variant="body2">{analysis.root_cause}</Typography>
            </Paper>
          </Box>

          {/* Recommended Action - Single Point */}
          {topFix && (
            <Box>
              <Box display="flex" alignItems="center" gap={0.5} mb={0.5}>
                <LightbulbIcon sx={{ fontSize: 18, color: 'success.main' }} />
                <Typography variant="subtitle2" fontWeight={600} fontSize="0.8rem">
                  Recommended Action
                </Typography>
              </Box>
              <Paper
                elevation={0}
                sx={{
                  p: 1.5,
                  backgroundColor: 'success.50',
                  borderLeft: '3px solid',
                  borderColor: 'success.main',
                }}
              >
                <Typography variant="body2" fontWeight={500}>
                  {topFix.action}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {topFix.rationale}
                </Typography>
              </Paper>
            </Box>
          )}
        </Box>
      </Collapse>
    </Paper>
  );
};

export default AILogInsights;
