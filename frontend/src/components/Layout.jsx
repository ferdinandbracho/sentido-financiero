import { Link } from 'react-router-dom';
import { BarChart3 } from 'lucide-react';

export function Layout({ children }) {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Navigation Bar */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link 
                to="/" 
                className="flex items-center text-gray-900 hover:text-gray-700 transition-colors"
              >
                <BarChart3 className="h-6 w-6 text-primary-600" />
                <span className="ml-2 text-xl font-semibold">StatementSense</span>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </div>
      </main>
    </div>
  )
}