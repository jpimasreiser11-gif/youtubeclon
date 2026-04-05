import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

export async function GET(request: Request) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const userId = session.user.id;

    try {
        const client = await pool.connect();
        try {
            const result = await client.query(
                `SELECT
                    platform,
                    is_active as connected,
                    updated_at as last_sync,
                    account_name,
                    credentials_type,
                    expires_at,
                    credentials_data
                 FROM platform_credentials
                 WHERE user_id = $1::uuid`,
                [userId]
            );

            const connections: any[] = [
                { platform: 'youtube', connected: false },
                { platform: 'tiktok', connected: false }
            ];

            result.rows.forEach(row => {
                const conn = connections.find(c => c.platform === row.platform);
                if (conn) {
                    conn.connected = row.connected;
                    conn.accountName = row.account_name || 'Cuenta Conectada';
                    conn.lastSync = row.last_sync;
                    conn.credentialsType = row.credentials_type || null;
                    conn.expiresAt = row.expires_at || null;
                    conn.tokenObtainedAt = row.credentials_data?.obtained_at || null;
                    conn.lastValidatedAt = row.credentials_data?.last_validated_at || null;
                }
            });

            return NextResponse.json({ connections });
        } finally {
            client.release();
        }
    } catch (error) {
        console.error('Error checking connections:', error);
        // Return default disconnected state on error
        return NextResponse.json({
            connections: [
                { platform: 'youtube', connected: false },
                { platform: 'tiktok', connected: false }
            ]
        });
    }
}
