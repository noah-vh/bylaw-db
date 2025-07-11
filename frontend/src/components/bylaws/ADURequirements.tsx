import React, { useState, useEffect } from 'react';
import { Bylaw } from '../../types/bylaw.types';

interface ADURequirement {
  id: string;
  category: 'zoning' | 'parking' | 'size' | 'design' | 'permit' | 'other';
  requirement: string;
  value?: string;
  unit?: string;
  confidence: number;
  source_text: string;
  page_reference?: string;
}

interface ADURequirementsProps {
  bylaw: Bylaw;
}

export const ADURequirements: React.FC<ADURequirementsProps> = ({ bylaw }) => {
  const [requirements, setRequirements] = useState<ADURequirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [minConfidence, setMinConfidence] = useState(70);

  useEffect(() => {
    extractADURequirements();
  }, [bylaw.id]);

  const extractADURequirements = async () => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call to extract ADU requirements
      // In a real app, this would call an AI service to extract requirements
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Mock extracted requirements
      const mockRequirements: ADURequirement[] = [
        {
          id: '1',
          category: 'zoning',
          requirement: 'Permitted in R-1 and R-2 residential zones',
          confidence: 95,
          source_text: 'Accessory dwelling units are permitted as a conditional use in R-1 and R-2 residential zones...',
          page_reference: 'Section 4.2.1'
        },
        {
          id: '2',
          category: 'size',
          requirement: 'Maximum floor area',
          value: '1000',
          unit: 'sq ft',
          confidence: 88,
          source_text: 'The maximum floor area of an accessory dwelling unit shall not exceed 1,000 square feet...',
          page_reference: 'Section 4.2.3'
        },
        {
          id: '3',
          category: 'parking',
          requirement: 'Additional parking spaces required',
          value: '1',
          unit: 'spaces',
          confidence: 92,
          source_text: 'One additional off-street parking space shall be provided for each accessory dwelling unit...',
          page_reference: 'Section 4.2.5'
        },
        {
          id: '4',
          category: 'design',
          requirement: 'Must maintain character of neighborhood',
          confidence: 76,
          source_text: 'The design of the accessory dwelling unit shall be compatible with the architectural character of the primary dwelling and neighborhood...',
          page_reference: 'Section 4.2.4'
        },
        {
          id: '5',
          category: 'permit',
          requirement: 'Conditional use permit required',
          confidence: 98,
          source_text: 'A conditional use permit is required for all accessory dwelling units...',
          page_reference: 'Section 4.2.2'
        },
        {
          id: '6',
          category: 'size',
          requirement: 'Minimum lot size',
          value: '7000',
          unit: 'sq ft',
          confidence: 65,
          source_text: 'Properties with accessory dwelling units should have adequate lot size to accommodate the additional use...',
          page_reference: 'Section 4.2.1'
        }
      ];

      setRequirements(mockRequirements);
    } catch (err) {
      setError('Failed to extract ADU requirements');
    } finally {
      setLoading(false);
    }
  };

  const filteredRequirements = requirements.filter(req => {
    const categoryMatch = selectedCategory === 'all' || req.category === selectedCategory;
    const confidenceMatch = req.confidence >= minConfidence;
    return categoryMatch && confidenceMatch;
  });

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'text-green-600 bg-green-100';
    if (confidence >= 75) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'zoning':
        return '🏘️';
      case 'parking':
        return '🚗';
      case 'size':
        return '📏';
      case 'design':
        return '🎨';
      case 'permit':
        return '📋';
      default:
        return '📄';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'zoning':
        return 'bg-blue-100 text-blue-800';
      case 'parking':
        return 'bg-green-100 text-green-800';
      case 'size':
        return 'bg-purple-100 text-purple-800';
      case 'design':
        return 'bg-pink-100 text-pink-800';
      case 'permit':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'zoning', label: 'Zoning' },
    { value: 'parking', label: 'Parking' },
    { value: 'size', label: 'Size Requirements' },
    { value: 'design', label: 'Design Standards' },
    { value: 'permit', label: 'Permits' },
    { value: 'other', label: 'Other' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">Extracting ADU requirements...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Extraction Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header and Filters */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-blue-900">ADU Requirements Analysis</h3>
            <p className="text-sm text-blue-700 mt-1">
              AI-extracted accessory dwelling unit requirements from this bylaw
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-blue-700">Found {requirements.length} requirements</span>
            <button
              onClick={extractADURequirements}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Re-analyze
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Category</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                {categories.map(cat => (
                  <option key={cat.value} value={cat.value}>{cat.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Min Confidence</label>
              <div className="flex items-center space-x-2 mt-1">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={minConfidence}
                  onChange={(e) => setMinConfidence(Number(e.target.value))}
                  className="w-24"
                />
                <span className="text-sm text-gray-600">{minConfidence}%</span>
              </div>
            </div>
          </div>
          <div className="text-sm text-gray-600">
            Showing {filteredRequirements.length} of {requirements.length} requirements
          </div>
        </div>
      </div>

      {/* Requirements List */}
      {filteredRequirements.length === 0 ? (
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="mt-2 text-gray-500">
            No ADU requirements found matching your filters
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredRequirements.map((req) => (
            <div key={req.id} className="bg-white border rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-lg">{getCategoryIcon(req.category)}</span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(req.category)}`}>
                      {req.category.charAt(0).toUpperCase() + req.category.slice(1)}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(req.confidence)}`}>
                      {req.confidence}% confidence
                    </span>
                  </div>
                  
                  <h4 className="text-lg font-medium text-gray-900 mb-2">
                    {req.requirement}
                    {req.value && (
                      <span className="ml-2 text-blue-600 font-semibold">
                        {req.value} {req.unit}
                      </span>
                    )}
                  </h4>
                  
                  <div className="bg-gray-50 rounded-md p-3 mb-3">
                    <p className="text-sm text-gray-700 italic">
                      "{req.source_text}"
                    </p>
                  </div>
                  
                  {req.page_reference && (
                    <div className="flex items-center text-sm text-gray-500">
                      <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Reference: {req.page_reference}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Analysis Summary */}
      <div className="bg-white border rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Analysis Summary</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-600">
              {requirements.length}
            </div>
            <div className="text-sm text-blue-700">Total Requirements</div>
          </div>
          
          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-600">
              {requirements.filter(r => r.confidence >= 90).length}
            </div>
            <div className="text-sm text-green-700">High Confidence</div>
          </div>
          
          <div className="bg-yellow-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-600">
              {Math.round(requirements.reduce((sum, r) => sum + r.confidence, 0) / requirements.length)}%
            </div>
            <div className="text-sm text-yellow-700">Avg Confidence</div>
          </div>
        </div>
        
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 14.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-orange-800">AI Analysis Disclaimer</h3>
              <div className="mt-2 text-sm text-orange-700">
                <p>
                  This analysis is generated by AI and should be used as a starting point only. 
                  Requirements may be incomplete, misinterpreted, or outdated. Always consult the 
                  full bylaw text and seek professional advice for legal compliance.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};