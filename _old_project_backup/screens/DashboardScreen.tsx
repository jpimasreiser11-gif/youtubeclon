
import React from 'react';
import { Link } from 'react-router-dom';
import { UserProfile } from '../types';

interface DashboardProps {
  profile: UserProfile | null;
}

const DashboardScreen: React.FC<DashboardProps> = ({ profile }) => {
  const adventures = [
    { title: "Quantum Mechanics Basics", cat: "Physics", time: "15m", img: "https://picsum.photos/seed/physics/400/300", desc: "A low-pressure introduction to the weird and wonderful world of particles." },
    { title: "Renaissance Poetry", cat: "Literature", time: "20m", img: "https://picsum.photos/seed/literature/400/300", desc: "Explore the rhythm and emotion of the 16th-century masters." },
    { title: "Probability Sparks", cat: "Math", time: "10m", img: "https://picsum.photos/seed/math/400/300", desc: "Quick puzzles to sharpen your logic for upcoming Algebra quests." }
  ];

  return (
    <div className="flex-1 flex flex-col items-center py-8 px-6 overflow-y-auto">
      <div className="max-w-[1000px] w-full flex flex-col gap-6">
        <div className="flex flex-wrap justify-between items-end gap-3 px-4 text-left">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-3 mb-1">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center border border-primary/30">
                <span className="material-symbols-outlined text-primary text-3xl">smart_toy</span>
              </div>
              <span className="bg-primary/20 text-primary text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">Personalized</span>
            </div>
            <h2 className="text-slate-900 dark:text-white text-4xl font-black leading-tight tracking-[-0.033em]">
              Good morning, {profile?.name || 'Explorer'}.
            </h2>
            <p className="text-slate-500 dark:text-[#9dabb9] text-base font-normal leading-normal">
              EduMind has prepared topics about {profile?.goals || 'your goals'} using your interest in {profile?.hobbies || 'learning'}.
            </p>
          </div>
          <button className="flex min-w-[84px] cursor-pointer items-center justify-center rounded-lg h-10 px-4 bg-slate-200 dark:bg-[#283039] text-slate-900 dark:text-white text-sm font-bold transition-all hover:bg-primary/20">
            <span className="material-symbols-outlined mr-2 text-lg">map</span>
            <span className="truncate">Full Journey Map</span>
          </button>
        </div>

        {/* The rest of the dashboard remains the same visually, but feels more personal */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 px-4">
          <div className="lg:col-span-2 group">
            <div className="relative overflow-hidden bg-slate-900 rounded-xl h-full min-h-[240px] shadow-lg flex flex-col justify-end p-6 border border-slate-800">
              <div 
                className="absolute inset-0 opacity-40 group-hover:opacity-50 transition-opacity" 
                style={{backgroundImage: 'linear-gradient(to top, #101922 0%, transparent 100%), url("https://picsum.photos/seed/learning/800/600")', backgroundSize: 'cover', backgroundPosition: 'center'}}
              ></div>
              <div className="relative z-10 flex flex-col gap-2 text-left">
                <div className="flex items-center gap-2">
                  <span className="bg-primary text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-widest">Tailored Spark</span>
                  <span className="material-symbols-outlined text-yellow-400 text-sm">auto_awesome</span>
                </div>
                <h3 className="text-white text-2xl font-bold leading-tight">Focusing on your goals!</h3>
                <p className="text-slate-300 text-sm font-medium max-w-md">Yesterday you explored {profile?.goals || 'new concepts'}. Your tutor has refined today's sessions based on your feedback.</p>
                <div className="mt-4 flex gap-3">
                  <button className="bg-primary hover:bg-blue-600 text-white text-xs font-bold py-2 px-4 rounded-lg transition-colors">Resume Lesson</button>
                </div>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-[#1c2632] p-6 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col justify-between text-left">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-slate-900 dark:text-white font-bold">Your Progress</h3>
                <span className="material-symbols-outlined text-primary">analytics</span>
              </div>
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center">
                  <p className="text-slate-500 dark:text-[#9dabb9] text-xs">Milestones</p>
                  <p className="text-slate-900 dark:text-white text-xs font-bold">4 / 10</p>
                </div>
                <div className="h-2 rounded-full bg-slate-100 dark:bg-[#3b4754] overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{width: '40%'}}></div>
                </div>
              </div>
            </div>
            <div className="pt-6 border-t border-slate-100 dark:border-slate-800 flex flex-col gap-1">
              <p className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">Interest Anchor</p>
              <p className="text-slate-900 dark:text-white text-sm font-medium truncate">{profile?.hobbies}</p>
            </div>
          </div>
        </div>

        <div className="px-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-slate-900 dark:text-white text-[22px] font-bold leading-tight tracking-[-0.015em]">Recommended Adventures</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {adventures.map((adv, idx) => (
              <div key={idx} className="bg-white dark:bg-[#1c2632] border border-slate-200 dark:border-slate-800 rounded-xl p-4 hover:border-primary/50 transition-all cursor-pointer group text-left">
                <div className="w-full h-32 rounded-lg mb-4 overflow-hidden relative">
                  <img className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" src={adv.img} alt={adv.title}/>
                  <div className="absolute top-2 right-2 bg-black/50 backdrop-blur-md px-2 py-1 rounded text-[10px] text-white">
                    {adv.time}
                  </div>
                </div>
                <h4 className="text-slate-900 dark:text-white font-bold mb-1">{adv.title}</h4>
                <p className="text-slate-500 dark:text-[#9dabb9] text-xs mb-4 line-clamp-2">{adv.desc}</p>
                <span className="text-[10px] text-primary bg-primary/10 px-2 py-0.5 rounded font-bold uppercase">{adv.cat}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardScreen;
