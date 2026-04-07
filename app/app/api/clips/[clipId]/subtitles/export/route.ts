import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

export async function GET(
    request: Request,
    context: { params: Promise<{ clipId: string }> }
) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const format = searchParams.get('format') || 'vtt'; // vtt, srt, ass
    const params = await context.params;
    const clipId = params.clipId;
    if (!/^[0-9a-fA-F-]{36}$/.test(clipId)) {
        return NextResponse.json({ error: 'Invalid clip id' }, { status: 400 });
    }

    try {
        const client = await pool.connect();

        try {
            // Get transcription
            const result = await client.query(
                `SELECT t.words, t.language, COALESCE(p.title, c.id::text) AS title
                 FROM transcriptions t
                 JOIN clips c ON t.clip_id = c.id
                 JOIN projects p ON c.project_id = p.id
                 WHERE t.clip_id = $1::uuid AND p.user_id = $2::uuid`,
                [clipId, session.user.id]
            );

            if (result.rows.length === 0) {
                return NextResponse.json({
                    error: 'Transcription not found'
                }, { status: 404 });
            }

            const { words, language, title } = result.rows[0];

            // Generate subtitle content based on format
            let content: string;
            let contentType: string;
            let filename: string;

            switch (format.toLowerCase()) {
                case 'vtt':
                    content = generateVTT(words);
                    contentType = 'text/vtt';
                    filename = `${title || 'subtitle'}.vtt`;
                    break;

                case 'srt':
                    content = generateSRT(words);
                    contentType = 'text/srt';
                    filename = `${title || 'subtitle'}.srt`;
                    break;

                case 'ass':
                    content = generateASS(words, language);
                    contentType = 'text/x-ssa';
                    filename = `${title || 'subtitle'}.ass`;
                    break;

                default:
                    return NextResponse.json({
                        error: 'Invalid format. Use vtt, srt, or ass'
                    }, { status: 400 });
            }

            return new Response(content, {
                headers: {
                    'Content-Type': contentType,
                    'Content-Disposition': `attachment; filename="${filename}"`,
                    'Access-Control-Allow-Origin': '*',
                },
            });

        } finally {
            client.release();
        }

    } catch (error) {
        console.error('Error exporting subtitles:', error);
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}

// Generate WebVTT format
function generateVTT(words: any[]): string {
    let vtt = 'WEBVTT\n\n';

    let index = 1;
    for (const word of words) {
        vtt += `${index}\n`;
        vtt += `${formatTimestampVTT(word.start)} --> ${formatTimestampVTT(word.end)}\n`;
        vtt += `${word.word}\n\n`;
        index++;
    }

    return vtt;
}

// Generate SRT format
function generateSRT(words: any[]): string {
    let srt = '';

    let index = 1;
    for (const word of words) {
        srt += `${index}\n`;
        srt += `${formatTimestampSRT(word.start)} --> ${formatTimestampSRT(word.end)}\n`;
        srt += `${word.word}\n\n`;
        index++;
    }

    return srt;
}

// Generate ASS format (Advanced SubStation Alpha) for animations
function generateASS(words: any[], language: string): string {
    let ass = `[Script Info]
Title: Viral Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,70,&H00FFFF00,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
`;

    for (const word of words) {
        const start = formatTimestampASS(word.start);
        const end = formatTimestampASS(word.end);
        ass += `Dialogue: 0,${start},${end},Default,,0,0,0,,${word.word}\n`;
    }

    return ass;
}

// Timestamp formatters
function formatTimestampVTT(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);

    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
}

function formatTimestampSRT(seconds: number): string {
    return formatTimestampVTT(seconds).replace('.', ',');
}

function formatTimestampASS(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const cs = Math.floor((seconds % 1) * 100);

    return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${cs.toString().padStart(2, '0')}`;
}
