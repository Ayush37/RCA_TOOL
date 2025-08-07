import React, { useState, KeyboardEvent } from 'react';
import {
  Box,
  TextField,
  IconButton,
} from '@mui/material';
import { Send } from '@mui/icons-material';

interface SimpleChatInputProps {
  onSendMessage: (message: string) => void;
  loading: boolean;
  disabled?: boolean;
}

const SimpleChatInput: React.FC<SimpleChatInputProps> = ({
  onSendMessage,
  loading,
  disabled = false,
}) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !loading && !disabled) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box
      sx={{
        p: 2,
        borderTop: '1px solid',
        borderColor: 'divider',
        backgroundColor: 'background.paper',
      }}
    >
      <Box display="flex" gap={1} alignItems="flex-end">
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about derivatives processing (e.g., 'How is the processing for COB Aug 1st?')"
          disabled={loading || disabled}
          variant="outlined"
          sx={{
            '& .MuiOutlinedInput-root': {
              fontSize: '0.95rem',
              borderRadius: 2,
              backgroundColor: 'background.default',
              '& fieldset': {
                borderColor: 'divider',
              },
              '&:hover fieldset': {
                borderColor: 'text.secondary',
              },
              '&.Mui-focused fieldset': {
                borderColor: 'primary.main',
                borderWidth: 1,
              },
            },
            '& .MuiInputBase-input': {
              padding: '12px 14px',
            },
          }}
        />
        <IconButton
          onClick={handleSend}
          disabled={!input.trim() || loading || disabled}
          sx={{
            backgroundColor: input.trim() && !loading && !disabled
              ? 'primary.main'
              : 'action.disabled',
            color: 'white',
            '&:hover': {
              backgroundColor: 'primary.dark',
            },
            '&:disabled': {
              backgroundColor: 'action.disabled',
              color: 'text.disabled',
            },
            width: 40,
            height: 40,
          }}
        >
          <Send fontSize="small" />
        </IconButton>
      </Box>
    </Box>
  );
};

export default SimpleChatInput;