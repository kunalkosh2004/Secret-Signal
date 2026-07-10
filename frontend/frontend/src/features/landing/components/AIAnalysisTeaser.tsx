import { Link } from 'react-router-dom'

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
              SUSPICION ANALYSIS
            </h3>
            <p className="mt-2 text-xs text-gray-600 max-w-xl mx-auto">
              Post-game breakdown showing each player&apos;s behavioral profile
              and suspicion score across rounds.
            </p>
            <div className="mt-6 space-y-2 text-left max-w-md mx-auto">
              <div className="flex items-center space-x-3 py-2 px-4 bg-gray-200 border border-gray-400/30 rounded">
                <span className="w-2.5 h-2.5 bg-red-500 rounded-full glow-red"></span>
                <span className="text-sm font-mono text-gray-800">High suspicion player</span>
                <span className="ml-auto text-sm font-mono text-red-500">78%</span>
              </div>
              <div className="flex items-center space-x-3 py-2 px-4 bg-gray-200 border border-gray-400/30 rounded">
                <span className="w-2.5 h-2.5 bg-yellow-500 rounded-full"></span>
                <span className="text-sm font-mono text-gray-800">Medium suspicion player</span>
                <span className="ml-auto text-sm font-mono text-yellow-500">42%</span>
              </div>
              <div className="flex items-center space-x-3 py-2 px-4 bg-gray-200 border border-gray-400/30 rounded">
                <span className="w-2.5 h-2.5 bg-green-500 rounded-full"></span>
                <span className="text-sm font-mono text-gray-800">Low suspicion player</span>
                <span className="ml-auto text-sm font-mono text-green-500">15%</span>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-12 text-center">
          <Link
            to="/auth"
            className="inline-flex items-center px-4 py-2 border border-accent/50 rounded text-sm font-mono text-accent bg-accent/10 hover:bg-accent/20 transition-all"
          >
            PLAY TO UNLOCK ANALYSIS &rarr;
          </Link>
        </div>
      </div>
    </section>
  )
}
