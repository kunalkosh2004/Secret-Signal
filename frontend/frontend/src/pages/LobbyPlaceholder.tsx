import { Link } from 'react-router-dom'

export const LobbyPlaceholder = () => {
  return (
    <section className="min-h-screen flex items-center justify-center bg-gray-50 bg-grid">
      <div className="text-center max-w-lg mx-auto px-4">
        <div className="text-4xl font-mono text-accent mb-6 animate-pulse-glow inline-flex items-center justify-center w-16 h-16 rounded-full border border-accent/30 bg-accent/5">
          <span>?</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-4 font-mono tracking-wider">
          <span className="text-accent">&gt;</span> Lobby
        </h1>
        <p className="text-sm text-gray-600 mb-8 leading-relaxed">
          The game lobby is under construction. Soon you&apos;ll be able to
          create rooms, invite friends, and start matches here.
        </p>
        <Link
          to="/"
          className="inline-flex items-center px-6 py-3 border border-accent/50 text-sm font-medium rounded-md text-gray-900 bg-accent/10 hover:bg-accent/20 hover:border-accent transition-all glow-red font-mono tracking-wider"
        >
          [ RETURN HOME ]
        </Link>
      </div>
    </section>
  )
}
