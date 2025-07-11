import React, { useState } from 'react'
import { BylawService } from '../services/bylawService'
import { 
  MapPin, 
  Search, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Clock,
  FileText,
  Home,
  Building,
  Ruler,
  Car,
  Info
} from 'lucide-react'

interface ComplianceResult {
  compliant: boolean
  requirements: {
    type: string
    description: string
    status: 'compliant' | 'non-compliant' | 'warning'
    details: string
  }[]
  summary: {
    total: number
    compliant: number
    warnings: number
    violations: number
  }
}

export const ComplianceChecker: React.FC = () => {
  const [address, setAddress] = useState('')
  const [selectedRequirements, setSelectedRequirements] = useState<string[]>([])
  const [isChecking, setIsChecking] = useState(false)
  const [results, setResults] = useState<ComplianceResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const availableRequirements = [
    { id: 'height', label: 'Height Restrictions', icon: Building },
    { id: 'setback', label: 'Setback Requirements', icon: Ruler },
    { id: 'lot-size', label: 'Lot Size Requirements', icon: Home },
    { id: 'parking', label: 'Parking Requirements', icon: Car },
    { id: 'adu', label: 'ADU Regulations', icon: Building },
    { id: 'zoning', label: 'Zoning Compliance', icon: FileText }
  ]

  const handleRequirementToggle = (requirementId: string) => {
    setSelectedRequirements(prev => 
      prev.includes(requirementId)
        ? prev.filter(id => id !== requirementId)
        : [...prev, requirementId]
    )
  }

  const handleComplianceCheck = async () => {
    if (!address.trim()) {
      setError('Please enter a property address')
      return
    }

    if (selectedRequirements.length === 0) {
      setError('Please select at least one requirement to check')
      return
    }

    setIsChecking(true)
    setError(null)
    setResults(null)

    try {
      // First geocode the address
      await BylawService.geocodeAddress(address)
      
      // Then check compliance
      const complianceResult = await BylawService.checkPropertyCompliance(
        address,
        selectedRequirements
      )

      setResults(complianceResult)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check compliance')
    } finally {
      setIsChecking(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle2 className="w-5 h-5 text-green-600" />
      case 'non-compliant':
        return <XCircle className="w-5 h-5 text-red-600" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />
      default:
        return <Info className="w-5 h-5 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'non-compliant':
        return 'bg-red-50 border-red-200 text-red-800'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Property Compliance Checker
          </h1>
          <p className="text-lg text-gray-600">
            Check if your property meets municipal bylaw requirements
          </p>
        </div>

        {/* Main Form */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-8">
          <div className="space-y-6">
            {/* Address Input */}
            <div>
              <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-2">
                Property Address
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  id="address"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="123 Main Street, Toronto, ON"
                />
              </div>
            </div>

            {/* Requirements Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Select Requirements to Check
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {availableRequirements.map((requirement) => (
                  <label
                    key={requirement.id}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedRequirements.includes(requirement.id)
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedRequirements.includes(requirement.id)}
                      onChange={() => handleRequirementToggle(requirement.id)}
                      className="sr-only"
                    />
                    <requirement.icon className="w-5 h-5 mr-3 text-gray-600" />
                    <span className="text-sm font-medium">{requirement.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <XCircle className="w-5 h-5 text-red-500 mr-2" />
                  <span className="text-sm text-red-700">{error}</span>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              onClick={handleComplianceCheck}
              disabled={isChecking}
              className="w-full bg-primary-600 text-white py-3 px-4 rounded-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isChecking ? (
                <div className="flex items-center justify-center">
                  <Clock className="w-5 h-5 animate-spin mr-2" />
                  Checking Compliance...
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <Search className="w-5 h-5 mr-2" />
                  Check Compliance
                </div>
              )}
            </button>
          </div>
        </div>

        {/* Results */}
        {results && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Compliance Summary
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {results.summary.total}
                  </div>
                  <div className="text-sm text-gray-600">Total Checks</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {results.summary.compliant}
                  </div>
                  <div className="text-sm text-gray-600">Compliant</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">
                    {results.summary.warnings}
                  </div>
                  <div className="text-sm text-gray-600">Warnings</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {results.summary.violations}
                  </div>
                  <div className="text-sm text-gray-600">Violations</div>
                </div>
              </div>
            </div>

            {/* Detailed Results */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Detailed Results
              </h2>
              <div className="space-y-4">
                {results.requirements.map((requirement, index) => (
                  <div
                    key={index}
                    className={`border rounded-lg p-4 ${getStatusColor(requirement.status)}`}
                  >
                    <div className="flex items-start">
                      <div className="mr-3 mt-0.5">
                        {getStatusIcon(requirement.status)}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 mb-1">
                          {requirement.type}
                        </h3>
                        <p className="text-sm text-gray-700 mb-2">
                          {requirement.description}
                        </p>
                        <p className="text-sm text-gray-600">
                          {requirement.details}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Next Steps */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                Next Steps
              </h3>
              <div className="text-sm text-blue-800 space-y-2">
                <p>• Review any violations or warnings identified above</p>
                <p>• Contact your municipality for specific guidance on compliance</p>
                <p>• Consider consulting with a professional for complex requirements</p>
                <p>• Keep documentation of all compliance checks for your records</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}