
import React, { useState } from 'react';
import { generateCourseOutline } from '../services/geminiService';
import { PersonalityStyle, UserProfile } from '../types';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';

interface CreatorScreenProps {
  profile: UserProfile | null;
}

const CreatorScreen: React.FC<CreatorScreenProps> = ({ profile }) => {
  const [courseTitle, setCourseTitle] = useState('New Learning Path');
  const [description, setDescription] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [outline, setOutline] = useState<any[]>([]);
  const [selectedPersonality, setSelectedPersonality] = useState('Mentor');

  const personalities: PersonalityStyle[] = [
    { id: 'Mentor', name: 'Mentor', icon: 'school', description: 'Patient and encouraging style.' },
    { id: 'Strict', name: 'Strict', icon: 'psychiatry', description: 'Focuses on precision and standards.' },
    { id: 'Socratic', name: 'Socratic', icon: 'rocket_launch', description: 'Teaches by asking questions.' },
    { id: 'Witty', name: 'Witty', icon: 'theater_comedy', description: 'Uses humor and memes.' }
  ];

  const handleGenerate = async () => {
    if (!description.trim()) return;
    setIsGenerating(true);
    try {
      const result = await generateCourseOutline(description, profile || undefined);
      setOutline(result);
    } catch (e) {
      console.error(e);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex-1 h-full overflow-y-auto bg-slate-50 dark:bg-slate-900/50 p-6 md:p-8 space-y-8 scroll-smooth">
      <header className="flex flex-col gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
        <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-wider">
          <span className="material-symbols-outlined text-sm">auto_stories</span>
          Course Draft
        </div>
        <input
          className="bg-transparent text-4xl md:text-5xl font-black text-slate-900 dark:text-white border-none focus:ring-0 p-0 placeholder:text-slate-300 dark:placeholder:text-slate-700"
          value={courseTitle}
          onChange={(e) => setCourseTitle(e.target.value)}
        />
        <p className="text-slate-500 text-lg max-w-2xl">
          Let's design a perfectly tailored learning path based on your interests in <span className="text-slate-900 dark:text-white font-semibold">{profile?.hobbies}</span>.
        </p>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 space-y-6">
          <h3 className="font-bold text-xl text-slate-900 dark:text-white">What do you want to learn?</h3>
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. Quantum Physics basics..."
                className="bg-slate-50 dark:bg-slate-900"
              />
            </div>
            <Button
              onClick={handleGenerate}
              disabled={!description.trim() || isGenerating}
              isLoading={isGenerating}
              className="gap-2"
            >
              <span className="material-symbols-outlined">auto_awesome</span>
              Generate
            </Button>
          </div>
        </Card>

        <div className="space-y-4">
          <h3 className="font-bold text-sm text-slate-500 uppercase tracking-widest px-1">AI Tutor Persona</h3>
          <div className="grid grid-cols-1 gap-3">
            {personalities.map((pers) => (
              <div
                key={pers.id}
                onClick={() => setSelectedPersonality(pers.id)}
                className={`
                   group flex items-center gap-4 p-3 rounded-xl cursor-pointer border transition-all duration-200
                   ${selectedPersonality === pers.id
                    ? 'bg-primary/5 border-primary shadow-sm'
                    : 'bg-white dark:bg-slate-800 border-transparent hover:border-slate-200 dark:hover:border-slate-700'
                  }
                 `}
              >
                <div className={`
                   size-10 rounded-lg flex items-center justify-center transition-colors
                   ${selectedPersonality === pers.id ? 'bg-primary text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-500 group-hover:text-slate-700'}
                 `}>
                  <span className="material-symbols-outlined">{pers.icon}</span>
                </div>
                <div>
                  <h4 className={`font-bold text-sm ${selectedPersonality === pers.id ? 'text-primary' : 'text-slate-900 dark:text-white'}`}>{pers.name}</h4>
                  <p className="text-[10px] text-slate-500">{pers.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {outline.length > 0 && (
        <section className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-2xl text-slate-900 dark:text-white">Your Syllabus</h3>
            <Button variant="outline" size="sm" onClick={() => setOutline([])}>Clear</Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {outline.map((item, i) => (
              <Card key={i} className="group relative overflow-hidden border-l-4 border-l-primary hover:border-l-primary">
                <div className="absolute top-4 right-4 text-xs font-bold text-slate-400 bg-slate-100 dark:bg-slate-700/50 px-2 py-1 rounded">
                  {item.time}
                </div>
                <div className="mb-2">
                  <span className="text-[10px] font-bold text-primary tracking-wider uppercase mb-1 block">{item.category}</span>
                  <h4 className="font-bold text-lg text-slate-900 dark:text-white group-hover:text-primary transition-colors">{item.title}</h4>
                </div>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{item.description}</p>

                <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700/50 flex justify-end">
                  <button className="text-xs font-bold text-primary hover:underline flex items-center gap-1">
                    Start Module <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </button>
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default CreatorScreen;
