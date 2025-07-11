import React, { useState, useEffect } from 'react';
import { Bylaw, BylawVersion } from '../../types/bylaw.types';
import { BylawService } from '../../services/bylawService';
import { BylawVersionHistory } from './BylawVersionHistory';
import { SourceVerification } from './SourceVerification';
import { ADURequirements } from './ADURequirements';
import { DocumentDownload } from './DocumentDownload';
import { PDFViewer } from './PDFViewer';

interface BylawViewerProps {
  bylawId: string;
  onClose?: () => void;
}

export const BylawViewer: React.FC<BylawViewerProps> = ({ bylawId, onClose }) => {
  const [bylaw, setBylaw] = useState<Bylaw | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<BylawVersion | null>(null);
  const [activeTab, setActiveTab] = useState<'content' | 'versions' | 'source' | 'adu'>('content');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBylaw();
  }, [bylawId]);

  const loadBylaw = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await BylawService.getBylawById(bylawId);
      setBylaw(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bylaw');
    } finally {
      setLoading(false);
    }
  };

  const handleVersionSelect = (version: BylawVersion) => {
    setSelectedVersion(version);
  };

  const getDisplayContent = () => {
    if (selectedVersion) {
      return selectedVersion.content;
    }
    return bylaw?.content || '';
  };

  const getDisplayDate = () => {
    if (selectedVersion) {
      return new Date(selectedVersion.created_at).toLocaleDateString();
    }
    return bylaw?.date_last_amended 
      ? new Date(bylaw.date_last_amended).toLocaleDateString()
      : new Date(bylaw?.date_enacted || '').toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
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
            <h3 className="text-sm font-medium text-red-800">Error loading bylaw</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!bylaw) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Bylaw not found</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 px-6 py-4 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{bylaw.title}</h1>
            <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
              <span>Bylaw #{bylaw.number}</span>
              <span>{bylaw.municipality?.name}, {bylaw.municipality?.province}</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                bylaw.status === 'active' ? 'bg-green-100 text-green-800' :
                bylaw.status === 'repealed' ? 'bg-red-100 text-red-800' :
                bylaw.status === 'superseded' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {bylaw.status.charAt(0).toUpperCase() + bylaw.status.slice(1)}
              </span>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <DocumentDownload bylaw={bylaw} />
            {onClose && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 p-2"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          {[
            { id: 'content', name: 'Content', icon: '📄' },
            { id: 'versions', name: 'Version History', icon: '📋' },
            { id: 'source', name: 'Source Verification', icon: '🔍' },
            { id: 'adu', name: 'ADU Requirements', icon: '🏠' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
            >
              <span>{tab.icon}</span>
              <span>{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'content' && (
          <div className="space-y-6">
            {/* Version indicator */}
            {selectedVersion && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-blue-800">
                      Viewing Version {selectedVersion.version_number}
                    </h3>
                    <p className="text-sm text-blue-600 mt-1">
                      Created on {getDisplayDate()}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedVersion(null)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    View Current Version
                  </button>
                </div>
              </div>
            )}

            {/* PDF Viewer for PDF documents */}
            {bylaw.source_type === 'pdf' && (
              <PDFViewer sourceUrl={bylaw.source_url} />
            )}

            {/* Content Display */}
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Document Content</h2>
                <span className="text-sm text-gray-500">
                  Last updated: {getDisplayDate()}
                </span>
              </div>
              
              <div className="prose max-w-none">
                {bylaw.source_type === 'html' ? (
                  <div dangerouslySetInnerHTML={{ __html: getDisplayContent() }} />
                ) : (
                  <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                    {getDisplayContent()}
                  </pre>
                )}
              </div>
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white border rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-3">Document Information</h3>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Category</dt>
                    <dd className="text-sm text-gray-900">{bylaw.category}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Date Enacted</dt>
                    <dd className="text-sm text-gray-900">
                      {new Date(bylaw.date_enacted).toLocaleDateString()}
                    </dd>
                  </div>
                  {bylaw.date_last_amended && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Last Amended</dt>
                      <dd className="text-sm text-gray-900">
                        {new Date(bylaw.date_last_amended).toLocaleDateString()}
                      </dd>
                    </div>
                  )}
                </dl>
              </div>

              <div className="bg-white border rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-3">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {bylaw.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'versions' && (
          <BylawVersionHistory 
            bylaw={bylaw} 
            onVersionSelect={handleVersionSelect}
            selectedVersion={selectedVersion}
          />
        )}

        {activeTab === 'source' && (
          <SourceVerification bylaw={bylaw} />
        )}

        {activeTab === 'adu' && (
          <ADURequirements bylaw={bylaw} />
        )}
      </div>
    </div>
  );
};