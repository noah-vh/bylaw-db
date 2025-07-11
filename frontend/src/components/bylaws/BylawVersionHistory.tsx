import React, { useState, useEffect } from 'react';
import { Bylaw, BylawVersion } from '../../types/bylaw.types';
import { BylawService } from '../../services/bylawService';

interface BylawVersionHistoryProps {
  bylaw: Bylaw;
  onVersionSelect: (version: BylawVersion) => void;
  selectedVersion: BylawVersion | null;
}

export const BylawVersionHistory: React.FC<BylawVersionHistoryProps> = ({
  bylaw,
  onVersionSelect,
  selectedVersion
}) => {
  const [versions, setVersions] = useState<BylawVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedVersion, setExpandedVersion] = useState<string | null>(null);

  useEffect(() => {
    loadVersions();
  }, [bylaw.id]);

  const loadVersions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await BylawService.getBylawVersions(bylaw.id);
      setVersions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load versions');
    } finally {
      setLoading(false);
    }
  };

  const toggleVersionExpansion = (versionId: string) => {
    setExpandedVersion(expandedVersion === versionId ? null : versionId);
  };

  const getContentPreview = (content: string, maxLength: number = 200) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  const calculateContentDiff = (version: BylawVersion) => {
    // Find the previous version
    const currentIndex = versions.findIndex(v => v.id === version.id);
    const previousVersion = versions[currentIndex + 1];
    
    if (!previousVersion) {
      return { added: version.content.length, removed: 0 };
    }

    // Simple diff calculation (in a real app, you'd use a proper diff library)
    const currentLength = version.content.length;
    const previousLength = previousVersion.content.length;
    
    return {
      added: Math.max(0, currentLength - previousLength),
      removed: Math.max(0, previousLength - currentLength)
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
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
            <h3 className="text-sm font-medium text-red-800">Error loading versions</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Current Version */}
      <div className={`bg-green-50 border-2 rounded-lg p-4 ${
        !selectedVersion ? 'border-green-300' : 'border-green-200'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-green-900">
                Current Version
                {!selectedVersion && (
                  <span className="ml-2 text-sm font-normal text-green-700">(viewing)</span>
                )}
              </h3>
              <p className="text-sm text-green-700">
                Last updated: {new Date(bylaw.updated_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {selectedVersion && (
              <button
                onClick={() => onVersionSelect(null as any)}
                className="px-3 py-1 text-sm font-medium text-green-800 bg-green-100 rounded-md hover:bg-green-200"
              >
                View Current
              </button>
            )}
            <span className="text-sm text-green-600">
              {bylaw.content.length.toLocaleString()} characters
            </span>
          </div>
        </div>
      </div>

      {/* Version History */}
      <div className="space-y-3">
        <h3 className="text-lg font-medium text-gray-900">Version History</h3>
        
        {versions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="mt-2">No version history available</p>
          </div>
        ) : (
          <div className="space-y-3">
            {versions.map((version) => {
              const isSelected = selectedVersion?.id === version.id;
              const isExpanded = expandedVersion === version.id;
              const diff = calculateContentDiff(version);
              
              return (
                <div
                  key={version.id}
                  className={`border rounded-lg p-4 ${
                    isSelected ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="h-8 w-8 bg-gray-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-600">
                            v{version.version_number}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <h4 className="text-sm font-medium text-gray-900">
                          Version {version.version_number}
                          {isSelected && (
                            <span className="ml-2 text-xs font-normal text-blue-600">(viewing)</span>
                          )}
                        </h4>
                        <p className="text-sm text-gray-500">
                          {new Date(version.created_at).toLocaleDateString()} by {version.created_by}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {/* Change indicators */}
                      <div className="flex items-center space-x-1 text-xs">
                        {diff.added > 0 && (
                          <span className="text-green-600">+{diff.added}</span>
                        )}
                        {diff.removed > 0 && (
                          <span className="text-red-600">-{diff.removed}</span>
                        )}
                      </div>
                      
                      <button
                        onClick={() => toggleVersionExpansion(version.id)}
                        className="text-gray-400 hover:text-gray-600 p-1"
                      >
                        <svg 
                          className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          fill="none" 
                          viewBox="0 0 24 24" 
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                      
                      <button
                        onClick={() => onVersionSelect(version)}
                        className="px-3 py-1 text-sm font-medium text-blue-600 bg-blue-100 rounded-md hover:bg-blue-200"
                      >
                        View
                      </button>
                    </div>
                  </div>
                  
                  {/* Change summary */}
                  <div className="mt-3">
                    <p className="text-sm text-gray-700">{version.change_summary}</p>
                  </div>
                  
                  {/* Expanded content */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <h5 className="text-sm font-medium text-gray-900 mb-2">Content Preview</h5>
                      <div className="bg-gray-50 rounded-md p-3">
                        <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                          {getContentPreview(version.content, 500)}
                        </pre>
                      </div>
                      
                      <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
                        <span>Source: {version.source_url}</span>
                        <span>{version.content.length.toLocaleString()} characters</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};