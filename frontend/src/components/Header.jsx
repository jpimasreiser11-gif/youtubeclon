import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { fetchChannels, triggerGeneration } from '../api';
import { MOCK_CHANNELS } from '../mockData';

const PAGE_TITLES = {
  '/': 'Dashboard',
  '/channels': 'Channels',
  '/queue': 'Queue',
  '/calendar': 'Calendar',
  '/analytics': 'Analytics',
  '/quality': 'Quality',
  '/settings': 'Settings',
};

export default function Header() {
  const location = useLocation();
  const title = PAGE_TITLES[location.pathname] || 'YouTube Automation Pro';

  const [channels, setChannels] = useState(MOCK_CHANNELS);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState(MOCK_CHANNELS[0]?.channel_id || '');
  const [generating, setGenerating] = useState(false);
  const [feedback, setFeedback] = useState(null);

  useEffect(() => {
    fetchChannels()
      .then((list) => {
        if (Array.isArray(list) && list.length > 0) {
          setChannels(list);
          setSelectedChannel(list[0].channel_id);
        }
      })
      .catch(() => setChannels(MOCK_CHANNELS));
  }, []);

  useEffect(() => {
    if (!feedback) return;
    const timer = setTimeout(() => setFeedback(null), 3600);
    return () => clearTimeout(timer);
  }, [feedback]);

  const selectedName = useMemo(
    () => channels.find((ch) => ch.channel_id === selectedChannel)?.name || selectedChannel,
    [channels, selectedChannel]
  );

  const handleGenerateNow = async () => {
    if (!selectedChannel) return;
    setGenerating(true);

    try {
      const res = await triggerGeneration(selectedChannel, null, false);
      setFeedback({ type: 'success', message: res.message || `Generation started for ${selectedName}` });
      window.dispatchEvent(new CustomEvent('yt-generate-now', { detail: { mode: 'backend', channelId: selectedChannel } }));
      setIsModalOpen(false);
    } catch (error) {
      const message = `Backend unavailable. Mocked Generate Now triggered for ${selectedName}.`;
      setFeedback({ type: 'info', message });
      window.dispatchEvent(new CustomEvent('yt-generate-now', { detail: { mode: 'mock', channelId: selectedChannel } }));
      setIsModalOpen(false);
      console.warn(error);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <>
      <header className="header">
        <div>
          <h2 className="header-title">{title}</h2>
          {feedback && (
            <div className={`badge ${feedback.type === 'success' ? 'badge-success' : 'badge-info'}`} style={{ marginTop: 6 }}>
              <span className="badge-dot"></span>
              {feedback.message}
            </div>
          )}
        </div>
        <div className="header-actions">
          <span className="badge badge-success">
            <span className="badge-dot"></span>
            System active
          </span>
          <button className="btn btn-primary btn-sm" onClick={() => setIsModalOpen(true)}>
            ⚡ Generate Now
          </button>
        </div>
      </header>

      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-content" style={{ maxWidth: 520, background: '#111827' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: '24px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: 20, fontWeight: 700 }}>Generate Now</h3>
              <button className="modal-close" onClick={() => setIsModalOpen(false)}>×</button>
            </div>
            <div style={{ padding: 24 }}>
              <label className="fs-12 text-muted" style={{ display: 'block', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>
                Channel
              </label>
              <select className="input" value={selectedChannel} onChange={(e) => setSelectedChannel(e.target.value)}>
                {channels.map((ch) => (
                  <option key={ch.channel_id} value={ch.channel_id}>
                    {ch.language === 'es' ? '🇪🇸' : '🇬🇧'} {ch.name}
                  </option>
                ))}
              </select>
              <p className="text-secondary fs-12" style={{ marginTop: 10 }}>
                Calls /api/pipeline/generate when backend is available. Falls back to a mocked action path otherwise.
              </p>
              <div className="flex gap-12" style={{ marginTop: 20, justifyContent: 'flex-end' }}>
                <button className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button className="btn btn-primary" onClick={handleGenerateNow} disabled={generating}>
                  {generating ? 'Starting…' : 'Start generation'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
