/**
 * API Service for Minute AI
 */

const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('minute_ai_token') || 'demo-token';
  const headers = {
    'Authorization': `Bearer ${token}`,
    ...options.headers,
  };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || 'API request failed');
  }

  return response.json();
}

export const api = {
  // Auth
  demoLogin: () => request('/auth/demo', { method: 'POST' }),
  login: (email, password) => request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  }),

  // Dashboard
  getDashboardSummary: () => request('/dashboard/summary'),

  // Projects
  getProjects: (activeOnly = false) => request(`/projects?active_only=${activeOnly}`),
  createProject: (data) => request('/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  updateProject: (id, data) => request(`/projects/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  toggleProject: (id, isActive) => request(`/projects/${id}/toggle?is_active=${isActive}`, {
    method: 'PATCH',
  }),
  deleteProject: (id) => request(`/projects/${id}`, { method: 'DELETE' }),

  // Transcripts
  getTranscripts: () => request('/transcripts'),
  getTranscript: (id) => request(`/transcripts/${id}`),
  processText: (data) => request('/transcripts/process-text', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  processFile: (formData) => request('/transcripts/process-file', {
    method: 'POST',
    body: formData,
  }),
  reprocessTranscript: (id) => request(`/transcripts/${id}/reprocess`, { method: 'POST' }),
  deleteTranscript: (id) => request(`/transcripts/${id}`, { method: 'DELETE' }),

  // Action Items
  getActionItems: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '' && v !== 'All') {
        query.append(k, v);
      }
    });
    return request(`/action-items?${query.toString()}`);
  },
  updateActionItem: (id, fields) => request(`/action-items/${id}`, {
    method: 'PUT',
    body: JSON.stringify(fields),
  }),
  updateStatus: (id, status) => request(`/action-items/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  }),
  deleteActionItem: (id) => request(`/action-items/${id}`, { method: 'DELETE' }),

  // Export
  exportCsvUrl: `${API_BASE}/export/csv`,
  exportExcelUrl: `${API_BASE}/export/excel`,

  // Settings
  getSettings: () => request('/settings'),
  updateSettings: (data) => request('/settings', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
};
