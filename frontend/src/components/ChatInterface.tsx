import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  IconButton,
  Typography,
  Chip,
  Alert,
  Snackbar,
  Tooltip,
} from '@mui/material';
import {
  DarkMode,
  LightMode,
  Analytics,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import ChatHeader from './ChatHeader';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import Timeline from './Timeline';
import MetricsPanel from './MetricsPanel';
import { Message, ChatResponse } from '../types';
import { sendChatMessage } from '../services/api';
import { v4 as uuidv4 } from 'uuid';

interface ChatInterfaceProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
  backendStatus: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  darkMode,
  toggleDarkMode,
  backendStatus,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: uuidv4(),
      content: "Hello! I'm your RCA Analysis Assistant. I can help you understand root causes for derivatives processing delays and failures. Try asking me about the August 1st SLA breach or any infrastructure issues.",
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [selectedDate, setSelectedDate] = useState('2025-08-01');
  const [showTimeline, setShowTimeline] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);
  const [currentResponse, setCurrentResponse] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: uuidv4(),
      content,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    const typingMessage: Message = {
      id: uuidv4(),
      content: '',
      sender: 'bot',
      timestamp: new Date(),
      isTyping: true,
    };

    setMessages((prev) => [...prev, typingMessage]);

    try {
      const response = await sendChatMessage(content, selectedDate);
      setCurrentResponse(response);

      const botMessage: Message = {
        id: uuidv4(),
        content: response.analysis,
        sender: 'bot',
        timestamp: new Date(),
        metadata: {
          timeline: response.timeline,
          metrics_summary: response.metrics_summary,
          sla_status: response.sla_status,
          root_causes: response.root_causes,
        },
      };

      setMessages((prev) =>
        prev.filter((msg) => msg.id !== typingMessage.id).concat(botMessage)
      );

      if (response.timeline && response.timeline.length > 0) {
        setShowTimeline(true);
      }
      if (response.metrics_summary) {
        setShowMetrics(true);
      }
    } catch (err) {
      setMessages((prev) => prev.filter((msg) => msg.id !== typingMessage.id));
      
      let errorMessage = 'An error occurred';
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      }
      
      setError(errorMessage);

      const errorBotMessage: Message = {
        id: uuidv4(),
        content: `I encountered an error while processing your request: ${errorMessage}. Please make sure the backend service is running and configured properly.`,
        sender: 'bot',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorBotMessage]);
    } finally {
      setLoading(false);
    }
  };

  const suggestedQueries = [
    "Why did derivatives processing fail on August 1st?",
    "What caused the SLA breach today?",
    "Show me the RCA timeline for derivatives",
    "What infrastructure issues occurred?",
  ];

  return (
    <Container maxWidth="xl" sx={{ height: '100vh', py: 2 }}>
      <Box display="flex" flexDirection="column" height="100%">
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4" component="h1" fontWeight="bold">
            RCA Analysis Chatbot
          </Typography>
          <Box display="flex" gap={2} alignItems="center">
            <Chip
              icon={backendStatus ? <CheckCircle /> : <Error />}
              label={backendStatus ? 'Connected' : 'Disconnected'}
              color={backendStatus ? 'success' : 'error'}
              variant="outlined"
            />
            <Tooltip title={showMetrics ? "Hide Metrics" : "Show Metrics"}>
              <IconButton onClick={() => setShowMetrics(!showMetrics)} color="primary">
                <Analytics />
              </IconButton>
            </Tooltip>
            <Tooltip title={darkMode ? "Light Mode" : "Dark Mode"}>
              <IconButton onClick={toggleDarkMode}>
                {darkMode ? <LightMode /> : <DarkMode />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Box display="flex" gap={2} flex={1} overflow="hidden">
          <Box flex={1} display="flex" flexDirection="column">
            <Paper
              elevation={3}
              sx={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                borderRadius: 2,
              }}
            >
              <ChatHeader 
                selectedDate={selectedDate} 
                onDateChange={setSelectedDate}
              />
              
              <MessageList 
                messages={messages} 
                messagesEndRef={messagesEndRef}
              />

              <ChatInput
                onSendMessage={handleSendMessage}
                loading={loading}
                suggestedQueries={suggestedQueries}
                disabled={!backendStatus}
              />
            </Paper>
          </Box>

          {showTimeline && currentResponse?.timeline && (
            <Box width={400}>
              <Timeline 
                events={currentResponse.timeline}
                onClose={() => setShowTimeline(false)}
              />
            </Box>
          )}

          {showMetrics && currentResponse && (
            <Box width={350}>
              <MetricsPanel
                metricsSummary={currentResponse.metrics_summary}
                slaStatus={currentResponse.sla_status}
                rootCauses={currentResponse.root_causes}
                onClose={() => setShowMetrics(false)}
              />
            </Box>
          )}
        </Box>
      </Box>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ChatInterface;