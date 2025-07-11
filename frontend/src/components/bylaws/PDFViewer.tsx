import React, { useState } from 'react';

interface PDFViewerProps {
  sourceUrl: string;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({ sourceUrl }) => {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const handleLoad = () => {
    setLoading(false);
    setError(null);
  };

  const handleError = () => {
    setLoading(false);
    setError('Failed to load PDF document');
  };

  // For now, we'll use a simple iframe approach
  // In a production app, you might want to use react-pdf for better control
  return (
    <div className="bg-white border rounded-lg overflow-hidden">
      <div className="bg-gray-50 px-4 py-3 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900">Source Document (PDF)</h3>
          <div className="flex items-center space-x-2">
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Open in new tab
            </a>
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 m-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">PDF Loading Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              <p className="text-sm text-red-700 mt-1">
                Try opening the document in a new tab or downloading it directly.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="relative" style={{ height: '600px' }}>
        <iframe
          src={sourceUrl}
          className="w-full h-full"
          onLoad={handleLoad}
          onError={handleError}
          title="PDF Document"
          style={{ display: loading || error ? 'none' : 'block' }}
        />
      </div>

      {/* Alternative PDF viewer using embed */}
      {error && (
        <div className="p-4">
          <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">PDF Preview Unavailable</h3>
            <p className="mt-1 text-sm text-gray-500">
              Unable to display PDF in browser. Use the link above to view the document.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};