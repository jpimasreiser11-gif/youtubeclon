
import React, { useState, useRef } from 'react';
import { analyzeImage } from '../services/geminiService';
import { UserProfile } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';

interface VisionScreenProps {
  profile: UserProfile | null;
}

const VisionScreen: React.FC<VisionScreenProps> = ({ profile }) => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImage(reader.result as string);
        setAnalysis(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const triggerAnalysis = async () => {
    if (!selectedImage) return;
    setIsAnalyzing(true);
    try {
      const base64 = selectedImage.split(',')[1];
      const result = await analyzeImage(
        base64,
        "Analyze this image and provide a helpful learning observation. Point out any interesting patterns.",
        profile || undefined
      );
      setAnalysis(result);
    } catch (e) {
      console.error(e);
      setAnalysis("Sorry, failed to analyze the image.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="flex h-full bg-slate-50 dark:bg-slate-900/50 overflow-hidden">
      <aside className="w-80 border-r border-slate-200 dark:border-slate-800 p-6 flex flex-col gap-6 bg-white dark:bg-slate-900/80 backdrop-blur-sm z-10 shadow-sm">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-1">Vision Tools</h2>
          <p className="text-xs text-slate-500">Analyze images with AI context.</p>
        </div>

        <Card className="flex flex-col gap-4 border-dashed border-2 bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 transition-colors">
          <div
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center justify-center py-8 cursor-pointer gap-2 text-slate-400 hover:text-primary transition-colors"
          >
            <span className="material-symbols-outlined text-4xl">cloud_upload</span>
            <p className="text-sm font-bold">Upload Image</p>
            <p className="text-[10px] text-slate-400">Supports JPG, PNG</p>
            <input type="file" ref={fileInputRef} onChange={handleImageSelect} className="hidden" accept="image/*" />
          </div>
        </Card>

        {selectedImage && (
          <div className="space-y-4 animate-in slide-in-from-left-4 duration-500">
            <Button
              onClick={triggerAnalysis}
              disabled={isAnalyzing}
              isLoading={isAnalyzing}
              className="w-full gap-2"
            >
              <span className="material-symbols-outlined">analytics</span>
              Analyze Image
            </Button>
            <p className="text-[10px] text-center text-slate-500 italic">
              I'll explain what I see using analogies related to <span className="font-bold">{profile?.hobbies}</span>.
            </p>
          </div>
        )}
      </aside>

      <main className="flex-1 p-6 lg:p-10 overflow-y-auto flex flex-col items-center">
        {selectedImage ? (
          <div className="w-full max-w-4xl space-y-6">
            <div className="relative group rounded-3xl overflow-hidden shadow-2xl shadow-slate-200 dark:shadow-black/50 border-4 border-white dark:border-slate-800 bg-white dark:bg-slate-800">
              <img src={selectedImage} className="w-full max-h-[60vh] object-contain bg-slate-100 dark:bg-black/20" alt="Analysis Target" />

              {isAnalyzing && (
                <div className="absolute inset-0 bg-slate-900/10 backdrop-blur-sm flex items-center justify-center">
                  <div className="bg-white dark:bg-slate-800 px-6 py-4 rounded-2xl shadow-xl flex items-center gap-4 border border-white/20">
                    <div className="size-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-sm font-bold text-slate-700 dark:text-white animate-pulse">Scanning visual patterns...</span>
                  </div>
                </div>
              )}
            </div>

            {analysis && (
              <Card className="animate-in slide-in-from-bottom-8 duration-700 p-8 border-l-4 border-l-primary flex gap-5 items-start">
                <div className="size-12 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-primary text-2xl">auto_awesome</span>
                </div>
                <div className="space-y-2">
                  <h3 className="font-bold text-lg text-slate-900 dark:text-white">Analysis Results</h3>
                  <p className="text-slate-600 dark:text-slate-300 leading-relaxed text-sm md:text-base">
                    {analysis}
                  </p>
                </div>
              </Card>
            )}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center opacity-40 max-w-md">
            <span className="material-symbols-outlined text-9xl mb-4 text-slate-300 dark:text-slate-700">image_search</span>
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">No Image Selected</h3>
            <p className="text-slate-500">Upload an image from the sidebar to start the visual analysis.</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default VisionScreen;
