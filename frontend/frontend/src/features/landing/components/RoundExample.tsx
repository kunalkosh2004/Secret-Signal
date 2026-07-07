export const RoundExample = () => {
  return (
    <section className="py-20 bg-gray-50 bg-grid">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-center text-2xl font-bold tracking-tight text-gray-900 font-mono">
          <span className="text-accent">&gt;</span> Example Round Flow
        </h2>
        <p className="mt-4 text-center text-base text-gray-600 max-w-xl mx-auto">
          See how a typical round progresses from public prompt to mission completion.
        </p>
        <div className="mt-16 max-w-2xl mx-auto space-y-6">
          <div className="flex items-start space-x-4 p-4 bg-gray-100 border border-gray-400/20 rounded">
            <div className="flex-shrink-0 h-8 w-8 rounded bg-accent/10 text-accent font-mono text-sm border border-accent/30 flex items-center justify-center">01</div>
            <div>
              <h3 className="font-mono text-sm tracking-wider text-gray-800">Public Prompt</h3>
              <p className="mt-1 text-sm text-gray-600">You receive Rs.10 crore but must live in one city forever. Where would you live?</p>
            </div>
          </div>
          <div className="flex items-start space-x-4 p-4 bg-gray-100 border border-gray-400/20 rounded">
            <div className="flex-shrink-0 h-8 w-8 rounded bg-accent/10 text-accent font-mono text-sm border border-accent/30 flex items-center justify-center">02</div>
            <div>
              <h3 className="font-mono text-sm tracking-wider text-gray-800">Secret Objectives</h3>
              <p className="mt-1 text-sm text-gray-600">Coordinator: Get 3 players to mention different countries.</p>
            </div>
          </div>
          <div className="flex items-start space-x-4 p-4 bg-gray-100 border border-gray-400/20 rounded">
            <div className="flex-shrink-0 h-8 w-8 rounded bg-accent/10 text-accent font-mono text-sm border border-accent/30 flex items-center justify-center">03</div>
            <div>
              <h3 className="font-mono text-sm tracking-wider text-gray-800">Interaction</h3>
              <p className="mt-1 text-sm text-gray-600 font-mono">
                Player 1 mentions Japan → 1/3<br />
                Player 2 mentions Switzerland → 2/3<br />
                Player 3 mentions India → 3/3
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-4 p-4 bg-gray-100 border border-gray-400/20 rounded">
            <div className="flex-shrink-0 h-8 w-8 rounded bg-accent/10 text-accent font-mono text-sm border border-accent/30 flex items-center justify-center">04</div>
            <div>
              <h3 className="font-mono text-sm tracking-wider text-gray-800">Discussion &amp; Accusation</h3>
              <p className="mt-1 text-sm text-gray-600">Players discuss suspicions and vote for who they think is the Coordinator.</p>
            </div>
          </div>
          <div className="flex items-start space-x-4 p-4 bg-gray-100 border border-accent/20 rounded">
            <div className="flex-shrink-0 h-8 w-8 rounded bg-accent/10 text-accent font-mono text-sm border border-accent/30 flex items-center justify-center">05</div>
            <div>
              <h3 className="font-mono text-sm tracking-wider text-accent">Round Result</h3>
              <p className="mt-1 text-sm text-gray-600">Mission Complete! Coordinator earns points for successful influence.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
