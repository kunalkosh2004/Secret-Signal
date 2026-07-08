import type { ReactNode } from 'react'

interface AuthLayoutProps {
  children: ReactNode
}

/**
 * Two-column auth layout.
 *
 * Desktop: left visual panel + right form card.
 * Mobile: single column with simplified visuals.
 */
export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-5 gap-0 rounded border border-gray-400/20 bg-gray-100 overflow-hidden">
        {/* Left panel — visual / game branding */}
        <div className="hidden lg:flex lg:col-span-2 flex-col justify-between p-8 bg-gray-150 border-r border-gray-400/20">
          <div>
            <div className="text-sm font-mono tracking-wider text-gray-900">
              <span className="text-accent">//</span> SECRET_SIGNAL
            </div>
            <div className="mt-8 space-y-4">
              <p className="text-sm text-gray-600 leading-relaxed font-mono">
                &gt; Influence the conversation.
              </p>
              <p className="text-sm text-gray-600 leading-relaxed font-mono">
                &gt; Hide your intent.
              </p>
              <p className="text-sm text-gray-600 leading-relaxed font-mono">
                &gt; Find the <span className="text-accent">signal</span>.
              </p>
            </div>
          </div>

          {/* Decorative player nodes */}
          <div className="relative h-48">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="relative w-36 h-36">
                {/* Concentric rings */}
                <div className="absolute inset-0 rounded-full border border-accent/10" />
                <div className="absolute inset-4 rounded-full border border-gray-400/20" />
                <div className="absolute inset-8 rounded-full border border-gray-400/10" />
                {/* Center node */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-accent/10 border border-accent/30 rounded-full flex items-center justify-center">
                  <span className="text-xs text-accent font-mono">?</span>
                </div>
                {/* Orbiting player dots */}
                <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-6 h-6 bg-gray-200 border border-gray-400 rounded-full flex items-center justify-center">
                  <span className="text-[10px] text-gray-700 font-mono">A</span>
                </div>
                <div className="absolute top-1/3 -right-2 w-6 h-6 bg-gray-200 border border-gray-400 rounded-full flex items-center justify-center">
                  <span className="text-[10px] text-gray-700 font-mono">B</span>
                </div>
                <div className="absolute bottom-1/3 -left-2 w-6 h-6 bg-gray-200 border border-gray-400 rounded-full flex items-center justify-center">
                  <span className="text-[10px] text-gray-700 font-mono">C</span>
                </div>
                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-6 h-6 bg-gray-200 border border-gray-400 rounded-full flex items-center justify-center">
                  <span className="text-[10px] text-gray-700 font-mono">D</span>
                </div>
              </div>
            </div>
          </div>

          <div className="text-[10px] text-gray-600 font-mono">
            4-8 PLAYERS &nbsp;|&nbsp; 15-20 MIN &nbsp;|&nbsp; REAL-TIME
          </div>
        </div>

        {/* Right panel — auth form */}
        <div className="lg:col-span-3 p-8">
          {children}
        </div>
      </div>
    </div>
  )
}
