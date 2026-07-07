import { GamePreviewCard } from './GamePreviewCard'
import { PlayerAvatar } from './PlayerAvatar'

export const GamePreview = () => {
  return (
    <section className="py-20 bg-gray-100 border-t border-gray-300/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-center text-2xl font-bold tracking-tight text-gray-900 font-mono">
          <span className="text-accent">&gt;</span> See How It Works
        </h2>
        <p className="mt-4 text-center text-base text-gray-600 max-w-2xl mx-auto">
          A preview of a game round showing the Coordinator&apos;s secret mission,
          player interactions, and suspicion tracking.
        </p>
        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-4">
            <h3 className="text-lg font-mono tracking-wider text-gray-700 border-b border-gray-400/30 pb-2">
              <span className="text-accent">#</span> PLAYERS
            </h3>
            <div className="space-y-2">
              <PlayerAvatar name="Aman" isCoordinator={false} />
              <PlayerAvatar name="Riya" isCoordinator={false} />
              <PlayerAvatar name="Kunal" isCoordinator={false} />
              <PlayerAvatar name="Priya" isCoordinator={true} />
              <PlayerAvatar name="Arjun" isCoordinator={false} />
            </div>
          </div>
          <div className="space-y-4">
            <h3 className="text-lg font-mono tracking-wider text-gray-700 border-b border-gray-400/30 pb-2">
              <span className="text-accent">#</span> CHAT LOG
            </h3>
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 h-7 w-7 bg-gray-200 rounded flex items-center justify-center font-mono text-xs text-gray-700">A</div>
                <div>
                  <p className="text-xs font-mono text-gray-700">Aman</p>
                  <p className="text-sm text-gray-600">I would love to visit Japan.</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 h-7 w-7 bg-gray-200 rounded flex items-center justify-center font-mono text-xs text-gray-700">R</div>
                <div>
                  <p className="text-xs font-mono text-gray-700">Riya</p>
                  <p className="text-sm text-gray-600">Switzerland looks beautiful.</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 h-7 w-7 bg-gray-200 rounded flex items-center justify-center font-mono text-xs text-gray-700">K</div>
                <div>
                  <p className="text-xs font-mono text-gray-700">Kunal</p>
                  <p className="text-sm text-gray-600">What about somewhere warmer?</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 h-7 w-7 bg-gray-200 rounded flex items-center justify-center font-mono text-xs text-gray-700">P</div>
                <div>
                  <p className="text-xs font-mono text-gray-700">Priya</p>
                  <p className="text-sm text-gray-600">I think I&apos;ll stay in India.</p>
                </div>
              </div>
            </div>
          </div>
          <GamePreviewCard
            title="SECRET MISSION"
            description="Get 3 different players to mention a country."
            progress={2}
            total={3}
          />
        </div>
      </div>
    </section>
  )
}
