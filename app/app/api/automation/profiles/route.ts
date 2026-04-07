import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

export async function GET(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const client = await pool.connect();

    try {
        let result;
        try {
            result = await client.query(
                `SELECT * FROM automation_profiles 
                 WHERE user_id = $1::uuid 
                 ORDER BY created_at DESC`,
                [session.user.id]
            );
        } catch (error: any) {
            if (error?.code === '42P01') {
                return NextResponse.json({ profiles: [] });
            }
            throw error;
        }

        return NextResponse.json({ profiles: result.rows });

    } finally {
        client.release();
    }
}

export async function POST(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        const data = await request.json();

        const client = await pool.connect();

        try {
            const result = await client.query(
                `INSERT INTO automation_profiles 
                 (user_id, name, source_type, source_config, min_virality_score, 
                  categories, platforms, posts_per_day, schedule_times, 
                  subtitle_preset, auto_seo, generate_long_form, active)
                 VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                 RETURNING *`,
                [
                    session.user.id,
                    data.name,
                    data.source_type,
                    JSON.stringify(data.source_config),
                    data.min_virality_score || 85,
                    data.categories || [],
                    data.platforms || ['youtube'],
                    data.posts_per_day || 3,
                    data.schedule_times || ['09:00', '14:00', '19:00'],
                    data.subtitle_preset || 'tiktok',
                    data.auto_seo !== false,
                    data.generate_long_form || false,
                    data.active !== false
                ]
            );

            return NextResponse.json({
                success: true,
                profile: result.rows[0]
            });

        } finally {
            client.release();
        }

    } catch (error) {
        console.error('Error creating automation profile:', error);
        if ((error as any)?.code === '42P01') {
            return NextResponse.json({ error: 'automation_profiles table missing' }, { status: 503 });
        }
        return NextResponse.json({
            error: 'Internal server error'
        }, { status: 500 });
    }
}
