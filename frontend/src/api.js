const API_BASE = '/api';

export async function fetchChannels() {
  const res = await fetch(`${API_BASE}/channels/`);
  if (!res.ok) throw new Error('Failed to fetch channels');
  return res.json();
}

export async function fetchChannel(channelId) {
  const res = await fetch(`${API_BASE}/channels/${channelId}`);
  if (!res.ok) throw new Error('Failed to fetch channel');
  return res.json();
}

export async function updateChannelConfig(channelId, payload) {
  const res = await fetch(`${API_BASE}/channels/${channelId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update channel');
  return res.json();
}

export async function fetchDashboardStats() {
  const res = await fetch(`${API_BASE}/analytics/dashboard`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchVideos(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/videos/?${query}`);
  if (!res.ok) throw new Error('Failed to fetch videos');
  return res.json();
}

export async function deleteVideo(videoId) {
  const res = await fetch(`${API_BASE}/videos/${videoId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete video');
  return res.json();
}

export async function purgeAllVideos() {
  const res = await fetch(`${API_BASE}/videos/purge/all`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to purge videos');
  return res.json();
}

export async function fetchPipelineStatus() {
  const res = await fetch(`${API_BASE}/pipeline/status`);
  if (!res.ok) throw new Error('Failed to fetch pipeline status');
  return res.json();
}

export async function triggerGeneration(channelId, topic = null, upload = false) {
  const res = await fetch(`${API_BASE}/pipeline/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ channel_id: channelId, topic, upload }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to start generation');
  }
  return res.json();
}

export async function triggerTrendFinding(channelId) {
  const res = await fetch(`${API_BASE}/pipeline/find-trends/${channelId}`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to find trends');
  return res.json();
}

export async function fetchTrends(channelId) {
  const res = await fetch(`${API_BASE}/pipeline/trends/${channelId}`);
  if (!res.ok) throw new Error('Failed to fetch trends');
  return res.json();
}

export async function fetchLogs(limit = 100) {
  const res = await fetch(`${API_BASE}/analytics/logs?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch logs');
  return res.json();
}

export async function fetchApiUsage() {
  const res = await fetch(`${API_BASE}/analytics/api-usage`);
  if (!res.ok) throw new Error('Failed to fetch API usage');
  return res.json();
}

export async function fetchAgentsTeamStatus() {
  const candidates = [
    `${API_BASE}/analytics/agents-team`,
    'http://localhost:8012/api/analytics/agents-team',
    'http://localhost:8011/api/analytics/agents-team',
    'http://localhost:8001/api/analytics/agents-team',
    'http://localhost:8000/api/analytics/agents-team',
  ];
  let lastError = null;
  for (const url of candidates) {
    try {
      const res = await fetch(url);
      if (res.ok) return res.json();
      lastError = new Error(`HTTP ${res.status} from ${url}`);
    } catch (e) {
      lastError = e;
    }
  }
  throw new Error(lastError?.message || 'Failed to fetch agents team status');
}

export async function fetchScheduledJobs(status = 'pending') {
  const res = await fetch(`${API_BASE}/schedule?status=${status}`);
  if (!res.ok) throw new Error('Failed to fetch schedule');
  return res.json();
}

export async function addScheduledJob(videoId, channelId, scheduledAt) {
  const res = await fetch(`${API_BASE}/schedule/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ video_id: videoId, channel_id: channelId, scheduled_at: scheduledAt })
  });
  if (!res.ok) throw new Error('Failed to schedule video');
  return res.json();
}

export async function cancelScheduledJob(jobId) {
  const res = await fetch(`${API_BASE}/schedule/${jobId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to cancel schedule');
  return res.json();
}

export async function publishNow(videoId) {
  const res = await fetch(`${API_BASE}/schedule/publish-now/${videoId}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to publish now');
  return res.json();
}

export async function fetchIncomeTracking() {
  const res = await fetch(`${API_BASE}/analytics/income`);
  if (!res.ok) throw new Error('Failed to fetch income tracking');
  return res.json();
}
