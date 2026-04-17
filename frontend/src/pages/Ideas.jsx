import { useState, useEffect } from 'react';
import { CHANNEL_COLORS, CHANNEL_FALLBACK_COLOR, STRATEGY_COLORS } from '../theme';

const API = '/api/ideas';

const CHANNEL_NAMES = {
  'impacto-mundial': 'Impacto Mundial',
  'mentes-rotas': 'Mentes Rotas',
  'el-loco-de-la-ia': 'El Loco de la IA',
  'mind-warp': 'Mind Warp',
  'wealth-files': 'Wealth Files',
  'dark-science': 'Dark Science',
};

const CHANNEL_FLAGS = {
  'impacto-mundial': '🇪🇸',
  'mentes-rotas': '🇪🇸',
  'el-loco-de-la-ia': '🇪🇸',
  'mind-warp': '🇬🇧',
  'wealth-files': '🇬🇧',
  'dark-science': '🇬🇧',
};

const STRATEGY_INFO = {
  trending_hooks:    { icon: '🔥', name: 'Trending Hooks',       color: STRATEGY_COLORS.trending_hooks },
  evergreen_magnets: { icon: '🧲', name: 'Evergreen Magnets',    color: STRATEGY_COLORS.evergreen_magnets },
  controversy_sparks:{ icon: '⚡', name: 'Controversy Sparks',   color: STRATEGY_COLORS.controversy_sparks },
  curiosity_gaps:    { icon: '🧠', name: 'Curiosity Gaps',       color: STRATEGY_COLORS.curiosity_gaps },
  fear_fomo:         { icon: '😱', name: 'Fear & FOMO',          color: STRATEGY_COLORS.fear_fomo },
  story_driven:      { icon: '📖', name: 'Story-Driven',         color: STRATEGY_COLORS.story_driven },
};

export default function Ideas() {
  const [ideas, setIdeas] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedChannel, setSelectedChannel] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState('');
  const [unusedOnly, setUnusedOnly] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [genChannel, setGenChannel] = useState('impacto-mundial');
  const [genCount, setGenCount] = useState(5);
  const [toast, setToast] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch ideas
  const loadIdeas = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedChannel) params.set('channel', selectedChannel);
      if (selectedStrategy) params.set('strategy', selectedStrategy);
      if (unusedOnly) params.set('unused_only', 'true');
      params.set('limit', '100');
      const res = await fetch(`${API}/list?${params}`);
      const data = await res.json();
      setIdeas(data.ideas || []);
    } catch { setIdeas([]); }
    setLoading(false);
  };

  const loadStats = async () => {
    try {
      const res = await fetch(`${API}/stats`);
      setStats(await res.json());
    } catch { setStats(null); }
  };

  useEffect(() => { loadIdeas(); loadStats(); }, [selectedChannel, selectedStrategy, unusedOnly]);

  // Generate ideas
  const handleGenerate = async () => {
    setGenerating(true);
    setToast(null);
    try {
      const res = await fetch(`${API}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel_id: genChannel,
          ideas_per_strategy: genCount,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Error');
      setToast({ type: 'info', msg: `Generando ideas para ${CHANNEL_NAMES[genChannel]}... tarda ~1 minuto` });

      // Poll until done
      const poll = setInterval(async () => {
        try {
          const sr = await fetch(`${API}/status`);
          const st = await sr.json();
          if (!st.running) {
            clearInterval(poll);
            setGenerating(false);
            const lr = st.last_result;
            if (lr && !lr.error) {
              setToast({ type: 'success', msg: `${lr.total_generated} ideas generadas, ${lr.new_saved} nuevas guardadas` });
            } else {
              setToast({ type: 'error', msg: lr?.error || 'Error desconocido' });
            }
            loadIdeas();
            loadStats();
          }
        } catch { /* skip */ }
      }, 3000);
    } catch (err) {
      setGenerating(false);
      setToast({ type: 'error', msg: err.message });
    }
  };

  // Generate all
  const handleGenerateAll = async () => {
    setGenerating(true);
    setToast({ type: 'info', msg: 'Generando ideas para los 6 canales... tarda 3-5 minutos' });
    try {
      await fetch(`${API}/generate-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ideas_per_strategy: genCount }),
      });
      const poll = setInterval(async () => {
        try {
          const sr = await fetch(`${API}/status`);
          const st = await sr.json();
          if (!st.running) {
            clearInterval(poll);
            setGenerating(false);
            setToast({ type: 'success', msg: 'Ideas generadas para todos los canales' });
            loadIdeas();
            loadStats();
          }
        } catch { /* skip */ }
      }, 5000);
    } catch (err) {
      setGenerating(false);
      setToast({ type: 'error', msg: err.message });
    }
  };

  // Mark idea as used
  const handleUse = async (id) => {
    await fetch(`${API}/${id}/use`, { method: 'POST' });
    loadIdeas();
    loadStats();
  };

  // Delete idea
  const handleDelete = async (id) => {
    await fetch(`${API}/${id}`, { method: 'DELETE' });
    setIdeas(prev => prev.filter(i => i.id !== id));
    loadStats();
  };

  return (
    <div className="animate-fade-in">
      {/* Toast */}
      {toast && (
        <div className="toast-container">
          <div className={`toast toast-${toast.type}`} style={{ boxShadow: '0 0 20px var(--accent-glow)' }}>
            {toast.type === 'success' ? '✅' : toast.type === 'error' ? '❌' : '⏳'} {toast.msg}
          </div>
        </div>
      )}

      <div className="section-header mb-24">
        <div>
          <h3 className="section-title text-accent" style={{ textShadow: '0 0 10px var(--accent-glow-strong)' }}>
            💡 Motor de Ideas Virales
          </h3>
          <p className="section-subtitle">
            Genera ideas reales y virales por nicho con IA — 6 estrategias de viralidad
          </p>
        </div>
      </div>

      {/* Stats Strip */}
      {stats && (
        <div className="grid-4 mb-24">
          <div className="stat-card card-glass" style={{ borderLeft: '2px solid var(--accent)' }}>
            <div className="stat-label">Total Ideas</div>
            <div className="stat-value text-accent" style={{ textShadow: '0 0 12px var(--accent-glow)' }}>{stats.total}</div>
          </div>
          <div className="stat-card card-glass" style={{ borderLeft: '2px solid var(--success)' }}>
            <div className="stat-label">Disponibles</div>
            <div className="stat-value text-success" style={{ textShadow: '0 0 12px var(--success-dim)' }}>{stats.unused}</div>
          </div>
          <div className="stat-card card-glass" style={{ borderLeft: '2px solid var(--warning)' }}>
            <div className="stat-label">Canales con Ideas</div>
            <div className="stat-value text-warning" style={{ textShadow: '0 0 12px var(--warning-dim)' }}>{stats.by_channel?.length || 0}</div>
          </div>
          <div className="stat-card card-glass" style={{ borderLeft: '2px solid var(--info)' }}>
            <div className="stat-label">Estrategias Usadas</div>
            <div className="stat-value" style={{ color: 'var(--info)', textShadow: '0 0 12px var(--info-dim)' }}>
              {stats.by_strategy?.length || 0}
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 24 }}>
        {/* Left Panel — Generator + Filters */}
        <div className="flex flex-col gap-16">
          {/* Generator Card */}
          <div className="card-glass" style={{ borderTop: '4px solid var(--accent)', boxShadow: '0 10px 30px var(--accent-glow)' }}>
            <h4 className="fw-700 mb-16 text-accent" style={{ textShadow: '0 0 8px var(--accent-glow)' }}>⚡ Generar Ideas</h4>

            <div className="mb-16">
              <label className="fs-12 text-muted" style={{ display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>
                Canal
              </label>
              <select className="input" value={genChannel} onChange={e => setGenChannel(e.target.value)}>
                {Object.entries(CHANNEL_NAMES).map(([id, name]) => (
                  <option key={id} value={id}>{CHANNEL_FLAGS[id]} {name}</option>
                ))}
              </select>
            </div>

            <div className="mb-16">
              <label className="fs-12 text-muted" style={{ display: 'block', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>
                Ideas por estrategia
              </label>
              <select className="input" value={genCount} onChange={e => setGenCount(+e.target.value)}>
                <option value={3}>3 ideas (rápido)</option>
                <option value={5}>5 ideas (normal)</option>
                <option value={8}>8 ideas (completo)</option>
                <option value={10}>10 ideas (máximo)</option>
              </select>
            </div>

            <button
              className={`btn ${generating ? 'btn-secondary' : 'btn-primary'}`}
              style={{ width: '100%', justifyContent: 'center', marginBottom: 8, boxShadow: generating ? 'none' : '0 0 15px var(--accent-glow-strong)' }}
              onClick={handleGenerate}
              disabled={generating}
            >
              {generating ? <><span className="animate-pulse">⏳</span> Generando...</> : <>⚡ Generar para 1 Canal</>}
            </button>

            <button
              className="btn btn-secondary"
              style={{ width: '100%', justifyContent: 'center', border: '1px solid var(--accent)', color: 'var(--accent)' }}
              onClick={handleGenerateAll}
              disabled={generating}
            >
              🌐 Generar para los 6 Canales
            </button>
          </div>

          {/* Filters */}
          <div className="card-glass" style={{ border: '1px solid var(--border)' }}>
            <h4 className="fw-700 mb-16">🔍 Filtros</h4>

            <div className="mb-12">
              <label className="fs-12 text-muted" style={{ display: 'block', marginBottom: 6 }}>Canal</label>
              <select className="input" value={selectedChannel} onChange={e => setSelectedChannel(e.target.value)}>
                <option value="">Todos los canales</option>
                {Object.entries(CHANNEL_NAMES).map(([id, name]) => (
                  <option key={id} value={id}>{name}</option>
                ))}
              </select>
            </div>

            <div className="mb-12">
              <label className="fs-12 text-muted" style={{ display: 'block', marginBottom: 6 }}>Estrategia</label>
              <select className="input" value={selectedStrategy} onChange={e => setSelectedStrategy(e.target.value)}>
                <option value="">Todas</option>
                {Object.entries(STRATEGY_INFO).map(([key, s]) => (
                  <option key={key} value={key}>{s.icon} {s.name}</option>
                ))}
              </select>
            </div>

            <label className="flex items-center gap-8" style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={unusedOnly}
                onChange={e => setUnusedOnly(e.target.checked)}
                style={{ width: 16, height: 16, accentColor: 'var(--accent)' }}
              />
              <span className="fs-14">Solo ideas sin usar</span>
            </label>
          </div>

          {/* Strategies Legend */}
          <div className="card-glass">
            <h4 className="fw-700 mb-12" style={{ color: 'var(--text-secondary)' }}>📊 Estrategias</h4>
            {Object.entries(STRATEGY_INFO).map(([key, s]) => (
              <div key={key} className="flex items-center gap-8 mb-8" style={{ fontSize: 12 }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: s.color, flexShrink: 0,
                  boxShadow: `0 0 8px ${s.color}`
                }}></span>
                <span>{s.icon} {s.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right Panel — Ideas List */}
        <div>
          {loading ? (
            <div className="flex flex-col gap-12">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="card-glass">
                  <div className="skeleton" style={{ width: '70%', height: 20, marginBottom: 8 }}></div>
                  <div className="skeleton" style={{ width: '100%', height: 14, marginBottom: 6 }}></div>
                  <div className="skeleton" style={{ width: '60%', height: 12 }}></div>
                </div>
              ))}
            </div>
          ) : ideas.length === 0 ? (
            <div className="card-glass" style={{ border: '1px dashed var(--accent)' }}>
              <div className="empty-state">
                <div className="empty-state-icon" style={{ textShadow: '0 0 15px var(--accent)' }}>💡</div>
                <div className="empty-state-title text-primary">Sin ideas todavía</div>
                <p className="text-muted fs-14">
                  Usa el generador para crear ideas virales con IA para tus canales.
                </p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-12">
              <div className="text-accent fs-12 fw-700" style={{ textTransform: 'uppercase', letterSpacing: 1, textShadow: '0 0 5px var(--accent-glow)' }}>
                {ideas.length} ideas · Ordenadas por viralidad
              </div>
              {ideas.map((idea, idx) => (
                <IdeaCard
                  key={idea.id}
                  idea={idea}
                  idx={idx}
                  onUse={() => handleUse(idea.id)}
                  onDelete={() => handleDelete(idea.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function IdeaCard({ idea, idx, onUse, onDelete }) {
  const strat = STRATEGY_INFO[idea.strategy] || { icon: '💡', name: idea.strategy, color: 'var(--text-muted)' };
  const chColor = CHANNEL_COLORS[idea.channel_id] || CHANNEL_FALLBACK_COLOR;
  const score = Math.round(idea.virality_score || 0);
  const isUsed = idea.used === 1;

  // Compute neon glow colors based on score
  const scoreColor = score >= 80 ? 'var(--success)' : score >= 60 ? 'var(--warning)' : 'var(--accent)';
  const glow = score >= 80 ? '0 0 15px rgba(0, 229, 255, 0.4)' 
             : score >= 60 ? '0 0 10px rgba(251, 191, 36, 0.3)' 
             : '0 0 0 transparent';

  return (
    <div
      className="card-glass animate-fade-in"
      style={{
        animationDelay: `${idx * 40}ms`,
        opacity: isUsed ? 0.3 : 1, // Make used items much dimmer
        borderLeft: `4px solid ${strat.color}`,
        borderTop: isUsed ? 'none' : `1px solid ${strat.color}`,
        boxShadow: isUsed ? 'none' : `inset 2px 0 20px -10px ${strat.color}, ${glow}`,
      }}
    >
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-8">
          {/* Channel dot */}
          <span style={{
            width: 10, height: 10, borderRadius: '50%',
            background: chColor, flexShrink: 0,
            boxShadow: `0 0 10px ${chColor}`
          }}></span>
          <span className="fs-12 text-primary fw-600">
            {CHANNEL_NAMES[idea.channel_id] || idea.channel_id}
          </span>
          <span className="badge badge-neutral" style={{ fontSize: 10, border: `1px solid ${strat.color}` }}>
            {strat.icon} {strat.name}
          </span>
        </div>
        {/* Score */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '4px 12px', borderRadius: 20,
          background: 'rgba(0,0,0,0.4)',
          border: `1px solid ${scoreColor}`,
          color: scoreColor,
          textShadow: `0 0 5px ${scoreColor}`,
          fontSize: 13, fontWeight: 700,
          fontFamily: "'JetBrains Mono', monospace",
        }}>
          {score >= 80 ? '🔥' : score >= 60 ? '⭐' : '💡'} {score}
        </div>
      </div>

      {/* Title */}
      <h4 style={{ fontSize: 16, fontWeight: 800, lineHeight: 1.4, marginBottom: 8, color: 'var(--text-primary)' }}>
        {idea.title}
      </h4>

      {/* Hook */}
      {idea.hook && (
        <div style={{
          fontSize: 13, color: 'var(--text-secondary)',
          fontStyle: 'italic', marginBottom: 8,
          padding: '8px 12px', background: 'rgba(0,0,0,0.3)',
          borderRadius: 8, borderLeft: `3px solid ${strat.color}`,
        }}>
          🎣 "{idea.hook}"
        </div>
      )}

      {/* Details grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 16px', marginBottom: 12 }}>
        {idea.angle && (
          <div style={{ fontSize: 12 }}>
            <span className="text-muted">Ángulo: </span>
            <span className="text-secondary">{idea.angle}</span>
          </div>
        )}
        {idea.why_viral && (
          <div style={{ fontSize: 12 }}>
            <span className="text-muted">Viral porque: </span>
            <span style={{ color: 'var(--accent)' }}>{idea.why_viral}</span>
          </div>
        )}
        {idea.search_potential && (
          <div style={{ fontSize: 12 }}>
            <span className="text-muted">Búsqueda: </span>
            <span className={`badge ${
              idea.search_potential === 'alto' || idea.search_potential === 'high' ? 'badge-success'
              : idea.search_potential === 'medio' || idea.search_potential === 'medium' ? 'badge-warning'
              : 'badge-neutral'
            }`} style={{ fontSize: 10, background: 'transparent', border: '1px solid currentColor' }}>
              {idea.search_potential}
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-8">
        {!isUsed && (
          <button className="btn btn-primary btn-sm" style={{ boxShadow: '0 0 10px var(--accent-glow)' }} onClick={onUse}>
            ✅ Usar para video
          </button>
        )}
        {isUsed && (
          <span className="badge badge-success" style={{ background: 'transparent', border: '1px solid var(--success)' }}>
            <span className="badge-dot"></span>
            En Producción / Usada
          </span>
        )}
        <button className="btn btn-danger btn-sm" style={{ background: 'transparent' }} onClick={onDelete}>
          🗑️ Descartar
        </button>
      </div>
    </div>
  );
}
