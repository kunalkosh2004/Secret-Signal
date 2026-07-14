import { useState, useEffect } from 'react'
import { AdminTopBar } from '../components/TopBar'
import { LogViewer } from '../components/LogViewer'
import { fetchLogEntries } from '../services/adminApi'

import type { LogEntry } from '../types/admin.types'

export function LogsPage() {
  const [entries, setEntries] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLogEntries().then((e) => {
      setEntries(e)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xs font-mono text-gray-600 animate-pulse">
          <span className="text-accent">{'//'}</span> Loading logs...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <AdminTopBar
        title="Log Viewer"
        subtitle="Structured application logs"
      />
      <LogViewer entries={entries} />
    </div>
  )
}
