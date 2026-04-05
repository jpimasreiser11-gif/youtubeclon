
import React, { useState } from 'react';
import { UserProfile } from '../types';

interface OnboardingScreenProps {
  onComplete: (profile: UserProfile) => void;
}

const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ onComplete }) => {
  const [profile, setProfile] = useState<UserProfile>({
    name: '',
    hobbies: '',
    goals: '',
    onboarded: true
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (profile.name.trim()) {
      onComplete(profile);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background-dark p-6 overflow-y-auto">
      <div className="absolute inset-0 opacity-20 pointer-events-none journey-map-bg"></div>
      
      <div className="max-w-md w-full bg-[#1c2632] border border-slate-800 rounded-3xl p-8 shadow-2xl relative animate-in fade-in zoom-in duration-500">
        <div className="flex flex-col items-center gap-4 text-center mb-8">
          <div className="w-20 h-20 rounded-2xl bg-primary/20 flex items-center justify-center border border-primary/30 mb-2">
            <span className="material-symbols-outlined text-primary text-5xl">psychology</span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">Welcome to EduMind</h1>
          <p className="text-slate-400 text-sm">Let's personalize your learning journey. Tell us a bit about yourself.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-[10px] font-bold text-primary uppercase tracking-widest px-1">How should I call you?</label>
            <input 
              required
              type="text" 
              placeholder="e.g. Alex"
              className="w-full bg-slate-900 border-slate-800 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              value={profile.name}
              onChange={e => setProfile({...profile, name: e.target.value})}
            />
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-bold text-primary uppercase tracking-widest px-1">Your hobbies or interests</label>
            <textarea 
              placeholder="e.g. Playing guitar, basketball, space exploration..."
              rows={2}
              className="w-full bg-slate-900 border-slate-800 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all resize-none"
              value={profile.hobbies}
              onChange={e => setProfile({...profile, hobbies: e.target.value})}
            />
            <p className="text-[10px] text-slate-500 italic px-1">I'll use these to create analogies you'll understand better!</p>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-bold text-primary uppercase tracking-widest px-1">What do you want to learn?</label>
            <input 
              type="text" 
              placeholder="e.g. Quantum physics, world history..."
              className="w-full bg-slate-900 border-slate-800 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              value={profile.goals}
              onChange={e => setProfile({...profile, goals: e.target.value})}
            />
          </div>

          <button 
            type="submit"
            className="w-full bg-primary hover:bg-blue-600 text-white font-bold py-4 rounded-xl shadow-lg shadow-primary/20 transition-all transform hover:scale-[1.02] active:scale-95 flex items-center justify-center gap-2"
          >
            Start My Journey
            <span className="material-symbols-outlined">arrow_forward</span>
          </button>
        </form>
      </div>
    </div>
  );
};

export default OnboardingScreen;
