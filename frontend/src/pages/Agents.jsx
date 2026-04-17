import { useEffect, useMemo, useState } from 'react';
import { fetchAgentsTeamStatus } from '../api';

const AVATARS = ['🧑‍💻', '👩‍🔬', '🕵️', '🎙️', '🎬', '🧠', '🖼️', '🛡️', '⚙️', '📈'];
const DESKS = [
  { x: 6, y: 8 }, { x: 26, y: 8 }, { x: 46, y: 8 }, { x: 66, y: 8 }, { x: 86, y: 8 },
  { x: 6, y: 58 }, { x: 26, y: 58 }, { x: 46, y: 58 }, { x: 66, y: 58 }, { x: 86, y: 58 },
];

function prettyName(fileName) {
  return fileName
    .replace('.agent.md', '')
    .replace(/^\d+-/, '')
    .split('-')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

function getActivity(agent, running) {
  const status = (agent.status || '').toLowerCase();
  const action = (agent.action || '').toLowerCase();
  if (status === 'error') return { key: 'error', label: 'Error', bubble: `❌ ${agent.last_error || 'fallo'}` };
  if (status === 'done') return { key: 'reviewing', label: 'Completado', bubble: `✅ ${agent.last_result || agent.action || 'ok'}` };
  if (status === 'running') {
    if (action.includes('handoff')) return { key: 'walking', label: 'Handoff', bubble: `➡️ ${agent.action}` };
    if (action.includes('scan') || action.includes('inspect') || action.includes('check')) return { key: 'reading', label: 'Analizando', bubble: `📚 ${agent.action}` };
    if (action.includes('validate') || action.includes('quality')) return { key: 'reviewing', label: 'Validando', bubble: `✅ ${agent.action}` };
    return { key: 'typing', label: 'Trabajando', bubble: `⌨️ ${agent.action || 'ejecutando tarea'}` };
  }
  if (!running) return { key: 'idle', label: 'Parado', bubble: '⏸️ ciclo detenido' };
  return { key: 'idle', label: 'En espera', bubble: agent.last_result ? `🕒 ${agent.last_result}` : '🕒 esperando turno' };
}

export default function Agents() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      setError('');
      const res = await fetchAgentsTeamStatus();
      setData(res);
    } catch (e) {
      setError(e.message || 'Error loading agents status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const poll = setInterval(load, 5000);
    return () => {
      clearInterval(poll);
    };
  }, []);

  const agents = useMemo(() => {
    const fromApi = data?.agents || [];
    const ordered = fromApi.length
      ? fromApi
      : (data?.execution_order || []).map((f) => ({ agent_file: f, status: 'ready' }));

    return ordered.slice(0, 10).map((a, idx) => ({
      ...a,
      name: prettyName(a.agent_file),
      avatar: AVATARS[idx % AVATARS.length],
      desk: DESKS[idx % DESKS.length],
      activity: getActivity(a, Boolean(data?.running)),
    }));
  }, [data]);

  if (loading) return <div className="card-glass">Cargando oficina de agentes...</div>;
  if (error) return <div className="card-glass">Error: {error}</div>;

  return (
    <div className="animate-fade-in">
      <div className="section-header mb-24">
        <div>
          <h3 className="section-title text-accent">Agents Office Live</h3>
          <p className="section-subtitle">Telemetría real por agente: acción, estado, duración y resultado</p>
        </div>
        <div className="flex gap-8">
          <span className={`badge ${data?.runner_alive ? 'badge-success' : 'badge-error'}`}>
            {data?.runner_alive ? 'Runner online' : 'Runner offline'}
          </span>
          <span className={`badge ${data?.running ? 'badge-warning' : 'badge-neutral'}`}>
            {data?.running ? 'Ciclo ejecutándose' : 'Ciclo en espera'}
          </span>
        </div>
      </div>

      <div className="agent-office card-glass">
        <div className="office-grid">
          {agents.map((agent, idx) => (
            <div
              key={agent.agent_file}
              className={`office-agent ${agent.activity.key}`}
              style={{ left: `${agent.desk.x}%`, top: `${agent.desk.y}%` }}
              title={`${agent.name} · ${agent.activity.label} · ${agent.action || 'sin acción'}`}
            >
              <div className="desk" />
              <div className="agent-avatar">{agent.avatar}</div>
              <div className="agent-bubble">{agent.activity.bubble}</div>
              <div className="agent-tag">{idx + 1}. {agent.name}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid-2 mt-16">
        <div className="card-glass">
          <div className="fw-600 mb-8">Estado del sistema</div>
          <div className="fs-12 text-muted">PID: {data?.master_pid ?? '—'}</div>
          <div className="fs-12 text-muted">Agente actual: {data?.current_agent || '—'}</div>
          <div className="fs-12 text-muted">Inicio último ciclo: {data?.last_cycle_started || '—'}</div>
          <div className="fs-12 text-muted">Fin último ciclo: {data?.last_cycle_finished || '—'}</div>
        </div>
        <div className="card-glass">
          <div className="fw-600 mb-8">Handoffs</div>
          {(data?.handoff_rules || []).map((h) => (
            <div key={h} className="mono fs-12 text-secondary">{h}</div>
          ))}
        </div>
      </div>

      <div className="table-container card-glass mt-16">
        <table>
          <thead>
            <tr>
              <th>Agente</th>
              <th>Estado</th>
              <th>Acción real</th>
              <th>Resultado</th>
              <th>Duración</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((a) => (
              <tr key={`${a.agent_file}-row`}>
                <td className="mono fs-12">{a.name}</td>
                <td>
                  <span className={`badge ${
                    a.status === 'running' ? 'badge-warning' :
                    a.status === 'done' ? 'badge-success' :
                    a.status === 'error' ? 'badge-error' : 'badge-neutral'
                  }`}>
                    {a.status || 'idle'}
                  </span>
                </td>
                <td className="fs-12">{a.action || '—'}</td>
                <td className="fs-12">{a.last_error || a.last_result || '—'}</td>
                <td className="mono fs-12">{typeof a.duration_ms === 'number' ? `${a.duration_ms} ms` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
