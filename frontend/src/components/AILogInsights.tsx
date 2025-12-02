import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Collapse,
  IconButton,
  Chip,
  Divider,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  AlertTitle,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Psychology as AIIcon,
  BugReport as BugIcon,
  Lightbulb as LightbulbIcon,
  Timeline as TimelineIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckIcon,
  ArrowForward as ArrowIcon,
  Build as BuildIcon,
  Memory as MemoryIcon,
} from '@mui/icons-material';
import { FailureLogs, AILogAnalysis, SuggestedFix } from '../types';

interface AILogInsightsProps {
  failureLogs: FailureLogs;
}

const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' | 'success' => {
  switch (severity?.toLowerCase()) {
    case 'critical':
      return 'error';
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

const getPriorityColor = (priority: string): 'error' | 'warning' | 'info' => {
  switch (priority?.toLowerCase()) {
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
  const [showErrorChain, setShowErrorChain] = useState(false);
  const [showFixes, setShowFixes] = useState(true);

  if (!failureLogs?.ai_analysis) {
    return null;
  }

  const analysis: AILogAnalysis = failureLogs.ai_analysis;
  const severityColor = getSeverityColor(analysis.severity_assessment);

  return (
    <Paper
      elevation={0}
      sx={{
        mt: 2,
        border: '2px solid',
        borderColor: 'primary.main',
        borderRadius: 2,
        overflow: 'hidden',
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%)',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 2,
          background: 'linear-gradient(90deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Box display="flex" alignItems="center" gap={1.5}>
          <AIIcon sx={{ color: 'primary.main', fontSize: 28 }} />
          <Box>
            <Typography variant="subtitle1" fontWeight={700} color="primary.main">
              AI-Powered Log Analysis
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Intelligent insights from failure logs
            </Typography>
          </Box>
          <Chip
            label={analysis.severity_assessment?.toUpperCase() || 'ANALYSIS'}
            size="small"
            color={severityColor}
            sx={{ ml: 1, fontWeight: 600 }}
          />
        </Box>
        <IconButton size="small">
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>

      {/* Content */}
      <Collapse in={expanded}>
        <Box sx={{ p: 2 }}>
          {/* Executive Summary */}
          <Alert
            severity={severityColor}
            icon={<BugIcon />}
            sx={{ mb: 3 }}
          >
            <AlertTitle sx={{ fontWeight: 600 }}>Executive Summary</AlertTitle>
            {analysis.summary}
          </Alert>

          {/* Root Cause */}
          <Box sx={{ mb: 3 }}>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <ErrorIcon color="error" />
              <Typography variant="subtitle2" fontWeight={600}>
                Root Cause Identified
              </Typography>
            </Box>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                backgroundColor: 'error.50',
                borderLeft: '4px solid',
                borderColor: 'error.main',
              }}
            >
              <Typography variant="body2">
                {analysis.root_cause}
              </Typography>
            </Paper>
          </Box>

          {/* Error Chain */}
          {analysis.error_chain && analysis.error_chain.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Box
                display="flex"
                alignItems="center"
                gap={1}
                mb={1}
                sx={{ cursor: 'pointer' }}
                onClick={() => setShowErrorChain(!showErrorChain)}
              >
                <TimelineIcon color="warning" />
                <Typography variant="subtitle2" fontWeight={600}>
                  Error Propagation Chain
                </Typography>
                <Chip label={`${analysis.error_chain.length} steps`} size="small" variant="outlined" />
                <IconButton size="small">
                  {showErrorChain ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                </IconButton>
              </Box>
              <Collapse in={showErrorChain}>
                <Box sx={{ pl: 2 }}>
                  {analysis.error_chain.map((step, index) => (
                    <Box
                      key={index}
                      display="flex"
                      alignItems="flex-start"
                      gap={1}
                      sx={{
                        mb: 1,
                        pb: 1,
                        borderLeft: '2px solid',
                        borderColor: 'warning.light',
                        pl: 2,
                      }}
                    >
                      <Chip
                        label={index + 1}
                        size="small"
                        sx={{
                          minWidth: 24,
                          height: 24,
                          fontSize: '0.75rem',
                          bgcolor: 'warning.main',
                          color: 'white',
                        }}
                      />
                      <Typography variant="body2" sx={{ pt: 0.25 }}>
                        {step}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </Collapse>
            </Box>
          )}

          {/* Affected Components */}
          {analysis.affected_components && analysis.affected_components.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <MemoryIcon color="info" />
                <Typography variant="subtitle2" fontWeight={600}>
                  Affected Components
                </Typography>
              </Box>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {analysis.affected_components.map((component, index) => (
                  <Chip
                    key={index}
                    label={component}
                    size="small"
                    variant="outlined"
                    color="info"
                    icon={<ArrowIcon />}
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Patterns Detected */}
          {analysis.patterns_detected && analysis.patterns_detected.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <WarningIcon color="warning" />
                <Typography variant="subtitle2" fontWeight={600}>
                  Patterns Detected
                </Typography>
              </Box>
              <List dense sx={{ bgcolor: 'warning.50', borderRadius: 1 }}>
                {analysis.patterns_detected.map((pattern, index) => (
                  <ListItem key={index}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <ArrowIcon fontSize="small" color="warning" />
                    </ListItemIcon>
                    <ListItemText
                      primary={pattern}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          <Divider sx={{ my: 2 }} />

          {/* Suggested Fixes */}
          {analysis.suggested_fixes && analysis.suggested_fixes.length > 0 && (
            <Box>
              <Box
                display="flex"
                alignItems="center"
                gap={1}
                mb={2}
                sx={{ cursor: 'pointer' }}
                onClick={() => setShowFixes(!showFixes)}
              >
                <LightbulbIcon sx={{ color: 'success.main' }} />
                <Typography variant="subtitle2" fontWeight={600}>
                  Recommended Actions
                </Typography>
                <Chip
                  label={`${analysis.suggested_fixes.length} suggestions`}
                  size="small"
                  color="success"
                  variant="outlined"
                />
                <IconButton size="small">
                  {showFixes ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                </IconButton>
              </Box>
              <Collapse in={showFixes}>
                {analysis.suggested_fixes.map((fix: SuggestedFix, index: number) => (
                  <Paper
                    key={index}
                    elevation={0}
                    sx={{
                      p: 2,
                      mb: 1.5,
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 2,
                      '&:hover': {
                        borderColor: 'primary.light',
                        bgcolor: 'action.hover',
                      },
                    }}
                  >
                    <Box display="flex" alignItems="flex-start" gap={2}>
                      <Box
                        sx={{
                          p: 1,
                          borderRadius: 1,
                          bgcolor: `${getPriorityColor(fix.priority)}.50`,
                        }}
                      >
                        <BuildIcon sx={{ color: `${getPriorityColor(fix.priority)}.main` }} />
                      </Box>
                      <Box flex={1}>
                        <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                          <Typography variant="subtitle2" fontWeight={600}>
                            {fix.action}
                          </Typography>
                          <Chip
                            label={fix.priority?.toUpperCase()}
                            size="small"
                            color={getPriorityColor(fix.priority)}
                            sx={{ height: 20, fontSize: '0.65rem' }}
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {fix.rationale}
                        </Typography>
                      </Box>
                    </Box>
                  </Paper>
                ))}
              </Collapse>
            </Box>
          )}

          {/* Log Stats Footer */}
          <Box
            sx={{
              mt: 2,
              pt: 2,
              borderTop: '1px solid',
              borderColor: 'divider',
              display: 'flex',
              gap: 3,
              flexWrap: 'wrap',
            }}
          >
            <Typography variant="caption" color="text.secondary">
              <strong>{failureLogs.total_errors_found}</strong> errors found
            </Typography>
            <Typography variant="caption" color="text.secondary">
              <strong>{failureLogs.warnings_found}</strong> warnings found
            </Typography>
            <Typography variant="caption" color="text.secondary">
              <strong>{failureLogs.log_metadata?.total_lines || 0}</strong> total log lines analyzed
            </Typography>
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
};

export default AILogInsights;
