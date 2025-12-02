import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
} from '@mui/lab';
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  Storage as DatabaseIcon,
  CloudQueue as QueueIcon,
  Memory as ComputeIcon,
  Schedule as ClockIcon,
  BugReport as BugIcon,
  Speed as PerformanceIcon,
} from '@mui/icons-material';

interface TimelineEvent {
  timestamp: string;
  event: string;
  severity: 'critical' | 'warning' | 'info' | 'success';
  details: string;
  impact?: string;
  metrics?: any;
}

interface TimelineGraphProps {
  events: TimelineEvent[];
  title?: string;
}

const TimelineGraph: React.FC<TimelineGraphProps> = ({ events, title = "Processing Timeline" }) => {
  const theme = useTheme();

  const formatTime = (timestamp: string): string => {
    try {
      // Handle different timestamp formats
      let date: Date;
      
      if (timestamp.includes('T')) {
        // ISO format with time
        if (timestamp.endsWith('Z')) {
          // UTC timestamp like "2025-08-01T07:15:00Z"
          date = new Date(timestamp);
        } else if (timestamp.includes('+') || timestamp.includes('-')) {
          // Timestamp with timezone offset
          date = new Date(timestamp);
        } else {
          // Assume local time if no timezone info
          date = new Date(timestamp + 'Z'); // Treat as UTC
        }
      } else {
        // Format like "2025-08-01 15:41:48.558433" - treat as local/UTC
        date = new Date(timestamp.replace(' ', 'T') + 'Z');
      }
      
      // Format in UTC time (since our data is in UTC)
      const hours = date.getUTCHours();
      const minutes = date.getUTCMinutes();
      const ampm = hours >= 12 ? 'PM' : 'AM';
      const displayHours = hours % 12 || 12;
      
      return `${displayHours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')} ${ampm}`;
    } catch (e) {
      console.error('Error formatting time:', timestamp, e);
      return timestamp;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return theme.palette.error.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'success':
        return theme.palette.success.main;
      default:
        return theme.palette.info.main;
    }
  };

  const getSeverityIcon = (event: TimelineEvent) => {
    // Check event type for specific icons
    if (event.event.toLowerCase().includes('rds') || event.event.toLowerCase().includes('database')) {
      return <DatabaseIcon />;
    }
    if (event.event.toLowerCase().includes('sqs') || event.event.toLowerCase().includes('queue')) {
      return <QueueIcon />;
    }
    if (event.event.toLowerCase().includes('eks') || event.event.toLowerCase().includes('cluster')) {
      return <ComputeIcon />;
    }
    if (event.event.toLowerCase().includes('marker')) {
      return <ClockIcon />;
    }
    if (event.event.toLowerCase().includes('fail')) {
      return <BugIcon />;
    }
    if (event.event.toLowerCase().includes('performance') || event.event.toLowerCase().includes('degradation')) {
      return <PerformanceIcon />;
    }

    // Default icons based on severity
    switch (event.severity) {
      case 'critical':
        return <ErrorIcon />;
      case 'warning':
        return <WarningIcon />;
      case 'success':
        return <SuccessIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const getEventBackgroundColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return theme.palette.mode === 'dark' 
          ? 'rgba(244, 67, 54, 0.1)' 
          : 'rgba(244, 67, 54, 0.05)';
      case 'warning':
        return theme.palette.mode === 'dark'
          ? 'rgba(255, 152, 0, 0.1)'
          : 'rgba(255, 152, 0, 0.05)';
      case 'success':
        return theme.palette.mode === 'dark'
          ? 'rgba(76, 175, 80, 0.1)'
          : 'rgba(76, 175, 80, 0.05)';
      default:
        return 'transparent';
    }
  };

  if (!events || events.length === 0) {
    return null;
  }

  // Sort events in ascending chronological order
  const sortedEvents = [...events].sort((a, b) => {
    const dateA = new Date(a.timestamp).getTime();
    const dateB = new Date(b.timestamp).getTime();
    return dateA - dateB;
  });

  return (
    <Paper 
      elevation={0}
      sx={{ 
        p: 3, 
        mb: 2,
        background: theme.palette.mode === 'dark' 
          ? 'linear-gradient(135deg, rgba(25,25,25,0.95) 0%, rgba(35,35,35,0.95) 100%)'
          : 'linear-gradient(135deg, rgba(250,250,250,0.95) 0%, rgba(245,245,245,0.95) 100%)',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
      }}
    >
      <Box display="flex" alignItems="center" mb={3}>
        <Typography variant="h6" fontWeight={600} sx={{ flexGrow: 1 }}>
          {title}
        </Typography>
        <Chip 
          label={`${events.length} Events`}
          size="small"
          variant="outlined"
          sx={{ ml: 2 }}
        />
      </Box>

      <Timeline position="alternate">
        {sortedEvents.map((event, index) => (
          <TimelineItem key={index}>
            <TimelineOppositeContent
              sx={{ m: 'auto 0' }}
              variant="body2"
              color="text.secondary"
            >
              <Typography variant="caption" fontWeight={600}>
                {formatTime(event.timestamp)}
              </Typography>
            </TimelineOppositeContent>
            
            <TimelineSeparator>
              <TimelineConnector 
                sx={{ 
                  bgcolor: index === 0 ? 'transparent' : 'grey.300',
                  opacity: index === 0 ? 0 : 1,
                }} 
              />
              <Tooltip 
                title={`${event.severity.toUpperCase()}: ${event.impact || event.details}`}
                placement={index % 2 === 0 ? "right" : "left"}
              >
                <TimelineDot 
                  sx={{ 
                    bgcolor: getSeverityColor(event.severity),
                    boxShadow: theme.shadows[3],
                    '&:hover': {
                      transform: 'scale(1.2)',
                      transition: 'transform 0.2s',
                    }
                  }}
                >
                  {getSeverityIcon(event)}
                </TimelineDot>
              </Tooltip>
              <TimelineConnector 
                sx={{ 
                  bgcolor: index === sortedEvents.length - 1 ? 'transparent' : 'grey.300',
                  opacity: index === sortedEvents.length - 1 ? 0 : 1,
                }} 
              />
            </TimelineSeparator>
            
            <TimelineContent sx={{ py: '12px', px: 2 }}>
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  backgroundColor: getEventBackgroundColor(event.severity),
                  border: '1px solid',
                  borderColor: getSeverityColor(event.severity),
                  borderLeft: `4px solid ${getSeverityColor(event.severity)}`,
                  transition: 'all 0.3s',
                  '&:hover': {
                    transform: 'translateX(4px)',
                    boxShadow: theme.shadows[2],
                  }
                }}
              >
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  {event.event}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {event.details}
                </Typography>
                {event.impact && (
                  <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="caption" color="text.secondary" display="flex" alignItems="center">
                      <InfoIcon sx={{ fontSize: 14, mr: 0.5 }} />
                      Impact: {event.impact}
                    </Typography>
                  </Box>
                )}
                {event.metrics && Object.keys(event.metrics).length > 0 && (
                  <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {Object.entries(event.metrics).slice(0, 3).map(([key, value]) => (
                      <Chip
                        key={key}
                        label={`${key}: ${value}`}
                        size="small"
                        variant="outlined"
                        sx={{ 
                          height: 20,
                          fontSize: '0.7rem',
                          borderColor: getSeverityColor(event.severity),
                          color: getSeverityColor(event.severity),
                        }}
                      />
                    ))}
                  </Box>
                )}
              </Paper>
            </TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>

      {/* Summary Section */}
      <Box 
        sx={{ 
          mt: 3, 
          pt: 2, 
          borderTop: '2px solid',
          borderColor: 'divider',
          display: 'flex',
          justifyContent: 'space-around',
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        <Box textAlign="center">
          <Typography variant="caption" color="text.secondary">
            Critical Issues
          </Typography>
          <Typography variant="h6" color="error.main" fontWeight={600}>
            {events.filter(e => e.severity === 'critical').length}
          </Typography>
        </Box>
        <Box textAlign="center">
          <Typography variant="caption" color="text.secondary">
            Warnings
          </Typography>
          <Typography variant="h6" color="warning.main" fontWeight={600}>
            {events.filter(e => e.severity === 'warning').length}
          </Typography>
        </Box>
        <Box textAlign="center">
          <Typography variant="caption" color="text.secondary">
            Total Duration
          </Typography>
          <Typography variant="h6" color="text.primary" fontWeight={600}>
            {(() => {
              if (events.length < 2) return 'N/A';
              try {
                const start = new Date(events[0].timestamp);
                const end = new Date(events[events.length - 1].timestamp);
                const duration = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
                return `${duration.toFixed(1)} hrs`;
              } catch {
                return 'N/A';
              }
            })()}
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
};

export default TimelineGraph;