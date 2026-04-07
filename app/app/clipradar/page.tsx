'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Sidebar } from '@/components/sidebar'
import { Radar, Search, TrendingUp, DollarSign, Sparkles, Globe, Languages, Play } from 'lucide-react'
import { trackEvent } from '@/lib/analytics'

interface VideoData {
  id: string
  title: string
  channel: string
  thumbnail: string
  publishedAt: string
  views: number
  likes: number
  comments: number
  engagement: number
  durSecs: number
  viralScore: number
  clipsEstimados: number
  rpm: number
  grade: 'S' | 'A' | 'B' | 'C'
  url: string
}

interface YouTubeStats {
  viewCount?: string
  likeCount?: string
  commentCount?: string
}

interface YouTubeSnippet {
  title?: string
  channelTitle?: string
  publishedAt?: string
  thumbnails?: {
    high?: { url?: string }
  }
}

interface YouTubeItem {
  id: string
  statistics?: YouTubeStats
  contentDetails?: { duration?: string }
  snippet?: YouTubeSnippet
}

const NICHOS_ES = [
  'entretenimiento espanol',
  'ibai gaming stream',
  'concurso desafio viral',
  'humor espana viral',
  'finanzas inversion',
  'fitness deporte espanol',
  'tecnologia ia espanol',
]

const NICHOS_EN = [
  'personal finance',
  'investing for beginners',
  'ai tools for business',
  'side hustle ideas',
  'productivity systems',
  'software engineering career',
  'credit cards and debt',
]

function parseDuration(iso: string): number {
  const m = iso.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/)
  return m ? (parseInt(m[1] || '0', 10) * 3600 + parseInt(m[2] || '0', 10) * 60 + parseInt(m[3] || '0', 10)) : 0
}

function compact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

function dur(secs: number): string {
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  const s = secs % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

function getAgo(dateStr: string): string {
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  if (diff < 604800) return `${Math.floor(diff / 86400)}d`
  return `${Math.floor(diff / 604800)}w`
}

function estimateRPM(title: string, engagement: number, views: number): number {
  const t = title.toLowerCase()
  let base = 1.5
  if (/finanz|invest|money|trading|credit|tax/.test(t)) base = 6.8
  else if (/tech|softw|ai|program|coding/.test(t)) base = 5.2
  else if (/fitness|health|gym|diet/.test(t)) base = 3.6
  else if (/travel|tourism/.test(t)) base = 3.0
  else if (/gaming|stream|twitch/.test(t)) base = 2.2
  else if (/humor|funny|meme|joke/.test(t)) base = 1.3

  const em = engagement > 5 ? 1.3 : engagement > 2 ? 1.1 : 0.92
  const vm = views > 1_000_000 ? 1.2 : views > 100_000 ? 1.08 : 0.95
  return Number((base * em * vm).toFixed(2))
}

function viralScore(views: number, likes: number, comments: number, engagement: number, durSecs: number, publishedAt: string): number {
  const viewScore = Math.min((Math.log10(Math.max(views, 1)) / 8) * 35, 35)
  const engScore = Math.min((engagement / 8) * 30, 30)
  const likeRatio = views > 0 ? (likes / views) * 100 : 0
  const likeScore = Math.min((likeRatio / 5) * 20, 20)
  const hours = (Date.now() - new Date(publishedAt).getTime()) / 3_600_000
  const freshness = hours < 24 ? 15 : hours < 72 ? 10 : hours < 168 ? 5 : 0
  const m = durSecs / 60
  const durScore = m >= 10 && m <= 60 ? 10 : m > 60 ? 5 : 3
  const commentRatio = views > 0 ? (comments / views) * 1000 : 0
  const commentScore = Math.min(commentRatio * 2, 10)
  return Math.min(Math.round(viewScore + engScore + likeScore + freshness + durScore + commentScore), 100)
}

function enrich(video: YouTubeItem): VideoData | null {
  const s = video.statistics || {}
  const views = parseInt(s.viewCount || '0', 10)
  const likes = parseInt(s.likeCount || '0', 10)
  const comments = parseInt(s.commentCount || '0', 10)
  if (views < 10000) return null

  const engagement = views > 0 ? ((likes + comments) / views) * 100 : 0
  const durSecs = parseDuration(video.contentDetails?.duration || 'PT0S')
  const publishedAt = video.snippet?.publishedAt || new Date().toISOString()
  const score = viralScore(views, likes, comments, engagement, durSecs, publishedAt)

  let grade: VideoData['grade'] = 'C'
  if (score >= 80) grade = 'S'
  else if (score >= 65) grade = 'A'
  else if (score >= 45) grade = 'B'

  return {
    id: video.id,
    title: video.snippet?.title || 'Untitled',
    channel: video.snippet?.channelTitle || 'Unknown channel',
    thumbnail: video.snippet?.thumbnails?.high?.url || '',
    publishedAt,
    views,
    likes,
    comments,
    engagement,
    durSecs,
    viralScore: score,
    clipsEstimados: Math.max(1, Math.floor(durSecs / 120)),
    rpm: estimateRPM(video.snippet?.title || '', engagement, views),
    grade,
    url: `https://youtube.com/watch?v=${video.id}`,
  }
}

export default function ClipRadarPage() {
  const router = useRouter()
  const [lang, setLang] = useState<'es' | 'en' | 'any'>('es')
  const [query, setQuery] = useState('entretenimiento espanol')
  const [items, setItems] = useState<VideoData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const presets = useMemo(() => {
    if (lang === 'en') return NICHOS_EN
    if (lang === 'any') return [...NICHOS_EN.slice(0, 4), ...NICHOS_ES.slice(0, 4)]
    return NICHOS_ES
  }, [lang])

  const totals = useMemo(() => {
    const totalViews = items.reduce((acc, v) => acc + v.views, 0)
    const totalClips = items.reduce((acc, v) => acc + v.clipsEstimados, 0)
    const avgRpm = items.length ? (items.reduce((acc, v) => acc + v.rpm, 0) / items.length).toFixed(2) : '0.00'
    return { totalViews, totalClips, avgRpm }
  }, [items])

  const search = async () => {
    setLoading(true)
    setError('')
    setItems([])
    trackEvent('clipradar_search_started', { lang, query })

    try {
      const res = await fetch(`/api/youtube?nicho=${encodeURIComponent(query)}&lang=${lang}&days=30`)
      const data = await res.json()
      if (!res.ok || data.error) throw new Error(data.error || 'Error consultando YouTube')

      const enriched = (data.items || []).map(enrich).filter(Boolean) as VideoData[]
      enriched.sort((a, b) => b.viralScore - a.viralScore)
      setItems(enriched)
      trackEvent('clipradar_search_completed', { lang, query, results_count: enriched.length })
      if (!enriched.length) setError('No hay resultados con suficiente señal viral para este filtro.')
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Error inesperado'
      setError(message)
      trackEvent('clipradar_search_failed', { lang, query })
    } finally {
      setLoading(false)
    }
  }

  const createMotorAJob = async (videoUrl: string) => {
    try {
      trackEvent('clipradar_motor_a_job_create_clicked', { source_url: videoUrl, niche: query })
      const res = await fetch('/api/create-job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: videoUrl,
          creationSystem: 'viral_motor_a',
          viralNiche: query,
          viralDryRun: false,
        }),
      })
      const data = await res.json()
      if (!res.ok || data.error) throw new Error(data.error || 'No se pudo crear el job')
      if (data.jobId) {
        trackEvent('clipradar_motor_a_job_created', { job_id: data.jobId, niche: query })
      }
      if (data.jobId) router.push(`/projects/${data.jobId}`)
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Error creando job'
      setError(message)
      trackEvent('clipradar_motor_a_job_create_failed', { niche: query })
    }
  }

  return (
    <div className="min-h-screen bg-[#0b0f16] text-white">
      <Sidebar />
      <main className="ml-[60px] p-6 md:p-10">
        <div className="max-w-7xl mx-auto space-y-6">
          <section className="rounded-3xl border border-[#1f2937] bg-gradient-to-br from-[#0f172a] via-[#111827] to-[#0b1220] p-6 md:p-8 shadow-2xl">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <div className="inline-flex items-center gap-2 rounded-lg border border-[#374151] bg-[#111827]/70 px-3 py-1 text-xs text-[#93c5fd]">
                  <Radar className="h-3.5 w-3.5" />
                  ClipRadar
                </div>
                <h1 className="mt-3 text-2xl md:text-4xl font-black tracking-tight">YouTube Viral Discovery para Motor A</h1>
                <p className="mt-2 text-sm text-[#94a3b8] max-w-2xl">Busca videos en espanol o ingles, analiza viralidad y monetizacion estimada, y lanza el procesamiento de Motor A en un clic.</p>
              </div>
              <div className="rounded-xl border border-[#1f2937] bg-[#0b1220] px-4 py-3 text-sm">
                <div className="text-[#93c5fd] font-semibold">Soporte de idioma</div>
                <div className="text-[#94a3b8] mt-1">ES, EN y mixto</div>
              </div>
            </div>

            <div className="mt-6 grid gap-3 md:grid-cols-[190px_1fr_170px]">
              <div className="rounded-xl border border-[#243147] bg-[#0b1220] px-3 py-2">
                <div className="mb-1 text-[11px] uppercase tracking-wide text-[#94a3b8]">Idioma</div>
                <div className="relative">
                  <Languages className="pointer-events-none absolute left-2 top-2.5 h-4 w-4 text-[#64748b]" />
                  <select
                    value={lang}
                    onChange={(e) => {
                      const v = e.target.value as 'es' | 'en' | 'any'
                      setLang(v)
                      setQuery(v === 'en' ? 'personal finance' : v === 'any' ? 'viral videos' : 'entretenimiento espanol')
                    }}
                    className="w-full appearance-none rounded-md bg-transparent pl-8 pr-2 py-2 text-sm outline-none"
                  >
                    <option value="es">Espanol</option>
                    <option value="en">English</option>
                    <option value="any">Mixto</option>
                  </select>
                </div>
              </div>

              <div className="rounded-xl border border-[#243147] bg-[#0b1220] px-3 py-2">
                <div className="mb-1 text-[11px] uppercase tracking-wide text-[#94a3b8]">Busqueda</div>
                <div className="relative">
                  <Search className="pointer-events-none absolute left-2 top-2.5 h-4 w-4 text-[#64748b]" />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="ej. ibai gaming stream / personal finance"
                    className="w-full rounded-md bg-transparent pl-8 pr-2 py-2 text-sm outline-none"
                  />
                </div>
              </div>

              <button
                onClick={search}
                disabled={loading}
                className="rounded-xl bg-[#f97316] hover:bg-[#ea580c] disabled:opacity-60 text-black font-bold px-4 py-2 inline-flex items-center justify-center gap-2"
              >
                <TrendingUp className="h-4 w-4" />
                {loading ? 'Analizando...' : 'Buscar virales'}
              </button>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {presets.map((p) => (
                <button
                  key={p}
                  onClick={() => setQuery(p)}
                  className="rounded-lg border border-[#27354d] bg-[#0b1220] px-3 py-1.5 text-xs text-[#cbd5e1] hover:border-[#60a5fa]"
                >
                  {p}
                </button>
              ))}
            </div>
          </section>

          {error && <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">{error}</div>}

          {items.length > 0 && (
            <section className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-[#243147] bg-[#0b1220] p-4">
                <div className="text-xs uppercase text-[#94a3b8]">Videos</div>
                <div className="mt-1 text-2xl font-black">{items.length}</div>
              </div>
              <div className="rounded-xl border border-[#243147] bg-[#0b1220] p-4">
                <div className="text-xs uppercase text-[#94a3b8]">Clips potenciales</div>
                <div className="mt-1 text-2xl font-black">{totals.totalClips}</div>
              </div>
              <div className="rounded-xl border border-[#243147] bg-[#0b1220] p-4">
                <div className="text-xs uppercase text-[#94a3b8]">RPM medio</div>
                <div className="mt-1 text-2xl font-black">€{totals.avgRpm}</div>
              </div>
            </section>
          )}

          <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {items.map((v) => (
              <article key={v.id} className="overflow-hidden rounded-2xl border border-[#1f2937] bg-[#0b1220]">
                <div className="relative aspect-video bg-black">
                  <img src={v.thumbnail || `https://i.ytimg.com/vi/${v.id}/hqdefault.jpg`} alt={v.title} className="h-full w-full object-cover" />
                  <span className="absolute bottom-2 right-2 rounded bg-black/70 px-2 py-1 text-xs">{dur(v.durSecs)}</span>
                  <span className="absolute top-2 left-2 rounded bg-orange-500/85 px-2 py-1 text-xs font-semibold">{v.grade} · {v.viralScore}</span>
                </div>

                <div className="p-4">
                  <h3 className="line-clamp-2 font-semibold text-sm">{v.title}</h3>
                  <p className="mt-1 text-xs text-[#94a3b8]">{v.channel} · {getAgo(v.publishedAt)}</p>

                  <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-lg border border-[#243147] bg-[#0f172a] p-2">
                      <div className="text-[10px] text-[#94a3b8]">Views</div>
                      <div className="text-sm font-bold">{compact(v.views)}</div>
                    </div>
                    <div className="rounded-lg border border-[#243147] bg-[#0f172a] p-2">
                      <div className="text-[10px] text-[#94a3b8]">Eng</div>
                      <div className="text-sm font-bold">{v.engagement.toFixed(2)}%</div>
                    </div>
                    <div className="rounded-lg border border-[#243147] bg-[#0f172a] p-2">
                      <div className="text-[10px] text-[#94a3b8]">RPM</div>
                      <div className="text-sm font-bold">€{v.rpm.toFixed(2)}</div>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between rounded-lg border border-[#243147] bg-[#0f172a] px-3 py-2">
                    <span className="text-xs text-[#94a3b8] inline-flex items-center gap-1"><Sparkles className="h-3.5 w-3.5" /> ~{v.clipsEstimados} clips</span>
                    <span className="text-xs text-[#fbbf24] inline-flex items-center gap-1"><DollarSign className="h-3.5 w-3.5" /> monetizable</span>
                  </div>

                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={() => createMotorAJob(v.url)}
                      className="flex-1 rounded-lg bg-[#22c55e] hover:bg-[#16a34a] px-3 py-2 text-sm font-bold text-black"
                    >
                      Generar Motor A
                    </button>
                    <button
                      onClick={() => window.open(v.url, '_blank')}
                      className="rounded-lg border border-[#243147] bg-[#0f172a] px-3 py-2"
                      aria-label="Ver en YouTube"
                    >
                      <Play className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </section>

          {!loading && !items.length && !error && (
            <section className="rounded-2xl border border-[#1f2937] bg-[#0b1220] p-8 text-center text-[#94a3b8]">
              <Globe className="mx-auto h-8 w-8 mb-2" />
              Elige idioma y nicho para descubrir videos con mayor potencial para Motor A.
            </section>
          )}
        </div>
      </main>
    </div>
  )
}
