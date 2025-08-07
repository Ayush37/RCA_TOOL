import React, { useState, KeyboardEvent } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Chip,
  Stack,
  Tooltip,
  InputAdornment,
} from '@mui/material';
import { Send, Psychology, TipsAndUpdates } from '@mui/icons-material';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  loading: boolean;
  suggestedQueries: string[];
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  loading,
  suggestedQueries,
  disabled = false,
}) => {
  const [input, setInput] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(true);

  const handleSend = () => {
    if (input.trim() && !loading && !disabled) {
      onSendMessage(input.trim());
      setInput('');
      setShowSuggestions(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (query: string) => {
    setInput(query);
    setShowSuggestions(false);
  };

  return (
    <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
      {showSuggestions && suggestedQueries.length > 0 && (
        <Stack
          direction="row"
          spacing={1}
          sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}
        >
          <Chip
            size="small"
            icon={<TipsAndUpdates />}
            label="Suggestions:"
            variant="outlined"
            color="primary"
          />
          {suggestedQueries.map((query, index) => (
            <Chip
              key={index}
              label={query}
              size="small"
              onClick={() => handleSuggestionClick(query)}
              clickable
              sx={{
                '&:hover': {
                  backgroundColor: 'primary.main',
                  color: 'white',
                },
              }}
            />
          ))}
        </Stack>
      )}

      <Box display="flex" gap={1}>
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={
            disabled
              ? "Backend service is not available..."
              : "Ask about derivatives processing, SLA breaches, or infrastructure issues..."
          }
          disabled={loading || disabled}
          variant="outlined"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Psychology color="action" />
              </InputAdornment>
            ),
            sx: {
              borderRadius: 3,
            },
          }}
        />
        <Tooltip title={disabled ? "Backend not connected" : "Send message"}>
          <span>
            <IconButton
              color="primary"
              onClick={handleSend}
              disabled={!input.trim() || loading || disabled}
              sx={{
                backgroundColor: 'primary.main',
                color: 'white',
                '&:hover': {
                  backgroundColor: 'primary.dark',
                },
                '&:disabled': {
                  backgroundColor: 'action.disabledBackground',
                },
              }}
            >
              <Send />
            </IconButton>
          </span>
        </Tooltip>
      </Box>
    </Box>
  );
};

export default ChatInput;