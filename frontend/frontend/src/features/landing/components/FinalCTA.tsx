import { Link } from 'react-router-dom'

export const FinalCTA = () => {
  return (
    <section className="py-20 bg-gray-50 border-t border-red-900/10 bg-grid">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 leading-tight">
            Can You Control the Conversation<br />
            <span className="text-accent">Without Getting Caught?</span>
          </h2>
          <p className="mt-4 text-base text-gray-600">
            Create a room, invite your friends, and discover who can manipulate the group
            without leaving a trace.
          </p>
          <div className="mt-8">
            <Link
              to="/play"
              className="inline-flex items-center px-6 py-3 border border-accent/50 text-base font-medium rounded-md text-gray-900 bg-accent/10 hover:bg-accent/20 hover:border-accent transition-all glow-red font-mono tracking-wider"
            >
              PLAY SECRET SIGNAL
            </Link>
          </div>
          <p className="mt-6 text-sm text-gray-600">
            The game is currently in development. Check back soon to play.
          </p>
        </div>
      </div>
    </section>
  )
}
