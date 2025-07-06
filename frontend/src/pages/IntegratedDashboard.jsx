import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { 
  Upload, 
  FileText, 
  TrendingUp, 
  DollarSign,
  Calendar,
  AlertCircle,
  CheckCircle,
  Download,
  Trash2,
  Eye,
  Play,
  Search,
  Filter,
  RefreshCw,
  MoreVertical,
  Check,
  Minus
} from 'lucide-react'
import { 
  useStatements, 
  useDeleteStatement, 
  useProcessStatement,
  useBulkDeleteStatements,
  useBulkDownloadStatements
} from '../hooks/useStatements'
import { 
  formatFileSize, 
  formatDate, 
  formatCurrency, 
  getStatusInfo, 
  formatStatementName 
} from '../utils/helpers'
import { clsx } from 'clsx'
import ConfirmationModal from '../components/ConfirmationModal'

export default function IntegratedDashboard() {
  // State for filtering and sorting
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('upload_date')
  const [sortOrder, setSortOrder] = useState('desc')
  const [openMenuId, setOpenMenuId] = useState(null)
  
  // State for bulk operations
  const [selectedStatements, setSelectedStatements] = useState(new Set())

  // State for delete confirmation modal
  const [deleteModal, setDeleteModal] = useState({
    isOpen: false,
    id: null,
    isBulk: false,
  })
  
  // Fetch data and mutations
  const { data: statements = [], isLoading, error, refetch } = useStatements()
  const deleteStatement = useDeleteStatement()
  const processStatement = useProcessStatement()
  const bulkDeleteStatements = useBulkDeleteStatements()
  const bulkDownloadStatements = useBulkDownloadStatements()
  const navigate = useNavigate()
  
  // Handle dropdown menu toggle
  const handleMenuToggle = (id, isOpen) => {
    setOpenMenuId(isOpen ? id : null);
  }
  
  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (openMenuId) {
        const dropdown = document.querySelector(`[data-menu-id="${openMenuId}"]`);
        if (dropdown && !dropdown.contains(event.target)) {
          handleMenuToggle(openMenuId, false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [openMenuId]);

  // Filter and sort statements
  const filteredStatements = statements
    .filter(statement => {
      return searchTerm === '' || 
        statement.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (statement.bank_name && statement.bank_name.toLowerCase().includes(searchTerm.toLowerCase()))
    })
    .sort((a, b) => {
      let aVal = a[sortBy]
      let bVal = b[sortBy]
      
      if (sortBy === 'upload_date') {
        aVal = new Date(aVal)
        bVal = new Date(bVal)
      }
      
      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })

  // Calculate dashboard stats
  const stats = {
    totalStatements: statements.length,
    processed: statements.filter(s => s.processing_status === 'processed').length,
    processing: statements.filter(s => s.processing_status === 'processing').length,
    totalTransactions: statements.reduce((sum, s) => sum + (s.total_transactions || 0), 0),
    totalAmount: statements.reduce((sum, s) => sum + (s.total_debits || 0), 0),
  }

  // Get recent statements for quick view
  const recentStatements = filteredStatements
    .slice(0, 5)

  // Action handlers
  const onConfirmDelete = async () => {
    const { id, isBulk } = deleteModal

    try {
      if (isBulk) {
        const selectedIds = Array.from(selectedStatements)
        await bulkDeleteStatements.mutateAsync(selectedIds)
        setSelectedStatements(new Set())
        setIsSelectionMode(false)
      } else {
        await deleteStatement.mutateAsync(id)
      }
    } catch (error) {
      console.error('Error during deletion:', error)
    } finally {
      setDeleteModal({ isOpen: false, id: null, isBulk: false })
    }
  }

  const handleDelete = (id) => {
    setDeleteModal({ isOpen: true, id, isBulk: false })
  }

  const handleProcess = async (id) => {
    try {
      await processStatement.mutateAsync(id)
    } catch (error) {
      console.error('Error processing statement:', error)
    }
  }

  // Bulk operation handlers
  const toggleStatementSelection = (statementId) => {
    const newSelected = new Set(selectedStatements)
    if (newSelected.has(statementId)) {
      newSelected.delete(statementId)
    } else {
      newSelected.add(statementId)
    }
    setSelectedStatements(newSelected)
  }

  const selectAllStatements = () => {
    const allIds = new Set(filteredStatements.map(s => s.id))
    setSelectedStatements(allIds)
  }

  const deselectAllStatements = () => {
    setSelectedStatements(new Set())
  }

  const handleBulkDelete = () => {
    if (selectedStatements.size === 0) return
    setDeleteModal({ isOpen: true, id: null, isBulk: true })
  }

  const handleBulkDownload = async () => {
    const selectedIds = Array.from(selectedStatements)
    if (selectedIds.length === 0) return

    try {
      await bulkDownloadStatements.mutateAsync(selectedIds)
    } catch (error) {
      console.error('Error in bulk download:', error)
    }
  }

  // Check if all visible statements are selected
  const allVisible = filteredStatements.length > 0
  const allSelected = allVisible && filteredStatements.every(s => selectedStatements.has(s.id))
  const someSelected = selectedStatements.size > 0
  const indeterminate = someSelected && !allSelected

  // Error state
  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Error al cargar datos</h3>
        <p className="mt-1 text-sm text-gray-500">
          No se pudieron cargar los estados de cuenta.
        </p>
        <div className="mt-6">
          <button
            onClick={() => refetch()}
            className="btn btn-primary btn-sm"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Resumen de tus estados de cuenta y análisis financiero
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Link to="/upload" className="btn btn-primary btn-md">
            <Upload className="h-4 w-4 mr-2" />
            Subir Nuevo
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <StatCard
          title="Total de Estados"
          value={stats.totalStatements}
          icon={FileText}
          color="blue"
        />
        <StatCard
          title="Total Transacciones"
          value={stats.totalTransactions}
          icon={TrendingUp}
          color="purple"
        />
        <StatCard
          title="Monto Total"
          value={formatCurrency(stats.totalAmount)}
          icon={DollarSign}
          color="orange"
        />
      </div>

      {/* Filters and Search */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4">
          <div className="sm:flex sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            {/* Search */}
            <div className="flex-1 max-w-lg">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar por nombre de archivo o banco..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="input pl-10"
                />
              </div>
            </div>

            {/* Sort */}
            <div className="flex items-center">
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [field, order] = e.target.value.split('-')
                  setSortBy(field)
                  setSortOrder(order)
                }}
                className="input w-auto"
              >
                <option value="upload_date-desc">Más recientes</option>
                <option value="upload_date-asc">Más antiguos</option>
                <option value="filename-asc">Nombre A-Z</option>
                <option value="filename-desc">Nombre Z-A</option>
                <option value="total_debits-desc">Mayor monto</option>
                <option value="total_debits-asc">Menor monto</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Statements List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        {isLoading ? (
          <div className="px-6 py-4">
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <div className="rounded-lg bg-gray-200 h-12 w-12"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                  <div className="h-8 bg-gray-200 rounded w-20"></div>
                </div>
              ))}
            </div>
          </div>
        ) : filteredStatements.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              {searchTerm 
                ? 'No se encontraron resultados' 
                : 'No hay estados de cuenta'
              }
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm
                ? 'Intenta ajustar los términos de búsqueda'
                : 'Comienza subiendo tu primer estado de cuenta'
              }
            </p>
            {!searchTerm && (
              <div className="mt-6">
                <Link to="/upload" className="btn btn-primary btn-sm">
                  <Upload className="h-4 w-4 mr-2" />
                  Subir Archivo
                </Link>
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Bulk Operations Toolbar */}
            <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {/* Select All Checkbox */}
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      checked={allSelected}
                      ref={(el) => {
                        if (el) el.indeterminate = indeterminate
                      }}
                      onChange={() => allSelected ? deselectAllStatements() : selectAllStatements()}
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      {selectedStatements.size > 0 
                        ? `${selectedStatements.size} seleccionados`
                        : 'Seleccionar todo'}
                    </span>
                  </label>
                </div>

                {/* Bulk Action Buttons */}
                {selectedStatements.size > 0 && (
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleBulkDownload}
                      className="btn btn-secondary btn-sm"
                      disabled={selectedStatements.size === 0 || bulkDownloadStatements.isPending}
                    >
                      {bulkDownloadStatements.isPending ? (
                        <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                      ) : (
                        <Download className="h-4 w-4 mr-1" />
                      )}
                      Descargar ({selectedStatements.size})
                    </button>
                    <button
                      onClick={handleBulkDelete}
                      className="btn btn-danger btn-sm"
                      disabled={selectedStatements.size === 0 || bulkDeleteStatements.isPending}
                    >
                      {bulkDeleteStatements.isPending ? (
                        <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4 mr-1" />
                      )}
                      Eliminar ({selectedStatements.size})
                    </button>
                  </div>
                )}
              </div>
            </div>

            <ul className="divide-y divide-gray-200">
              {filteredStatements.map((statement) => (
                <StatementItem
                  key={statement.id}
                  statement={statement}
                  onDelete={() => handleDelete(statement.id)}
                  onProcess={() => handleProcess(statement.id)}
                  isDeleting={deleteStatement.isPending && deleteStatement.variables === statement.id}
                  isProcessing={processStatement.isPending && processStatement.variables === statement.id}
                  isMenuOpen={openMenuId === statement.id}
                  onMenuToggle={handleMenuToggle}
                  isSelected={selectedStatements.has(statement.id)}
                  onSelectionToggle={() => toggleStatementSelection(statement.id)}
                />
              ))}
            </ul>

            {/* Summary Footer */}
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-900 mb-4">Resumen de la vista actual</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900">
                    {filteredStatements.length}
                  </p>
                  <p className="text-sm text-gray-500">Estados mostrados</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {filteredStatements.reduce((sum, s) => sum + (s.total_transactions || 0), 0)}
                  </p>
                  <p className="text-sm text-gray-500">Transacciones</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-purple-600">
                    {formatCurrency(filteredStatements.reduce((sum, s) => sum + (s.total_debits || 0), 0))}
                  </p>
                  <p className="text-sm text-gray-500">Monto total</p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      <ConfirmationModal
        isOpen={deleteModal.isOpen}
        onClose={() => setDeleteModal({ isOpen: false, id: null, isBulk: false })}
        onConfirm={onConfirmDelete}
        title={
          deleteModal.isBulk
            ? `Eliminar ${selectedStatements.size} estados de cuenta`
            : 'Eliminar estado de cuenta'
        }
        message={
          deleteModal.isBulk
            ? `¿Estás seguro de que deseas eliminar los ${selectedStatements.size} estados de cuenta seleccionados? Esta acción no se puede deshacer.`
            : '¿Estás seguro de que deseas eliminar este estado de cuenta? Esta acción no se puede deshacer.'
        }
        confirmText="Eliminar"
        cancelText="Cancelar"
        isDanger={true}
        isLoading={deleteStatement.isPending || bulkDeleteStatements.isPending}
      />
    </div>
  )
}

// Statement item component
function StatementItem({ statement, onDelete, onProcess, isDeleting, isProcessing, isMenuOpen, onMenuToggle, isSelected, onSelectionToggle }) {
  const dropdownRef = useRef(null);
  const statusInfo = getStatusInfo(statement.processing_status)
  
  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        if (isMenuOpen) {
          onMenuToggle(statement.id, false);
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMenuOpen, onMenuToggle, statement.id]);

  return (
    <li className="px-6 py-4 hover:bg-gray-50">
      <div className="flex items-center justify-between">
        <div className="flex items-center min-w-0 flex-1">
          {/* Selection Checkbox - Always visible */}
          <div className="flex-shrink-0 mr-3">
            <input
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              checked={isSelected}
              onChange={onSelectionToggle}
              onClick={(e) => e.stopPropagation()}
            />
          </div>
          
          <div className="flex-shrink-0">
            <div className={clsx(
              'h-10 w-10 rounded-lg flex items-center justify-center',
              statusInfo.color.replace('text-', 'bg-').replace('-800', '-100')
            )}>
              <FileText className={clsx(
                'h-5 w-5',
                statusInfo.color.replace('-100', '-600')
              )} />
            </div>
          </div>

          <div className="ml-4 flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <Link
                to={`/statements/${statement.id}`}
                className="text-sm font-medium text-primary-600 hover:text-primary-500 truncate"
              >
                {formatStatementName(statement)}
              </Link>
              <span className={`badge ${statusInfo.color}`}>
                {statusInfo.name}
              </span>
            </div>
            
            <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
              <span>{statement.bank_name || 'Banco no identificado'}</span>
              <span>•</span>
              <span>Subido {formatDate(statement.upload_date, 'relative')}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* Stats */}
          <div className="hidden sm:block text-right">
            <p className="text-sm font-medium text-gray-900">
              {statement.total_transactions || 0} transacciones
            </p>
            <p className="text-sm text-gray-500">
              {formatCurrency(statement.total_debits || 0)}
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            {statement.processing_status === 'uploaded' && (
              <button
                onClick={onProcess}
                disabled={isProcessing}
                className="btn btn-primary btn-sm"
                title="Procesar estado de cuenta"
              >
                {isProcessing ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
              </button>
            )}

            <Link
              to={`/statements/${statement.id}`}
              className="btn btn-secondary btn-sm"
              title="Ver detalles"
            >
              <Eye className="h-4 w-4" />
            </Link>

            <div className="relative inline-block text-left" data-menu-id={statement.id} ref={dropdownRef}>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onMenuToggle(statement.id, !isMenuOpen);
                }}
                className="btn btn-secondary btn-sm"
                aria-expanded={isMenuOpen}
                aria-haspopup="true"
              >
                <MoreVertical className="h-4 w-4" />
              </button>

              {isMenuOpen && (
                <div 
                  className="fixed right-4 mt-1 w-48 bg-white rounded-md shadow-lg z-[1000] border border-gray-200 overflow-visible"
                  style={{
                    // Position the dropdown relative to the viewport
                    position: 'fixed',
                    top: dropdownRef.current 
                      ? `${dropdownRef.current.getBoundingClientRect().bottom + window.scrollY}px` 
                      : 'auto',
                    right: 'auto',
                    left: dropdownRef.current 
                      ? `${dropdownRef.current.getBoundingClientRect().right - 192}px`
                      : 'auto',
                    zIndex: 1000
                  }}
                >
                  <div className="py-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        // Download the statement PDF
                        window.open(`/api/v1/statements/${statement.id}/download`, '_blank');
                        onMenuToggle(statement.id, false);
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 whitespace-nowrap"
                    >
                      <Download className="h-4 w-4 mr-2 inline" />
                      Descargar PDF
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete();
                        onMenuToggle(statement.id, false);
                      }}
                      disabled={isDeleting}
                      className="block w-full text-left px-4 py-2 text-sm text-red-700 hover:bg-red-50 whitespace-nowrap"
                    >
                      <Trash2 className="h-4 w-4 mr-2 inline" />
                      Eliminar
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </li>
  )
}

// Stat card component
function StatCard({ title, value, icon: Icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
  }

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={clsx('flex items-center justify-center h-12 w-12 rounded-md', colorClasses[color])}>
              <Icon className="h-6 w-6" aria-hidden="true" />
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
              <dd className="text-2xl font-semibold text-gray-900">{value}</dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}
