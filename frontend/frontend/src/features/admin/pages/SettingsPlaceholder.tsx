import { AdminTopBar } from '../components/TopBar'
import { SectionHeader } from '../components/SectionHeader'

export function SettingsPlaceholder() {
  return (
    <div className="space-y-6">
      <AdminTopBar
        title="Settings"
        subtitle="Platform configuration"
      />

      <SectionHeader title="General" subtitle="Platform settings (coming soon)" />
      <div className="border border-gray-800/50 rounded bg-gray-950 p-8 text-center">
        <div className="text-xs font-mono text-gray-600">
          Settings page will be implemented when backend configuration endpoints are available.
        </div>
      </div>
    </div>
  )
}
