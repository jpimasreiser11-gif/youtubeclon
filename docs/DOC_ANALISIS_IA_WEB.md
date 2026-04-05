# 📄 Documentación de Código para Análisis de IA (Web App)

Este documento contiene el código fuente principal y la arquitectura de la aplicación web **Project Sovereign**. Está diseñado para que una IA lo analice en busca de errores lógicos, cuellos de botella o fallos de seguridad.

---

## 🛠 Arquitectura General
- **Framework**: Next.js 16 (App Router)
- **Lenguaje**: TypeScript
- **Base de Datos**: PostgreSQL (Instanciado en Docker)
- **Autenticación**: NextAuth.js
- **Procesamiento**: Los scripts de Python se ejecutan de forma asíncrona mediante `child_process.exec` desde las API Routes.

---

## 📂 Directorios Clave
- `app/api/`: Rutas de la API servidor.
- `app/lib/`: Utilidades y conexión a base de datos.
- `app/components/`: Componentes de UI reactivos.
- `scripts/`: Núcleo de procesamiento en Python.

---

## 1. Configuración y Dependencias (`package.json`)
Define las dependencias críticas y scripts de ejecución.

```json
{
  "dependencies": {
    "@auth/pg-adapter": "^1.11.1",
    "next": "16.1.4",
    "next-auth": "^5.0.0-beta.30",
    "pg": "^8.17.2",
    "react": "19.2.3",
    "zod": "^4.3.6"
  }
}
```

---

## 2. Conexión a Base de Datos (`app/lib/db.ts`)
Gestiona el pool de conexiones a PostgreSQL.

```typescript
import { Pool } from 'pg';

const pool = new Pool({
    user: process.env.POSTGRES_USER || 'n8n',
    host: process.env.POSTGRES_HOST || 'localhost',
    database: process.env.POSTGRES_DB || 'antigravity',
    password: process.env.POSTGRES_PASSWORD || 'n8n',
    port: parseInt(process.env.POSTGRES_PORT || '5432'),
});

export default pool;
```

---

## 3. Creación de Trabajos (`app/app/api/create-job/route.ts`)
Esta es la ruta más crítica. Recibe una URL, busca metadatos de YouTube y dispara el script de Python.

```typescript
import { NextResponse } from 'next/server';
import pool from '@/lib/db';
import { auth } from "@/auth";
import { exec } from 'child_process';
import path from 'path';

export async function POST(request: Request) {
    const session = await auth();
    if (!session || !session.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const userId = session.user.id;
    try {
        const body = await request.json();
        const { url } = body;
        if (!url) return NextResponse.json({ error: 'URL is required' }, { status: 400 });

        const client = await pool.connect();
        try {
            // 1. Insertar proyecto en DB
            const result = await client.query(
                "INSERT INTO projects (user_id, source_video_url, project_status) VALUES ($1, $2, 'QUEUED') RETURNING id",
                [userId, url]
            );
            const projectId = result.rows[0].id;

            // 2. Disparar Motor de IA (Python)
            const scriptPath = path.join(process.cwd(), 'scripts', 'ingest.py');
            const pythonPath = 'c:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide\\venv_sovereign\\Scripts\\python.exe';
            const cmd = `"${pythonPath}" "${scriptPath}" "${projectId}" "${url}"`;

            const pythonProcess = exec(cmd, { cwd: process.cwd(), env: { ...process.env } });
            pythonProcess.unref(); // Ejecución independiente

            return NextResponse.json({ success: true, jobId: projectId });
        } finally {
            client.release();
        }
    } catch (error) {
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
```

---

## 4. Consulta de Estado y Polling (`app/app/api/get-job/route.ts`)
Permite al Frontend saber en qué fase está el procesamiento.

```typescript
export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const client = await pool.connect();
    try {
        // Obtiene proyecto y clips asociados
        const project = await client.query("SELECT * FROM projects WHERE id = $1", [id]);
        const clips = await client.query("SELECT * FROM clips WHERE project_id = $1", [id]);
        return NextResponse.json({ job: project.rows[0], clips: clips.rows });
    } finally {
        client.release();
    }
}
```

---

## 5. Frontend: Dashboard Principal (`app/app/page.tsx`)
Contiene la lógica de polling cada 3000ms y la gestión de estados de la UI.

```typescript
// Lógica de Polling en React
useEffect(() => {
  if (!jobId || jobStatus === 'COMPLETED' || view !== 'PROCESSING') return;

  const interval = setInterval(async () => {
    const res = await fetch(`/api/get-job?id=${jobId}`);
    const data = await res.json();
    if (data.job) {
      setJobStatus(data.job.status);
      if (data.job.status === 'COMPLETED') clearInterval(interval);
    }
    if (data.clips) setClips(data.clips);
  }, 3000);

  return () => clearInterval(interval);
}, [jobId, jobStatus, view]);
```

---

## 6. Puente de Backend (`scripts/ingest.py`)
Aunque es Python, es vital para entender cómo la web se comunica con el motor.

```python
import sys
import os
import psycopg2
from sovereign_core import ViralEngine

def main():
    project_id = sys.argv[1]
    video_url = sys.argv[2]
    
    # El core de procesamiento
    engine = ViralEngine()
    engine.process_video(video_url, project_id)

if __name__ == "__main__":
    main()
```

---

## 🚩 Posibles Puntos de Error para Análisis
1. **Timeouts de `exec`**: Si el script de Python tarda demasiado en arrancar.
2. **Conexiones de DB**: Posible agotamiento del pool si no se liberan clientes correctamente.
3. **Persistencia de Sesión**: Validación de `userId` en todas las rutas de API.
4. **Manejo de Archivos**: Rutas relativas vs absolutas en diferentes sistemas operativos.
