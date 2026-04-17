import { useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Cell, Legend } from 'recharts';
import { fetchApiUsage, fetchChannels, fetchDashboardStats } from '../api';
import { CHANNEL_COLORS, CHANNEL_FALLBACK_COLOR } from '../theme';
import { buildMockApiUsage, buildMockDashboardStats, MOCK_CHANNELS, MOCK_DAILY_METRICS } from '../mockData';

export default function Analytics() {
  const [stats, setStats] = useState(buildMockDashboardStats());
  const [channels, setChannels] = useState(MOCK_CHANNELS);
  const [apiUsage, setApiUsage] = useState(buildMockApiUsage());

  useEffect(() => {
    Promise.all([
      fetchDashboardStats().catch(() => buildMockDashboardStats()),
      fetchChannels().catch(() => MOCK_CHANNELS),
      fetchApiUsage().catch(() => buildMockApiUsage()),
    ]).then(([dashboard, chs, usage]) => {
      setStats(dashboard || buildMockDashboardStats(chs));
      setChannels(Array.isArray(chs) && chs.length ? chs : MOCK_CHANNELS);
      setApiUsage(Array.isArray(usage) && usage.length ? usage : buildMockApiUsage());
    });
  }, []);

  const channelPerformance = useMemo(() => {
    return (stats.channels?.length ? stats.channels : buildMockDashboardStats(channels).channels).map((ch) => ({
      name: ch.name,
      views: Number(ch.total_views || 0),
      revenue: Number(ch.total_revenue || 0),
      accent: CHANNEL_COLORS[ch.channel_id] || ch.accent || CHANNEL_FALLBACK_COLOR,
    }));
  }, [stats, channels]);

  const usagePie = useMemo(() => apiUsage.slice(0, 6).map((u) => ({ name: u.service, value: Number(u.total_requests || 0) })), [apiUsage]);

  return (
    <div className="animate-fade-in">
      <div className="section-header mb-24">
        <div>
          <h3 className="section-title" style={{ fontSize: 22 }}>Analytics</h3>
          <p className="section-subtitle">30-day trends and service usage with Recharts</p>
        </div>
      </div>

      <div className="grid-2 mb-24">
        <div className="card-glass">
          <h4 className="mb-12">Audience growth (30 days)</h4>
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={MOCK_DAILY_METRICS}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                <XAxis dataKey="day" stroke="#94A3B8" />
                <YAxis stroke="#94A3B8" />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                <Legend />
                <Line dataKey="views" name="Views" stroke="#38BDF8" strokeWidth={2} dot={false} />
                <Line dataKey="uploads" name="Uploads" stroke="#A855F7" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card-glass">
          <h4 className="mb-12">API request share</h4>
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={usagePie} dataKey="value" nameKey="name" outerRadius={95} innerRadius={52}>
                  {usagePie.map((entry, index) => (
                    <Cell key={entry.name} fill={["#A855F7", "#22D3EE", "#22C55E", "#F59E0B", "#EF4444", "#6366F1"][index % 6]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card-glass mb-24">
        <h4 className="mb-12">Channel performance mix</h4>
        <div style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={channelPerformance}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
              <XAxis dataKey="name" stroke="#94A3B8" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="left" stroke="#94A3B8" />
              <YAxis yAxisId="right" orientation="right" stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
              <Bar yAxisId="left" dataKey="views" name="Views" radius={[6, 6, 0, 0]}>
                {channelPerformance.map((entry) => (
                  <Cell key={entry.name} fill={entry.accent} />
                ))}
              </Bar>
              <Bar yAxisId="right" dataKey="revenue" name="Revenue" fill="#22C55E" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="table-container card-glass">
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
  );
}
