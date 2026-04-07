import { NextResponse } from 'next/server';
import { auth } from '@/auth';

function getBaseUrl(request: Request) {
    const envUrl = process.env.NEXTAUTH_URL || process.env.APP_BASE_URL;
    if (envUrl) return envUrl.replace(/\/$/, '');
    const url = new URL(request.url);
    return `${url.protocol}//${url.host}`;
}

export async function GET(request: Request) {
    const session = await auth();
    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const clientId = process.env.YOUTUBE_CLIENT_ID || process.env.GOOGLE_CLIENT_ID;
    if (!clientId) {
        return NextResponse.json({ error: 'Missing YOUTUBE_CLIENT_ID/GOOGLE_CLIENT_ID' }, { status: 400 });
    }

    const baseUrl = getBaseUrl(request);
    const redirectUri = `${baseUrl}/api/auth/youtube/callback`;

    const state = Buffer.from(JSON.stringify({
        userId: session.user.id,
        ts: Date.now(),
    })).toString('base64url');

    const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
    authUrl.searchParams.set('client_id', clientId);
    authUrl.searchParams.set('redirect_uri', redirectUri);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('access_type', 'offline');
    authUrl.searchParams.set('prompt', 'consent');
    authUrl.searchParams.set('include_granted_scopes', 'true');
    authUrl.searchParams.set('scope', [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube.readonly',
    ].join(' '));
    authUrl.searchParams.set('state', state);

    return NextResponse.redirect(authUrl.toString());
}
