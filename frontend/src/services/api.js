const API_BASE = '/api';

async function request(url, options = {}) {
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };

  // Don't set Content-Type for FormData
  if (options.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  const response = await fetch(`${API_BASE}${url}`, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ─── Chat ─────────────────────────────────────────────────────

export async function sendMessage(content, conversationId = null, mode = 'chat', documentId = null, datasetId = null) {
  return request('/chat', {
    method: 'POST',
    body: JSON.stringify({
      content,
      conversation_id: conversationId,
      mode,
      document_id: documentId,
      dataset_id: datasetId,
    }),
  });
}

export async function getChats() {
  return request('/chats');
}

export async function createChat(title = 'New Chat') {
  return request('/chats', {
    method: 'POST',
    body: JSON.stringify({ title }),
  });
}

export async function getChat(conversationId) {
  return request(`/chats/${conversationId}`);
}

export async function deleteChat(conversationId) {
  return request(`/chats/${conversationId}`, { method: 'DELETE' });
}

export async function clearAllChats() {
  return request('/chats', { method: 'DELETE' });
}

export async function renameChat(conversationId, title) {
  return request(`/chats/${conversationId}`, {
    method: 'PUT',
    body: JSON.stringify({ title }),
  });
}

export async function searchChats(query) {
  return request(`/chats/search/${encodeURIComponent(query)}`);
}

// ─── Research ─────────────────────────────────────────────────

export async function searchPapers(query, sources = null, limit = 10, conversationId = null) {
  return request('/research/search', {
    method: 'POST',
    body: JSON.stringify({
      query,
      sources,
      limit,
      conversation_id: conversationId,
    }),
  });
}

// ─── Documents ────────────────────────────────────────────────

export async function uploadDocument(file, conversationId = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (conversationId) {
    formData.append('conversation_id', conversationId);
  }

  return request('/documents/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function askDocument(docId, question, conversationId = null) {
  return request(`/documents/${docId}/ask`, {
    method: 'POST',
    body: JSON.stringify({ question, conversation_id: conversationId }),
  });
}

// ─── Datasets ─────────────────────────────────────────────────

export async function uploadDataset(file, conversationId = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (conversationId) {
    formData.append('conversation_id', conversationId);
  }

  return request('/datasets/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function analyzeDataset(datasetId, operation, params = {}, question = null) {
  return request(`/datasets/${datasetId}/analyze`, {
    method: 'POST',
    body: JSON.stringify({ operation, params, question }),
  });
}

export async function createChart(datasetId, chartType, xCol = null, yCol = null, groupCol = null, agg = 'mean') {
  return request(`/datasets/${datasetId}/chart`, {
    method: 'POST',
    body: JSON.stringify({
      chart_type: chartType,
      x_col: xCol,
      y_col: yCol,
      group_col: groupCol,
      agg,
    }),
  });
}

// ─── Reports ──────────────────────────────────────────────────

export async function generateReport(conversationId, title = null, reportType = 'research') {
  return request('/reports/generate', {
    method: 'POST',
    body: JSON.stringify({
      conversation_id: conversationId,
      title,
      report_type: reportType,
    }),
  });
}

export async function comparePapers(paperIds, conversationId = null) {
  return request('/reports/compare', {
    method: 'POST',
    body: JSON.stringify({
      paper_ids: paperIds,
      conversation_id: conversationId,
    }),
  });
}

// ─── Settings ─────────────────────────────────────────────────

export async function getSettings() {
  return request('/settings');
}

export async function updateSettings(settings) {
  return request('/settings', {
    method: 'POST',
    body: JSON.stringify(settings),
  });
}
