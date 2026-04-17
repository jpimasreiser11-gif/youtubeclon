import { useState, useEffect, useRef } from 'react';
import { fetchChannels, triggerGeneration, fetchPipelineStatus } from '../api';
import { CHANNEL_COLORS, CHANNEL_FALLBACK_COLOR } from '../theme';

export default function Generator() {
  const [channels, setChannels] = useState([]);
  const [selectedChannel, setSelectedChannel] = useState('');
  const [topic, setTopic] = useState('');
  const [upload, setUpload] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [logs, setLogs] = useState([]);
  const pollRef = useRef(null);

  useEffect(() => {
    fetchChannels()
      .then(chs => {
        setChannels(chs);
        if (chs.length > 0) setSelectedChannel(chs[0].channel_id);
      })
      .catch(() => {});
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const handleGenerate = async () => {
    if (!selectedChannel) return;
    setGenerating(true);
    setError('');
    setResult(null);
    setLogs([{ time: new Date().toLocaleTimeString(), msg: '🚀 Iniciando pipeline...' }]);

    try {
      const res = await triggerGeneration(selectedChannel, topic || null, upload);
      setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), msg: `✅ ${res.message}` }]);

      // Poll for updates
      pollRef.current = setInterval(async () => {
        try {
          const status = await fetchPipelineStatus();
          const chStatus = status.running_jobs?.[selectedChannel];
          const newLogs = (status.recent_logs || []).slice(0, 5).map(l => ({
            time: l.created_at ? new Date(l.created_at).toLocaleTimeString() : '',
            msg: `${l.status === 'ok' ? '✅' : l.status === 'error' ? '❌' : '⏳'} ${l.step?.replace(/_/g, ' ')}: ${l.message?.slice(0, 80) || ''}`,
          }));

          if (newLogs.length > 0) {
            setLogs(prev => {
              const existing = new Set(prev.map(l => l.msg));
              const fresh = newLogs.filter(l => !existing.has(l.msg));
              return [...prev, ...fresh];
            });
          }

          if (chStatus === 'done' || chStatus === 'error') {
            clearInterval(pollRef.current);
            setGenerating(false);
            if (chStatus === 'done') {
              setResult({ status: 'ok', message: 'Video generado exitosamente' });
            } else {
              setError('El pipeline terminó con errores. Revisa los logs.');
            }
          }
        } catch {
          // Skip polling errors
        }
      }, 3000);

    } catch (err) {
      setGenerating(false);
      setError(err.message || 'Error al iniciar la generación');
    }
  };

  const selectedCh = channels.find(c => c.channel_id === selectedChannel);

  return (
    <div className="animate-fade-in">
      <div className="section-header mb-24">
        <div>
          <h3 className="section-title">Generador de Videos</h3>
          <p className="section-subtitle">Genera un video completo para cualquier canal</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Generator Form */}
        <div className="card">
          <h4 className="fw-700 mb-16">Configuración</h4>

          {/* Channel Selector */}
          <div className="mb-16">
            <label className="fs-12 text-muted" style={{ display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>
              Canal
            </label>
            <select
              className="input"
              value={selectedChannel}
              onChange={e => setSelectedChannel(e.target.value)}
              disabled={generating}
            >
              {channels.map(ch => (
                <option key={ch.channel_id} value={ch.channel_id}>
                  {ch.language === 'es' ? '🇪🇸' : '🇬🇧'} {ch.name}
                </option>
              ))}
            </select>
          </div>

          {/* Topic */}
          <div className="mb-16">
            <label className="fs-12 text-muted" style={{ display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>
              Tema (opcional — detecta tendencias automáticamente)
            </label>
            <input
              type="text"
              className="input"
              placeholder="Ej: Los secretos que la NASA no quiere que sepas..."
              value={topic}
              onChange={e => setTopic(e.target.value)}
              disabled={generating}
            />
          </div>

          {/* Upload toggle */}
          <div className="mb-24">
            <label className="flex items-center gap-12" style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={upload}
                onChange={e => setUpload(e.target.checked)}
                disabled={generating}
                style={{ width: 18, height: 18, accentColor: 'var(--accent)' }}
              />
              <span className="fs-14">Subir a YouTube automáticamente</span>
            </label>
          </div>

          {/* Generate Button */}
          <button
            className={`btn ${generating ? 'btn-secondary' : 'btn-primary'} btn-lg`}
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating ? (
              <>
                <span className="animate-pulse">⏳</span>
                Generando... Este proceso tarda varios minutos
              </>
            ) : (
              <>⚡ Generar Video</>
            )}
          </button>

          {/* Error */}
          {error && (
            <div className="mt-16" style={{
              padding: '12px 16px', background: 'var(--error-dim)',
              borderRadius: 8, fontSize: 13, color: 'var(--error)',
              border: '1px solid rgba(244, 63, 94, 0.2)',
            }}>
              ❌ {error}
            </div>
          )}

          {/* Success */}
          {result?.status === 'ok' && (
            <div className="mt-16" style={{
              padding: '12px 16px', background: 'var(--success-dim)',
              borderRadius: 8, fontSize: 13, color: 'var(--success)',
              border: '1px solid rgba(52, 211, 153, 0.2)',
            }}>
              ✅ {result.message}
            </div>
          )}

          {/* Selected channel info */}
          {selectedCh && (
            <div className="mt-24" style={{
              padding: '16px', background: 'var(--bg-surface)',
              borderRadius: 12, borderLeft: `3px solid ${CHANNEL_COLORS[selectedCh.channel_id] || CHANNEL_FALLBACK_COLOR}`,
            }}>
              <div className="fw-600 fs-14 mb-8">{selectedCh.name}</div>
              <div className="fs-12 text-secondary mb-8">{selectedCh.tone}</div>
              <div className="flex gap-16 fs-12">
                <span className="text-muted">Duración: {selectedCh.duration_min}-{selectedCh.duration_max} min</span>
                <span className="text-muted">CPM: ${selectedCh.cpm_estimate}</span>
              </div>
            </div>
          )}
        </div>

        {/* Real-time Logs */}
        <div className="card" style={{ maxHeight: 600, overflow: 'auto' }}>
          <h4 className="fw-700 mb-16">
            📡 Pipeline en tiempo real
            {generating && <span className="badge badge-warning ml-8" style={{ marginLeft: 8 }}>
              <span className="badge-dot animate-pulse"></span>
              En progreso
            </span>}
          </h4>

          {logs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <div className="empty-state-title">Esperando inicio</div>
              <p className="text-muted fs-14">
                Los logs aparecerán aquí cuando inicies la generación.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-8">
              {logs.map((log, idx) => (
                <div key={idx} className="animate-fade-in" style={{
                  padding: '10px 14px', background: 'var(--bg-surface)',
                  borderRadius: 8, fontSize: 12, fontFamily: "'JetBrains Mono', monospace",
                }}>
                  <span className="text-muted">[{log.time}]</span>{' '}
                  <span>{log.msg}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
