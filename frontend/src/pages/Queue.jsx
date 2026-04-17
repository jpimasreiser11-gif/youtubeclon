import { useEffect, useMemo, useState } from 'react';
import { fetchPipelineStatus, fetchVideos, publishNow } from '../api';
import { CHANNEL_COLORS, CHANNEL_FALLBACK_COLOR } from '../theme';
import { MOCK_QUEUE_ITEMS } from '../mockData';

const STATUS_OPTIONS = ['all', 'pending', 'generating', 'ready', 'published', 'error'];

export default function Queue() {
  const [items, setItems] = useState(MOCK_QUEUE_ITEMS);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selected, setSelected] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState({});
  const [toast, setToast] = useState(null);

  const loadQueue = () => {
    fetchVideos({ limit: 200 })
      .then((data) => {
        if (!Array.isArray(data?.videos) || !data.videos.length) return setItems(MOCK_QUEUE_ITEMS);
        const mapped = data.videos.map((v) => ({
          id: v.id,
          title: v.title || v.topic || `Video #${v.id}`,
          topic: v.topic || 'Auto generated topic',
          channel_id: v.channel_slug,
          channel_name: v.channel_name || v.channel_slug,
          status: v.status || 'pending',
          scheduled_at: v.created_at,
          duration_seconds: v.duration_seconds || 480,
          quality_score: 70,
          priority: 'normal',
        }));
        setItems(mapped);
      })
      .catch(() => setItems(MOCK_QUEUE_ITEMS));

    fetchPipelineStatus()
      .then((res) => setPipelineStatus(res?.running_jobs || {}))
      .catch(() => setPipelineStatus({}));
  };

  useEffect(() => {
    loadQueue();
    const handler = () => loadQueue();
    window.addEventListener('yt-generate-now', handler);
    return () => window.removeEventListener('yt-generate-now', handler);
  }, []);

  const filtered = useMemo(
    () => items.filter((i) => statusFilter === 'all' || i.status === statusFilter),
    [items, statusFilter]
  );

  const launchPublishNow = async (item) => {
    try {
      await publishNow(item.id);
      setToast({ type: 'success', msg: `Publish-now queued for ${item.title}` });
    } catch {
      setToast({ type: 'info', msg: `Mock publish-now executed for ${item.title}` });
    }
  };

  return (
    <div className="animate-fade-in">
      {toast && <div className={`toast toast-${toast.type === 'success' ? 'success' : 'info'}`}>{toast.msg}</div>}

      <div className="section-header mb-16">
        <div>
          <h3 className="section-title" style={{ fontSize: 22 }}>Production Queue</h3>
          <p className="section-subtitle">Track draft → generate → ready → publish lifecycle</p>
        </div>
      </div>

      <div className="flex gap-8 mb-24" style={{ flexWrap: 'wrap' }}>
        {STATUS_OPTIONS.map((status) => (
          <button
            key={status}
            className={`btn btn-sm ${status === statusFilter ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setStatusFilter(status)}
          >
            {status}
          </button>
        ))}
      </div>

      <div className="card-glass mb-24">
        <div className="section-header" style={{ marginBottom: 12 }}>
          <h3 className="section-title" style={{ fontSize: 18 }}>Active backend jobs</h3>
        </div>
        {Object.keys(pipelineStatus).length === 0 ? (
          <p className="text-secondary fs-14">No live backend jobs detected. Showing queue snapshot only.</p>
        ) : (
          Object.entries(pipelineStatus).map(([channel, state]) => (
            <div key={channel} className="activity-item">
              <div className="activity-dot" style={{ background: state === 'running' ? 'var(--warning)' : state === 'done' ? 'var(--success)' : 'var(--error)' }}></div>
              <div className="activity-content"><strong>{channel}</strong> · {state}</div>
            </div>
          ))
        )}
      </div>

      <div className="table-container card-glass">
        <table>
          <thead>
            <tr>
              <th>Video</th>
              <th>Channel</th>
              <th>Status</th>
              <th>Scheduled</th>
              <th>Quality</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => {
              const color = CHANNEL_COLORS[item.channel_id] || CHANNEL_FALLBACK_COLOR;
              return (
                <tr key={item.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{item.title}</div>
                    <div className="text-secondary fs-12">{item.topic}</div>
                  </td>
                  <td>
                    <span className="badge badge-neutral" style={{ border: `1px solid ${color}` }}>{item.channel_name}</span>
                  </td>
                  <td>
                    <span className={`badge ${item.status === 'error' ? 'badge-error' : item.status === 'published' ? 'badge-success' : item.status === 'ready' ? 'badge-info' : 'badge-warning'}`}>
                      {item.status}
                    </span>
                  </td>
                  <td>{item.scheduled_at ? new Date(item.scheduled_at).toLocaleString() : '—'}</td>
                  <td>{item.quality_score || 0}%</td>
                  <td>
                    <div className="flex gap-8">
                      <button className="btn btn-secondary btn-sm" onClick={() => setSelected(item)}>Details</button>
                      {(item.status === 'ready' || item.status === 'published') && (
                        <button className="btn btn-primary btn-sm" onClick={() => launchPublishNow(item)}>Publish now</button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal-content" style={{ maxWidth: 600, background: '#111827' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: 24, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: 18 }}>{selected.title}</h3>
              <button className="modal-close" onClick={() => setSelected(null)}>×</button>
            </div>
            <div style={{ padding: 24 }}>
              <div className="grid-2">
                <Detail label="Channel" value={selected.channel_name} />
                <Detail label="Status" value={selected.status} />
                <Detail label="Duration" value={`${Math.round((selected.duration_seconds || 0) / 60)} min`} />
                <Detail label="Quality" value={`${selected.quality_score || 0}%`} />
              </div>
              <p className="text-secondary fs-14" style={{ marginTop: 18 }}>{selected.topic}</p>
              <div className="flex" style={{ justifyContent: 'flex-end', marginTop: 20 }}>
                <button className="btn btn-primary" onClick={() => setSelected(null)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div style={{ padding: '10px 12px', border: '1px solid var(--border)', borderRadius: 10 }}>
      <div className="text-muted fs-12">{label}</div>
      <div style={{ marginTop: 4, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
