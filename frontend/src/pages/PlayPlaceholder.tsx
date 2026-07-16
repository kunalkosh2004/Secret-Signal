import { Link } from 'react-router-dom'

export const PlayPlaceholder = () => {
  return (
    <section className="min-h-screen flex items-center justify-center bg-gray-50 bg-grid">
      <div className="text-center max-w-lg mx-auto px-4">
        <div className="text-4xl font-mono text-accent mb-6">[ ... ]</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-4 font-mono tracking-wider">
          <span className="text-accent">&gt;</span> Play Page
        </h1>
        <p className="text-sm text-gray-600 mb-8 leading-relaxed">
          The multiplayer game is currently under development. Check back soon to
          start playing Secret Signal with your friends.
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
