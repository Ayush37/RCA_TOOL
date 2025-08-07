import React from 'react';
import {
  Paper,
  Box,
  Typography,
  IconButton,
  Chip,
  Divider,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Close,
  ExpandMore,
  Speed,
  Storage,
  Cloud,
  Queue,
  Warning,
  CheckCircle,
  TrendingUp,
  BugReport,
} from '@mui/icons-material';
import { MetricsSummary, SLAStatus, RootCause } from '../types';

interface MetricsPanelProps {
  metricsSummary?: MetricsSummary;
  slaStatus?: SLAStatus;
  rootCauses?: RootCause[];
  onClose: () => void;
}

const MetricsPanel: React.FC<MetricsPanelProps> = ({
  metricsSummary,
  slaStatus,
  rootCauses,
  onClose,
}) => {
  const getServiceIcon = (service: string) => {
    switch (service.toLowerCase()) {
      case 'eks':
        return <Cloud />;
      case 'rds':
        return <Storage />;
      case 'sqs':
        return <Queue />;
      default:
        return <Speed />;
    }
  };

  const calculateSLAPercentage = () => {
    if (!slaStatus) return 0;
    return Math.min(100, (slaStatus.duration_hours / slaStatus.expected_hours) * 100);
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
              ? 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)'
              : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        <Box display="flex" alignItems="center" gap={1}>
          <Speed sx={{ color: 'white' }} />
          <Typography variant="h6" fontWeight="bold" color="white">
            Metrics Analysis
          </Typography>
        </Box>
        <IconButton size="small" onClick={onClose} sx={{ color: 'white' }}>
          <Close />
        </IconButton>
      </Box>

      <Box sx={{ flex: 1, overflowY: 'auto' }}>
        {slaStatus && (
          <Box sx={{ p: 2 }}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
              SLA Performance
            </Typography>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              {slaStatus.breached ? (
                <Warning color="error" />
              ) : (
                <CheckCircle color="success" />
              )}
              <Typography
                variant="h4"
                color={slaStatus.breached ? 'error' : 'success'}
                fontWeight="bold"
              >
                {slaStatus.duration_hours}h
              </Typography>
              <Typography variant="body2" color="text.secondary">
                / {slaStatus.expected_hours}h target
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={calculateSLAPercentage()}
              color={slaStatus.breached ? 'error' : 'success'}
              sx={{ height: 8, borderRadius: 4, mb: 1 }}
            />
            {slaStatus.breached && (
              <Chip
                size="small"
                label={`Exceeded by ${slaStatus.excess_hours}h`}
                color="error"
                variant="outlined"
              />
            )}
          </Box>
        )}

        <Divider />

        {metricsSummary && (
          <Box sx={{ p: 2 }}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
              Infrastructure Status
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <TrendingUp color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Marker Event"
                  secondary={metricsSummary.marker_event}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Speed color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="DAG Processing"
                  secondary={metricsSummary.dag_processing}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Cloud color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="EKS Status"
                  secondary={metricsSummary.eks_status}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Storage color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="RDS Status"
                  secondary={metricsSummary.rds_status}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Queue color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="SQS Status"
                  secondary={metricsSummary.sqs_status}
                />
              </ListItem>
            </List>
          </Box>
        )}

        {rootCauses && rootCauses.length > 0 && (
          <>
            <Divider />
            <Box sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                Root Causes Identified
              </Typography>
              {rootCauses.map((cause, index) => (
                <Accordion key={index} elevation={0}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <BugReport
                        color={cause.severity === 'critical' ? 'error' : 'warning'}
                      />
                      <Typography variant="body2" fontWeight="medium">
                        {cause.category}
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="body2" paragraph>
                        <strong>Cause:</strong> {cause.cause}
                      </Typography>
                      <Typography variant="body2" paragraph>
                        <strong>Impact:</strong> {cause.impact}
                      </Typography>
                      {cause.evidence && (
                        <Typography variant="body2" color="text.secondary">
                          <strong>Evidence:</strong> {cause.evidence}
                        </Typography>
                      )}
                      {cause.contribution_percentage > 0 && (
                        <Box mt={1}>
                          <Chip
                            size="small"
                            label={`${cause.contribution_percentage.toFixed(0)}% contribution`}
                            color="warning"
                            variant="outlined"
                          />
                        </Box>
                      )}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          </>
        )}
      </Box>
    </Paper>
  );
};

export default MetricsPanel;