import { useEffect, useMemo, useState } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, BarChart, Bar } from 'recharts';
import { fetchLogs, fetchVideos } from '../api';
import { MOCK_DAILY_METRICS, MOCK_QUALITY_ALERTS, MOCK_QUEUE_ITEMS } from '../mockData';

export default function Quality() {
  const [videos, setVideos] = useState(MOCK_QUEUE_ITEMS);
  const [alerts, setAlerts] = useState(MOCK_QUALITY_ALERTS);
  const [selectedAlert, setSelectedAlert] = useState(null);

  useEffect(() => {
    Promise.all([
      fetchVideos({ limit: 120 }).catch(() => ({ videos: MOCK_QUEUE_ITEMS })),
      fetchLogs(80).catch(() => []),
    ]).then(([videoRes, logs]) => {
      const list = Array.isArray(videoRes?.videos) && videoRes.videos.length ? videoRes.videos : MOCK_QUEUE_ITEMS;
      setVideos(list);

      if (Array.isArray(logs) && logs.length) {
        const derived = logs.slice(0, 4).map((l, i) => ({
          id: `live-${i}`,
          severity: l.status === 'error' ? 'error' : l.status === 'ok' ? 'info' : 'warning',
          message: `[${l.step || 'pipeline'}] ${l.message || 'No message'}`,
        }));
        setAlerts(derived);
      }
    });
  }, []);

  const qualityBars = useMemo(
    () => videos.slice(0, 12).map((v, idx) => ({
      name: `V${idx + 1}`,
      quality: Math.max(45, 62 + (idx % 7) * 5 - (v.status === 'error' ? 10 : 0)),
      retention: Math.max(40, 58 + (idx % 5) * 7),
    })),
    [videos]
  );

  return (
    <div className="animate-fade-in">
      <div className="section-header mb-24">
        <div>
          <h3 className="section-title" style={{ fontSize: 22 }}>Quality</h3>
          <p className="section-subtitle">Script, audio and publish-readiness quality controls</p>
        </div>
      </div>

      <div className="grid-4 mb-24">
        <QualityStat label="Avg Quality" value={`${Math.round(average(qualityBars.map((x) => x.quality)))}%`} color="var(--success)" />
        <QualityStat label="Avg Retention" value={`${Math.round(average(qualityBars.map((x) => x.retention)))}%`} color="var(--info)" />
        <QualityStat label="Issues" value={alerts.filter((a) => a.severity !== 'info').length} color="var(--warning)" />
        <QualityStat label="Ready Videos" value={videos.filter((v) => v.status === 'ready' || v.status === 'published').length} color="var(--accent)" />
      </div>

      <div className="grid-2 mb-24">
        <div className="card-glass">
          <h4 className="mb-12">Quality trend (30 days)</h4>
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={MOCK_DAILY_METRICS}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                <XAxis dataKey="day" stroke="#94A3B8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94A3B8" />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                <Area dataKey="quality" stroke="#22C55E" fill="#22C55E44" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card-glass">
          <h4 className="mb-12">Per-video quality checks</h4>
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={qualityBars}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                <XAxis dataKey="name" stroke="#94A3B8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94A3B8" />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                <Bar dataKey="quality" fill="#A855F7" radius={[5, 5, 0, 0]} />
                <Bar dataKey="retention" fill="#22D3EE" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card-glass">
        <h4 className="mb-12">Quality alerts</h4>
        <div className="flex flex-col gap-8">
          {alerts.map((alert) => (
            <button
              key={alert.id}
              className="card"
              style={{ textAlign: 'left', padding: 14, borderLeft: `3px solid ${severityColor(alert.severity)}`, background: 'rgba(15,23,42,0.5)' }}
              onClick={() => setSelectedAlert(alert)}
            >
              <div className={`badge ${alert.severity === 'error' ? 'badge-error' : alert.severity === 'warning' ? 'badge-warning' : 'badge-info'}`}>{alert.severity}</div>
              <div style={{ marginTop: 8 }}>{alert.message}</div>
            </button>
          ))}
        </div>
      </div>

      {selectedAlert && (
        <div className="modal-overlay" onClick={() => setSelectedAlert(null)}>
          <div className="modal-content" style={{ maxWidth: 560, background: '#111827' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: 24, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: 18 }}>Quality Alert</h3>
              <button className="modal-close" onClick={() => setSelectedAlert(null)}>×</button>
            </div>
            <div style={{ padding: 24 }}>
              <div className={`badge ${selectedAlert.severity === 'error' ? 'badge-error' : selectedAlert.severity === 'warning' ? 'badge-warning' : 'badge-info'}`}>
                {selectedAlert.severity}
              </div>
              <p style={{ marginTop: 12 }}>{selectedAlert.message}</p>
              <ul style={{ marginTop: 12, paddingLeft: 18, color: 'var(--text-secondary)' }}>
                <li>Review script and hook line.</li>
                <li>Run audio cleanup and normalize levels.</li>
                <li>Re-run quality checks before publish.</li>
              </ul>
              <div className="flex" style={{ justifyContent: 'flex-end', marginTop: 20 }}>
                <button className="btn btn-primary" onClick={() => setSelectedAlert(null)}>Acknowledge</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function QualityStat({ label, value, color }) {
  return (
    <div className="stat-card" style={{ borderLeft: `3px solid ${color}` }}>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ fontSize: 28, color }}>{value}</div>
    </div>
  );
}

function average(values) {
  if (!values.length) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function severityColor(level) {
  if (level === 'error') return 'var(--error)';
  if (level === 'warning') return 'var(--warning)';
  return 'var(--info)';
}
