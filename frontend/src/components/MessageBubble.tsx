import React from 'react';
import { Box, Paper, Typography, Chip, CircularProgress } from '@mui/material';
import { Person, SmartToy, Warning, CheckCircle } from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Message } from '../types';
import { format } from 'date-fns';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  if (message.isTyping) {
    return (
      <Box display="flex" justifyContent="flex-start">
        <Paper
          elevation={1}
          sx={{
            p: 2,
            maxWidth: '70%',
            backgroundColor: (theme) =>
              theme.palette.mode === 'dark' ? '#2a2a3e' : '#f0f0f0',
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <CircularProgress size={16} />
          <Typography variant="body2" color="text.secondary">
            Analyzing...
          </Typography>
        </Paper>
      </Box>
    );
  }

  return (
    <Box
      display="flex"
      justifyContent={isUser ? 'flex-end' : 'flex-start'}
      alignItems="flex-start"
      gap={1}
    >
      {!isUser && (
        <Box
          sx={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            backgroundColor: 'primary.main',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <SmartToy sx={{ color: 'white', fontSize: 20 }} />
        </Box>
      )}

      <Box maxWidth="70%">
        <Paper
          elevation={isUser ? 2 : 1}
          sx={{
            p: 2,
            backgroundColor: isUser
              ? 'primary.main'
              : (theme) => theme.palette.mode === 'dark' ? '#2a2a3e' : '#f5f5f5',
            color: isUser ? 'white' : 'text.primary',
            borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          }}
        >
          {isUser ? (
            <Typography variant="body1">{message.content}</Typography>
          ) : (
            <Box className="markdown-content">
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <Typography variant="body1" paragraph>
                      {children}
                    </Typography>
                  ),
                  h2: ({ children }) => (
                    <Typography variant="h6" gutterBottom fontWeight="bold">
                      {children}
                    </Typography>
                  ),
                  h3: ({ children }) => (
                    <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                      {children}
                    </Typography>
                  ),
                  ul: ({ children }) => (
                    <Box component="ul" sx={{ pl: 2, my: 1 }}>
                      {children}
                    </Box>
                  ),
                  li: ({ children }) => (
                    <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
                      {children}
                    </Typography>
                  ),
                  strong: ({ children }) => (
                    <Typography component="span" fontWeight="bold">
                      {children}
                    </Typography>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </Box>
          )}

          {message.metadata?.sla_status && (
            <Box mt={2} display="flex" gap={1}>
              <Chip
                size="small"
                icon={message.metadata.sla_status.breached ? <Warning /> : <CheckCircle />}
                label={message.metadata.sla_status.breached ? 'SLA Breached' : 'SLA Met'}
                color={message.metadata.sla_status.breached ? 'error' : 'success'}
              />
              <Chip
                size="small"
                label={`${message.metadata.sla_status.duration_hours}h processing`}
                variant="outlined"
              />
            </Box>
          )}
        </Paper>

        <Typography
          variant="caption"
          sx={{
            mt: 0.5,
            display: 'block',
            color: 'text.secondary',
            textAlign: isUser ? 'right' : 'left',
          }}
        >
          {format(message.timestamp, 'HH:mm')}
        </Typography>
      </Box>

      {isUser && (
        <Box
          sx={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            backgroundColor: 'secondary.main',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Person sx={{ color: 'white', fontSize: 20 }} />
        </Box>
      )}
    </Box>
  );
};

export default MessageBubble;