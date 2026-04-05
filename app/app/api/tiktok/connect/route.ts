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
        const { sessionCookie } = await request.json();

        if (!sessionCookie || sessionCookie.trim().length < 10) {
            return NextResponse.json({
                error: 'Cookie de sesión inválida. Debe ser el valor de "sessionid" de TikTok.'
            }, { status: 400 });
        }

        const sid = sessionCookie.trim();
        console.log(`[TikTok Connect] Fetching username for sessionid: ${sid.substring(0, 5)}...`);

        // 1. Fetch TikTok username using the python script
        const { exec } = require('child_process');
        const { promisify } = require('util');
        const execAsync = promisify(exec);

        let accountName = 'TikTok User';
        try {
            const pythonPath = 'python'; // Or get from config
            const scriptPath = 'c:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide\\scripts\\get_tiktok_user.py';
            const { stdout } = await execAsync(`"${pythonPath}" "${scriptPath}" --sessionid "${sid}"`, { timeout: 45000 });

            const match = stdout.match(/USERNAME:(.*)/);
            if (match && match[1]) {
                accountName = match[1].trim();
                console.log(`[TikTok Connect] Found username: ${accountName}`);
            }
        } catch (fetchError: any) {
            console.warn('[TikTok Connect] Could not fetch username (will use default):', fetchError.message);
            // Non-fatal, we still save the credentials
        }

        const client = await pool.connect();
        try {
            // Build cookies in Netscape format for tiktok-uploader
            const cookiesContent = `# Netscape HTTP Cookie File
.tiktok.com\tTRUE\t/\tTRUE\t0\tsessionid\t${sid}`;

            const credentialsData = JSON.stringify({
                cookies: cookiesContent,
                session_id: sid
            });

            // Upsert into platform_credentials
            await client.query(`
                INSERT INTO platform_credentials (user_id, platform, credentials_type, credentials_data, account_name, is_active)
                VALUES ($1::uuid, 'tiktok', 'cookies', $2::jsonb, $3, true)
                ON CONFLICT (user_id, platform)
                DO UPDATE SET credentials_data = $2::jsonb, account_name = $3, is_active = true, updated_at = NOW()
            `, [userId, credentialsData, accountName]);

            return NextResponse.json({
                success: true,
                message: 'TikTok conectado exitosamente',
                accountName
            });

        } finally {
            client.release();
        }

    } catch (error: any) {
        console.error('Error connecting TikTok:', error);
        return NextResponse.json({
            error: error.message || 'Error interno del servidor'
        }, { status: 500 });
    }
}
