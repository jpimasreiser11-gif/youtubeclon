import { NextRequest, NextResponse } from 'next/server'

type SearchItem = {
  id?: { videoId?: string }
}

function resolveLocale(lang: string) {
  const normalized = (lang || 'es').toLowerCase()
  if (normalized === 'en') {
    return { relevanceLanguage: 'en', regionCode: 'US' }
  }
  if (normalized === 'any') {
    return { relevanceLanguage: '', regionCode: '' }
  }
  return { relevanceLanguage: 'es', regionCode: 'ES' }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const nicho = searchParams.get('nicho') || 'entretenimiento espanol'
  const lang = searchParams.get('lang') || 'es'
  const days = Number(searchParams.get('days') || '30')
  const apiKey = process.env.YOUTUBE_API_KEY

  if (!apiKey) {
    return NextResponse.json({ error: 'API key no configurada' }, { status: 500 })
  }

  try {
    const fechaLimite = new Date()
    fechaLimite.setDate(fechaLimite.getDate() - Math.min(60, Math.max(3, days)))
    const publishedAfter = fechaLimite.toISOString()

    const locale = resolveLocale(lang)

    const searchUrl = new URL('https://www.googleapis.com/youtube/v3/search')
    searchUrl.searchParams.set('part', 'snippet')
    searchUrl.searchParams.set('q', nicho)
    searchUrl.searchParams.set('type', 'video')
    searchUrl.searchParams.set('order', 'viewCount')
    searchUrl.searchParams.set('maxResults', '20')
    if (locale.relevanceLanguage) searchUrl.searchParams.set('relevanceLanguage', locale.relevanceLanguage)
    if (locale.regionCode) searchUrl.searchParams.set('regionCode', locale.regionCode)
    searchUrl.searchParams.set('publishedAfter', publishedAfter)
    searchUrl.searchParams.set('videoDuration', 'medium')
    searchUrl.searchParams.set('key', apiKey)

    const searchRes = await fetch(searchUrl.toString(), { cache: 'no-store' })
    if (!searchRes.ok) {
      const err = await searchRes.json().catch(() => ({}))
      return NextResponse.json(
        { error: err.error?.message || 'Error YouTube API' },
        { status: searchRes.status }
      )
    }

    const searchData = await searchRes.json()
    const videoIds = ((searchData.items || []) as SearchItem[])
      .map((i) => i?.id?.videoId)
      .filter(Boolean)
      .join(',')

    if (!videoIds) {
      return NextResponse.json({ items: [] })
    }

    const statsUrl = new URL('https://www.googleapis.com/youtube/v3/videos')
    statsUrl.searchParams.set('part', 'statistics,contentDetails,snippet')
    statsUrl.searchParams.set('id', videoIds)
    statsUrl.searchParams.set('key', apiKey)

    const statsRes = await fetch(statsUrl.toString(), { cache: 'no-store' })
    if (!statsRes.ok) {
      const err = await statsRes.json().catch(() => ({}))
      return NextResponse.json(
        { error: err.error?.message || 'Error YouTube API stats' },
        { status: statsRes.status }
      )
    }

    const statsData = await statsRes.json()
    return NextResponse.json({ items: statsData.items || [] })
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Error interno'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
