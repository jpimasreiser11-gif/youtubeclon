import { useState, useEffect } from 'react';
import { fetchVideos, fetchChannels, addScheduledJob, deleteVideo, purgeAllVideos, triggerGeneration } from '../api';
import { CHANNEL_COLORS, CHANNEL_FALLBACK_COLOR } from '../theme';

const STATUS_MAP = {
  pending: { label: 'Pendiente', badge: 'badge-neutral' },
  generating: { label: 'Generando', badge: 'badge-warning' },
  script_ready: { label: 'Guión OK', badge: 'badge-info' },
  audio_ready: { label: 'Audio OK', badge: 'badge-info' },
  video_ready: { label: 'Video OK', badge: 'badge-info' },
  thumbnail_ready: { label: 'Thumb OK', badge: 'badge-info' },
  metadata_ready: { label: 'Metadata OK', badge: 'badge-info' },
  ready: { label: 'Listo', badge: 'badge-success' },
  published: { label: 'Publicado', badge: 'badge-success' },
  error: { label: 'Error', badge: 'badge-error' },
};

const CHANNEL_DIRS = {
  'impacto-mundial': 'channel_1_impacto_mundial',
  'mentes-rotas': 'channel_2_mentes_rotas',
  'el-loco-de-la-ia': 'channel_3_loco_ia',
  'mind-warp': 'channel_4_mind_warp',
  'wealth-files': 'channel_5_wealth_files',
  'dark-science': 'channel_6_dark_science',
};

export default function Library() {
  const [videos, setVideos] = useState([]);
  const [channels, setChannels] = useState([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState({ channel: '', status: '' });
  const [loading, setLoading] = useState(true);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [regeneratingId, setRegeneratingId] = useState(null);

  useEffect(() => {
    fetchChannels().then(setChannels).catch(() => {});
  }, []);

  const loadVideos = () => {
    setLoading(true);
    const params = {};
    if (filter.channel) params.channel = filter.channel;
    if (filter.status) params.status = filter.status;
    fetchVideos(params)
      .then(data => {
        setVideos(data.videos || []);
        setTotal(data.total || 0);
      })
      .catch(() => { setVideos([]); setTotal(0); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadVideos(); }, [filter]);

  const openVideo = (v) => {
    if (!v.video_path) return;
    const filename = v.video_path.split('\\').pop().split('/').pop();
    const dir = CHANNEL_DIRS[v.channel_slug] || v.channel_slug;
    const path = `/media/${dir}/videos/${filename}`;
    setSelectedVideo({ ...v, url: path });
  };

  const handleSchedule = async (v) => {
    const defaultDate = new Date(Date.now() + 86400000); // tomorrow
    
    // offset for local timezone string formatting
    const tzOffset = defaultDate.getTimezoneOffset() * 60000;
    const localISOTime = new Date(defaultDate - tzOffset).toISOString().slice(0,16);

    const d = prompt("Introduce fecha y hora para programar (YYYY-MM-DD HH:MM)", localISOTime.replace('T', ' '));
    if (!d) return;

    try {
      const scheduledAt = new Date(d).toISOString();
      await addScheduledJob(v.id, v.channel_id, scheduledAt);
      alert('¡Video encolado para publicación automática!');
    } catch (e) {
      alert('Error al programar: ' + e.message);
    }
  };

  const handleDeleteVideo = async (v) => {
    const ok = window.confirm(`¿Borrar este video?\n\n${v.title || v.topic || `Video #${v.id}`}`);
    if (!ok) return;
    try {
      setDeleting(true);
      await deleteVideo(v.id);
      if (selectedVideo?.id === v.id) setSelectedVideo(null);
      loadVideos();
    } catch (e) {
      alert('Error al borrar video: ' + e.message);
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteAllVideos = async () => {
    const ok = window.confirm('Esto borrará TODOS los videos y archivos generados. ¿Continuar?');
    if (!ok) return;
    try {
      setDeleting(true);
      await purgeAllVideos();
      setSelectedVideo(null);
      loadVideos();
    } catch (e) {
      alert('Error al borrar todos los videos: ' + e.message);
    } finally {
      setDeleting(false);
    }
  };

  const handleRegeneratePro = async (v) => {
    const baseTopic = (v.topic || v.title || '').trim();
    if (!v.channel_slug || !baseTopic) {
      alert('No se puede regenerar: falta canal o tema.');
      return;
    }
    const ok = window.confirm(`Regenerar versión PRO de este video?\n\n${baseTopic}`);
    if (!ok) return;
    try {
      setRegeneratingId(v.id);
      await triggerGeneration(v.channel_slug, baseTopic, false);
      alert('Regeneración iniciada. En unos segundos aparecerá el nuevo video en la biblioteca.');
      loadVideos();
    } catch (e) {
      alert('Error al regenerar: ' + e.message);
    } finally {
      setRegeneratingId(null);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="section-header mb-24">
        <div>
          <h3 className="section-title text-accent" style={{ textShadow: '0 0 10px var(--accent-glow-strong)' }}>
            Biblioteca de Videos
          </h3>
          <p className="section-subtitle">{total} videos generados en el sistema</p>
        </div>
        <button
          className="btn btn-secondary"
          style={{ background: 'transparent', border: '1px solid #ef4444', color: '#ef4444' }}
          onClick={handleDeleteAllVideos}
          disabled={deleting}
        >
          🗑 Borrar todos
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-12 mb-24">
        <select
          className="input"
          style={{ width: 220, border: '1px solid var(--accent)' }}
          value={filter.channel}
          onChange={e => setFilter(f => ({ ...f, channel: e.target.value }))}
        >
          <option value="">Todos los canales</option>
          {channels.map(ch => (
            <option key={ch.channel_id} value={ch.channel_id}>{ch.name}</option>
          ))}
        </select>
        <select
          className="input"
          style={{ width: 180, border: '1px solid var(--accent)' }}
          value={filter.status}
          onChange={e => setFilter(f => ({ ...f, status: e.target.value }))}
        >
          <option value="">Todos los estados</option>
          <option value="published">Publicado</option>
          <option value="ready">Listo</option>
          <option value="generating">Generando</option>
          <option value="error">Error</option>
        </select>
      </div>

      {/* Videos Grid / Table */}
      {loading ? (
        <div className="card-glass">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex gap-16 mb-16">
              <div className="skeleton" style={{ width: 120, height: 68, borderRadius: 8 }}></div>
              <div style={{ flex: 1 }}>
                <div className="skeleton" style={{ width: '70%', height: 16, marginBottom: 8 }}></div>
                <div className="skeleton" style={{ width: '40%', height: 12 }}></div>
              </div>
            </div>
          ))}
        </div>
      ) : videos.length === 0 ? (
        <div className="card-glass" style={{ border: '1px solid var(--accent)' }}>
          <div className="empty-state">
            <div className="empty-state-icon" style={{ textShadow: '0 0 20px var(--accent)' }}>🎬</div>
            <div className="empty-state-title" style={{ color: 'var(--text-primary)' }}>Sin videos aún</div>
            <p className="text-muted fs-14">
              Ve al motor de ideas para generar contenido viral.
            </p>
          </div>
        </div>
      ) : (
        <div className="table-container card-glass" style={{ border: '1px solid var(--accent)' }}>
          <table>
            <thead>
              <tr>
                <th style={{ color: 'var(--accent)' }}>Miniatura / Video</th>
                <th style={{ color: 'var(--accent)' }}>Canal</th>
                <th style={{ color: 'var(--accent)' }}>Estado</th>
                <th style={{ color: 'var(--accent)' }}>Duración</th>
                <th style={{ color: 'var(--accent)' }}>Creado</th>
                <th style={{ color: 'var(--accent)' }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {videos.map((v, idx) => {
                const st = STATUS_MAP[v.status] || STATUS_MAP.pending;
                const isPlayable = v.video_path && (v.status === 'video_ready' || v.status === 'ready' || v.status === 'published');
                
                let thumbUrl = null;
                if (v.thumbnail_path) {
                    const t_file = v.thumbnail_path.split('\\').pop().split('/').pop();
                    const dir = CHANNEL_DIRS[v.channel_slug] || v.channel_slug;
                    thumbUrl = `/media/${dir}/thumbnails/${t_file}`;
                }

                return (
                  <tr key={v.id} className="animate-fade-in" style={{ animationDelay: `${idx * 30}ms` }}>
                    <td style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                      <div 
                        style={{ 
                          width: '120px', 
                          height: '68px', 
                          backgroundColor: 'var(--bg-elevated)',
                          backgroundImage: thumbUrl ? `url("${thumbUrl}")` : 'none',
                          backgroundPosition: 'center',
                          backgroundSize: 'cover',
                          borderRadius: '8px',
                          border: isPlayable ? '2px solid var(--accent)' : '1px solid var(--border)',
                          cursor: isPlayable ? 'pointer' : 'default',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          boxShadow: isPlayable ? '0 0 10px var(--accent-glow)' : 'none'
                        }}
                        onClick={() => { if (isPlayable) openVideo(v); }}
                      >
                         {!thumbUrl && <span style={{ fontSize: '24px', opacity: 0.5 }}>🎬</span>}
                         {isPlayable && thumbUrl && (
                             <div style={{ background: 'rgba(0,0,0,0.6)', borderRadius: '50%', padding: '4px 8px', fontSize: '10px' }}>
                                 ▶
                             </div>
                         )}
                      </div>
                      <div>
                        <div className="fw-600 fs-14" style={{ maxWidth: 300, color: 'var(--text-primary)' }}>
                          {v.title || v.topic || 'Sin título'}
                        </div>
                        {v.youtube_url && (
                          <a href={v.youtube_url} target="_blank" rel="noopener" className="fs-12 text-success mt-4 inline-block">
                            🔗 Ver en YouTube
                          </a>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="flex items-center gap-8">
                        <span style={{
                          width: 8, height: 8, borderRadius: '50%',
                          background: CHANNEL_COLORS[v.channel_slug] || CHANNEL_FALLBACK_COLOR,
                          boxShadow: `0 0 8px ${CHANNEL_COLORS[v.channel_slug] || CHANNEL_FALLBACK_COLOR}`
                        }}></span>
                        <span style={{ color: 'var(--text-secondary)' }}>
                           {v.channel_name || v.channel_slug || '—'}
                        </span>
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${st.badge}`} style={{ border: '1px solid currentColor', background: 'transparent' }}>
                        {st.label}
                      </span>
                    </td>
                    <td className="mono fs-12 text-secondary">
                      {v.duration_seconds ? formatDuration(v.duration_seconds) : '—'}
                    </td>
                    <td className="mono fs-12 text-muted">
                      {v.created_at ? new Date(v.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td>
                      <div className="flex gap-8">
                        {isPlayable && (
                          <button
                            className="btn btn-primary btn-sm"
                            style={{ background: 'transparent', border: '1px solid var(--accent)', color: 'var(--accent)' }}
                            onClick={() => openVideo(v)}
                          >
                            ▶ VIP Play
                          </button>
                        )}
                        {(v.status === 'ready' || v.status === 'video_ready' || v.status === 'thumbnail_ready') && (
                          <button
                            className="btn btn-secondary btn-sm"
                            style={{ background: 'transparent', border: '1px solid var(--warning)', color: 'var(--warning)' }}
                            onClick={() => handleSchedule(v)}
                          >
                            📅 Programar
                          </button>
                        )}
                        <button
                          className="btn btn-secondary btn-sm"
                          style={{ background: 'transparent', border: '1px solid #22c55e', color: '#22c55e' }}
                          onClick={() => handleRegeneratePro(v)}
                          disabled={deleting || regeneratingId === v.id}
                        >
                          {regeneratingId === v.id ? '⏳ Regenerando...' : '♻ Regenerar PRO'}
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          style={{ background: 'transparent', border: '1px solid #ef4444', color: '#ef4444' }}
                          onClick={() => handleDeleteVideo(v)}
                          disabled={deleting || regeneratingId === v.id}
                        >
                          🗑 Borrar
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Embedded Video Modal */}
      {selectedVideo && (
        <div className="modal-overlay" onClick={() => setSelectedVideo(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedVideo.title || selectedVideo.topic}</h3>
              <button className="modal-close" onClick={() => setSelectedVideo(null)}>×</button>
            </div>
            <video 
              src={selectedVideo.url} 
              controls 
              autoPlay 
              style={{ width: '100%', maxHeight: '80vh', display: 'block', background: 'var(--bg-base)' }}
            >
              Tu navegador no soporta el reproductor de video.
            </video>
          </div>
        </div>
      )}

    </div>
  );
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}
