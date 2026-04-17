import { useState, useEffect } from 'react';
import { fetchScheduledJobs, cancelScheduledJob } from '../api';

const STATUS_COLORS = {
  pending: 'var(--warning)',
  processing: 'var(--accent)',
  completed: 'var(--success)',
  error: 'var(--error)',
};

export default function Scheduler() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const loadData = () => {
    setLoading(true);
    fetchScheduledJobs(filter)
      .then(data => setJobs(data.schedules || []))
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [filter]);

  const handleCancel = async (jobId) => {
    if (!window.confirm('¿Seguro que deseas cancelar esta publicación programada?')) return;
    try {
      await cancelScheduledJob(jobId);
      loadData();
    } catch (e) {
      alert('Error cancelando: ' + e.message);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="section-header mb-24">
        <div>
          <h3 className="section-title text-accent" style={{ textShadow: '0 0 10px var(--accent-glow-strong)' }}>
            Línea de Tiempo de Publicación
          </h3>
          <p className="section-subtitle">Gestiona los videos programados para subirse a YouTube automáticamente.</p>
        </div>
      </div>

      <div className="flex gap-12 mb-24">
        <button 
          className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setFilter('all')}
        >Todos</button>
        <button 
          className={`btn btn-sm ${filter === 'pending' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setFilter('pending')}
        >Pendientes</button>
        <button 
          className={`btn btn-sm ${filter === 'completed' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setFilter('completed')}
        >Completados</button>
      </div>

      <div className="card-glass" style={{ minHeight: '60vh' }}>
        {loading ? (
          <div className="skeleton" style={{ width: '100%', height: '200px' }}></div>
        ) : jobs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon" style={{ textShadow: '0 0 15px var(--accent)' }}>📅</div>
            <div className="empty-state-title text-primary">El calendario está vacío</div>
            <p className="text-muted fs-14">Puedes programar videos desde la Biblioteca para que se suban en piloto automático.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {jobs.map((job, i) => {
              const d = new Date(job.scheduled_at);
              const color = STATUS_COLORS[job.status] || 'var(--text-muted)';
              return (
                <div key={job.schedule_id} className="card-glass flex items-center justify-between" style={{ padding: '16px 24px', borderLeft: `3px solid ${color}`, animationDelay: `${i*50}ms` }}>
                  <div className="flex items-center gap-24">
                    <div style={{ textAlign: 'center', minWidth: 100 }}>
                      <div className="fw-600 fs-18" style={{ color: 'var(--text-primary)' }}>{d.toLocaleDateString()}</div>
                      <div className="fs-14" style={{ color: 'var(--accent)' }}>{d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                    </div>
                    <div>
                      <div className="fw-500 fs-16" style={{ color: 'var(--text-primary)' }}>{job.title || 'Video #'+job.video_id}</div>
                      <div className="flex items-center gap-12 mt-4">
                        <span className="fs-12 text-secondary">{job.channel_name}</span>
                        <span className="badge" style={{ backgroundColor: 'transparent', border: `1px solid ${color}`, color: color }}>
                          {job.status.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div>
                    {job.status === 'pending' && (
                      <button className="btn btn-secondary btn-sm" onClick={() => handleCancel(job.schedule_id)}>
                        Cancelar
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
