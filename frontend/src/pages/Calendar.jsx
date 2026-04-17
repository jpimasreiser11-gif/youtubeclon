import { useEffect, useMemo, useState } from 'react';
import { addScheduledJob, cancelScheduledJob, fetchChannels, fetchScheduledJobs, fetchVideos } from '../api';
import { CHANNEL_COLORS, CHANNEL_FALLBACK_COLOR } from '../theme';
import { MOCK_CHANNELS, MOCK_QUEUE_ITEMS } from '../mockData';

export default function Calendar() {
  const [events, setEvents] = useState([]);
  const [videos, setVideos] = useState([]);
  const [channels, setChannels] = useState(MOCK_CHANNELS);
  const [openModal, setOpenModal] = useState(false);
  const [form, setForm] = useState({ videoId: '', channelId: '', scheduledAt: '' });

  const loadData = () => {
    Promise.all([
      fetchScheduledJobs('all').catch(() => ({ schedules: [] })),
      fetchVideos({ limit: 100 }).catch(() => ({ videos: [] })),
      fetchChannels().catch(() => MOCK_CHANNELS),
    ]).then(([scheduleRes, videoRes, channelRes]) => {
      const scheduleRows = Array.isArray(scheduleRes?.schedules) ? scheduleRes.schedules : [];
      if (scheduleRows.length > 0) {
        setEvents(scheduleRows);
      } else {
        setEvents(MOCK_QUEUE_ITEMS.filter((i) => i.scheduled_at).map((i, idx) => ({
          schedule_id: `mock-${idx}`,
          title: i.title,
          channel_name: i.channel_name,
          channel_slug: i.channel_id,
          status: i.status === 'error' ? 'error' : 'pending',
          scheduled_at: i.scheduled_at,
          video_id: i.id,
        })));
      }

      const videoRows = Array.isArray(videoRes?.videos) ? videoRes.videos : [];
      setVideos(videoRows.length ? videoRows : MOCK_QUEUE_ITEMS.map((i) => ({
        id: i.id,
        title: i.title,
        channel_id: 1 + (i.id % 6),
        channel_slug: i.channel_id,
      })));

      setChannels(Array.isArray(channelRes) && channelRes.length ? channelRes : MOCK_CHANNELS);
    });
  };

  useEffect(() => {
    loadData();
  }, []);

  const grouped = useMemo(() => {
    return events
      .slice()
      .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
      .reduce((acc, event) => {
        const day = new Date(event.scheduled_at).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
        acc[day] ||= [];
        acc[day].push(event);
        return acc;
      }, {});
  }, [events]);

  const addEvent = async () => {
    if (!form.videoId || !form.scheduledAt) return;
    const selectedVideo = videos.find((v) => String(v.id) === String(form.videoId));
    const fallbackChannel = channels.find((ch) => ch.channel_id === form.channelId);

    try {
      await addScheduledJob(Number(form.videoId), Number(selectedVideo?.channel_id || 0), new Date(form.scheduledAt).toISOString());
      setOpenModal(false);
      setForm({ videoId: '', channelId: '', scheduledAt: '' });
      loadData();
    } catch {
      setEvents((prev) => [
        {
          schedule_id: `local-${Date.now()}`,
          title: selectedVideo?.title || 'Manual event',
          channel_name: fallbackChannel?.name || selectedVideo?.channel_slug || 'Unknown',
          channel_slug: fallbackChannel?.channel_id || selectedVideo?.channel_slug || 'impacto-mundial',
          status: 'pending',
          scheduled_at: new Date(form.scheduledAt).toISOString(),
          video_id: Number(form.videoId),
        },
        ...prev,
      ]);
      setOpenModal(false);
    }
  };

  const removeEvent = async (id) => {
    if (String(id).startsWith('mock-') || String(id).startsWith('local-')) {
      setEvents((prev) => prev.filter((e) => e.schedule_id !== id));
      return;
    }
    try {
      await cancelScheduledJob(id);
      loadData();
    } catch {
      setEvents((prev) => prev.filter((e) => e.schedule_id !== id));
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="section-header mb-24">
        <div>
          <h3 className="section-title" style={{ fontSize: 22 }}>Calendar</h3>
          <p className="section-subtitle">Scheduling board with backend + mock fallback</p>
        </div>
        <button className="btn btn-primary" onClick={() => setOpenModal(true)}>+ Add Schedule</button>
      </div>

      <div className="card-glass">
        {Object.keys(grouped).length === 0 ? (
          <div className="empty-state"><div className="empty-state-title">No scheduled jobs</div></div>
        ) : (
          Object.entries(grouped).map(([day, dayEvents]) => (
            <div key={day} style={{ marginBottom: 20 }}>
              <div className="badge badge-info" style={{ marginBottom: 10 }}>{day}</div>
              <div className="flex flex-col gap-8">
                {dayEvents.map((event) => {
                  const color = CHANNEL_COLORS[event.channel_slug] || CHANNEL_FALLBACK_COLOR;
                  return (
                    <div key={event.schedule_id} className="card" style={{ padding: 16, borderLeft: `3px solid ${color}` }}>
                      <div className="flex items-center justify-between">
                        <div>
                          <div style={{ fontWeight: 700 }}>{event.title || `Video #${event.video_id}`}</div>
                          <div className="text-secondary fs-12">{event.channel_name} · {new Date(event.scheduled_at).toLocaleTimeString()}</div>
                        </div>
                        <div className="flex gap-8 items-center">
                          <span className={`badge ${event.status === 'error' ? 'badge-error' : event.status === 'completed' ? 'badge-success' : 'badge-warning'}`}>{event.status}</span>
                          <button className="btn btn-secondary btn-sm" onClick={() => removeEvent(event.schedule_id)}>Cancel</button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))
        )}
      </div>

      {openModal && (
        <div className="modal-overlay" onClick={() => setOpenModal(false)}>
          <div className="modal-content" style={{ maxWidth: 580, background: '#111827' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: 24, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: 18 }}>Create schedule</h3>
              <button className="modal-close" onClick={() => setOpenModal(false)}>×</button>
            </div>
            <div style={{ padding: 24 }}>
              <div className="mb-12">
                <label className="text-muted fs-12" style={{ display: 'block', marginBottom: 6 }}>Video</label>
                <select className="input" value={form.videoId} onChange={(e) => setForm((prev) => ({ ...prev, videoId: e.target.value }))}>
                  <option value="">Select a video</option>
                  {videos.slice(0, 60).map((v) => (
                    <option key={v.id} value={v.id}>{v.title || `Video #${v.id}`}</option>
                  ))}
                </select>
              </div>
              <div className="mb-12">
                <label className="text-muted fs-12" style={{ display: 'block', marginBottom: 6 }}>Channel (for fallback mode)</label>
                <select className="input" value={form.channelId} onChange={(e) => setForm((prev) => ({ ...prev, channelId: e.target.value }))}>
                  <option value="">Select channel</option>
                  {channels.map((ch) => (
                    <option key={ch.channel_id} value={ch.channel_id}>{ch.name}</option>
                  ))}
                </select>
              </div>
              <div className="mb-12">
                <label className="text-muted fs-12" style={{ display: 'block', marginBottom: 6 }}>Date & time</label>
                <input className="input" type="datetime-local" value={form.scheduledAt} onChange={(e) => setForm((prev) => ({ ...prev, scheduledAt: e.target.value }))} />
              </div>
              <div className="flex" style={{ justifyContent: 'flex-end', marginTop: 20 }}>
                <button className="btn btn-primary" onClick={addEvent}>Save schedule</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
