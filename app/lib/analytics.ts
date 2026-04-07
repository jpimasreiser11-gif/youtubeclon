type Primitive = string | number | boolean | null;
type AnalyticsValue = Primitive | Primitive[];

export type AnalyticsProps = Record<string, AnalyticsValue>;

declare global {
  interface Window {
    dataLayer?: Array<Record<string, unknown>>;
    gtag?: (...args: unknown[]) => void;
  }
}

function normalizeProps(props: AnalyticsProps = {}): Record<string, unknown> {
  const output: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(props)) {
    if (Array.isArray(value)) {
      output[key] = value.filter((item) => item !== undefined);
      continue;
    }
    output[key] = value;
  }
  return output;
}

export function trackEvent(eventName: string, props: AnalyticsProps = {}): void {
  if (typeof window === 'undefined') return;

  const normalized = normalizeProps(props);

  if (typeof window.gtag === 'function') {
    window.gtag('event', eventName, normalized);
  }

  if (Array.isArray(window.dataLayer)) {
    window.dataLayer.push({ event: eventName, ...normalized });
  }

  if (process.env.NODE_ENV !== 'production') {
    // Keep visibility in development even without GA/GTM connected.
    console.debug('[analytics]', eventName, normalized);
  }
}
