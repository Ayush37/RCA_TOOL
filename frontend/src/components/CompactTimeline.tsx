import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Collapse,
  Chip,
  LinearProgress,
  useTheme,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Timeline as TimelineIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

interface TimelineEvent {
  timestamp: string;
  event: string;
  severity: 'critical' | 'warning' | 'info' | 'success';
  details: string;
  impact?: string;
}

interface CompactTimelineProps {
  events: TimelineEvent[];
  processingDuration?: number;
  slaHours?: number;
}

const CompactTimeline: React.FC<CompactTimelineProps> = ({ 
  events, 
  processingDuration = 0,
  slaHours = 3 
}) => {
  const [expanded, setExpanded] = useState(false);
  const theme = useTheme();

  const criticalCount = events.filter(e => e.severity === 'critical').length;
  const warningCount = events.filter(e => e.severity === 'warning').length;
  const slaBreached = processingDuration > slaHours;

  const formatTime = (timestamp: string): string => {
    try {
      const date = new Date(timestamp.replace('Z', '+00:00'));
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      });
    } catch {
      return timestamp;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return theme.palette.error.main;
      case 'warning':
        return theme.palette.warning.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        mt: 2,
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      {/* Header Section */}
      <Box
        sx={{
          px: 2,
          py: 1.5,
          backgroundColor: theme.palette.mode === 'dark' 
            ? 'rgba(255,255,255,0.02)' 
            : 'rgba(0,0,0,0.02)',
          borderBottom: '1px solid',
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <TimelineIcon sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
        <Typography variant="subtitle2" fontWeight={600} sx={{ flexGrow: 1 }}>
          Timeline Analysis
        </Typography>
        
        {/* Issue counts */}
        {criticalCount > 0 && (
          <Chip
            icon={<ErrorIcon sx={{ fontSize: 16 }} />}
            label={criticalCount}
            size="small"
            color="error"
            variant="outlined"
            sx={{ mr: 1, height: 24 }}
          />
        )}
        {warningCount > 0 && (
          <Chip
            icon={<WarningIcon sx={{ fontSize: 16 }} />}
            label={warningCount}
            size="small"
            color="warning"
            variant="outlined"
            sx={{ mr: 1, height: 24 }}
          />
        )}
        
        <IconButton size="small">
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>

      {/* SLA Progress Bar */}
      <Box sx={{ px: 2, py: 1 }}>
        <Box display="flex" justifyContent="space-between" mb={0.5}>
          <Typography variant="caption" color="text.secondary">
            Processing Duration
          </Typography>
          <Typography 
            variant="caption" 
            fontWeight={600}
            color={slaBreached ? 'error.main' : 'success.main'}
          >
            {processingDuration.toFixed(1)} / {slaHours} hours
          </Typography>
        </Box>
        <Tooltip title={`${((processingDuration / slaHours) * 100).toFixed(0)}% of SLA`}>
          <LinearProgress
            variant="determinate"
            value={Math.min((processingDuration / slaHours) * 100, 100)}
            sx={{
              height: 6,
              borderRadius: 1,
              backgroundColor: theme.palette.mode === 'dark' 
                ? 'rgba(255,255,255,0.1)' 
                : 'rgba(0,0,0,0.1)',
              '& .MuiLinearProgress-bar': {
                backgroundColor: slaBreached 
                  ? theme.palette.error.main 
                  : theme.palette.success.main,
              },
            }}
          />
        </Tooltip>
      </Box>

      {/* Expandable Timeline Details */}
      <Collapse in={expanded}>
        <Box sx={{ p: 2, pt: 0 }}>
          {events.map((event, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                alignItems: 'flex-start',
                mb: 2,
                position: 'relative',
                '&:last-child': { mb: 0 },
              }}
            >
              {/* Timeline connector */}
              {index < events.length - 1 && (
                <Box
                  sx={{
                    position: 'absolute',
                    left: 9,
                    top: 20,
                    bottom: -16,
                    width: 2,
                    backgroundColor: 'divider',
                  }}
                />
              )}

              {/* Timeline dot */}
              <Box
                sx={{
                  width: 20,
                  height: 20,
                  borderRadius: '50%',
                  backgroundColor: getSeverityColor(event.severity),
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  mr: 2,
                  zIndex: 1,
                }}
              >
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: 'background.paper',
                  }}
                />
              </Box>

              {/* Event content */}
              <Box sx={{ flexGrow: 1 }}>
                <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                  <Typography variant="caption" fontWeight={600}>
                    {formatTime(event.timestamp)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    •
                  </Typography>
                  <Typography variant="caption" fontWeight={500}>
                    {event.event}
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary" display="block">
                  {event.details}
                </Typography>
                {event.impact && (
                  <Typography 
                    variant="caption" 
                    color="text.secondary" 
                    display="block"
                    sx={{ 
                      mt: 0.5,
                      pl: 2,
                      borderLeft: '2px solid',
                      borderColor: 'divider',
                      fontStyle: 'italic',
                    }}
                  >
                    → {event.impact}
                  </Typography>
                )}
              </Box>
            </Box>
          ))}
        </Box>
      </Collapse>
    </Paper>
  );
};

export default CompactTimeline;