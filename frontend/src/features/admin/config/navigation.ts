import type { AdminNavSection } from '../types/admin.types'

export const ADMIN_NAV_SECTIONS: AdminNavSection[] = [
  {
    id: 'overview',
    label: 'Overview',
    icon: '\u25C8',
    children: [
      { id: 'overview-dashboard', label: 'Dashboard', path: '/admin', icon: '\u25C8' },
      { id: 'overview-activity', label: 'Activity', path: '/admin/activity', icon: '\u25CB' },
    ],
  },
  {
    id: 'games',
    label: 'Games',
    icon: '\u2B50',
    children: [
      { id: 'games-active', label: 'Active Matches', path: '/admin/matches', icon: '\u25CF' },
      { id: 'games-history', label: 'History', path: '/admin/matches/history', icon: '\u25CB' },
    ],
  },
  {
    id: 'infrastructure',
    label: 'Infrastructure',
    icon: '\u2630',
    children: [
      { id: 'infra-services', label: 'Services', path: '/admin/infrastructure', icon: '\u25CF' },
      { id: 'infra-redis', label: 'Redis', path: '/admin/infrastructure/redis', icon: '\u25CB' },
      { id: 'infra-postgres', label: 'PostgreSQL', path: '/admin/infrastructure/postgres', icon: '\u25CB' },
    ],
  },
  {
    id: 'replay',
    label: 'Replay Engine',
    icon: '\u23EA',
    children: [
      { id: 'replay-overview', label: 'Overview', path: '/admin/replay', icon: '\u25CF' },
    ],
  },
  {
    id: 'signal-ai',
    label: 'Signal AI',
    icon: '\u{1F916}',
    children: [
      { id: 'signal-ai-overview', label: 'Overview', path: '/admin/signal-ai', icon: '\u25CF' },
      { id: 'signal-ai-model', label: 'Model', path: '/admin/signal-ai/model', icon: '\u25CB' },
    ],
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: '\u{1F4CA}',
    children: [
      { id: 'analytics-overview', label: 'Overview', path: '/admin/analytics', icon: '\u25CF' },
    ],
  },
  {
    id: 'logs',
    label: 'Logs',
    icon: '\u{1F4DC}',
    children: [
      { id: 'logs-viewer', label: 'Viewer', path: '/admin/logs', icon: '\u25CF' },
    ],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: '\u2699\uFE0F',
    children: [
      { id: 'settings-general', label: 'General', path: '/admin/settings', icon: '\u25CB' },
    ],
  },
]
