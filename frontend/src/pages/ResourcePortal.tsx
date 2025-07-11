import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { SearchBar } from '../components/common/SearchBar'
import { DataTable } from '../components/common/DataTable'
import { BylawService } from '../services/bylawService'
import { Bylaw, BylawSearchFilters } from '../types/bylaw.types'
import { ExternalLink, Calendar, MapPin, Tag, Clock, Download, AlertCircle, X, Loader2 } from 'lucide-react'
import { format } from 'date-fns'

export const ResourcePortal: React.FC = () => {
  const [filters, setFilters] = useState<BylawSearchFilters>({})
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedBylaw, setSelectedBylaw] = useState<Bylaw | null>(null)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const itemsPerPage = 20

  // Fetch search results
  const { data: searchResults, isLoading: searchLoading, error: searchError, refetch } = useQuery({
    queryKey: ['bylaws', 'search', filters, currentPage],
    queryFn: async () => {
      return await BylawService.searchBylaws(filters, currentPage, itemsPerPage)
    },
    // keepPreviousData: true, // Removed in newer versions of React Query
    // onError: (error) => {
    //   setError(error instanceof Error ? error.message : 'Search failed')
    // }
  })

  // Fetch municipalities for filters
  const { data: municipalities = [], isLoading: municipalitiesLoading } = useQuery<{ id: string; name: string; province: string }[]>({
    queryKey: ['municipalities'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/municipalities')
      if (!response.ok) {
        throw new Error('Failed to fetch municipalities')
      }
      return response.json()
    },
    // onError: (error) => {
    //   console.error('Failed to load municipalities:', error)
    // }
  })

  // Fetch categories for filters
  const { data: categories = [], isLoading: categoriesLoading } = useQuery<string[]>({
    queryKey: ['bylaws', 'categories'],
    queryFn: async () => {
      return await BylawService.getBylawCategories()
    },
    // onError: (error) => {
    //   console.error('Failed to load categories:', error)
    // }
  })

  // Note: Tags removed as they're not currently used in SearchBar

  const initialLoading = municipalitiesLoading || categoriesLoading

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [filters])

  // Trigger search when filters change
  useEffect(() => {
    refetch()
  }, [filters, currentPage, refetch])

  // Handle search error
  useEffect(() => {
    if (searchError) {
      setError(searchError instanceof Error ? searchError.message : 'Search failed')
    }
  }, [searchError])

  const handleBylawClick = (bylaw: Bylaw) => {
    setSelectedBylaw(bylaw)
  }

  const handleViewSource = (bylaw: Bylaw) => {
    window.open(bylaw.source_url, '_blank')
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handleDownload = async (bylaw: Bylaw) => {
    setDownloading(true)
    setError(null)
    try {
      const filename = `${bylaw.municipality?.name}_${bylaw.number}_${bylaw.title}.pdf`
      await BylawService.downloadBylaw(bylaw.id, filename)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Download failed'
      setError(errorMessage)
      console.error('Download failed:', error)
    } finally {
      setDownloading(false)
    }
  }

  const clearError = () => {
    setError(null)
  }

  if (initialLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading Resource Portal...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Bylaw Resource Portal
          </h1>
          <p className="text-lg text-gray-600">
            Search and explore municipal bylaws with full source transparency and audit trails
          </p>
        </div>

        {/* Error Alert */}
        {(error || searchError) && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <h3 className="text-sm font-medium text-red-800">Error</h3>
              </div>
              <button
                onClick={clearError}
                className="text-red-400 hover:text-red-600 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-sm text-red-700 mt-1">
              {error || (searchError instanceof Error ? searchError.message : 'An error occurred')}
            </p>
          </div>
        )}

        {/* Search Bar */}
        <div className="mb-8">
          <SearchBar
            filters={filters}
            onFiltersChange={setFilters}
            municipalities={municipalities as { id: string; name: string; province: string }[]}
            categories={categories as string[]}
            loading={searchLoading}
          />
        </div>

        {/* Results */}
        <div className="mb-8">
          {searchResults && searchResults.bylaws && (
            <DataTable
              bylaws={searchResults.bylaws}
              loading={searchLoading}
              onBylawClick={handleBylawClick}
              onViewSource={handleViewSource}
              pagination={{
                currentPage,
                totalPages: searchResults.total_pages,
                totalItems: searchResults.total_count,
                itemsPerPage: searchResults.per_page,
                onPageChange: handlePageChange
              }}
            />
          )}
        </div>


        {/* Bylaw Detail Modal */}
        {selectedBylaw && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex min-h-screen items-center justify-center p-4">
              <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" 
                   onClick={() => setSelectedBylaw(null)} />
              
              <div className="relative bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
                {/* Modal Header */}
                <div className="sticky top-0 bg-white border-b p-6 flex items-center justify-between">
                  <div className="flex-1">
                    <h2 className="text-2xl font-bold text-gray-900 mb-1">
                      {selectedBylaw.title}
                    </h2>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span className="flex items-center">
                        <Tag className="w-4 h-4 mr-1" />
                        #{selectedBylaw.number}
                      </span>
                      <span className="flex items-center">
                        <MapPin className="w-4 h-4 mr-1" />
                        {selectedBylaw.municipality?.name}, {selectedBylaw.municipality?.province}
                      </span>
                      <span className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        {format(new Date(selectedBylaw.date_enacted), 'MMM d, yyyy')}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedBylaw(null)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <span className="sr-only">Close</span>
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Modal Content */}
                <div className="p-6 space-y-6">
                  {/* Metadata */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Status:</span>
                      <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${
                        selectedBylaw.status === 'active' ? 'bg-green-100 text-green-800' :
                        selectedBylaw.status === 'repealed' ? 'bg-red-100 text-red-800' :
                        selectedBylaw.status === 'superseded' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {selectedBylaw.status.charAt(0).toUpperCase() + selectedBylaw.status.slice(1)}
                      </span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Category:</span>
                      <span className="ml-2 text-sm text-gray-900">{selectedBylaw.category}</span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Source Type:</span>
                      <span className="ml-2 text-sm text-gray-900 uppercase">{selectedBylaw.source_type}</span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Last Updated:</span>
                      <span className="ml-2 text-sm text-gray-900">
                        {format(new Date(selectedBylaw.updated_at), 'MMM d, yyyy')}
                      </span>
                    </div>
                  </div>

                  {/* Description */}
                  {selectedBylaw.description && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
                      <p className="text-gray-700 leading-relaxed">{selectedBylaw.description}</p>
                    </div>
                  )}

                  {/* Tags */}
                  {selectedBylaw.tags && selectedBylaw.tags.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Tags</h3>
                      <div className="flex flex-wrap gap-2">
                        {selectedBylaw.tags.map(tag => (
                          <span key={tag} className="px-3 py-1 bg-primary-100 text-primary-800 text-sm rounded-full">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Content */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Content</h3>
                    <div className="prose max-w-none">
                      <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                        <pre className="whitespace-pre-wrap text-sm text-gray-800">
                          {selectedBylaw.content}
                        </pre>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-4 pt-4 border-t">
                    <button
                      onClick={() => handleViewSource(selectedBylaw)}
                      className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                    >
                      <ExternalLink className="w-4 h-4" />
                      <span>View Original Source</span>
                    </button>
                    <button
                      onClick={() => handleDownload(selectedBylaw)}
                      disabled={downloading}
                      className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Download className="w-4 h-4" />
                      <span>{downloading ? 'Downloading...' : 'Download PDF'}</span>
                    </button>
                    <button
                      onClick={() => {/* Navigate to history */}}
                      className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                    >
                      <Clock className="w-4 h-4" />
                      <span>View History</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}