export const Footer = () => {
  return (
    <footer className="bg-gray-100 border-t border-red-900/10">
      <div className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center text-center space-y-6">
          <div className="text-sm tracking-widest text-gray-600 uppercase">
            <span className="text-accent">[</span> Secret Signal <span className="text-accent">]</span>
          </div>
          <div className="text-sm text-gray-600">
            Influence the conversation. Hide your intent. Find the signal.
          </div>
          <div className="flex space-x-6">
            <a href="#" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              How It Works
            </a>
            <a href="#" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              Roles
            </a>
            <a href="#" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              GitHub
            </a>
          </div>
          <div className="text-xs text-gray-600">
            <span className="text-gray-700">v1.0.0</span>
          </div>
        </div>
      </div>
    </footer>
  )
}