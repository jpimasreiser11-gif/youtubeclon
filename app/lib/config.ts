import path from 'path';

/**
 * Configuración centralizada de la aplicación
 * Lee variables de entorno y provee paths absolutos
 */
const config = {
    // Paths principales
    rootDir: process.env.PROJECT_ROOT || 'c:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide',
    pythonPath: process.env.PYTHON_PATH || null,
    storagePath: process.env.STORAGE_PATH || null,

    // Configuración de logging
    logLevel: process.env.LOG_LEVEL || 'info',

    // Configuración de DB (desde archivo db.ts)
    database: {
        host: process.env.POSTGRES_HOST || '127.0.0.1',
        port: parseInt(process.env.POSTGRES_PORT || '5432'),
        database: process.env.POSTGRES_DB || 'edumind_viral',
        user: process.env.POSTGRES_USER || 'postgres',
        password: process.env.POSTGRES_PASSWORD || 'password',
    },

    // APIs
    geminiApiKey: process.env.GEMINI_API_KEY || '',

    // Timeouts (en milisegundos)
    timeouts: {
        subtitles: parseInt(process.env.TIMEOUT_SUBTITLES || '300000'), // 5 min
        audio: parseInt(process.env.TIMEOUT_AUDIO || '600000'), // 10 min
        smartCrop: parseInt(process.env.TIMEOUT_SMART_CROP || '900000'), // 15 min
        ingest: parseInt(process.env.TIMEOUT_INGEST || '1800000'), // 30 min
    },

    // Paths derivados (computed properties)
    get pythonExecutable(): string {
        if (this.pythonPath) return this.pythonPath;
        // Use system python where dependencies are installed
        return 'C:\\Users\\jpima\\AppData\\Local\\Programs\\Python\\Python312\\python.exe';
    },

    get scriptsDir(): string {
        return path.join(this.rootDir, 'scripts');
    },

    get storageBase(): string {
        if (this.storagePath) return this.storagePath;
        return path.join(this.rootDir, 'app', 'storage');
    },

    get clipsDir(): string {
        return path.join(this.storageBase, 'clips');
    },

    get subtitledDir(): string {
        return path.join(this.storageBase, 'subtitled');
    },

    get enhancedDir(): string {
        return path.join(this.storageBase, 'enhanced');
    },

    get sourceDir(): string {
        return path.join(this.storageBase, 'source');
    },

    get previewsDir(): string {
        return path.join(this.storageBase, 'previews');
    },

    // Scripts paths
    scripts: {
        get sovereignCore(): string {
            return path.join(config.scriptsDir, 'sovereign_core.py');
        },
        get cliRunner(): string {
            return path.join(config.scriptsDir, 'cli_runner.py');
        },
        get ingest(): string {
            return path.join(config.scriptsDir, 'ingest.py');
        },
        get clipper(): string {
            return path.join(config.scriptsDir, 'clipper.py');
        },
        get renderWithSubtitles(): string {
            return path.join(config.scriptsDir, 'render_with_subtitles.py');
        },
        get pilSubtitleRenderer(): string {
            return path.join(config.scriptsDir, 'pil_subtitle_renderer.py');
        },
        get smartCrop(): string {
            return path.join(config.scriptsDir, 'smart_crop.py');
        },
        get audioProcessor(): string {
            return path.join(config.scriptsDir, 'audio_processor.py');
        },
        get uploadYoutube(): string {
            return path.join(config.scriptsDir, 'upload_youtube.py');
        },
        get uploadTiktok(): string {
            return path.join(config.scriptsDir, 'upload_with_fallback.py');
        },
        get scheduleUploads(): string {
            return path.join(config.scriptsDir, 'schedule_uploads.py');
        }
    }
};

export default config;
