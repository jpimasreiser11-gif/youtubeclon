# YouTube Automation Pro - MASTER Design System

## Product framing
- Product: Multi-channel YouTube automation dashboard.
- UX target: fast operator workflows, high signal density, low cognitive friction.
- Visual direction: dark premium + neon accents + glass panels.

## Foundations

### Color tokens
- Background: `#05010b`, `#0a0314`, elevated `#1e0938`
- Primary accent: `#a855f7` (hover `#c084fc`, dim `#7e22ce`)
- State:
  - success `#00E5FF`
  - warning `#FBBF24`
  - error `#F43F5E`
  - info `#38BDF8`
- Text:
  - primary `#f8fafc`
  - secondary `#c4b5fd`
  - muted `#8b5cf6`

### Typography
- Base: Inter.
- Numeric/data: JetBrains Mono.
- Hierarchy:
  - H1 24/700
  - H2 20/700
  - H3 18/700
  - body 14/400
  - caption 12/500

### Spacing and radius
- 4, 8, 12, 16, 24, 32 scale.
- Radius: 8/12/16/20.

### Elevation
- Surface border + soft shadow.
- Glass cards for analytics and activity areas.
- Hover lift max 3px to preserve stability.

## Layout system
- Fixed sidebar (`260px`) + fixed top header (`64px`) + fluid content.
- Desktop-first with sidebar collapse under 1024px.
- Data grids:
  - KPI strip: 4 columns
  - channel cards: 3 columns
  - dual panel workflows: `340px + 1fr`

## Core components
- Sidebar navigation (7 tabs).
- Header with context title + runtime status badge.
- Card/Card-glass.
- KPI stat card.
- Channel card with brand accent.
- Status badges (ok/running/error/pending).
- Buttons:
  - primary (action)
  - secondary (safe action)
  - danger (destructive)
- Form controls:
  - input/select/checkbox with consistent focus ring.
- Activity timeline item.
- Toast stack (success/info/error).
- Skeleton loaders and empty states.

## Interaction rules
- Primary action always singular and obvious per screen.
- Keep operator loops <= 2 clicks for high-frequency actions.
- Optimistic UI only for safe operations; for pipeline actions always reconcile with backend status.
- Polling surfaces must show "in progress" state at all times.

## Accessibility baseline
- Contrast >= WCAG AA for body text.
- Focus-visible ring on all interactive controls.
- Keyboard path: sidebar -> page CTA -> table/list actions.
- Do not use color as the only status cue (icon + text + color).

## Information architecture (7 tabs)
1. Dashboard: KPI + health + recent activity.
2. Channels: per-channel configuration and identity.
3. Ideas: ideation engine with strategy filters.
4. Generator: one-click pipeline trigger and live logs.
5. Library: generated videos and publish-ready states.
6. Scheduler: publication timeline and cancel flow.
7. Settings: environment and provider controls.

## Channel theming strategy
- Shared global shell + per-channel accent identity.
- Channel palettes and tone live in `design-system/channels/*.md`.
- Reuse component structure; only identity layer changes (accent, copy tone, thumbnail intent).

