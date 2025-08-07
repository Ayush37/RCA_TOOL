import React from 'react';
import { Box, Typography, Chip } from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { CalendarMonth } from '@mui/icons-material';
import dayjs, { Dayjs } from 'dayjs';

interface ChatHeaderProps {
  selectedDate: string;
  onDateChange: (date: string) => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({ selectedDate, onDateChange }) => {
  const handleDateChange = (value: Dayjs | null) => {
    if (value) {
      onDateChange(value.format('YYYY-MM-DD'));
    }
  };

  return (
    <Box
      sx={{
        p: 2,
        borderBottom: 1,
        borderColor: 'divider',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: (theme) =>
          theme.palette.mode === 'dark'
            ? 'linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%)'
            : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Box>
        <Typography variant="h6" fontWeight="bold" color="white">
          Derivatives Processing Analysis
        </Typography>
        <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
          Real-time root cause analysis for batch processing
        </Typography>
      </Box>
      
      <Box display="flex" alignItems="center" gap={2}>
        <Chip
          icon={<CalendarMonth />}
          label="Analysis Date"
          sx={{ 
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            color: 'white',
          }}
        />
        <DatePicker
          value={dayjs(selectedDate)}
          onChange={handleDateChange}
          format="YYYY-MM-DD"
          sx={{
            '& .MuiInputBase-root': {
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              height: 40,
            },
            '& .MuiOutlinedInput-input': {
              padding: '8px 14px',
            },
          }}
        />
      </Box>
    </Box>
  );
};

export default ChatHeader;