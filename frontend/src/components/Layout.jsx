import { Link } from 'react-router-dom';
import { BarChart3 } from 'lucide-react';
import { QuickThemeToggle } from './ThemeToggle';

export function Layout({ children }) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Navigation Bar */}
      <header className="bg-card border-b border-border shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <Link 
                to="/" 
                className="flex items-center text-foreground hover:text-primary transition-colors"
              >
                <BarChart3 className="h-7 w-7 text-primary" />
                <span className="ml-3 text-xl font-bold tracking-tight">SentidoFinanciero</span>
              </Link>
            </div>
            <nav className="flex items-center space-x-8">
              <Link 
                to="/upload" 
                className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
              >
                Subir Estado
              </Link>
              <QuickThemeToggle />
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </div>
      </main>
    </div>
  )
}