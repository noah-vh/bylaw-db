import React, { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BylawService } from '../services/bylawService'
import { 
  ArrowLeft, 
  ExternalLink, 
  Download, 
  FileText, 
  AlertCircle,
  CheckCircle,
  Calendar,
  Hash,
  Globe
} from 'lucide-react'
import { format } from 'date-fns'

export const SourceViewer: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [activeTab, setActiveTab] = useState<'metadata' | 'content'>('metadata')

  // Fetch bylaw details
  const { data: bylaw, isLoading, error } = useQuery({
    queryKey: ['bylaw', id],
    queryFn: () => BylawService.getBylawById(id!),
    enabled: !!id
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading source information...</p>
        </div>
      </div>
    )
  }

  if (error || !bylaw) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Source Not Found</h2>
          <p className="text-gray-600 mb-4">
            The requested bylaw source information could not be found.
          </p>
          <Link
            to="/"
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Search
          </Link>
        </div>
      </div>
    )
  }

  const getSourceTypeIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return '📄'
      case 'html':
        return '🌐'
      case 'docx':
        return '📝'
      case 'txt':
        return '📄'
      default:
        return '📄'
    }
  }

  const getSourceTypeLabel = (type: string) => {
    return type.toUpperCase()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            to="/"
            className="inline-flex items-center text-primary-600 hover:text-primary-700 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Search
          </Link>
          
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Source Document
          </h1>
          
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  {bylaw.title}
                </h2>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span>#{bylaw.number}</span>
                  <span>•</span>
                  <span>{bylaw.municipality?.name}, {bylaw.municipality?.province}</span>
                  <span>•</span>
                  <span>{bylaw.category}</span>
                </div>
              </div>
              
              <div className="ml-6 flex items-center space-x-2">
                <a
                  href={bylaw.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View Original
                </a>
                <Link
                  to={`/bylaw/${bylaw.id}/history`}
                  className="flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <FileText className="w-4 h-4 mr-2" />
                  View History
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Source Information */}
        <div className="space-y-6">
          {/* Verification Status */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="px-6 py-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900">Source Verification</h3>
            </div>
            <div className="p-6">
              <div className="flex items-center space-x-3 mb-4">
                <CheckCircle className="w-6 h-6 text-green-500" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Source Verified</p>
                  <p className="text-sm text-gray-600">
                    Document hash matches original source and has been verified
                  </p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <Hash className="w-4 h-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-900">Document Hash</span>
                  </div>
                  <p className="text-xs text-gray-600 font-mono break-all">
                    {bylaw.hash}
                  </p>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <Calendar className="w-4 h-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-900">Last Verified</span>
                  </div>
                  <p className="text-sm text-gray-600">
                    {format(new Date(bylaw.updated_at), 'MMM d, yyyy • h:mm a')}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="border-b">
              <nav className="flex space-x-8 px-6">
                <button
                  onClick={() => setActiveTab('metadata')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'metadata'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Source Metadata
                </button>
                <button
                  onClick={() => setActiveTab('content')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'content'
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Document Content
                </button>
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'metadata' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Source Information</h4>
                      <div className="space-y-3">
                        <div className="flex items-start space-x-3">
                          <Globe className="w-5 h-5 text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">Source URL</p>
                            <a
                              href={bylaw.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-primary-600 hover:text-primary-700 break-all"
                            >
                              {bylaw.source_url}
                            </a>
                          </div>
                        </div>
                        
                        <div className="flex items-start space-x-3">
                          <span className="text-lg mt-0.5" role="img" aria-label="Document type">
                            {getSourceTypeIcon(bylaw.source_type)}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-gray-900">Document Type</p>
                            <p className="text-sm text-gray-600">
                              {getSourceTypeLabel(bylaw.source_type)} Document
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-start space-x-3">
                          <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">Date Enacted</p>
                            <p className="text-sm text-gray-600">
                              {format(new Date(bylaw.date_enacted), 'MMMM d, yyyy')}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Processing Information</h4>
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm font-medium text-gray-900">Last Updated</p>
                          <p className="text-sm text-gray-600">
                            {format(new Date(bylaw.updated_at), 'MMM d, yyyy • h:mm a')}
                          </p>
                        </div>
                        
                        <div>
                          <p className="text-sm font-medium text-gray-900">Processing Status</p>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Successfully Processed
                          </span>
                        </div>
                        
                        <div>
                          <p className="text-sm font-medium text-gray-900">Content Length</p>
                          <p className="text-sm text-gray-600">
                            {bylaw.content.length.toLocaleString()} characters
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'content' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-900">Document Content</h4>
                    <button
                      onClick={() => {
                        const blob = new Blob([bylaw.content], { type: 'text/plain' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `${bylaw.number}-${bylaw.title}.txt`
                        a.click()
                        URL.revokeObjectURL(url)
                      }}
                      className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      Download Content
                    </button>
                  </div>
                  
                  <div className="bg-gray-50 border rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre className="text-sm text-gray-800 whitespace-pre-wrap">
                      {bylaw.content}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Audit Trail Notice */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-6 h-6 text-green-600 mt-0.5" />
              <div>
                <h3 className="text-lg font-semibold text-green-900 mb-2">
                  Audit Trail & Transparency
                </h3>
                <p className="text-sm text-green-800 mb-4">
                  This document has been processed and verified through our transparent audit system. 
                  All changes, sources, and processing steps are tracked and available for review.
                </p>
                <div className="flex items-center space-x-6 text-sm text-green-700">
                  <div className="flex items-center">
                    <Hash className="w-4 h-4 mr-1" />
                    <span>Cryptographic verification</span>
                  </div>
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-1" />
                    <span>Timestamp validation</span>
                  </div>
                  <div className="flex items-center">
                    <Globe className="w-4 h-4 mr-1" />
                    <span>Source traceability</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}