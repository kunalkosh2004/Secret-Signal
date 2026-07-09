import { useEffect } from 'react'
import { router } from './router';
import { useAuthStore } from '../stores/authStore'

function App() {
  const loadFromStorage = useAuthStore((s) => s.loadFromStorage)

  useEffect(() => {
    loadFromStorage()
  }, [loadFromStorage])

  return (
    <div className="min-h-screen bg-gray-50 relative">
      <div className="fixed inset-0 pointer-events-none z-50 bg-scanlines opacity-20" />
      {router()}
    </div>
  );
}

export default App;
