import pool from '@/lib/db';

/**
 * SSE Endpoint for Real-time Job Progress
 * Connect to /api/jobs/stream?id=PROJECT_ID
 */
export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get('id');

    if (!projectId) {
        return new Response('Missing project ID', { status: 400 });
    }

    const encoder = new TextEncoder();

    const stream = new ReadableStream({
        async start(controller) {
            const sendUpdate = (data: Record<string, any>) => {
                try {
                    controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
                } catch {
                    // Controller already closed
                }
            };

            // BUG 4 FIX: Send the FIRST update immediately, before the interval kicks in.
            // This prevents showing 0% for 2 seconds on every page load.
            try {
                const initial = await pool.query(
                    `SELECT project_status as status,
                            COALESCE(progress_percent, 0) as progress,
                            COALESCE(eta_seconds, 0) as eta,
                            COALESCE(current_step, 'Iniciando...') as step,
                            error_log
                     FROM projects WHERE id = $1`,
                    [projectId]
                );
                if (initial.rows.length > 0) {
                    const job = initial.rows[0];
                    sendUpdate({ status: job.status, progress: Number(job.progress), eta: Number(job.eta), step: job.step, error: job.error_log });

                    // If already done, close immediately
                    if (['COMPLETED', 'FAILED', 'ERROR'].includes(job.status)) {
                        controller.close();
                        return;
                    }
                }
            } catch (initErr) {
                console.error('SSE init error:', initErr);
            }

            // Poll every 1 second (was 2s)
            const interval = setInterval(async () => {
                try {
                    const result = await pool.query(
                        `SELECT project_status as status,
                                COALESCE(progress_percent, 0) as progress,
                                COALESCE(eta_seconds, 0) as eta,
                                COALESCE(current_step, 'Procesando...') as step,
                                error_log
                         FROM projects WHERE id = $1`,
                        [projectId]
                    );

                    if (result.rows.length > 0) {
                        const job = result.rows[0];
                        sendUpdate({
                            status: job.status,
                            progress: Number(job.progress),
                            eta: Number(job.eta),
                            step: job.step,
                            error: job.error_log,
                        });

                        if (['COMPLETED', 'FAILED', 'ERROR'].includes(job.status)) {
                            clearInterval(interval);
                            controller.close();
                        }
                    }
                } catch (err) {
                    console.error('SSE poll error:', err);
                    clearInterval(interval);
                    controller.close();
                }
            }, 1000);

            // Cleanup when client disconnects
            request.signal.addEventListener('abort', () => {
                clearInterval(interval);
                try { controller.close(); } catch { }
            });
        },
    });

    return new Response(stream, {
        headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache, no-transform',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no', // Disable Nginx buffering (important for SSE)
        },
    });
}
