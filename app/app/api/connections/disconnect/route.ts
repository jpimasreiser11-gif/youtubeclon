import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

export async function POST(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const userId = session.user.id;

    try {
        const { platform } = await request.json();

        if (!platform || !['youtube', 'tiktok'].includes(platform)) {
            return NextResponse.json({
                error: 'Platform must be "youtube" or "tiktok"'
            }, { status: 400 });
        }

        const client = await pool.connect();
        try {
            // Deactivate credentials
            await client.query(`
                UPDATE platform_credentials 
                SET is_active = false, updated_at = NOW()
                WHERE user_id = $1::uuid AND platform = $2
            `, [userId, platform]);

            return NextResponse.json({
                success: true,
                message: `${platform} desconectado`
            });

        } finally {
            client.release();
        }

    } catch (error: any) {
        console.error('Error disconnecting platform:', error);
        return NextResponse.json({
            error: error.message || 'Error interno del servidor'
        }, { status: 500 });
    }
}
