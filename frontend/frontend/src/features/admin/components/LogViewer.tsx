import { useState, useMemo } from 'react'
import type { LogEntry, LogLevel } from '../types/admin.types'

const LEVEL_COLORS: Record<LogLevel, string> = {
  INFO: 'text-blue-400',
  WARN: 'text-yellow-400',
  ERROR: 'text-red-400',
  DEBUG: 'text-gray-500',
}

const LEVEL_BG: Record<LogLevel, string> = {
  INFO: 'bg-blue-500/10',
  WARN: 'bg-yellow-500/10',
  ERROR: 'bg-red-500/10',
  DEBUG: 'bg-gray-500/10',
}

interface LogViewerProps {
  entries: LogEntry[]
}

export function LogViewer({ entries }: LogViewerProps) {
  const [filter, setFilter] = useState<LogLevel | 'ALL'>('ALL')
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    return entries.filter((entry) => {
      if (filter !== 'ALL' && entry.level !== filter) return false
      if (search && !entry.message.toLowerCase().includes(search.toLowerCase()) && !entry.source.toLowerCase().includes(search.toLowerCase())) return false
      return true
    })
  }, [entries, filter, search])

  return (
    <div className="border border-gray-800/50 rounded bg-gray-950">
      {/* Toolbar */}
      <div className="px-3 py-2 border-b border-gray-800/50 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1">
          {(['ALL', 'ERROR', 'WARN', 'INFO', 'DEBUG'] as const).map((level) => (
            <button
              key={level}
              onClick={() => setFilter(level)}
              className={`px-2 py-0.5 text-[10px] font-mono rounded transition-colors ${
                filter === level
                  ? level === 'ALL'
                    ? 'bg-gray-700 text-gray-200'
                    : `${LEVEL_BG[level]} ${LEVEL_COLORS[level]}`
                  : 'text-gray-600 hover:text-gray-400'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Filter logs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-2 py-1 text-[11px] font-mono bg-gray-900 border border-gray-800 rounded text-gray-300 placeholder-gray-700 focus:outline-none focus:border-gray-600 flex-1 min-w-[120px]"
          aria-label="Filter logs"
        />
        <span className="text-[10px] font-mono text-gray-700">
          {filtered.length}/{entries.length}
        </span>
      </div>

      {/* Log entries */}
      <div className="max-h-[500px] overflow-y-auto font-mono">
        {filtered.length === 0 && (
          <div className="px-3 py-8 text-center text-[11px] text-gray-600">
            No matching log entries
          </div>
        )}
        {filtered.map((entry) => (
          <div
            key={entry.id}
            className="px-3 py-1.5 border-b border-gray-800/20 hover:bg-gray-800/20 transition-colors flex items-start gap-2"
          >
            <span className="text-[10px] text-gray-700 shrink-0 w-16">
              {new Date(entry.timestamp).toLocaleTimeString()}
            </span>
            <span
              className={`text-[10px] font-bold shrink-0 w-10 ${LEVEL_COLORS[entry.level]}`}
            >
              {entry.level}
            </span>
            <span className="text-[10px] text-gray-500 shrink-0 w-24 truncate">
              {entry.source}
            </span>
            <span className="text-[11px] text-gray-300 flex-1 min-w-0">
              {entry.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
