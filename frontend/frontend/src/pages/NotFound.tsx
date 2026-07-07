import { Link } from 'react-router-dom'

export const NotFound = () => {
  return (
    <section className="min-h-screen flex items-center justify-center bg-gray-50 bg-grid">
      <div className="text-center max-w-lg mx-auto px-4">
        <div className="text-6xl font-mono text-accent mb-4 font-bold">404</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-4 font-mono tracking-wider">
          <span className="text-accent">&gt;</span> Signal Lost
        </h1>
        <p className="text-sm text-gray-600 mb-8 leading-relaxed">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <Link
          to="/"
          className="inline-flex items-center px-6 py-3 border border-accent/50 text-sm font-medium rounded-md text-gray-900 bg-accent/10 hover:bg-accent/20 hover:border-accent transition-all glow-red font-mono tracking-wider"
        >
          [ RETURN TO BASE ]
        </Link>
      </div>
    </section>
  )
}
