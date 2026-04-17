import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { path: '/', icon: '📊', label: 'Dashboard' },
  { path: '/channels', icon: '📺', label: 'Channels' },
  { path: '/queue', icon: '🧠', label: 'Queue' },
  { path: '/calendar', icon: '📅', label: 'Calendar' },
  { path: '/analytics', icon: '📈', label: 'Analytics' },
  { path: '/quality', icon: '✨', label: 'Quality' },
  { path: '/agents', icon: '🕹️', label: 'Agents Live' },
  { path: '/income', icon: '💸', label: 'Income' },
  { path: '/settings', icon: '⚙️', label: 'Settings' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>YT Automation Pro</h1>
        <p>Dashboard Upgrade · Phase 5</p>
      </div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            end={item.path === '/'}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>System status</div>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>6 channels · 30d analytics</div>
      </div>
    </aside>
  );
}
