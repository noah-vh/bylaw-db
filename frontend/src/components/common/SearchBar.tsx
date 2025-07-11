import React, { useState } from 'react'
import { Search, Filter, X, MapPin, Home } from 'lucide-react'
import { BylawSearchFilters } from '../../types/bylaw.types'

interface SearchBarProps {
  filters: BylawSearchFilters
  onFiltersChange: (filters: BylawSearchFilters) => void
  municipalities: Array<{ id: string; name: string; province: string }>
  categories: string[]
  loading?: boolean
}

export const SearchBar: React.FC<SearchBarProps> = ({
  filters,
  onFiltersChange,
  municipalities,
  categories,
  loading
}) => {
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [searchText, setSearchText] = useState(filters.search_text || '')
  const [propertyAddress, setPropertyAddress] = useState(filters.property_address || '')
  const [searchType, setSearchType] = useState<'general' | 'address'>('general')

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchType === 'address') {
      onFiltersChange({ ...filters, property_address: propertyAddress, search_text: undefined })
    } else {
      onFiltersChange({ ...filters, search_text: searchText, property_address: undefined })
    }
  }

  const handleFilterChange = (key: keyof BylawSearchFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const clearFilters = () => {
    setSearchText('')
    setPropertyAddress('')
    onFiltersChange({})
  }

  const hasActiveFilters = Object.keys(filters).some(key => 
    key !== 'search_text' && key !== 'property_address' && filters[key as keyof BylawSearchFilters]
  )

  const aduCategories = [
    'Height Restrictions',
    'Setback Requirements', 
    'Lot Size Requirements',
    'Parking Requirements',
    'Design Guidelines'
  ]

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 space-y-4">
      {/* Search Type Toggle */}
      <div className="flex space-x-2 mb-4">
        <button
          type="button"
          onClick={() => setSearchType('general')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
            searchType === 'general'
              ? 'bg-primary-50 border-primary-200 text-primary-700'
              : 'bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100'
          }`}
        >
          <Search className="w-4 h-4" />
          <span>General Search</span>
        </button>
        <button
          type="button"
          onClick={() => setSearchType('address')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
            searchType === 'address'
              ? 'bg-primary-50 border-primary-200 text-primary-700'
              : 'bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100'
          }`}
        >
          <MapPin className="w-4 h-4" />
          <span>Property Address</span>
        </button>
      </div>

      {/* Main Search */}
      <form onSubmit={handleSearchSubmit} className="flex space-x-4">
        <div className="flex-1 relative">
          {searchType === 'general' ? (
            <>
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search bylaws by title, number, or content..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </>
          ) : (
            <>
              <Home className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Enter property address (e.g., 123 Main St, Vancouver, BC)"
                value={propertyAddress}
                onChange={(e) => setPropertyAddress(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </>
          )}
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
        <button
          type="button"
          onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          className={`px-4 py-3 rounded-lg border transition-colors ${
            showAdvancedFilters || hasActiveFilters
              ? 'bg-primary-50 border-primary-200 text-primary-700'
              : 'bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100'
          }`}
        >
          <Filter className="w-5 h-5" />
        </button>
      </form>

      {/* Advanced Filters */}
      {showAdvancedFilters && (
        <div className="space-y-6 p-4 bg-gray-50 rounded-lg">
          {/* Standard Filters */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Municipality Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Municipality
            </label>
            <select
              value={filters.municipality_id || ''}
              onChange={(e) => handleFilterChange('municipality_id', e.target.value || undefined)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Municipalities</option>
              {municipalities.map(municipality => (
                <option key={municipality.id} value={municipality.id}>
                  {municipality.name}, {municipality.province}
                </option>
              ))}
            </select>
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={filters.category || ''}
              onChange={(e) => handleFilterChange('category', e.target.value || undefined)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={filters.status || ''}
              onChange={(e) => handleFilterChange('status', e.target.value || undefined)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="repealed">Repealed</option>
              <option value="superseded">Superseded</option>
              <option value="draft">Draft</option>
            </select>
          </div>

          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date Enacted From
            </label>
            <input
              type="date"
              value={filters.date_enacted_from ? filters.date_enacted_from.toISOString().split('T')[0] : ''}
              onChange={(e) => handleFilterChange('date_enacted_from', e.target.value ? new Date(e.target.value) : undefined)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date Enacted To
            </label>
            <input
              type="date"
              value={filters.date_enacted_to ? filters.date_enacted_to.toISOString().split('T')[0] : ''}
              onChange={(e) => handleFilterChange('date_enacted_to', e.target.value ? new Date(e.target.value) : undefined)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Clear Filters */}
          <div className="flex items-end">
            <button
              type="button"
              onClick={clearFilters}
              className="w-full px-4 py-2 text-sm text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              <X className="w-4 h-4 inline mr-2" />
              Clear Filters
            </button>
          </div>
          </div>

          {/* ADU-Specific Filters */}
          <div className="border-t pt-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
              <Home className="w-5 h-5 mr-2" />
              ADU-Specific Requirements
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {aduCategories.map(category => {
                const key = category.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z_]/g, '') + '_requirements' as keyof BylawSearchFilters
                return (
                  <div key={category} className="flex items-center">
                    <input
                      type="checkbox"
                      id={key}
                      checked={Boolean(filters[key])}
                      onChange={(e) => handleFilterChange(key, e.target.checked || undefined)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                    <label htmlFor={key} className="ml-2 text-sm text-gray-700">
                      {category}
                    </label>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}