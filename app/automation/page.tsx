'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Button, Card, Input, Checkbox } from '@/components/ui';
import {
  Trending2,
  Play,
  RefreshCcw,
} from 'lucide-react';

export default function AutomationPage() {
  const [trend, setTrend] = useState('');
  const [url, setUrl] = useState('');
  const [processing, setProcessing] = useState(false);
  const [options, setOptions] = useState({
    audioPro: true,
    smartReframe: true,
    cleanSpeech: true,
    bRoll: true,
  });

  const handleTrend = async () => {
    if (!trend) return;
    setProcessing(true);
    try {
      const res = await fetch('/api/automation/trend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trend }),
      });
      const data = await res.json();
      if (res.ok) {
        alert('Processing started with trending videos!');
      }
    } finally {
      setProcessing(false);
    }
  };

  const handleStart = async () => {
    if (!url) return;
    setProcessing(true);
    try {
      const res = await fetch('/api/automation/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, ...options }),
      });
      if (res.ok) {
        alert('Job started! Progress will update via job list.');
      }
    } finally {
      setProcessing(false);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await fetch('/api/automation/upload', {
        method: 'POST',
        body: form,
      });
      const result = await res.json();
      if (res.ok) {
        alert('File uploaded successfully!');
      } else {
        alert('Upload failed: ' + (result as any).error);
      }
    } catch (err) {
      console.error(err);
      alert('Upload error');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="mb-8 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900">Video Automation Hub</h1>
          <p className="mt-2 text-lg text-gray-600">
            Manage, process, and publish AI-generated clips
          </p>
        </header>

        {/* Main Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Trend Search */}
          <Card className="bg-white rounded-lg shadow">
            <Card.Header>
              <div className="flex items-center gap-3">
                <Trending2 className="w-5 h-5 text-blue-600" />
                <span className="text-xl font-medium text-gray-900">Trending Search</span>
              </div>
            </Card.Header>
            <Card.Content className="p-4">
              <Input
                type="text"
                placeholder="Enter keyword (e.g., AI, curiosity)"
                value={trend}
                onChange={(e) => setTrend(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
              <Button
                variant="primary"
                onClick={handleTrend}
                disabled={processing}
                className="mt-2 w-full flex items-center gap-2"
              >
                {processing ? (
                  <RefreshCcw className="animate-spin w-5 h-5 text-blue-600" />
                ) : (
                  'Search'
                )}
              </Button>
            </Card.Content>
          </Card>

          {/* Job Controls */}
          <Card className="bg-white rounded-lg shadow">
            <Card.Header>
              <div className="flex items-center gap-3">
                <Play className="w-5 h-5 text-green-600" />
                <span className="text-xl font-medium text-gray-900">Job Controls</span>
              </div>
            </Card.Header>
            <Card.Content className="p-4">
              <div className="flex">
                <Input
                  type="text"
                  placeholder="Enter video URL or reference"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block font-medium text-gray-700 mb-1">Processing Options</label>
                  <div className="flex items-center gap-4">
                    {Object.entries(options).map(([key, checked]) => (
                      <label key={key} className="flex items-center gap-1">
                        <Checkbox checked={checked} className="rounded text-blue-600" />
                        <span className="text-sm text-gray-700">{key.replace(/([A-Z])/g, ' $1').trim()} (Pro)</Checkbox>
                      </label>
                    </div>
                  </div>
                </div>
                <Button
                  variant="secondary"
                  onClick={handleStart}
                  disabled={processing}
                  className="w-full px-4 py-2"
                >
                  {processing ? (
                    <RefreshCcw className="animate-spin w-5 h-5 text-blue-600" />
                  ) : (
                    'Start Processing'
                  )}
                </Button>
              </div>
              <div className="mt-2 flex justify-end">
                <a href="/upload" className="text-blue-600 hover:underline">
                  Upload File (placeholder)
                </a>
              </div>
              <div className="mt-4 flex items-center gap-2 text-xs text-gray-500">
                {/* Mock status indicator */}
                <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
                Processing in background…
              </div>
            </Card.Content>
          </Card>
        </div>

        {/* Generated Clips */}
        <Card className="bg-white rounded-lg shadow">
          <Card.Header>
            <div className="flex items-center gap-3">
              <Video className="w-5 h-5 text-purple-600" />
              <span className="text-xl font-medium text-gray-900">Generated Clips</span>
            </div>
          </Card.Header>
          <Card.Content className="p-4">
            <div className="space-y-4">
              {/* Mock clips grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="border rounded-lg p-3 hover:shadow">
                    <p className="text-sm text-gray-700">Clip {i + 1}</p>
                    <p className="text-xs text-gray-500">Duration: 45s</p>
                    <div className="mt-2 flex items-center gap-2">
                      <Play className="w-4 h-4 text-blue-600" />
                      <a href="#" className="text-blue-600 hover:text-blue-800 underline">
                        Download / Share
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card.Content>
        </Card>

        {/* Footer */}
        <footer className="mt-12 border-t pt-6 text-center text-sm text-gray-500">
          <div className="flex justify-center space-x-4">
            <Link href="/" className="hover-text-blue-600">Home</Link>
            <Link href="/automation" className="hover-text-blue-600">Automation</Link>
            <Link href="/upload" className="hover-text-blue-600">Upload</Link>
          </div>
        </footer>
      </div>
    </div>
  );
}

/* Mock API routes – replace with real implementations later */
export async function GET(request: Request) {
  return new Response(JSON.stringify({ status: 'ok' }), {
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function POST(request: Request) {
  const body = await request.json();
  // Simple dispatcher for demo
  if (body?.action === 'trend') {
    // Simulate returning trending videos
    return new Response(JSON.stringify({ videos: [{ title: 'AI Breakthrough' }] }), {
      headers: { 'Content-Type': 'application/json' },
    });
  }
  return new Response(JSON.stringify({ error: 'unknown action' }), { status: 400 });
}

/* Types for internal use */
type Job = {
  id: string;
  title: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  eta_seconds: number;
  created_at: string;
};
type Clip = {
  id: string;
  title: string;
  videoUrl: string;
  virality_score: number;
  wpm: number;
};