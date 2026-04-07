import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

function getBaseUrl(request: Request) {
    const envUrl = process.env.NEXTAUTH_URL || process.env.APP_BASE_URL;
    if (envUrl) return envUrl.replace(/\/$/, '');
    const url = new URL(request.url);
    return `${url.protocol}//${url.host}`;
}

function toDateFromSeconds(expiresIn?: number | null) {
    if (!expiresIn) return null;
    return new Date(Date.now() + expiresIn * 1000);
}

function redirectTo(request: Request, path: string) {
    return NextResponse.redirect(new URL(path, request.url));
}

export async function GET(request: Request) {
    const session = await auth();
    if (!session?.user) {
        return redirectTo(request, '/connections?youtube=error');
    }

    const reqUrl = new URL(request.url);
    const code = reqUrl.searchParams.get('code');
    const state = reqUrl.searchParams.get('state');
    const oauthError = reqUrl.searchParams.get('error');

    if (oauthError) {
        return redirectTo(request, '/connections?youtube=error');
    }

    if (!code || !state) {
        return redirectTo(request, '/connections?youtube=error');
    }

    let stateUserId: string | null = null;
    try {
        const parsed = JSON.parse(Buffer.from(state, 'base64url').toString('utf-8'));
        stateUserId = parsed.userId || null;
    } catch {
        return redirectTo(request, '/connections?youtube=error');
    }

    if (!stateUserId || stateUserId !== session.user.id) {
        return redirectTo(request, '/connections?youtube=error');
    }

    const clientId = process.env.YOUTUBE_CLIENT_ID || process.env.GOOGLE_CLIENT_ID;
    const clientSecret = process.env.YOUTUBE_CLIENT_SECRET || process.env.GOOGLE_CLIENT_SECRET;
    if (!clientId || !clientSecret) {
        return redirectTo(request, '/connections?youtube=error');
    }

    const baseUrl = getBaseUrl(request);
    const redirectUri = `${baseUrl}/api/auth/youtube/callback`;

    try {
        const tokenResp = await fetch('https://oauth2.googleapis.com/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                code,
                client_id: clientId,
                client_secret: clientSecret,
                redirect_uri: redirectUri,
                grant_type: 'authorization_code',
            }),
        });

        if (!tokenResp.ok) {
            return redirectTo(request, '/connections?youtube=error');
        }

        const tokenData = await tokenResp.json();
        const accessToken = tokenData.access_token as string | undefined;
        const refreshToken = tokenData.refresh_token as string | undefined;
        const expiresIn = tokenData.expires_in as number | undefined;

        if (!accessToken) {
            return redirectTo(request, '/connections?youtube=error');
        }

        // Fetch channel name for better UX
        let accountName = 'YouTube Channel';
        try {
            const channelResp = await fetch('https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true', {
                headers: { Authorization: `Bearer ${accessToken}` },
            });
            if (channelResp.ok) {
                const channelJson = await channelResp.json();
                const name = channelJson?.items?.[0]?.snippet?.title;
                if (name) accountName = String(name);
            }
        } catch {
            // non-fatal
        }

        const client = await pool.connect();
        try {
            // Preserve existing refresh token if Google does not return a new one
            const existing = await client.query(
                `SELECT credentials_data FROM platform_credentials WHERE user_id = $1::uuid AND platform = 'youtube' LIMIT 1`,
                [session.user.id]
            );
            const existingRefreshToken = existing.rows?.[0]?.credentials_data?.refresh_token;

            const credentialsData = {
                access_token: accessToken,
                refresh_token: refreshToken || existingRefreshToken || null,
                client_id: clientId,
                client_secret: clientSecret,
                token_type: tokenData.token_type || 'Bearer',
                scope: tokenData.scope || null,
                obtained_at: new Date().toISOString(),
            };

            await client.query(
                `INSERT INTO platform_credentials (user_id, platform, credentials_type, credentials_data, account_name, is_active, expires_at)
                 VALUES ($1::uuid, 'youtube', 'oauth', $2::jsonb, $3, true, $4)
                 ON CONFLICT (user_id, platform)
                 DO UPDATE SET
                    credentials_type = 'oauth',
                    credentials_data = $2::jsonb,
                    account_name = $3,
                    is_active = true,
                    expires_at = $4,
                    updated_at = NOW()`,
                [session.user.id, JSON.stringify(credentialsData), accountName, toDateFromSeconds(expiresIn)]
            );
        } finally {
            client.release();
        }

        return redirectTo(request, '/connections?youtube=connected');
    } catch {
        return redirectTo(request, '/connections?youtube=error');
    }
}
