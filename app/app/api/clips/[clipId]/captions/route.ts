import { NextResponse } from 'next/server';
import pool from '@/lib/db';

export async function GET(
    request: Request,
    context: { params: Promise<{ clipId: string }> }
) {
    const params = await context.params;
    const clipId = params.clipId;

    try {
        const client = await pool.connect();

        try {
            // Fetch clip data with hook/payoff descriptions
            const result = await client.query(
                `SELECT 
                    c.id,
                    c.start_time,
                    c.end_time,
                    c.hook_description,
                    c.payoff_description,
                    c.title
                 FROM clips c
                 WHERE c.id = $1::uuid`,
                [clipId]
            );

            if (result.rows.length === 0) {
                return NextResponse.json({ error: 'Clip not found' }, { status: 404 });
            }

            const clip = result.rows[0];

            // Generate WebVTT format
            const vtt = generateVTT(clip);

            return new Response(vtt, {
                headers: {
                    'Content-Type': 'text/vtt',
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'public, max-age=3600',
                },
            });

        } finally {
            client.release();
        }

    } catch (error) {
        console.error('Error generating VTT:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

function generateVTT(clip: any): string {
    const formatTimestamp = (seconds: number): string => {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);

        return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
    };

    const duration = clip.end_time - clip.start_time;
    const midPoint = clip.start_time + (duration / 2);

    let vtt = 'WEBVTT\n\n';

    // Hook cue
    vtt += `1\n`;
    vtt += `${formatTimestamp(0)} --> ${formatTimestamp(duration / 2)}\n`;
    vtt += `${clip.hook_description}\n\n`;

    // Payoff cue
    vtt += `2\n`;
    vtt += `${formatTimestamp(duration / 2)} --> ${formatTimestamp(duration)}\n`;
    vtt += `${clip.payoff_description}\n\n`;

    return vtt;
}
