
import React, { useState, useRef, useEffect } from 'react';
import { chatWithGemini, generateSpeech } from '../services/geminiService';
import { LiveSession } from '../services/liveService';
import { Message, UserProfile } from '../types';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

interface ChatScreenProps {
  profile: UserProfile | null;
}

const ChatScreen: React.FC<ChatScreenProps> = ({ profile }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hello ${profile?.name || 'Explorer'}! I'm EduMind AI. How can I help you master ${profile?.goals || 'something new'} today?`,
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [isLive, setIsLive] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const liveSessionRef = useRef<LiveSession | null>(null);

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGenerating]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isGenerating) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsGenerating(true);

    try {
      const history = messages.map(m => ({
        role: (m.role === 'assistant' ? 'model' : 'user') as 'model' | 'user',
        parts: [{ text: m.content }]
      }));

      const response = await chatWithGemini(userMessage.content, history, isThinking, profile || undefined);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
        isThinking: isThinking
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chat error:", error);
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleLiveMode = async () => {
    if (isLive) {
      liveSessionRef.current?.stop();
      liveSessionRef.current = null;
      setIsLive(false);
    } else {
      setIsLive(true);
      const session = new LiveSession();
      liveSessionRef.current = session;
      await session.start((text, isUser) => {
        if (!isUser) {
          setMessages(prev => {
            const last = prev[prev.length - 1];
            if (last && last.role === 'assistant' && last.id === 'live-stream') {
              return [...prev.slice(0, -1), { ...last, content: last.content + " " + text }];
            }
            return [...prev, {
              id: 'live-stream',
              role: 'assistant',
              content: text,
              timestamp: new Date()
            }];
          });
        }
      });
    }
  };

  const playResponse = async (text: string) => {
    try {
      const audioData = await generateSpeech(text);
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const buffer = await audioCtx.decodeAudioData(audioData);
      const source = audioCtx.createBufferSource();
      source.buffer = buffer;
      source.connect(audioCtx.destination);
      source.start(0);
    } catch (e) {
      console.error("TTS failed", e);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-900/50 relative">
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-blue-400 p-[2px]">
              <div className="w-full h-full rounded-full bg-white dark:bg-slate-900 flex items-center justify-center">
                <span className="material-symbols-outlined text-primary">smart_toy</span>
              </div>
            </div>
            {isGenerating && <div className="absolute -bottom-1 -right-1 size-3 bg-green-500 border-2 border-white dark:border-slate-900 rounded-full animate-bounce"></div>}
          </div>
          <div>
            <h2 className="font-bold text-slate-900 dark:text-white">AI Tutor</h2>
            <p className="text-xs text-slate-500">Always here to help</p>
          </div>
        </div>
        <Button
          variant={isLive ? "danger" : "ghost"}
          size="sm"
          onClick={toggleLiveMode}
          className="gap-2"
        >
          <span className="material-symbols-outlined text-lg">{isLive ? 'mic_off' : 'mic'}</span>
          {isLive ? 'End Voice' : 'Voice Mode'}
        </Button>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex items-start gap-4 max-w-3xl animate-in slide-in-from-bottom-2 duration-300 ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
            <div className={`size-8 shrink-0 rounded-full flex items-center justify-center shadow-sm ${msg.role === 'assistant' ? 'bg-white dark:bg-slate-800 text-primary' : 'bg-primary text-white'}`}>
              {msg.role === 'assistant' ? <span className="material-symbols-outlined text-base">smart_toy</span> : <span className="material-symbols-outlined text-base">person</span>}
            </div>
            <div className={`group flex flex-col gap-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`px-5 py-3.5 rounded-2xl shadow-sm text-sm leading-relaxed max-w-[85vw] md:max-w-md lg:max-w-lg whitespace-pre-wrap ${msg.role === 'assistant' ? 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-tl-none' : 'bg-primary text-white rounded-tr-none'}`}>
                {msg.isThinking && (
                  <div className="flex items-center gap-2 mb-2 p-2 bg-slate-50 dark:bg-slate-700/50 rounded-lg text-xs text-slate-500 font-medium italic border border-slate-100 dark:border-slate-700">
                    <span className="material-symbols-outlined text-sm">psychology</span>
                    Thinking Process Used
                  </div>
                )}
                {msg.content}
              </div>
              {msg.role === 'assistant' && !isLive && (
                <button onClick={() => playResponse(msg.content)} className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-[10px] items-center text-slate-400 hover:text-primary px-2">
                  <span className="material-symbols-outlined text-sm">volume_up</span> Play
                </button>
              )}
            </div>
          </div>
        ))}
        {isGenerating && (
          <div className="flex items-start gap-4">
            <div className="size-8 shrink-0 rounded-full bg-white dark:bg-slate-800 flex items-center justify-center shadow-sm">
              <span className="material-symbols-outlined text-primary text-base animate-spin">sync</span>
            </div>
            <div className="bg-white dark:bg-slate-800 px-5 py-4 rounded-2xl rounded-tl-none shadow-sm flex gap-1 items-center">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800">
        <div className="max-w-4xl mx-auto flex flex-col gap-2">
          <div className="flex items-center justify-between px-1">
            <label className="flex items-center gap-2 cursor-pointer group">
              <div className={`w-8 h-4 rounded-full transition-colors relative ${isThinking ? 'bg-primary' : 'bg-slate-200 dark:bg-slate-700'}`} onClick={() => setIsThinking(!isThinking)}>
                <div className={`absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-transform ${isThinking ? 'translate-x-4' : ''}`}></div>
              </div>
              <span className="text-xs font-medium text-slate-500 group-hover:text-primary transition-colors">Deep Thinking</span>
            </label>
          </div>

          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                placeholder="Ask anything..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                className="shadow-inner bg-slate-50 dark:bg-slate-800 border-transparent focus:bg-white dark:focus:bg-slate-900"
              />
            </div>
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isGenerating}
              className="w-12 h-[42px] rounded-xl p-0 flex items-center justify-center shrink-0"
            >
              <span className="material-symbols-outlined">send</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatScreen;
