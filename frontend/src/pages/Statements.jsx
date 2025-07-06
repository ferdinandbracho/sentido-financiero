import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  FileText, 
  Download, 
  Trash2, 
  Eye, 
  Play,
  Search,
  Filter,
  Upload,
  AlertCircle,
  RefreshCw,
  MoreVertical,
  Check,
  Minus
} from 'lucide-react'
import { useStatements, useDeleteStatement, useProcessStatement, useBulkDeleteStatements, useBulkDownloadStatements } from '../hooks/useStatements'
import ConfirmationModal from '../components/ConfirmationModal'
import { formatCurrency, formatDate, formatFileSize, getStatusInfo } from '../utils/helpers'
import { clsx } from 'clsx'

export function Statements() {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('upload_date')
  const [sortOrder, setSortOrder] = useState('desc')
  const [openMenuId, setOpenMenuId] = useState(null)
  const [selectedStatements, setSelectedStatements] = useState(new Set())
  const [deleteModal, setDeleteModal] = useState({
    isOpen: false,
    id: null,
    isBulk: false
  })
  
  const handleMenuToggle = (id, isOpen) => {
    setOpenMenuId(isOpen ? id : null);
  }

  const { data: statements = [], isLoading, error, refetch } = useStatements()
  const deleteStatement = useDeleteStatement()
  const processStatement = useProcessStatement()
  const bulkDeleteStatements = useBulkDeleteStatements()
  const bulkDownloadStatements = useBulkDownloadStatements()
  
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

  const handleDelete = async (id, isBulk = false) => {
    try {
      if (isBulk) {
        await bulkDeleteStatements.mutateAsync(Array.from(selectedStatements))
        setSelectedStatements(new Set())
      } else if (id) {
        await deleteStatement.mutateAsync(id)
      }
      setDeleteModal({ isOpen: false, id: null, isBulk: false })
    } catch (error) {
      console.error('Error deleting statement(s):', error)
    }
  }

  const handleProcess = async (id) => {
    try {
      await processStatement.mutateAsync(id)
    } catch (error) {
      console.error('Error processing statement:', error)
    }
  }

  // Selection handlers
  const handleSelectStatement = (id) => {
    const newSelected = new Set(selectedStatements)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedStatements(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedStatements.size === filteredStatements.length) {
      setSelectedStatements(new Set())
    } else {
      setSelectedStatements(new Set(filteredStatements.map(s => s.id)))
    }
  }

  const handleBulkDelete = () => {
    if (selectedStatements.size === 0) return
    setDeleteModal({
      isOpen: true,
      id: null,
      isBulk: true
    })
  }

  const handleBulkDownload = async () => {
    if (selectedStatements.size === 0) return
    
    try {
      await bulkDownloadStatements.mutateAsync(Array.from(selectedStatements))
    } catch (error) {
      console.error('Error bulk downloading statements:', error)
    }
  }

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
          <h1 className="text-2xl font-bold text-gray-900">Estados de Cuenta</h1>
          <p className="mt-1 text-sm text-gray-500">
            Gestiona y analiza tus estados de cuenta subidos
            {selectedStatements.size > 0 && (
              <span className="ml-2 text-primary-600 font-medium">
                {selectedStatements.size} seleccionados
              </span>
            )}
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex items-center space-x-3">
          {selectedStatements.size > 0 && (
            <>
              <button
                onClick={handleBulkDownload}
                disabled={bulkDownloadStatements.isPending}
                className="btn btn-secondary btn-md"
              >
                <Download className="h-4 w-4 mr-2" />
                Descargar ({selectedStatements.size})
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={bulkDeleteStatements.isPending}
                className="btn btn-danger btn-md"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Eliminar ({selectedStatements.size})
              </button>
              <button
                onClick={() => setSelectedStatements(new Set())}
                className="btn btn-outline-secondary btn-md"
              >
                Cancelar selección
              </button>
            </>
          )}
          <Link to="/upload" className="btn btn-primary btn-md">
            <Upload className="h-4 w-4 mr-2" />
            Subir Nuevo
          </Link>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4">
          <div className="sm:flex sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            {/* Select All + Search */}
            <div className="flex items-center space-x-4 flex-1 max-w-lg">
              {/* Select All Checkbox */}
              <div className="flex items-center">
                <label className="relative flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filteredStatements.length > 0 && selectedStatements.size === filteredStatements.length}
                    onChange={handleSelectAll}
                    className="sr-only"
                  />
                  <div className={clsx(
                    'w-5 h-5 rounded border-2 flex items-center justify-center transition-colors',
                    filteredStatements.length > 0 && selectedStatements.size === filteredStatements.length
                      ? 'bg-primary-600 border-primary-600'
                      : selectedStatements.size > 0
                      ? 'bg-primary-100 border-primary-300'
                      : 'border-gray-300 hover:border-gray-400'
                  )}>
                    {filteredStatements.length > 0 && selectedStatements.size === filteredStatements.length ? (
                      <Check className="w-3 h-3 text-white" />
                    ) : selectedStatements.size > 0 ? (
                      <Minus className="w-3 h-3 text-primary-600" />
                    ) : null}
                  </div>
                </label>
                <span className="ml-2 text-sm text-gray-600">
                  Seleccionar todos
                </span>
              </div>
              
              {/* Search */}
              <div className="flex-1">
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
          <ul className="divide-y divide-gray-200">
            {filteredStatements.map((statement) => (
              <StatementItem
                key={statement.id}
                statement={statement}
                onDelete={() => setDeleteModal({ isOpen: true, id: statement.id, isBulk: false })}
                onProcess={() => handleProcess(statement.id)}
                isDeleting={deleteStatement.isLoading && deleteStatement.variables === statement.id}
                isProcessing={processStatement.isLoading && processStatement.variables === statement.id}
                isMenuOpen={openMenuId === statement.id}
                onMenuToggle={handleMenuToggle}
                isSelected={selectedStatements.has(statement.id)}
                onSelect={() => handleSelectStatement(statement.id)}
              />
            ))}
          </ul>
        )}
      </div>

      {/* Summary Stats */}
      {filteredStatements.length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4">
            <h3 className="text-sm font-medium text-gray-900 mb-4">Resumen</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">
                  {filteredStatements.length}
                </p>
                <p className="text-sm text-gray-500">Total de estados</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {filteredStatements.reduce((sum, s) => sum + (s.total_transactions || 0), 0)}
                </p>
                <p className="text-sm text-gray-500">Total transacciones</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-600">
                  {formatCurrency(filteredStatements.reduce((sum, s) => sum + (s.total_amount || 0), 0))}
                </p>
                <p className="text-sm text-gray-500">Monto total</p>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteModal.isOpen}
        onClose={() => setDeleteModal({ isOpen: false, id: null, isBulk: false })}
        onConfirm={() => handleDelete(deleteModal.id, deleteModal.isBulk)}
        title={deleteModal.isBulk 
          ? `Eliminar ${selectedStatements.size} estados de cuenta` 
          : 'Eliminar estado de cuenta'}
        message={deleteModal.isBulk
          ? `¿Estás seguro de que deseas eliminar los ${selectedStatements.size} estados de cuenta seleccionados? Esta acción no se puede deshacer.`
          : '¿Estás seguro de que deseas eliminar este estado de cuenta? Esta acción no se puede deshacer.'}
        confirmText="Eliminar"
        cancelText="Cancelar"
        isDanger={true}
        isLoading={deleteStatement.isLoading || bulkDeleteStatements.isLoading}
      />
    </div>
  )
}

function StatementItem({ statement, onDelete, onProcess, isDeleting, isProcessing, isMenuOpen, onMenuToggle, isSelected, onSelect }) {
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
    <li className={clsx(
      'px-6 py-4 hover:bg-gray-50 transition-colors',
      isSelected && 'bg-primary-50'
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center min-w-0 flex-1">
          {/* Checkbox */}
          <div className="flex-shrink-0 mr-4">
            <label className="relative flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={isSelected}
                onChange={onSelect}
                className="sr-only"
              />
              <div className={clsx(
                'w-5 h-5 rounded border-2 flex items-center justify-center transition-colors',
                isSelected
                  ? 'bg-primary-600 border-primary-600'
                  : 'border-gray-300 hover:border-gray-400'
              )}>
                {isSelected && <Check className="w-3 h-3 text-white" />}
              </div>
            </label>
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
                {statement.filename}
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
              {formatCurrency(statement.total_amount || 0)}
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

            <div className="relative" data-menu-id={statement.id} ref={dropdownRef}>
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
                <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg z-50 border border-gray-200 overflow-hidden">
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
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        e.nativeEvent.stopImmediatePropagation();
                        onDelete();
                        // Close the dropdown menu
                        onMenuToggle(statement.id, false);
                      }}
                      disabled={isDeleting}
                      className="block w-full text-left px-4 py-2 text-sm text-red-700 hover:bg-red-50 whitespace-nowrap"
                    >
                      <Trash2 className="h-4 w-4 mr-2 inline" />
                      {isDeleting ? 'Eliminando...' : 'Eliminar'}
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