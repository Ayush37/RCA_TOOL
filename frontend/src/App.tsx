import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import SimpleChatInterface from './components/SimpleChatInterface';
import { checkHealth } from './services/api';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#ffffff',
    },
    secondary: {
      main: '#8e8ea0',
    },
    background: {
      default: '#212121',
      paper: '#2a2a2a',
    },
    text: {
      primary: '#ececf1',
      secondary: '#a4a4b8',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSize: 15,
    h6: {
      fontSize: '1.1rem',
    },
    body1: {
      fontSize: '0.95rem',
      lineHeight: 1.7,
    },
    body2: {
      fontSize: '0.9rem',
    },
  },
});

const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#10a37f',
    },
    secondary: {
      main: '#666',
    },
    background: {
      default: '#ffffff',
      paper: '#f7f7f8',
    },
    text: {
      primary: '#2d2d2d',
      secondary: '#666',
    },
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSize: 15,
    h6: {
      fontSize: '1.1rem',
    },
    body1: {
      fontSize: '0.95rem',
      lineHeight: 1.7,
    },
    body2: {
      fontSize: '0.9rem',
    },
  },
});

function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [backendStatus, setBackendStatus] = useState<boolean>(false);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const health = await checkHealth();
        setBackendStatus(health.status === 'healthy');
      } catch (error) {
        console.error('Backend health check failed:', error);
        setBackendStatus(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 30000);

    return () => clearInterval(interval);
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <ThemeProvider theme={darkMode ? darkTheme : lightTheme}>
      <LocalizationProvider dateAdapter={AdapterDayjs}>
        <CssBaseline />
        <SimpleChatInterface 
          darkMode={darkMode} 
          toggleDarkMode={toggleDarkMode}
          backendStatus={backendStatus}
        />
      </LocalizationProvider>
    </ThemeProvider>
  );
}

export default App;