import React from 'react';
import { Box } from '@mui/material';
import SimpleMessageBubble from './SimpleMessageBubble';
import { Message } from '../types';

interface SimpleMessageListProps {
  messages: Message[];
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

const SimpleMessageList: React.FC<SimpleMessageListProps> = ({ 
  messages, 
  messagesEndRef 
}) => {
  return (
    <Box
      sx={{
        flex: 1,
        overflowY: 'auto',
        py: 3,
        px: 1,
        '&::-webkit-scrollbar': {
          width: 6,
        },
        '&::-webkit-scrollbar-track': {
          backgroundColor: 'transparent',
        },
        '&::-webkit-scrollbar-thumb': {
          backgroundColor: 'divider',
          borderRadius: 3,
        },
        '&::-webkit-scrollbar-thumb:hover': {
          backgroundColor: 'text.disabled',
        },
      }}
    >
      {messages.map((message) => (
        <SimpleMessageBubble key={message.id} message={message} />
      ))}
      <div ref={messagesEndRef} />
    </Box>
  );
};

export default SimpleMessageList;