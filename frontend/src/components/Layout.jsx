import { Link } from 'react-router-dom';
import { BarChart3 } from 'lucide-react';

export function Layout({ children }) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Navigation Bar */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <Link 
                to="/" 
                className="flex items-center text-gray-900 hover:text-primary-600 transition-colors"
              >
                <BarChart3 className="h-7 w-7 text-primary-600" />
                <span className="ml-3 text-xl font-bold tracking-tight">SentidoFinanciero</span>
              </Link>
            </div>
            <nav className="hidden md:flex items-center space-x-8">
              <Link 
                to="/upload" 
                className="text-sm font-medium text-gray-700 hover:text-primary-600 transition-colors"
              >
                Subir Estado
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </div>
      </main>
    </div>
  )
}