import { useEffect, useMemo, useState } from 'react';
import { fetchApiUsage, fetchChannels, fetchLogs, updateChannelConfig } from '../api';
import { buildMockApiUsage, buildMockLogs, MOCK_CHANNELS } from '../mockData';

export default function Settings() {
  const [apiUsage, setApiUsage] = useState(buildMockApiUsage());
  const [logs, setLogs] = useState(buildMockLogs());
  const [channels, setChannels] = useState(MOCK_CHANNELS);
  const [selectedChannel, setSelectedChannel] = useState(MOCK_CHANNELS[0]);
  const [form, setForm] = useState({ frequency: '', cpm_estimate: '' });
  const [savedMsg, setSavedMsg] = useState('');

  useEffect(() => {
    Promise.all([
      fetchApiUsage().catch(() => buildMockApiUsage()),
      fetchLogs(40).catch(() => buildMockLogs()),
      fetchChannels().catch(() => MOCK_CHANNELS),
    ]).then(([usage, l, ch]) => {
      const channelList = Array.isArray(ch) && ch.length ? ch : MOCK_CHANNELS;
      setApiUsage(Array.isArray(usage) && usage.length ? usage : buildMockApiUsage());
      setLogs(Array.isArray(l) && l.length ? l : buildMockLogs());
      setChannels(channelList);
      setSelectedChannel(channelList[0]);
      setForm({ frequency: channelList[0]?.frequency || '', cpm_estimate: channelList[0]?.cpm_estimate || '' });
    });
  }, []);

  useEffect(() => {
    if (!selectedChannel) return;
    setForm({ frequency: selectedChannel.frequency || '', cpm_estimate: selectedChannel.cpm_estimate || '' });
  }, [selectedChannel]);

  const totalRequests = useMemo(
    () => apiUsage.reduce((acc, item) => acc + Number(item.total_requests || 0), 0),
    [apiUsage]
  );

  const saveChannel = async () => {
    if (!selectedChannel) return;
    const payload = {
      frequency: String(form.frequency || '').trim(),
      cpm_estimate: Number(form.cpm_estimate || 0),
    };

    try {
      await updateChannelConfig(selectedChannel.channel_id, payload);
      setSavedMsg('Saved to backend.');
    } catch {
      setChannels((prev) => prev.map((ch) => ch.channel_id === selectedChannel.channel_id ? { ...ch, ...payload } : ch));
      setSavedMsg('Backend unavailable. Saved locally (mock mode).');
    }

    setTimeout(() => setSavedMsg(''), 2800);
  };

  return (
    <div className="animate-fade-in">
      <div className="grid-4 mb-24">
        <Tile label="API Requests Today" value={totalRequests.toLocaleString()} />
        <Tile label="Connected Channels" value={channels.length} />
        <Tile label="Alerts" value={logs.filter((l) => l.status === 'error').length} />
        <Tile label="Version" value="v2.0" />
      </div>

      <div className="grid-2">
        <div className="card-glass">
          <h3 className="section-title" style={{ fontSize: 20, marginBottom: 16 }}>Service Usage</h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Requests</th>
                  <th>Chars</th>
                </tr>
              </thead>
              <tbody>
                {apiUsage.map((row) => (
                  <tr key={row.service}>
                    <td>{row.service}</td>
                    <td>{Number(row.total_requests || 0).toLocaleString()}</td>
                    <td>{Number(row.total_chars || 0).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card-glass">
          <h3 className="section-title" style={{ fontSize: 20, marginBottom: 16 }}>Channel Settings</h3>
          <div className="mb-12">
            <label className="text-muted fs-12" style={{ display: 'block', marginBottom: 6 }}>Channel</label>
            <select className="input" value={selectedChannel?.channel_id || ''} onChange={(e) => setSelectedChannel(channels.find((ch) => ch.channel_id === e.target.value))}>
              {channels.map((ch) => (
                <option key={ch.channel_id} value={ch.channel_id}>{ch.name}</option>
              ))}
            </select>
          </div>
          <div className="mb-12">
            <label className="text-muted fs-12" style={{ display: 'block', marginBottom: 6 }}>Publish frequency</label>
            <input className="input" value={form.frequency} onChange={(e) => setForm((prev) => ({ ...prev, frequency: e.target.value }))} />
          </div>
          <div className="mb-12">
            <label className="text-muted fs-12" style={{ display: 'block', marginBottom: 6 }}>Estimated CPM</label>
            <input className="input" type="number" value={form.cpm_estimate} onChange={(e) => setForm((prev) => ({ ...prev, cpm_estimate: e.target.value }))} />
          </div>
          <button className="btn btn-primary" onClick={saveChannel}>Save settings</button>
          {savedMsg && <div className="badge badge-info" style={{ marginTop: 12 }}>{savedMsg}</div>}

          <h4 style={{ marginTop: 20, marginBottom: 10 }}>Recent logs</h4>
          <div style={{ maxHeight: 220, overflow: 'auto' }}>
            {logs.slice(0, 12).map((log, i) => (
              <div key={i} className="activity-item" style={{ padding: '8px 0' }}>
                <div className="activity-dot" style={{ background: log.status === 'error' ? 'var(--error)' : log.status === 'ok' ? 'var(--success)' : 'var(--warning)' }}></div>
                <div className="activity-content">
                  <div className="fs-12" style={{ fontWeight: 600 }}>{log.step || 'pipeline'}</div>
                  <div className="text-secondary fs-12">{log.message}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Tile({ label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ fontSize: 27 }}>{value}</div>
    </div>
  );
}
