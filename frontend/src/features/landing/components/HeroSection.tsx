import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { useAuthStore } from '../../../stores/authStore'

export const HeroSection = () => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return (
    <section className="relative bg-gray-50 text-gray-900 overflow-hidden bg-grid">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(239,68,68,0.08)_0%,transparent_60%)] pointer-events-none" />
      <div className="relative pt-24 pb-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            <div className="space-y-6">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-mono tracking-wider bg-accent/10 text-accent border border-accent/30">
                [REAL-TIME SOCIAL DEDUCTION]
              </span>
              <h1 className="text-4xl font-bold tracking-tight sm:text-5xl leading-tight">
                INFLUENCE THE<br />
                <span className="text-accent">CONVERSATION.</span><br />
                HIDE YOUR INTENT.<br />
                FIND THE <span className="text-accent">SIGNAL</span>.
              </h1>
              <p className="max-w-xl text-base text-gray-600 leading-relaxed">
                Secret Signal is a multiplayer social deduction game where one hidden <span className="text-accent">Coordinator</span> manipulates
                conversations to complete secret missions while other players try to identify them.
              </p>
              <div className="flex items-center space-x-6">
                <Link
                  to={isAuthenticated ? '/lobby' : '/auth'}
                  className="inline-flex items-center px-6 py-3 border border-accent/50 text-base font-medium rounded-md text-gray-900 bg-accent/10 hover:bg-accent/20 hover:border-accent transition-all glow-red"
                >
                  PLAY NOW
                </Link>
                <Button variant="ghost" asChild>
                  <a href="#">[ HOW IT WORKS ]</a>
                </Button>
              </div>
              <div className="text-sm text-gray-600 flex items-center space-x-4 font-mono">
                <span>4-8 PLAYERS</span>
                <span className="text-gray-700">|</span>
                <span>15-20 MIN</span>
                <span className="text-gray-700">|</span>
                <span>REAL-TIME</span>
              </div>
            </div>
            <div className="hidden lg:block">
              <div className="relative h-96 w-full">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative w-64 h-64">
                    <div className="absolute inset-0 rounded-full border border-accent/20 animate-pulse-glow" />
                    <div className="absolute inset-4 rounded-full border border-accent/10" />
                    <div className="absolute inset-8 rounded-full border border-gray-500/20" />
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center w-16 h-16 bg-accent/10 border border-accent/30 rounded-full">
                      <span className="text-2xl text-accent font-mono">?</span>
                    </div>
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 flex items-center justify-center w-10 h-10 bg-gray-200 border border-gray-400 rounded-full">
                      <span className="text-sm text-gray-800 font-mono">A</span>
                    </div>
                    <div className="absolute top-1/4 -right-3 flex items-center justify-center w-10 h-10 bg-gray-200 border border-gray-400 rounded-full">
                      <span className="text-sm text-gray-800 font-mono">B</span>
                    </div>
                    <div className="absolute bottom-1/4 -left-3 flex items-center justify-center w-10 h-10 bg-gray-200 border border-gray-400 rounded-full">
                      <span className="text-sm text-gray-800 font-mono">C</span>
                    </div>
                    <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 flex items-center justify-center w-10 h-10 bg-gray-200 border border-gray-400 rounded-full">
                      <span className="text-sm text-gray-800 font-mono">D</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
