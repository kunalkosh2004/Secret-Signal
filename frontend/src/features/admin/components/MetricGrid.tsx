import type { ReactNode } from 'react'

interface MetricGridProps {
  children: ReactNode
  columns?: 2 | 3 | 4 | 5 | 6
}

export function MetricGrid({ children, columns = 4 }: MetricGridProps) {
  const colClass = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
    5: 'grid-cols-5',
    6: 'grid-cols-6',
  }[columns]

  return (
    <div
      className={`grid ${colClass} gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1`}
    >
      {children}
    </div>
  )
}
