const CHANNEL_ACCENTS = [
  '#C8A829', '#DC143C', '#00E5FF', '#7B1FA2', '#FFD700', '#1565C0'
];

export const MOCK_CHANNELS = [
  { channel_id: 'impacto-mundial', name: 'Impacto Mundial', language: 'es', niche: 'Noticias globales y geopolítica', frequency: '4 por semana', cpm_estimate: 8.4, is_active: 1 },
  { channel_id: 'mentes-rotas', name: 'Mentes Rotas', language: 'es', niche: 'Psicología extrema y casos reales', frequency: '3 por semana', cpm_estimate: 6.8, is_active: 1 },
  { channel_id: 'el-loco-de-la-ia', name: 'El Loco de la IA', language: 'es', niche: 'Herramientas, prompts y productividad IA', frequency: '5 por semana', cpm_estimate: 9.6, is_active: 1 },
  { channel_id: 'mind-warp', name: 'Mind Warp', language: 'en', niche: 'Mind-blowing science storytelling', frequency: '4 per week', cpm_estimate: 10.2, is_active: 1 },
  { channel_id: 'wealth-files', name: 'Wealth Files', language: 'en', niche: 'Finance breakdowns & market stories', frequency: '3 per week', cpm_estimate: 14.7, is_active: 1 },
  { channel_id: 'dark-science', name: 'Dark Science', language: 'en', niche: 'Unsolved experiments and history', frequency: '3 per week', cpm_estimate: 11.3, is_active: 1 },
].map((ch, i) => ({ ...ch, accent: CHANNEL_ACCENTS[i] }));

export const MOCK_DAILY_METRICS = Array.from({ length: 30 }, (_, index) => {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - (29 - index));

  const uploads = 5 + Math.floor(Math.sin(index / 2.5) * 2 + 2.5);
  const views = 42000 + Math.floor(18000 * Math.sin(index / 4)) + index * 750;
  const revenue = 520 + Math.floor(240 * Math.cos(index / 5)) + index * 9;
  const quality = 74 + Math.floor(Math.sin(index / 3.2) * 12 + 11);

  return {
    day: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    date: d.toISOString(),
    uploads,
    views: Math.max(8000, views),
    revenue: Math.max(120, revenue),
    quality: Math.min(99, Math.max(55, quality)),
  };
});

export const MOCK_QUEUE_ITEMS = Array.from({ length: 18 }, (_, i) => {
  const ch = MOCK_CHANNELS[i % MOCK_CHANNELS.length];
  const statusCycle = ['pending', 'generating', 'ready', 'published', 'error'];
  const status = statusCycle[i % statusCycle.length];
  const d = new Date();
  d.setDate(d.getDate() + (i % 8) - 3);
  d.setHours(8 + (i % 10), (i * 7) % 60, 0, 0);

  return {
    id: 900 + i,
    title: `${ch.name}: Storyline ${i + 1}`,
    topic: `High-retention topic #${i + 1}`,
    channel_id: ch.channel_id,
    channel_name: ch.name,
    status,
    scheduled_at: d.toISOString(),
    duration_seconds: 420 + (i % 6) * 55,
    quality_score: 63 + (i % 7) * 5,
    priority: i % 4 === 0 ? 'high' : i % 3 === 0 ? 'medium' : 'normal',
  };
});

export const MOCK_QUALITY_ALERTS = [
  { id: 'hook-drop', severity: 'warning', message: 'Hook retention dropped below 70% in 3 videos.' },
  { id: 'audio-noise', severity: 'error', message: 'Background noise detected in recent voice render.' },
  { id: 'title-length', severity: 'info', message: 'Average title length improved to 56 characters.' },
  { id: 'cta-gap', severity: 'warning', message: 'CTA missing in 2 ready-to-publish scripts.' },
];

export function buildMockDashboardStats(channels = MOCK_CHANNELS) {
  const totals = MOCK_DAILY_METRICS.reduce((acc, cur) => {
    acc.views += cur.views;
    acc.revenue += cur.revenue;
    acc.uploads += cur.uploads;
    return acc;
  }, { views: 0, revenue: 0, uploads: 0 });

  return {
    total_videos: totals.uploads,
    published: Math.floor(totals.uploads * 0.76),
    pending: 16,
    generating: 7,
    errors: 2,
    total_views: totals.views,
    total_revenue: totals.revenue,
    channels: channels.map((ch, idx) => ({
      ...ch,
      video_count: 40 + idx * 6,
      published_count: 28 + idx * 5,
      total_views: Math.floor(totals.views / channels.length + idx * 4200),
      total_revenue: Number((totals.revenue / channels.length + idx * 120).toFixed(2)),
      error_count: idx === 1 ? 1 : 0,
    })),
  };
}

export function buildMockApiUsage() {
  return [
    { service: 'gemini', total_requests: 642, total_chars: 921442 },
    { service: 'elevenlabs', total_requests: 89, total_chars: 145008 },
    { service: 'edge_tts', total_requests: 184, total_chars: 228942 },
    { service: 'pexels', total_requests: 134 },
    { service: 'pixabay', total_requests: 98 },
    { service: 'youtube_data_api', total_requests: 326 },
    { service: 'google_trends', total_requests: 74 },
    { service: 'reddit', total_requests: 118 },
  ];
}

export function buildMockLogs() {
  return MOCK_QUEUE_ITEMS.slice(0, 12).map((item, idx) => ({
    created_at: new Date(Date.now() - idx * 18 * 60000).toISOString(),
    status: item.status === 'error' ? 'error' : item.status === 'published' ? 'ok' : 'running',
    step: item.status === 'published' ? 'publish' : item.status,
    message: `${item.channel_name} · ${item.title}`,
  }));
}
