import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BylawService } from '../services/bylawService'
import { ArrowLeft, Clock, User, FileText, ExternalLink } from 'lucide-react'
import { format } from 'date-fns'

export const BylawHistory: React.FC = () => {
  const { id } = useParams<{ id: string }>()

  // Fetch bylaw details
  const { data: bylaw, isLoading: bylawLoading } = useQuery({
    queryKey: ['bylaw', id],
    queryFn: () => BylawService.getBylawById(id!),
    enabled: !!id
  })

  // Fetch bylaw versions
  const { data: versions = [], isLoading: versionsLoading } = useQuery({
    queryKey: ['bylaw', id, 'versions'],
    queryFn: () => BylawService.getBylawVersions(id!),
    enabled: !!id
  })

  if (bylawLoading || versionsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading bylaw history...</p>
        </div>
      </div>
    )
  }

  if (!bylaw) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Bylaw Not Found</h2>
          <p className="text-gray-600 mb-4">The requested bylaw could not be found.</p>
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
            Version History
          </h1>
          
          <div className="bg-white rounded-lg shadow-sm border p-6">
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
        </div>

        {/* Version History */}
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-gray-900">
            Version History ({versions.length} versions)
          </h3>

          {versions.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-gray-900 mb-2">No Version History</h4>
              <p className="text-gray-600">
                This bylaw doesn't have any recorded version history yet.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {versions.map((version, index) => (
                <div
                  key={version.id}
                  className={`bg-white rounded-lg shadow-sm border p-6 ${
                    index === 0 ? 'ring-2 ring-primary-200' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          index === 0 
                            ? 'bg-primary-100 text-primary-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          Version {version.version_number}
                          {index === 0 && ' (Current)'}
                        </span>
                        <span className="text-sm text-gray-500">
                          {format(new Date(version.created_at), 'MMM d, yyyy • h:mm a')}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-2 text-sm text-gray-600 mb-3">
                        <User className="w-4 h-4" />
                        <span>Created by {version.created_by || 'System'}</span>
                      </div>

                      {version.change_summary && (
                        <div className="mb-4">
                          <h4 className="text-sm font-medium text-gray-900 mb-2">
                            Change Summary
                          </h4>
                          <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
                            {version.change_summary}
                          </p>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-6">
                      <a
                        href={version.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center px-3 py-1 text-sm text-primary-600 hover:text-primary-700 border border-primary-200 rounded-lg hover:bg-primary-50 transition-colors"
                      >
                        <ExternalLink className="w-4 h-4 mr-1" />
                        Source
                      </a>
                      <button className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                        <FileText className="w-4 h-4 mr-1" />
                        View Content
                      </button>
                    </div>
                  </div>

                  {/* Content Preview */}
                  <div className="mt-4 pt-4 border-t">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      Content Preview
                    </h4>
                    <div className="bg-gray-50 p-3 rounded-lg max-h-40 overflow-y-auto">
                      <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                        {version.content.substring(0, 500)}
                        {version.content.length > 500 && '...'}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Source Transparency Notice */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            Source Transparency
          </h3>
          <p className="text-sm text-blue-800 mb-4">
            All versions of this bylaw are tracked with complete audit trails. Each version 
            includes the original source document, creation timestamp, and change summary 
            to ensure full transparency and accountability.
          </p>
          <div className="flex items-center space-x-4 text-sm text-blue-700">
            <div className="flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              <span>Real-time tracking</span>
            </div>
            <div className="flex items-center">
              <FileText className="w-4 h-4 mr-1" />
              <span>Complete audit trail</span>
            </div>
            <div className="flex items-center">
              <ExternalLink className="w-4 h-4 mr-1" />
              <span>Source verification</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}