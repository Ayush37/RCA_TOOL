import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  IconButton,
  Typography,
  CircularProgress,
} from '@mui/material';
import {
  DarkMode,
  LightMode,
} from '@mui/icons-material';
import SimpleMessageList from './SimpleMessageList';
import SimpleChatInput from './SimpleChatInput';
import { Message, ChatResponse } from '../types';
import { sendChatMessage } from '../services/api';
import { v4 as uuidv4 } from 'uuid';

interface SimpleChatInterfaceProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
  backendStatus: boolean;
}

const SimpleChatInterface: React.FC<SimpleChatInterfaceProps> = ({
  darkMode,
  toggleDarkMode,
  backendStatus,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: uuidv4(),
      content: "Hello! I can help you analyze derivatives processing and identify root causes for delays. Ask me about any processing date, like 'How is the derivatives batch processing for COB August 1st?'",
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const extractDateFromQuery = (query: string): string => {
    // Try to extract date from query
    const datePatterns = [
      /(\d{1,2})[- ](?:aug|august)[- ](\d{4})/i,
      /august[- ](\d{1,2})(?:st|nd|rd|th)?[, ]*(\d{4})?/i,
      /(\d{4})-(\d{2})-(\d{2})/,
      /cob[- ](\d{1,2})[- ](?:aug|august)/i,
    ];
    
    for (const pattern of datePatterns) {
      const match = query.match(pattern);
      if (match) {
        // For now, return the default date
        // In production, parse and format the matched date
        return '2025-08-01';
      }
    }
    
    return '2025-08-01'; // Default date
  };

  const simulateStreamingResponse = async (
    response: ChatResponse,
    messageId: string
  ) => {
    const steps = [
      { text: "✓ Checking marker event arrival time...", delay: 500 },
      { text: `\n→ Marker arrived at ${response.sla_status?.arrival_time || 'N/A'}`, delay: 800 },
      { text: "\n\n✓ Analyzing DAG processing metrics...", delay: 600 },
      { text: `\n→ Processing completed at ${response.sla_status?.completion_time || 'N/A'}`, delay: 800 },
      { text: `\n→ Duration: ${response.processing_duration} hours (SLA: 3 hours)`, delay: 700 },
      { text: "\n\n✓ Checking infrastructure metrics...", delay: 600 },
      { text: "\n→ Analyzing EKS, RDS, and SQS performance during processing window", delay: 1000 },
      { text: "\n\n✓ Generating Root Cause Analysis...\n\n", delay: 800 },
    ];

    let fullContent = "";
    
    for (const step of steps) {
      fullContent += step.text;
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId
            ? { ...msg, content: fullContent, isTyping: true }
            : msg
        )
      );
      await new Promise((resolve) => setTimeout(resolve, step.delay));
    }

    // Add the final analysis
    fullContent += response.analysis;
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId
          ? { ...msg, content: fullContent, isTyping: false, metadata: {
              timeline: response.timeline,
              metrics_summary: response.metrics_summary,
              sla_status: response.sla_status,
              root_causes: response.root_causes,
            }}
          : msg
      )
    );
  };

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: uuidv4(),
      content,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    const botMessageId = uuidv4();
    const initialBotMessage: Message = {
      id: botMessageId,
      content: "Analyzing derivatives processing...",
      sender: 'bot',
      timestamp: new Date(),
      isTyping: true,
    };

    setMessages((prev) => [...prev, initialBotMessage]);

    try {
      const date = extractDateFromQuery(content);
      const response = await sendChatMessage(content, date);
      
      // Simulate streaming response
      await simulateStreamingResponse(response, botMessageId);
      
    } catch (err) {
      let errorMessage = 'An error occurred';
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === botMessageId
            ? {
                ...msg,
                content: `I encountered an error: ${errorMessage}. Please make sure the backend service is running.`,
                isTyping: false,
              }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ height: '100vh', py: 2 }}>
      <Box display="flex" flexDirection="column" height="100%">
        {/* Minimal Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6" fontWeight={600} color="text.primary">
            RCA Analysis
          </Typography>
          <Box display="flex" gap={1} alignItems="center">
            {!backendStatus && (
              <Typography variant="caption" color="error">
                Backend disconnected
              </Typography>
            )}
            <IconButton size="small" onClick={toggleDarkMode}>
              {darkMode ? <LightMode /> : <DarkMode />}
            </IconButton>
          </Box>
        </Box>

        {/* Chat Area */}
        <Paper
          elevation={0}
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            borderRadius: 2,
            border: '1px solid',
            borderColor: 'divider',
            backgroundColor: 'background.default',
          }}
        >
          <SimpleMessageList messages={messages} messagesEndRef={messagesEndRef} />
          <SimpleChatInput
            onSendMessage={handleSendMessage}
            loading={loading}
            disabled={!backendStatus}
          />
        </Paper>
      </Box>
    </Container>
  );
};

export default SimpleChatInterface;