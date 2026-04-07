const { Client } = require('pg');

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
    const result = await db.query(
      `
      select
        p.id,
        p.title,
        p.project_status,
        count(c.id) as clips
      from projects p
      left join clips c on c.project_id = p.id
      where p.title like 'TEST Motor A %' or p.title like 'TEST Motor B %'
      group by p.id, p.title, p.project_status, p.created_at
      order by p.created_at desc
      limit 6
      `
    );

    console.log(JSON.stringify(result.rows, null, 2));
  } finally {
    await db.end();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
