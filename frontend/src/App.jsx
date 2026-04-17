import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Channels from './pages/Channels';
import Queue from './pages/Queue';
import Calendar from './pages/Calendar';
import Analytics from './pages/Analytics';
import Quality from './pages/Quality';
import Settings from './pages/Settings';
import Agents from './pages/Agents';
import Income from './pages/Income';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/channels" element={<Channels />} />
            <Route path="/queue" element={<Queue />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/quality" element={<Quality />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/income" element={<Income />} />
            <Route path="/settings" element={<Settings />} />

            {/* legacy route compatibility */}
            <Route path="/generator" element={<Navigate to="/queue" replace />} />
            <Route path="/ideas" element={<Navigate to="/analytics" replace />} />
            <Route path="/library" element={<Navigate to="/queue" replace />} />
            <Route path="/scheduler" element={<Navigate to="/calendar" replace />} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
