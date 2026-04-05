import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import pool from '@/lib/db';

export async function DELETE(
    request: Request,
    { params }: { params: { id: string } }
) {
    const session = await auth();

    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { id } = params;

    try {
        const client = await pool.connect();
        try {
            // Ensure the user owns this scheduled post through the clip/project chain
            const check = await client.query(
                `SELECT sp.id 
                 FROM scheduled_publications sp
                 JOIN clips c ON sp.clip_id = c.id
                 JOIN projects p ON c.project_id = p.id
                 WHERE sp.id = $1 AND p.user_id = $2::uuid`,
                [id, session.user.id]
            );

            if (check.rows.length === 0) {
                return NextResponse.json({ error: 'Post not found or unauthorized' }, { status: 404 });
            }

            await client.query('DELETE FROM scheduled_publications WHERE id = $1', [id]);
            return NextResponse.json({ success: true });
        } finally {
            client.release();
        }
    } catch (error: any) {
        console.error('Error deleting scheduled post:', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
