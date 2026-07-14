import { useParams, Link } from 'react-router-dom'
import { AdminTopBar } from '../components/TopBar'
import { SectionHeader } from '../components/SectionHeader'

export function MatchDetailPage() {
  const { gameId } = useParams<{ gameId: string }>()

  return (
    <div className="space-y-6">
      <AdminTopBar
        title={`Match #${gameId}`}
        subtitle="Match details and timeline"
        actions={
          <Link
            to="/admin/matches"
            className="text-[10px] font-mono text-gray-500 hover:text-gray-300 transition-colors"
          >
            {'<'} BACK
          </Link>
        }
      />

      {/* Placeholder sections for future implementation */}
      <SectionHeader title="Game Timeline" subtitle="Phase-by-phase breakdown" />
      <div className="border border-gray-800/50 rounded bg-gray-950 p-8 text-center">
        <div className="text-xs font-mono text-gray-600">
          Game timeline will be implemented when backend endpoints are available.
        </div>
        <div className="text-[10px] font-mono text-gray-700 mt-2">
          Future: Phase transitions, message flow, vote visualization
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 max-lg:grid-cols-1">
        <SectionHeader title="Replay" subtitle="Event replay" />
        <SectionHeader title="Signal AI Timeline" subtitle="AI scans and predictions" />
      </div>

      <div className="grid grid-cols-2 gap-3 max-lg:grid-cols-1">
        <div className="border border-gray-800/50 rounded bg-gray-950 p-6 text-center">
          <div className="text-[11px] font-mono text-gray-600">Replay viewer</div>
          <div className="text-[10px] font-mono text-gray-700 mt-1">
            Will embed replay engine for this match
          </div>
        </div>
        <div className="border border-gray-800/50 rounded bg-gray-950 p-6 text-center">
          <div className="text-[11px] font-mono text-gray-600">Signal AI timeline</div>
          <div className="text-[10px] font-mono text-gray-700 mt-1">
            Will show AI confidence over time
          </div>
        </div>
      </div>

      <SectionHeader title="Player Interaction Graph" subtitle="Social network analysis" />
      <div className="border border-gray-800/50 rounded bg-gray-950 p-8 text-center">
        <div className="text-xs font-mono text-gray-600">
          Player interaction graph will visualize messaging patterns and social dynamics.
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 max-lg:grid-cols-1">
        <SectionHeader title="Mission Progress" />
        <SectionHeader title="Voting History" />
      </div>

      <div className="grid grid-cols-2 gap-3 max-lg:grid-cols-1">
        <div className="border border-gray-800/50 rounded bg-gray-950 p-6 text-center">
          <div className="text-[11px] font-mono text-gray-600">Mission progress bars</div>
        </div>
        <div className="border border-gray-800/50 rounded bg-gray-950 p-6 text-center">
          <div className="text-[11px] font-mono text-gray-600">Voting history timeline</div>
        </div>
      </div>
    </div>
  )
}
