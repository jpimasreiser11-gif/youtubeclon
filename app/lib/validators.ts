import { z } from 'zod';

const NIL_UUID = '00000000-0000-0000-0000-000000000000';
const NonNilUuidSchema = z.string()
    .uuid('clipId debe ser un UUID válido')
    .refine((value) => value !== NIL_UUID, 'clipId no puede ser UUID nulo');

// Schema para procesamiento de videos
export const ProcessVideoSchema = z.object({
    url: z.string()
        .url('URL inválida')
        .refine((url) => {
            return url.includes('youtube.com') || url.includes('youtu.be');
        }, 'Solo se permiten URLs de YouTube'),
    title: z.string().max(200).optional(),
    thumbnail: z.string().url().optional(),
    options: z.object({
        smartCrop: z.boolean().optional(),
        audioPro: z.boolean().optional(),
        subtitles: z.boolean().optional(),
    }).optional()
});

// Schema para agregar subtítulos
export const AddSubtitlesSchema = z.object({
    clipId: NonNilUuidSchema,
    style: z.enum(['tiktok', 'youtube_shorts', 'instagram_reels', 'hormozi', 'minimalist', 'minimal', 'clean', 'default'])
        .default('tiktok'),
    customStyle: z.object({
        fontsize: z.number().min(20).max(200).optional(),
        color: z.string().optional(),
        position: z.tuple([z.string(), z.string()]).optional(),
    }).optional()
});

// Schema para mejorar audio
export const EnhanceAudioSchema = z.object({
    clipId: NonNilUuidSchema,
    targetLufs: z.number().min(-20).max(-10).default(-14),
    targetTp: z.number().min(-3).max(0).default(-1),
});

// Schema para smart crop
export const SmartCropSchema = z.object({
    clipId: NonNilUuidSchema,
    alpha: z.number().min(0).max(1).default(0.1),
});

// Schema para acciones enterprise
export const EnterpriseActionSchema = z.object({
    clipId: NonNilUuidSchema,
    action: z.enum(['reframe', 'clean_speech', 'add_broll', 'enhance_all']),
    options: z.record(z.string(), z.unknown()).optional()
});

// Schema para publicación
export const PublishClipSchema = z.object({
    clipId: NonNilUuidSchema,
    platform: z.enum(['youtube', 'tiktok', 'instagram']),
    scheduledAt: z.string().datetime().optional(), // ISO 8601 format
    metadata: z.object({
        title: z.string().min(1).max(200),
        description: z.string().max(5000).optional(),
        tags: z.string().max(500).optional(),
        privacy: z.enum(['public', 'private', 'unlisted']).default('private'),
    })
});

// Schema para actualizar clip
export const UpdateClipSchema = z.object({
    clipId: NonNilUuidSchema,
    updates: z.object({
        title: z.string().max(200).optional(),
        startTime: z.number().min(0).optional(),
        endTime: z.number().min(0).optional(),
        viralityScore: z.number().min(0).max(100).optional(),
    })
});

// Helper para validar y retornar errores formateados
export function validateSchema<T>(schema: z.ZodSchema<T>, data: unknown): { success: true; data: T } | { success: false; errors: z.ZodError } {
    try {
        const validated = schema.parse(data);
        return { success: true, data: validated };
    } catch (error) {
        if (error instanceof z.ZodError) {
            return { success: false, errors: error };
        }
        throw error;
    }
}

// Helper para formatear errores de Zod
export function formatZodErrors(zodError: z.ZodError): Record<string, string> {
    const formatted: Record<string, string> = {};

    zodError.issues.forEach((issue) => {
        const path = issue.path.join('.');
        formatted[path] = issue.message;
    });

    return formatted;
}
