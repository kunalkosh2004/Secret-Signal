import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { AdminSidebar } from './Sidebar'
import { AdminTopBar } from './TopBar'

export function AdminLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className="flex h-screen bg-gray-900 overflow-hidden">
      <AdminSidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <div className="flex flex-col flex-1 min-w-0">
        <AdminTopBar title="Operations Dashboard" />
        <main className="flex-1 overflow-y-auto p-4 bg-gray-900">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
