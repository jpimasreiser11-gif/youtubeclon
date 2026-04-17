import { useEffect, useMemo, useState } from 'react';
import { fetchChannels } from '../api';
import { CHANNEL_COLORS, CHANNEL_FALLBACK_COLOR } from '../theme';
import { MOCK_CHANNELS } from '../mockData';

export default function Channels() {
  const [channels, setChannels] = useState(MOCK_CHANNELS);
  const [selected, setSelected] = useState(MOCK_CHANNELS[0]);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    fetchChannels()
      .then((data) => {
        if (Array.isArray(data) && data.length) {
          setChannels(data);
          setSelected(data[0]);
        }
      })
      .catch(() => setChannels(MOCK_CHANNELS));
  }, []);

  const stats = useMemo(() => {
    const active = channels.filter((c) => Number(c.is_active) === 1).length;
    const avgCpm = channels.reduce((acc, c) => acc + Number(c.cpm_estimate || 0), 0) / (channels.length || 1);
    return { active, avgCpm: avgCpm.toFixed(1) };
  }, [channels]);

  return (
    <div className="animate-fade-in">
      <div className="grid-4 mb-24">
        <SimpleStat label="Channels" value={channels.length} />
        <SimpleStat label="Active" value={stats.active} />
        <SimpleStat label="Avg CPM" value={`$${stats.avgCpm}`} />
        <SimpleStat label="Languages" value="2" />
      </div>

      <div className="grid-2">
        <div className="card-glass">
          <div className="section-header">
            <div>
              <h3 className="section-title" style={{ fontSize: 20 }}>Channel Operations</h3>
              <p className="section-subtitle">Select channel to inspect profile</p>
            </div>
          </div>
          <div className="flex flex-col gap-12">
            {channels.map((ch) => {
              const color = CHANNEL_COLORS[ch.channel_id] || ch.accent || CHANNEL_FALLBACK_COLOR;
              return (
                <button
                  key={ch.channel_id}
                  className="channel-card"
                  onClick={() => setSelected(ch)}
                  style={{ '--channel-color': color, textAlign: 'left', cursor: 'pointer', borderColor: selected?.channel_id === ch.channel_id ? color : 'var(--border)' }}
                >
                  <div className="flex items-center justify-between mb-8">
                    <div>
                      <div className="channel-name" style={{ fontSize: 16 }}>{ch.name}</div>
                      <div className="channel-niche">{ch.niche || 'No niche provided'}</div>
                    </div>
                    <span className={`badge ${Number(ch.is_active) === 1 ? 'badge-success' : 'badge-neutral'}`}>
                      <span className="badge-dot"></span>
                      {Number(ch.is_active) === 1 ? 'Active' : 'Paused'}
                    </span>
                  </div>
                  <div className="channel-stats">
                    <div className="channel-stat-item"><span>Frequency</span><span>{ch.frequency || '—'}</span></div>
                    <div className="channel-stat-item"><span>Language</span><span>{(ch.language || '').toUpperCase()}</span></div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="card-glass">
          {selected ? (
            <>
              <div className="section-header">
                <div>
                  <h3 className="section-title" style={{ fontSize: 20 }}>{selected.name}</h3>
                  <p className="section-subtitle">{selected.niche || 'Niche not configured'}</p>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={() => setModalOpen(true)}>Open config modal</button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {[
                  ['Channel ID', selected.channel_id],
                  ['Audience', selected.audience || '—'],
                  ['Tone', selected.tone || '—'],
                  ['CPM', `$${selected.cpm_estimate || '0'}`],
                  ['Duration', `${selected.duration_min || 6}-${selected.duration_max || 14} min`],
                  ['Category', selected.category_id || '—'],
                ].map(([label, value]) => (
                  <div key={label} style={{ padding: '12px 14px', border: '1px solid var(--border)', borderRadius: 10, background: 'rgba(15,23,42,0.45)' }}>
                    <div className="text-muted fs-12">{label}</div>
                    <div style={{ marginTop: 4, fontWeight: 600 }}>{value}</div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty-state"><div className="empty-state-title">Select a channel</div></div>
          )}
        </div>
      </div>

      {modalOpen && selected && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal-content" style={{ maxWidth: 560, background: '#111827' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: 24, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: 18 }}>Channel Configuration</h3>
              <button className="modal-close" onClick={() => setModalOpen(false)}>×</button>
            </div>
            <div style={{ padding: 24 }}>
              <p className="text-secondary fs-14">{selected.name} is configured for <strong>{selected.frequency || 'custom cadence'}</strong> publishing.</p>
              <div className="mt-16">
                <span className="badge badge-info">Language: {(selected.language || 'n/a').toUpperCase()}</span>
                <span className="badge badge-warning" style={{ marginLeft: 8 }}>CPM ${selected.cpm_estimate || '0'}</span>
              </div>
              <div className="flex" style={{ justifyContent: 'flex-end', marginTop: 20 }}>
                <button className="btn btn-primary" onClick={() => setModalOpen(false)}>Done</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SimpleStat({ label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ fontSize: 26 }}>{value}</div>
    </div>
  );
}
