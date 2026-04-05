
import React, { useState, useEffect } from 'react';
import { HashRouter, Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar'; // Keep this if used indirectly, but Layout handles it. Wait, Layout imports Sidebar. 
// Actually, I should remove Sidebar import from App.tsx since it's now internal to Layout.
import Layout from './components/Layout';
import { ToastProvider } from './components/ToastProvider';
import DashboardScreen from './screens/DashboardScreen';
import ChatScreen from './screens/ChatScreen';
import CreatorScreen from './screens/CreatorScreen';
import VisionScreen from './screens/VisionScreen';
import OnboardingScreen from './screens/OnboardingScreen';
import { UserProfile } from './types';

import SettingsScreen from './screens/SettingsScreen';

const App: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedProfile = localStorage.getItem('edumind_profile');
    if (savedProfile) {
      setProfile(JSON.parse(savedProfile));
    }
    setLoading(false);
  }, []);

  const handleOnboardingComplete = (newProfile: UserProfile) => {
    localStorage.setItem('edumind_profile', JSON.stringify(newProfile));
    setProfile(newProfile);
  };

  if (loading) return null;

  return (
    <ToastProvider>
      <HashRouter>
        {!profile?.onboarded ? (
          <OnboardingScreen onComplete={handleOnboardingComplete} />
        ) : (
          <Layout profile={profile}>
            <Routes>
              <Route path="/" element={<DashboardScreen profile={profile} />} />
              <Route path="/chat" element={<ChatScreen profile={profile} />} />
              <Route path="/creator" element={<CreatorScreen profile={profile} />} />
              <Route path="/vision" element={<VisionScreen profile={profile} />} />
              <Route path="/settings" element={<SettingsScreen />} />
            </Routes>
          </Layout>
        )}
      </HashRouter>
    </ToastProvider>
  );
};

export default App;
