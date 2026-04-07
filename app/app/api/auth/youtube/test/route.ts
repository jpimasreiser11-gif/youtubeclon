import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

async function refreshAccessToken(refreshToken: string, clientId: string, clientSecret: string) {
    const resp = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            client_id: clientId,
            client_secret: clientSecret,
            refresh_token: refreshToken,
            grant_type: 'refresh_token',
        }),
    });

    if (!resp.ok) {
        const errText = await resp.text();
        throw new Error(`Token refresh failed: ${errText}`);
    }

    return resp.json();
}

export async function GET() {
    const session = await auth();
    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const client = await pool.connect();
    try {
        const q = await client.query(
            `SELECT id, credentials_data, account_name
             FROM platform_credentials
             WHERE user_id = $1::uuid
               AND platform = 'youtube'
               AND is_active = true
             LIMIT 1`,
            [session.user.id]
        );

        if (q.rows.length === 0) {
            return NextResponse.json({ ok: false, error: 'No hay conexión de YouTube activa' }, { status: 404 });
        }

        const row = q.rows[0];
        const credentials = row.credentials_data || {};
        let accessToken: string | undefined = credentials.access_token;
        const refreshToken: string | undefined = credentials.refresh_token;
        const clientId: string | undefined = credentials.client_id || process.env.YOUTUBE_CLIENT_ID || process.env.GOOGLE_CLIENT_ID;
        const clientSecret: string | undefined = credentials.client_secret || process.env.YOUTUBE_CLIENT_SECRET || process.env.GOOGLE_CLIENT_SECRET;

        if (!accessToken && refreshToken && clientId && clientSecret) {
            const refreshed = await refreshAccessToken(refreshToken, clientId, clientSecret);
            accessToken = refreshed.access_token;
            credentials.access_token = refreshed.access_token;
            credentials.token_type = refreshed.token_type || credentials.token_type || 'Bearer';
            credentials.obtained_at = new Date().toISOString();

            await client.query(
                `UPDATE platform_credentials
                 SET credentials_data = $1::jsonb, updated_at = NOW()
                 WHERE id = $2::uuid`,
                [JSON.stringify(credentials), row.id]
            );
        }

        if (!accessToken) {
            return NextResponse.json({ ok: false, error: 'No hay access token válido. Reconecta YouTube.' }, { status: 400 });
        }

        const ytResp = await fetch('https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true', {
            headers: { Authorization: `Bearer ${accessToken}` },
        });

        if (!ytResp.ok) {
            if (refreshToken && clientId && clientSecret) {
                const refreshed = await refreshAccessToken(refreshToken, clientId, clientSecret);
                credentials.access_token = refreshed.access_token;
                credentials.token_type = refreshed.token_type || credentials.token_type || 'Bearer';
                credentials.obtained_at = new Date().toISOString();

                await client.query(
                    `UPDATE platform_credentials
                     SET credentials_data = $1::jsonb, updated_at = NOW()
                     WHERE id = $2::uuid`,
                    [JSON.stringify(credentials), row.id]
                );

                const retry = await fetch('https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true', {
                    headers: { Authorization: `Bearer ${credentials.access_token}` },
                });

                if (!retry.ok) {
                    const txt = await retry.text();
                    return NextResponse.json({ ok: false, error: `YouTube API error: ${txt}` }, { status: 400 });
                }

                const payload = await retry.json();
                const name = payload?.items?.[0]?.snippet?.title || row.account_name || 'YouTube Channel';
                credentials.last_validated_at = new Date().toISOString();
                await client.query(
                    `UPDATE platform_credentials
                     SET account_name = $1,
                         credentials_data = $2::jsonb,
                         updated_at = NOW()
                     WHERE id = $3::uuid`,
                    [name, JSON.stringify(credentials), row.id]
                );

                return NextResponse.json({ ok: true, accountName: name, message: 'Conexión YouTube válida y token renovado' });
            }

            const txt = await ytResp.text();
            return NextResponse.json({ ok: false, error: `YouTube API error: ${txt}` }, { status: 400 });
        }

        const payload = await ytResp.json();
        const name = payload?.items?.[0]?.snippet?.title || row.account_name || 'YouTube Channel';
        credentials.last_validated_at = new Date().toISOString();

        await client.query(
            `UPDATE platform_credentials
             SET account_name = $1,
                 credentials_data = $2::jsonb,
                 updated_at = NOW()
             WHERE id = $3::uuid`,
            [name, JSON.stringify(credentials), row.id]
        );

        return NextResponse.json({ ok: true, accountName: name, message: 'Conexión YouTube válida' });
    } catch (error: any) {
        return NextResponse.json({ ok: false, error: error.message || 'Error validando YouTube OAuth' }, { status: 400 });
    } finally {
        client.release();
    }
}
