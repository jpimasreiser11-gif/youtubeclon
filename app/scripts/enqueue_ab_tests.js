const { Client } = require('pg');
const { Queue } = require('bullmq');

(async () => {
  const db = new Client({
    host: process.env.POSTGRES_HOST || 'localhost',
    port: Number(process.env.POSTGRES_PORT || 5432),
    database: process.env.POSTGRES_DB || 'antigravity',
    user: process.env.POSTGRES_USER || 'n8n',
    password: process.env.POSTGRES_PASSWORD || 'n8n',
  });

  await db.connect();

  try {
    const u = await db.query('select user_id from projects where user_id is not null limit 1');
    if (!u.rows.length) throw new Error('No user_id found in projects');
    const userId = u.rows[0].user_id;

    const queue = new Queue('video-processing', {
      connection: { host: '127.0.0.1', port: 6379, maxRetriesPerRequest: null },
    });

    const aIns = await db.query(
      "insert into projects (user_id, source_video_url, project_status, title) values ($1,$2,'QUEUED',$3) returning id",
      [userId, 'https://youtu.be/dQw4w9WgXcQ', `TEST Motor A ${Date.now()}`]
    );
    const aId = aIns.rows[0].id;

    await queue.add(
      'process-video',
      {
        projectId: aId,
        url: 'https://youtu.be/dQw4w9WgXcQ',
        enterpriseOptions: {},
        creationSystem: 'viral_motor_a',
        viralNiche: 'finanzas personales',
        viralDryRun: false,
      },
      { jobId: `video_${aId}` }
    );

    const sourceB = `motorb://from-scratch/${Date.now()}`;
    const bIns = await db.query(
      "insert into projects (user_id, source_video_url, project_status, title) values ($1,$2,'QUEUED',$3) returning id",
      [userId, sourceB, `TEST Motor B ${Date.now()}`]
    );
    const bId = bIns.rows[0].id;

    await queue.add(
      'process-video',
      {
        projectId: bId,
        url: sourceB,
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
      { jobId: `video_${bId}` }
    );

    console.log(JSON.stringify({ userId, motorAProjectId: aId, motorBProjectId: bId }, null, 2));

    await queue.close();
  } finally {
    await db.end();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
