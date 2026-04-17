import { useEffect, useMemo, useState } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Line, LineChart } from 'recharts';
import { fetchChannels, fetchDashboardStats, fetchLogs } from '../api';
import { CHANNEL_COLORS, CHANNEL_FALLBACK_COLOR } from '../theme';
import { buildMockDashboardStats, buildMockLogs, MOCK_CHANNELS, MOCK_DAILY_METRICS } from '../mockData';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [channels, setChannels] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchDashboardStats().catch(() => buildMockDashboardStats()),
      fetchChannels().catch(() => MOCK_CHANNELS),
      fetchLogs(12).catch(() => buildMockLogs()),
    ]).then(([s, c, l]) => {
      setStats(s || buildMockDashboardStats(c));
      setChannels(Array.isArray(c) && c.length ? c : MOCK_CHANNELS);
      setLogs(Array.isArray(l) && l.length ? l : buildMockLogs());
      setLoading(false);
    });
  }, []);

  const channelCards = useMemo(() => {
    if (stats?.channels?.length) return stats.channels;
    return buildMockDashboardStats(channels).channels;
  }, [stats, channels]);

  const s = stats || buildMockDashboardStats(channels);

  if (loading) {
    return <div className="skeleton" style={{ height: 280 }}></div>;
  }

  return (
    <div className="animate-fade-in">
      <div className="grid-4 mb-24">
        <StatCard label="Total Videos" value={s.total_videos} color="var(--accent)" />
        <StatCard label="Published" value={s.published} color="var(--success)" />
        <StatCard label="In Queue" value={(s.pending || 0) + (s.generating || 0)} color="var(--warning)" />
        <StatCard label="Errors" value={s.errors || 0} color="var(--error)" />
      </div>

      <div className="grid-2 mb-24">
        <div className="card-glass">
          <div className="section-header" style={{ marginBottom: 12 }}>
            <h3 className="section-title" style={{ fontSize: 18 }}>30-Day Volume</h3>
          </div>
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={MOCK_DAILY_METRICS}>
                <defs>
                  <linearGradient id="uploadsGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#A855F7" stopOpacity={0.45} />
                    <stop offset="100%" stopColor="#A855F7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                <XAxis dataKey="day" stroke="#94A3B8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94A3B8" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                <Area dataKey="uploads" stroke="#A855F7" fill="url(#uploadsGrad)" strokeWidth={2} />
                <Line dataKey="quality" stroke="#22D3EE" dot={false} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card-glass">
          <div className="section-header" style={{ marginBottom: 12 }}>
            <h3 className="section-title" style={{ fontSize: 18 }}>Views & Revenue</h3>
          </div>
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={MOCK_DAILY_METRICS}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                <XAxis dataKey="day" stroke="#94A3B8" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" stroke="#94A3B8" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" stroke="#94A3B8" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                <Line yAxisId="left" type="monotone" dataKey="views" stroke="#38BDF8" strokeWidth={2} dot={false} />
                <Line yAxisId="right" type="monotone" dataKey="revenue" stroke="#22C55E" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="section-header">
        <div>
          <h3 className="section-title" style={{ fontSize: 20 }}>Channel Snapshot</h3>
          <p className="section-subtitle">Per-channel accents and health indicators</p>
        </div>
      </div>

      <div className="grid-3 mb-24">
        {channelCards.map((ch) => {
          const color = CHANNEL_COLORS[ch.channel_id] || ch.accent || CHANNEL_FALLBACK_COLOR;
          return (
            <div key={ch.channel_id} className="channel-card" style={{ '--channel-color': color, borderLeft: `3px solid ${color}` }}>
              <div className="flex items-center justify-between mb-8">
                <div className="channel-name" style={{ fontSize: 16 }}>{ch.name}</div>
                <span className={`badge ${ch.error_count > 0 ? 'badge-warning' : 'badge-success'}`}>
                  <span className="badge-dot"></span>
                  {ch.error_count > 0 ? `${ch.error_count} issue` : 'Healthy'}
                </span>
              </div>
              <div className="channel-stats">
                <div className="channel-stat-item"><span>Videos</span><span>{ch.video_count || 0}</span></div>
                <div className="channel-stat-item"><span>Published</span><span>{ch.published_count || 0}</span></div>
                <div className="channel-stat-item"><span>Views</span><span>{formatNumber(ch.total_views || 0)}</span></div>
                <div className="channel-stat-item"><span>Revenue</span><span>${Number(ch.total_revenue || 0).toFixed(0)}</span></div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="card-glass">
        <div className="section-header" style={{ marginBottom: 4 }}>
          <h3 className="section-title" style={{ fontSize: 18 }}>Recent Pipeline Activity</h3>
        </div>
        {logs.slice(0, 10).map((log, i) => (
          <div key={`${log.created_at}-${i}`} className="activity-item">
            <div className="activity-dot" style={{ background: log.status === 'error' ? 'var(--error)' : log.status === 'ok' ? 'var(--success)' : 'var(--warning)' }}></div>
            <div className="activity-content">
              <div style={{ fontSize: 13, fontWeight: 600 }}>{(log.step || 'pipeline').replace(/_/g, ' ')}</div>
              <div className="text-secondary fs-12">{log.message || 'No message available'}</div>
            </div>
            <div className="activity-time">{new Date(log.created_at).toLocaleTimeString()}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div className="stat-card" style={{ borderLeft: `3px solid ${color}` }}>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ fontSize: 30, color }}>{value}</div>
    </div>
  );
}

function formatNumber(n) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n || 0);
}
