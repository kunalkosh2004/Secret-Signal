export const AIAnalysisTeaser = () => {
  return (
    <section className="py-20 bg-gray-100 border-t border-gray-300/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-center text-2xl font-bold tracking-tight text-gray-900 font-mono">
          <span className="text-accent">&gt;</span> Can AI Find the Coordinator Before You?
        </h2>
        <p className="mt-4 text-center text-base text-gray-600 max-w-xl mx-auto">
          After each match, Secret Signal analyzes behavioral patterns to detect
          subtle signs of influence and deception.
        </p>
        <div className="mt-16 space-y-8">
          <div className="text-center">
            <h3 className="text-sm font-mono tracking-wider text-gray-700">
              SUSPICION ANALYSIS (EXAMPLE)
            </h3>
            <p className="mt-2 text-xs text-gray-600 max-w-xl mx-auto">
              Post-game breakdown showing each player&apos;s suspicion score across rounds.
            </p>
            <div className="mt-6 space-y-2 text-left max-w-md mx-auto">
              <div className="flex items-center space-x-3 py-2 px-4 bg-gray-200 border border-gray-400/30 rounded">
                <span className="w-2.5 h-2.5 bg-red-500 rounded-full glow-red"></span>
                <span className="text-sm font-mono text-gray-800">Kunal</span>
                <span className="ml-auto text-sm font-mono text-red-500">78%</span>
              </div>
              <div className="flex items-center space-x-3 py-2 px-4 bg-gray-200 border border-gray-400/30 rounded">
                <span className="w-2.5 h-2.5 bg-blue-500 rounded-full"></span>
                <span className="text-sm font-mono text-gray-800">Aman</span>
                <span className="ml-auto text-sm font-mono text-blue-500">31%</span>
              </div>
              <div className="flex items-center space-x-3 py-2 px-4 bg-gray-200 border border-gray-400/30 rounded">
                <span className="w-2.5 h-2.5 bg-green-500 rounded-full"></span>
                <span className="text-sm font-mono text-gray-800">Riya</span>
                <span className="ml-auto text-sm font-mono text-green-500">22%</span>
              </div>
              <div className="flex items-center space-x-3 py-2 px-4 bg-gray-200 border border-gray-400/30 rounded">
                <span className="w-2.5 h-2.5 bg-yellow-500 rounded-full"></span>
                <span className="text-sm font-mono text-gray-800">Arjun</span>
                <span className="ml-auto text-sm font-mono text-yellow-500">18%</span>
              </div>
            </div>
            <p className="mt-4 text-xs text-gray-600 max-w-xl mx-auto italic">
              Note: This is a simulated example. AI analysis is a planned feature
              and not yet implemented in the current version.
            </p>
          </div>
        </div>
        <div className="mt-12 text-center">
          <span className="inline-flex items-center px-3 py-1 rounded text-xs font-mono tracking-wider bg-accent/10 text-accent border border-accent/30">
            [COMING SOON]
          </span>
        </div>
      </div>
    </section>
  )
}
