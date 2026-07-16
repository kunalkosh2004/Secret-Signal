import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { ADMIN_NAV_SECTIONS } from '../config/navigation'

interface AdminSidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export function AdminSidebar({ collapsed, onToggle }: AdminSidebarProps) {
  const location = useLocation()
  const [expandedSections, setExpandedSections] = useState<Set<string>>(() => {
    const active = ADMIN_NAV_SECTIONS.find((s: { id: string; children?: { path: string }[] }) =>
      s.children?.some((c: { path: string }) => location.pathname === c.path),
    )
    return new Set(active ? [active.id] : ['overview'])
  })

  const toggleSection = (id: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <aside
      className={`flex flex-col bg-gray-950 border-r border-gray-800/50 transition-all duration-200 ${
        collapsed ? 'w-12' : 'w-56'
      } shrink-0 h-full overflow-hidden`}
    >
      {/* Brand */}
      <div className="flex items-center h-10 px-3 border-b border-gray-800/50 shrink-0">
        {!collapsed && (
          <span className="text-[11px] font-mono font-bold tracking-widest text-gray-400 uppercase">
            Ops
          </span>
        )}
        <button
          onClick={onToggle}
          className="ml-auto p-1 text-gray-600 hover:text-gray-400 transition-colors"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <span className="text-xs">{collapsed ? '\u25B6' : '\u25C0'}</span>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-2" role="navigation" aria-label="Admin navigation">
        {ADMIN_NAV_SECTIONS.map((section: { id: string; icon: string; label: string; children?: { id: string; path: string; icon: string; label: string }[] }) => {
          const isExpanded = expandedSections.has(section.id)
          const isActive = section.children?.some(
            (c: { path: string }) => location.pathname === c.path,
          )

          return (
            <div key={section.id} className="mb-1">
              {/* Section header */}
              {!collapsed ? (
                <button
                  onClick={() => toggleSection(section.id)}
                  className={`w-full flex items-center gap-2 px-3 py-1.5 text-[11px] font-mono tracking-wider uppercase transition-colors ${
                    isActive
                      ? 'text-gray-300'
                      : 'text-gray-600 hover:text-gray-400'
                  }`}
                >
                  <span className="text-xs">{section.icon}</span>
                  <span>{section.label}</span>
                  <span className="ml-auto text-[8px] text-gray-700">
                    {isExpanded ? '\u25B2' : '\u25BC'}
                  </span>
                </button>
              ) : (
                <div className="flex justify-center py-1.5">
                  <span className="text-xs text-gray-600" title={section.label}>
                    {section.icon}
                  </span>
                </div>
              )}

              {/* Children */}
              {!collapsed && isExpanded && section.children && (
                <div className="ml-4 border-l border-gray-800/50">
                  {section.children.map((child: { id: string; path: string; label: string }) => (
                    <NavLink
                      key={child.id}
                      to={child.path}
                      className={({ isActive: linkActive }) =>
                        `block pl-4 pr-3 py-1 text-[11px] font-mono transition-colors ${
                          linkActive
                            ? 'text-gray-200 border-l border-gray-400 -ml-px'
                            : 'text-gray-600 hover:text-gray-400'
                        }`
                      }
                    >
                      {child.label}
                    </NavLink>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="px-3 py-2 border-t border-gray-800/50">
          <div className="text-[9px] font-mono text-gray-700">
            secret-signal v0.4.0
          </div>
        </div>
      )}
    </aside>
  )
}
