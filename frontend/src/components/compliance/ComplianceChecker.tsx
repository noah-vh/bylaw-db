import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BylawService } from '../../services/bylawService'
import { CheckCircle, XCircle, AlertCircle, Home, MapPin, Search, Loader2 } from 'lucide-react'

interface ComplianceResult {
  requirement: string
  compliant: boolean
  details: string
  bylaw_reference?: string
}

interface ComplianceResponse {
  address: string
  municipality: string
  province: string
  compliance_results: ComplianceResult[]
  overall_compliant: boolean
  warnings: string[]
}

export const ComplianceChecker: React.FC = () => {
  const [address, setAddress] = useState('')
  const [requirements, setRequirements] = useState<string[]>([])
  const [showResults, setShowResults] = useState(false)

  const availableRequirements = [
    'Height Restrictions',
    'Setback Requirements',
    'Lot Size Requirements',
    'Parking Requirements',
    'Design Guidelines',
    'Density Limits',
    'Fire Safety Requirements',
    'Accessibility Requirements'
  ]

  const { 
    data: complianceResults, 
    isLoading, 
    error, 
    refetch 
  } = useQuery<ComplianceResponse>({
    queryKey: ['compliance', address, requirements],
    queryFn: () => BylawService.checkPropertyCompliance(address, requirements),
    enabled: false
  })

  const handleRequirementToggle = (requirement: string) => {
    setRequirements(prev => 
      prev.includes(requirement) 
        ? prev.filter(r => r !== requirement)
        : [...prev, requirement]
    )
  }

  const handleCheckCompliance = async () => {
    if (!address.trim() || requirements.length === 0) {
      return
    }
    
    setShowResults(true)
    await refetch()
  }

  const getStatusIcon = (compliant: boolean) => {
    return compliant ? (
      <CheckCircle className="w-5 h-5 text-green-500" />
    ) : (
      <XCircle className="w-5 h-5 text-red-500" />
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center">
          <Home className="w-6 h-6 mr-2" />
          Property Compliance Checker
        </h2>
        <p className="text-gray-600">
          Check if your property meets ADU development requirements based on current bylaws.
        </p>
      </div>

      {/* Address Input */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Property Address
        </label>
        <div className="relative">
          <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="Enter property address (e.g., 123 Main St, Vancouver, BC)"
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      {/* Requirements Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Select Requirements to Check
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {availableRequirements.map(requirement => (
            <div key={requirement} className="flex items-center">
              <input
                type="checkbox"
                id={requirement}
                checked={requirements.includes(requirement)}
                onChange={() => handleRequirementToggle(requirement)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor={requirement} className="ml-3 text-sm text-gray-700">
                {requirement}
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Check Button */}
      <div className="mb-6">
        <button
          onClick={handleCheckCompliance}
          disabled={!address.trim() || requirements.length === 0 || isLoading}
          className="w-full px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
          ) : (
            <Search className="w-5 h-5 mr-2" />
          )}
          {isLoading ? 'Checking Compliance...' : 'Check Compliance'}
        </button>
      </div>

      {/* Results */}
      {showResults && (
        <div className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <XCircle className="w-5 h-5 text-red-500 mr-2" />
                <h3 className="text-sm font-medium text-red-800">Error Checking Compliance</h3>
              </div>
              <p className="text-sm text-red-700 mt-1">
                {error instanceof Error ? error.message : 'An error occurred while checking compliance'}
              </p>
            </div>
          )}

          {complianceResults && (
            <div className="space-y-4">
              {/* Overall Status */}
              <div className={`rounded-lg p-4 border ${
                complianceResults.overall_compliant 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center">
                  {getStatusIcon(complianceResults.overall_compliant)}
                  <h3 className={`ml-2 font-medium ${
                    complianceResults.overall_compliant 
                      ? 'text-green-800' 
                      : 'text-red-800'
                  }`}>
                    {complianceResults.overall_compliant 
                      ? 'Property is compliant' 
                      : 'Property has compliance issues'}
                  </h3>
                </div>
                <p className={`text-sm mt-1 ${
                  complianceResults.overall_compliant 
                    ? 'text-green-700' 
                    : 'text-red-700'
                }`}>
                  {complianceResults.address} - {complianceResults.municipality}, {complianceResults.province}
                </p>
              </div>

              {/* Warnings */}
              {complianceResults.warnings && complianceResults.warnings.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <AlertCircle className="w-5 h-5 text-yellow-500 mr-2" />
                    <h3 className="font-medium text-yellow-800">Warnings</h3>
                  </div>
                  <ul className="text-sm text-yellow-700 space-y-1">
                    {complianceResults.warnings.map((warning, index) => (
                      <li key={index}>• {warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Detailed Results */}
              <div className="space-y-3">
                <h3 className="font-medium text-gray-900">Compliance Details</h3>
                {complianceResults.compliance_results.map((result, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center">
                        {getStatusIcon(result.compliant)}
                        <span className="ml-2 font-medium text-gray-900">
                          {result.requirement}
                        </span>
                      </div>
                      <span className={`text-sm px-2 py-1 rounded ${
                        result.compliant 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {result.compliant ? 'Compliant' : 'Non-compliant'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-2">{result.details}</p>
                    {result.bylaw_reference && (
                      <p className="text-xs text-blue-600 mt-1">
                        Reference: {result.bylaw_reference}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}