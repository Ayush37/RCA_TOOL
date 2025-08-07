import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { Message } from '../types';
import ReactMarkdown from 'react-markdown';

interface SimpleMessageBubbleProps {
  message: Message;
}

const SimpleMessageBubble: React.FC<SimpleMessageBubbleProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 3,
        px: 2,
      }}
    >
      <Box
        sx={{
          maxWidth: '85%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start',
        }}
      >
        {/* Sender label */}
        <Typography
          variant="caption"
          sx={{
            mb: 0.5,
            color: 'text.secondary',
            fontWeight: 500,
          }}
        >
          {isUser ? 'You' : 'Assistant'}
        </Typography>

        {/* Message content */}
        <Paper
          elevation={0}
          sx={{
            p: 2,
            backgroundColor: isUser
              ? (theme) => theme.palette.mode === 'dark' ? '#2a2a2a' : '#f0f0f0'
              : 'transparent',
            borderRadius: 2,
            border: isUser ? 'none' : '1px solid',
            borderColor: 'divider',
          }}
        >
          {message.isTyping ? (
            <Box sx={{ whiteSpace: 'pre-wrap' }}>
              <Typography variant="body1" color="text.primary">
                {message.content}
              </Typography>
              {message.content && (
                <Box
                  component="span"
                  sx={{
                    display: 'inline-block',
                    width: 8,
                    height: 20,
                    backgroundColor: 'text.primary',
                    animation: 'blink 1s infinite',
                    ml: 0.5,
                    '@keyframes blink': {
                      '0%': { opacity: 1 },
                      '50%': { opacity: 0 },
                      '100%': { opacity: 1 },
                    },
                  }}
                />
              )}
            </Box>
          ) : isUser ? (
            <Typography variant="body1" color="text.primary">
              {message.content}
            </Typography>
          ) : (
            <Box sx={{ 
              '& pre': { 
                whiteSpace: 'pre-wrap',
                fontFamily: '"Inter", sans-serif',
                fontSize: '0.95rem',
                lineHeight: 1.7,
              },
              '& p': { 
                margin: 0,
                marginBottom: 1,
                fontSize: '0.95rem',
                lineHeight: 1.7,
              },
              '& ul, & ol': {
                marginTop: 0.5,
                marginBottom: 1,
                paddingLeft: 3,
              },
              '& li': {
                marginBottom: 0.5,
                fontSize: '0.95rem',
              },
              '& strong': {
                fontWeight: 600,
              },
            }}>
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <Typography variant="body1" paragraph sx={{ mb: 1.5 }}>
                      {children}
                    </Typography>
                  ),
                  pre: ({ children }) => (
                    <Box component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                      {children}
                    </Box>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </Box>
          )}

          {/* SLA Status Badge */}
          {message.metadata?.sla_status && !message.isTyping && (
            <Box
              sx={{
                mt: 2,
                pt: 2,
                borderTop: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Box display="flex" alignItems="center" gap={1}>
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: message.metadata.sla_status.breached
                      ? 'error.main'
                      : 'success.main',
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  SLA {message.metadata.sla_status.breached ? 'Breached' : 'Met'} •{' '}
                  {message.metadata.sla_status.duration_hours} hours processing
                </Typography>
              </Box>
            </Box>
          )}
        </Paper>
      </Box>
    </Box>
  );
};

export default SimpleMessageBubble;