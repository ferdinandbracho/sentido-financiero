import { Link } from 'react-router-dom'
import { 
  Upload, 
  FileText, 
  TrendingUp, 
  DollarSign,
  Calendar,
  AlertCircle,
  CheckCircle
} from 'lucide-react'
import { useStatements } from '../hooks/useStatements'
import { formatCurrency, formatDate, getStatusInfo } from '../utils/helpers'
import IntegratedDashboard from './IntegratedDashboard'

export function Dashboard() {
  return <IntegratedDashboard />
}

function StatCard({ title, value, icon: Icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 dark:bg-blue-900 dark:text-blue-300',
    green: 'bg-green-50 text-green-600 dark:bg-green-900 dark:text-green-300',
    purple: 'bg-purple-50 text-purple-600 dark:bg-purple-900 dark:text-purple-300',
    orange: 'bg-orange-50 text-orange-600 dark:bg-orange-900 dark:text-orange-300',
  }

  return (
    <div className="bg-card overflow-hidden shadow-md rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Icon className={`h-6 w-6 ${colorClasses[color]?.split(' ')[1] || 'text-muted-foreground'}`} />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-muted-foreground truncate">
                {title}
              </dt>
              <dd className="text-lg font-medium text-foreground">
                {value}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}