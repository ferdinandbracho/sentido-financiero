import { Sun, Moon, Monitor } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'

export const ThemeToggle = () => {
  const { theme, setTheme, effectiveTheme } = useTheme()

  const themes = [
    { id: 'light', icon: Sun, label: 'Light' },
    { id: 'dark', icon: Moon, label: 'Dark' },
    { id: 'system', icon: Monitor, label: 'System' }
  ]

  return (
    <div className="relative">
      <div className="flex items-center space-x-1 rounded-lg border border-border bg-background p-1">
        {themes.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => setTheme(id)}
            className={`
              relative inline-flex items-center justify-center rounded-md px-3 py-2 text-sm font-medium
              transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2
              ${theme === id 
                ? 'bg-primary text-primary-foreground shadow-sm' 
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              }
            `}
            title={label}
          >
            <Icon className="h-4 w-4" />
            <span className="sr-only">{label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export const QuickThemeToggle = () => {
  const { toggleTheme, effectiveTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className="inline-flex items-center justify-center rounded-md p-2 text-sm font-medium transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
      title={`Switch to ${effectiveTheme === 'light' ? 'dark' : 'light'} theme`}
    >
      {effectiveTheme === 'light' ? (
        <Moon className="h-5 w-5" />
      ) : (
        <Sun className="h-5 w-5" />
      )}
      <span className="sr-only">Toggle theme</span>
    </button>
  )
}