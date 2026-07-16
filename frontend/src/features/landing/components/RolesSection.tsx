export const RolesSection = () => {
  return (
    <section className="py-20 bg-gray-100 border-t border-gray-300/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-center text-2xl font-bold tracking-tight text-gray-900 font-mono">
          <span className="text-accent">&gt;</span> Player Roles
        </h2>
        <p className="mt-4 text-center text-base text-gray-600 max-w-xl mx-auto">
          Each player has a unique role with specific goals and abilities.
        </p>
        <div className="mt-16 grid gap-6 sm:grid-cols-1 lg:grid-cols-3">
          <div className="bg-gray-200 border border-gray-400/30 rounded p-6">
            <h3 className="flex items-center space-x-3 text-lg font-mono tracking-wider text-gray-800">
              <span className="w-3 h-3 bg-red-500 rounded-full glow-red"></span>
              <span>Coordinator</span>
            </h3>
            <p className="mt-3 text-sm text-gray-600 border-l-2 border-accent/30 pl-3">
              The secret influencer who must complete missions without being detected.
            </p>
            <h4 className="mt-4 text-xs font-mono tracking-wider text-gray-700 uppercase">Objective</h4>
            <ul className="mt-2 space-y-1 pl-4 text-sm text-gray-600 list-disc">
              <li>Complete your assigned mission by influencing other people&apos;s conversations.</li>
              <li>Avoid being identified as the Coordinator.</li>
            </ul>
            <h4 className="mt-4 text-xs font-mono tracking-wider text-gray-700 uppercase">Abilities</h4>
            <ul className="mt-2 space-y-1 pl-4 text-sm text-gray-600 list-disc">
              <li>Receive private missions each round that require specific player actions.</li>
              <li>Win by completing missions and avoiding correct accusations.</li>
            </ul>
          </div>
          <div className="bg-gray-200 border border-gray-400/30 rounded p-6">
            <h3 className="flex items-center space-x-3 text-lg font-mono tracking-wider text-gray-800">
              <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
              <span>Detective</span>
            </h3>
            <p className="mt-3 text-sm text-gray-600 border-l-2 border-blue-500/30 pl-3">
              The investigator tasked with identifying the Coordinator through observation.
            </p>
            <h4 className="mt-4 text-xs font-mono tracking-wider text-gray-700 uppercase">Objective</h4>
            <ul className="mt-2 space-y-1 pl-4 text-sm text-gray-600 list-disc">
              <li>Observe player behavior for signs of manipulation.</li>
              <li>Correctly identify the Coordinator.</li>
            </ul>
            <h4 className="mt-4 text-xs font-mono tracking-wider text-gray-700 uppercase">Abilities</h4>
            <ul className="mt-2 space-y-1 pl-4 text-sm text-gray-600 list-disc">
              <li>Gain suspicion insights based on player interactions.</li>
              <li>Future: Limited investigation abilities to confirm suspicions.</li>
            </ul>
          </div>
          <div className="bg-gray-200 border border-gray-400/30 rounded p-6">
            <h3 className="flex items-center space-x-3 text-lg font-mono tracking-wider text-gray-800">
              <span className="w-3 h-3 bg-green-500 rounded-full"></span>
              <span>Citizen</span>
            </h3>
            <p className="mt-3 text-sm text-gray-600 border-l-2 border-green-500/30 pl-3">
              Regular players with personal objectives who help identify the Coordinator.
            </p>
            <h4 className="mt-4 text-xs font-mono tracking-wider text-gray-700 uppercase">Objective</h4>
            <ul className="mt-2 space-y-1 pl-4 text-sm text-gray-600 list-disc">
              <li>Complete your personal objective to earn points.</li>
              <li>Help identify the Coordinator through observation.</li>
            </ul>
            <h4 className="mt-4 text-xs font-mono tracking-wider text-gray-700 uppercase">Abilities</h4>
            <ul className="mt-2 space-y-1 pl-4 text-sm text-gray-600 list-disc">
              <li>Receive personal objectives each round (e.g., make someone disagree with you).</li>
              <li>Win by correctly identifying the Coordinator or accumulating points.</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  )
}
