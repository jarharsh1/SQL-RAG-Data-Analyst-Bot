import axios from 'axios';
import { QueryResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function queryAnalyst(question: string, userId: string): Promise<QueryResponse> {
  const response = await api.post<QueryResponse>('/api/query', {
    question,
    user_id: userId,
    show_sql: true,
    show_transparency: true,
  });

  return response.data;
}

export async function getAuditLogs(userId: string): Promise<any[]> {
  const response = await api.get(`/api/audit/${userId}`);
  return response.data;
}

export async function healthCheck(): Promise<{ status: string }> {
  const response = await api.get('/health');
  return response.data;
}
