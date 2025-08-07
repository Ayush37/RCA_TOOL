import React from 'react';
import {
  Paper,
  Box,
  Typography,
  IconButton,
  Chip,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  Close,
  Error,
  Warning,
  Info,
  Timeline as TimelineIcon,
  AccessTime,
} from '@mui/icons-material';
import { TimelineEvent } from '../types';
import { format, parseISO } from 'date-fns';

interface TimelineProps {
  events: TimelineEvent[];
  onClose: () => void;
}

const Timeline: React.FC<TimelineProps> = ({ events, onClose }) => {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <Error sx={{ fontSize: 16 }} />;
      case 'warning':
        return <Warning sx={{ fontSize: 16 }} />;
      default:
        return <Info sx={{ fontSize: 16 }} />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'info';
    }
  };

  const formatTime = (timestamp: string) => {
    try {
      const date = parseISO(timestamp);
      return format(date, 'HH:mm:ss');
    } catch {
      return timestamp;
    }
  };

  return (
    <Paper
      elevation={3}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 2,
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          p: 2,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: 1,
          borderColor: 'divider',
          background: (theme) =>
            theme.palette.mode === 'dark'
              ? 'linear-gradient(135deg, #2a2a3e 0%, #1e1e2e 100%)'
              : 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
        }}
      >
        <Box display="flex" alignItems="center" gap={1}>
          <TimelineIcon sx={{ color: 'white' }} />
          <Typography variant="h6" fontWeight="bold" color="white">
            Event Timeline
          </Typography>
        </Box>
        <IconButton size="small" onClick={onClose} sx={{ color: 'white' }}>
          <Close />
        </IconButton>
      </Box>

      <Box sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
        {events.map((event, index) => (
          <Box key={index} sx={{ mb: 3, position: 'relative' }}>
            {index < events.length - 1 && (
              <Box
                sx={{
                  position: 'absolute',
                  left: 20,
                  top: 40,
                  bottom: -24,
                  width: 2,
                  backgroundColor: 'divider',
                }}
              />
            )}

            <Box display="flex" gap={2}>
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  backgroundColor: `${getSeverityColor(event.severity)}.main`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  flexShrink: 0,
                }}
              >
                {getSeverityIcon(event.severity)}
              </Box>

              <Box flex={1}>
                <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                  <Chip
                    icon={<AccessTime />}
                    label={formatTime(event.timestamp)}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={event.severity}
                    size="small"
                    color={getSeverityColor(event.severity) as any}
                  />
                </Box>

                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                  {event.event}
                </Typography>

                <Typography variant="body2" color="text.secondary" paragraph>
                  {event.details}
                </Typography>

                {event.impact && (
                  <Tooltip title="Impact Analysis">
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 1,
                        backgroundColor: (theme) =>
                          theme.palette.mode === 'dark'
                            ? 'rgba(255, 255, 255, 0.05)'
                            : 'rgba(0, 0, 0, 0.03)',
                      }}
                    >
                      <Typography variant="caption" color="text.secondary">
                        <strong>Impact:</strong> {event.impact}
                      </Typography>
                    </Paper>
                  </Tooltip>
                )}
              </Box>
            </Box>
          </Box>
        ))}
      </Box>

      <Divider />
      
      <Box sx={{ p: 2, backgroundColor: 'background.default' }}>
        <Typography variant="caption" color="text.secondary">
          {events.length} events tracked • Sorted chronologically
        </Typography>
      </Box>
    </Paper>
  );
};

export default Timeline;