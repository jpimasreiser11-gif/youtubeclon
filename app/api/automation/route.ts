import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  // Return list of jobs (mock for now)
  const jobs = [
    { id: '1', title: 'Sample Job 1', status: 'completed' as const, progress: 100, eta_seconds: 0, created_at: new Date().toISOString() },
    { id: '2', title: 'Sample Job 2', status: 'processing' as const, progress: 45, eta_seconds: 120, created_at: new Date().toISOString() },
  ];
  return NextResponse.json({ jobs });
}

export async function POST(request: Request) {
  const body = await request.json();
  const { action, query, url, ...options } = body;

  // Trending search endpoint
  if (action === 'trend' || request.url.includes('/trend')) {
    // Mock trending results based on query
    const mockTrending = [
      { title: 'AI Breakthrough', url: 'https://youtu.be/abc123' },
      { title: 'Space Exploration', url: 'https://youtu.be/def456' },
      { title: 'Science Facts', url: 'https://youtu.be/ghi789' },
    ].filter(v => v.title.toLowerCase().includes(query?.toLowerCase() ?? ''));
    return NextResponse.json({ trending: mockTrending });
  }

  // Start processing endpoint
  if (action === 'process' || request.url.includes('/process')) {
    if (!url) {
      return NextResponse.json({ error: 'URL is required' }, { status: 400 });
    }
    // Simulate job creation
    const jobId = Math.random().toString(36).substr(2, 9);
    // In a real app, you would spawn a background task (e.g., using bullmq or a worker)
    // For now, just return success
    return NextResponse.json({ success: true, jobId, message: 'Processing started' });
  }

  // Default error
  return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
}