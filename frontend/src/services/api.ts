import axios from 'axios';
import { ChatResponse, HealthStatus } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sendChatMessage = async (
  query: string,
  date: string = '2025-08-01'
): Promise<ChatResponse> => {
  try {
    const response = await api.post<ChatResponse>('/api/chat', {
      query,
      date,
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.error || 'Failed to process request');
    }
    throw error;
  }
};

export const checkHealth = async (): Promise<HealthStatus> => {
  try {
    const response = await api.get<HealthStatus>('/api/health');
    return response.data;
  } catch (error) {
    throw new Error('Backend service is unavailable');
  }
};

export const getAvailableDates = async (): Promise<string[]> => {
  try {
    const response = await api.get<{ dates: string[] }>('/api/available-dates');
    return response.data.dates;
  } catch (error) {
    console.error('Failed to fetch available dates:', error);
    return ['2025-08-01'];
  }
};

export const getMetrics = async (date: string): Promise<any> => {
  try {
    const response = await api.get(`/api/metrics/${date}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.error || 'Failed to fetch metrics');
    }
    throw error;
  }
};