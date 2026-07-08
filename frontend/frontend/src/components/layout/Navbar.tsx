import { Link } from 'react-router-dom'

export const Navbar = () => {
  return (
    <nav className="bg-gray-100/90 backdrop-blur-sm border-b border-red-900/20 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-xl font-bold tracking-wider text-gray-900">
                <span className="text-accent">//</span> SECRET_SIGNAL
              </span>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link to="/" className="px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-200 transition-colors">How It Works</Link>
                <Link to="/" className="px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-200 transition-colors">Roles</Link>
                <Link to="/" className="px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-200 transition-colors">About</Link>
              </div>
            </div>
          </div>
          <div className="hidden md:block mr-24 translate-y-3">
            <div className="ml-6">
              <Link
                to="/auth"
                className="inline-flex items-center px-4 py-2 border border-accent/50 text-sm font-medium rounded-md bg-accent/10 hover:bg-accent/20 hover:border-accent transition-all glow-red"
              >
                Play Now
              </Link>
            </div>
          </div>
          <div className="md:hidden">
            <button type="button" className="inline-flex items-center p-2 ml-3 text-sm text-gray-600 rounded-md hover:bg-gray-200 transition-colors"
              aria-controls="mobile-menu" aria-expanded="false">
              <span className="sr-only">Open main menu</span>
              <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}