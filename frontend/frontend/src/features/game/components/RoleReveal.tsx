import { useState, useEffect } from 'react'

const ROLE_COLORS: Record<string, { border: string; bg: string; text: string; accent: string }> = {
  coordinator: {
    border: 'border-red-500/50',
    bg: 'bg-red-500/5',
    text: 'text-red-400',
    accent: 'rgba(239,68,68,0.6)',
  },
  detective: {
    border: 'border-cyan-500/50',
    bg: 'bg-cyan-500/5',
    text: 'text-cyan-400',
    accent: 'rgba(6,182,212,0.6)',
  },
  citizen: {
    border: 'border-gray-500/50',
    bg: 'bg-gray-500/5',
    text: 'text-gray-300',
    accent: 'rgba(156,163,175,0.6)',
  },
}

const ROLE_DESCRIPTIONS: Record<string, string> = {
  coordinator:
    'You are the Coordinator. Complete your secret mission without being caught. Manipulate the conversation and achieve your objective before the Detective exposes you.',
  detective:
    'You are the Detective. The Coordinator is hiding among the citizens. Watch for suspicious behaviour and build your case. You win if the Coordinator is voted out.',
  citizen:
    'You are a Citizen. Your goal is to identify the Coordinator before their mission is complete. Trust no one — the Coordinator is listening.',
}

interface RoleRevealProps {
  role: string
}

type Stage = 'shuffle' | 'sealing' | 'flip' | 'revealed'

const STAGE_DURATIONS: Record<Stage, number> = {
  shuffle: 2000,
  sealing: 1500,
  flip: 1500,
  revealed: Infinity,
}

export function RoleReveal({ role }: RoleRevealProps) {
  const [stage, setStage] = useState<Stage>('shuffle')
  const [glitchText, setGlitchText] = useState('')

  const normalized = role.toLowerCase()
  const c = ROLE_COLORS[normalized] ?? ROLE_COLORS.citizen
  const description = ROLE_DESCRIPTIONS[normalized] ?? ''

  useEffect(() => {
    if (stage !== 'shuffle') return
    const roles = ['detective', 'citizen', 'coordinator', 'agent', 'spy', 'analyst', 'director']
    const interval = setInterval(() => {
      setGlitchText(roles[Math.floor(Math.random() * roles.length)])
    }, 120)
    return () => clearInterval(interval)
  }, [stage])

  useEffect(() => {
    if (stage === 'revealed') return
    const duration = STAGE_DURATIONS[stage]
    const timer = setTimeout(() => {
      if (stage === 'shuffle') setStage('sealing')
      else if (stage === 'sealing') setStage('flip')
      else if (stage === 'flip') setStage('revealed')
    }, duration)
    return () => clearTimeout(timer)
  }, [stage])

  const progress = stage === 'shuffle' ? 0 : stage === 'sealing' ? 33 : stage === 'flip' ? 66 : 100

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="max-w-md w-full">
        {/* Progress bar */}
        <div className="mb-8 flex items-center gap-3">
          <div className="flex-1 h-0.5 bg-gray-800/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-accent/60 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-[10px] font-mono text-gray-600 w-8 text-right">
            {stage === 'revealed' ? 'DONE' : `${progress}%`}
          </span>
        </div>

        {/* SHUFFLE stage */}
        {stage === 'shuffle' && (
          <div className="text-center space-y-6 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-2 border border-gray-400/20 rounded bg-gray-100/50">
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse-dot" />
              <span className="text-xs font-mono tracking-wider text-gray-600">ASSIGNING ROLE</span>
            </div>
            <div className="h-16 flex items-center justify-center">
              <span className="text-lg font-mono font-bold tracking-[0.3em] text-gray-500 animate-pulse select-none">
                {glitchText.toUpperCase() || '...'}
              </span>
            </div>
            <div className="flex justify-center gap-1.5">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-2 h-2 rounded-full bg-gray-500 animate-bounce"
                  style={{ animationDelay: `${i * 0.2}s`, animationDuration: '0.8s' }}
                />
              ))}
            </div>
          </div>
        )}

        {/* SEALING stage */}
        {stage === 'sealing' && (
          <div className="text-center space-y-6 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-2 border border-gray-400/20 rounded bg-gray-100/50">
              <span className="text-xs font-mono tracking-wider text-gray-600">SEALING ENVELOPE</span>
            </div>
            <div className="relative mx-auto w-48 h-48">
              <div className="absolute inset-0 border-2 border-gray-500/30 rounded-lg animate-pulse" />
              <div className="absolute inset-4 border border-gray-500/20 rounded" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <div
                  className="w-16 h-16 rounded-full border-2 flex items-center justify-center animate-seal-glow"
                  style={{ borderColor: c.accent }}
                >
                  <span className="text-2xl font-serif" style={{ color: c.accent }}>S</span>
                </div>
              </div>
              <div className="absolute bottom-8 left-1/2 -translate-x-1/2 text-[10px] font-mono tracking-widest text-gray-500">
                TOP SECRET
              </div>
            </div>
          </div>
        )}

        {/* FLIP stage */}
        {stage === 'flip' && (
          <div className="text-center space-y-6 animate-fade-in">
            <div className="text-xs font-mono tracking-widest text-gray-500">BREAKING SEAL...</div>
            <div className="mx-auto w-64 h-48" style={{ perspective: '600px' }}>
              <div className="relative w-full h-full animate-card-flip" style={{ transformStyle: 'preserve-3d' }}>
                <div
                  className="absolute inset-0 rounded border-2 border-gray-500/30 flex items-center justify-center"
                  style={{ backfaceVisibility: 'hidden', backgroundColor: 'rgba(22,22,34,0.8)' }}
                >
                  <span className="text-2xl font-mono font-bold tracking-wider text-gray-500">??</span>
                </div>
                <div
                  className={`absolute inset-0 rounded border-2 ${c.border} flex items-center justify-center`}
                  style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)', backgroundColor: 'rgba(22,22,34,0.95)' }}
                >
                  <div className="text-center space-y-2 px-4">
                    <div className="text-[10px] font-mono tracking-widest text-gray-500">YOUR ROLE</div>
                    <div className={`text-3xl font-mono font-bold tracking-[0.3em] uppercase ${c.text}`}>
                      {normalized}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* REVEALED stage */}
        {stage === 'revealed' && (
          <div className="animate-scale-in">
            <div className={`rounded border-2 ${c.border} ${c.bg} p-8 text-center space-y-6`}>
              <div className="text-xs font-mono tracking-widest text-gray-500">YOUR ROLE</div>
              <div className={`text-3xl font-mono font-bold tracking-[0.3em] uppercase ${c.text}`}>
                {normalized}
              </div>
              {description && (
                <p className="text-sm font-mono leading-relaxed text-gray-400">{description}</p>
              )}
              <div className="text-[10px] font-mono tracking-wider text-gray-600 pt-2">
                THIS INFORMATION IS PRIVATE TO YOU
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
