import pool from './lib/db';
import { getVideoQueue } from './lib/queue';

async function run() {
  const userRes = await pool.query('select user_id from projects where user_id is not null limit 1');
  const userId = userRes.rows[0]?.user_id;
  if (!userId) throw new Error('No user_id available');

  const a = await pool.query(
    "insert into projects (user_id, source_video_url, project_status, title) values ($1,$2,'QUEUED',$3) returning id",
    [userId, 'https://youtu.be/dQw4w9WgXcQ', 'TEST Motor A']
  );

  const bSource = `motorb://from-scratch/${Date.now()}`;
  const b = await pool.query(
    "insert into projects (user_id, source_video_url, project_status, title) values ($1,$2,'QUEUED',$3) returning id",
    [userId, bSource, 'TEST Motor B']
  );

  const q = getVideoQueue();

  await q.add(
    'process-video',
    {
      projectId: a.rows[0].id,
      url: 'https://youtu.be/dQw4w9WgXcQ',
      enterpriseOptions: {},
      creationSystem: 'viral_motor_a',
      viralNiche: 'finanzas personales',
      viralDryRun: false,
    },
    { jobId: `video_${a.rows[0].id}` }
  );

  await q.add(
    'process-video',
    {
      projectId: b.rows[0].id,
      url: bSource,
      enterpriseOptions: {},
      creationSystem: 'viral_motor_b',
      viralNiche: 'misterios y enigmas',
      viralDryRun: false,
      motorBInput: {
        tema: 'Caso imposible',
        hook: 'Nadie lo puede explicar',
        angulo: 'Narrativa misterio',
        nicho: 'misterios y enigmas',
        palabras_clave: ['misterio', 'enigma', 'secreto'],
      },
      motorBTrendMode: 'manual-only',
    },
    { jobId: `video_${b.rows[0].id}` }
  );

  console.log(JSON.stringify({ motorA: a.rows[0].id, motorB: b.rows[0].id }, null, 2));
  await pool.end();
}

run().catch(async (e) => {
  console.error(e?.message || e);
  try { await pool.end(); } catch {}
  process.exit(1);
});
