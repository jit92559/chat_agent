// API base URL
const API_BASE = 'http://localhost:8000';

// Helper to get auth token
function getToken() {
  return localStorage.getItem('access_token');
}

// Helper for authenticated JSON requests
function authHeaders() {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function apiRegister(name, email, password) {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Registration failed');
  return data;
}

export async function apiLogin(email, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Login failed');
  return data;
}

// ── Threads ───────────────────────────────────────────────────────────────────

export async function apiCreateThread() {
  const res = await fetch(`${API_BASE}/threads/new`, {
    method: 'POST',
    headers: authHeaders(),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to create thread');
  return data;
}

export async function apiGetThreads() {
  const res = await fetch(`${API_BASE}/threads/`, {
    headers: authHeaders(),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to fetch threads');
  return data;
}

export async function apiGetMessages(threadId) {
  const res = await fetch(`${API_BASE}/threads/${threadId}/messages`, {
    headers: authHeaders(),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to fetch messages');
  return data;
}


// ── Chat Text ─────────────────────────────────────────────────────────────────

export async function apiStreamChat({
  thread_id,
  message,
  selected_file_id,
  signal,
  onToken,
  onComplete,
}) {
  const token = getToken();

  const res = await fetch(`${API_BASE}/api/chat/stream`, {
    method: 'POST',
    signal,
    headers: {
      'Content-Type': 'application/json',
      ...(token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {}),
    },
    body: JSON.stringify({
      thread_id,
      message,
      selected_file_id: selected_file_id || null,
    }),
  });

  if (!res.ok) {
    throw new Error('Chat failed');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');

  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, {
      stream: true,
    });

    const events = buffer.split('\n\n');
    buffer = events.pop() || '';

    for (const event of events) {
      if (!event.startsWith('data: ')) continue;

      const payload = JSON.parse(
        event.replace('data: ', '')
      );

      if (payload.error) {
        throw new Error(payload.error);
      }

      if (payload.token) {
        onToken?.(payload.token);
      }

      if (payload.done) {
        onComplete?.({
          answer: payload.answer,
          suggestions: payload.suggestions || [],
        });

        return {
          answer: payload.answer,
          suggestions: payload.suggestions || [],
        };
      }
    }
  }
}
// ── File Upload ───────────────────────────────────────────────────────────────

export async function apiUploadFile({ thread_id, file }) {
  const token = getToken();

  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(
    `${API_BASE}/files/upload-rag?thread_id=${thread_id}`,
    {
      method: 'POST',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: formData,
    }
  );

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || 'Upload failed');
  return data;
}

export async function apiGetFiles(threadId) {
  const res = await fetch(
    `${API_BASE}/files/thread-files?thread_id=${threadId}`,
    {
      headers: authHeaders(),
    }
  );

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.error || 'Failed to fetch files');
  return data;
}



//DELETE THREADs
// ── Delete Thread ────────────────────────────────────────────────────────────

export async function apiDeleteThread(thread_id) {
  const res = await fetch(`${API_BASE}/threads/${thread_id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || 'Failed to delete thread');
  }

  return data;
}