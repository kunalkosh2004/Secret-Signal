const ROLE_COLORS: Record<string, string> = {
  coordinator: 'border-red-500/50 bg-red-500/5 text-red-500',
  detective: 'border-cyan-500/50 bg-cyan-500/5 text-cyan-500',
  citizen: 'border-gray-500/50 bg-gray-500/5 text-gray-500',
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

export function RoleReveal({ role }: RoleRevealProps) {
  const normalized = role.toLowerCase()
  const colors = ROLE_COLORS[normalized] ?? 'border-gray-500/50 bg-gray-500/5 text-gray-500'
  const description = ROLE_DESCRIPTIONS[normalized] ?? ''

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="max-w-md w-full animate-role-reveal perspective-[800px]">
        <div className={`rounded border-2 ${colors} p-8 text-center space-y-6`}>
          <div className="text-xs font-mono tracking-widest opacity-60">YOUR ROLE</div>
          <div className="text-2xl font-mono font-bold tracking-widest uppercase">
            {normalized}
          </div>
          {description && (
            <p className="text-sm font-mono leading-relaxed opacity-80">{description}</p>
          )}
          <div className="text-[10px] font-mono tracking-wider opacity-40 pt-2">
            THIS INFORMATION IS PRIVATE TO YOU
          </div>
        </div>
      </div>
    </div>
  )
}
