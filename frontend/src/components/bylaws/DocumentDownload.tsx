import React, { useState } from 'react';
import { Bylaw } from '../../types/bylaw.types';

interface DocumentDownloadProps {
  bylaw: Bylaw;
}

export const DocumentDownload: React.FC<DocumentDownloadProps> = ({ bylaw }) => {
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleDownload = async (type: 'source' | 'content' | 'metadata') => {
    setDownloading(type);
    
    try {
      let blob: Blob;
      let filename: string;

      switch (type) {
        case 'source':
          // Download the original source document
          if (bylaw.source_type === 'pdf') {
            // For PDF, we redirect to the source URL
            window.open(bylaw.source_url, '_blank');
            return;
          } else {
            // For other formats, create a downloadable file
            blob = new Blob([bylaw.content], { 
              type: bylaw.source_type === 'html' ? 'text/html' : 'text/plain' 
            });
            filename = `${bylaw.municipality?.name}_${bylaw.number}_source.${bylaw.source_type}`;
          }
          break;
          
        case 'content':
          // Download processed content as text
          blob = new Blob([bylaw.content], { type: 'text/plain' });
          filename = `${bylaw.municipality?.name}_${bylaw.number}_content.txt`;
          break;
          
        case 'metadata':
          // Download metadata as JSON
          const metadata = {
            id: bylaw.id,
            title: bylaw.title,
            number: bylaw.number,
            municipality: bylaw.municipality?.name,
            province: bylaw.municipality?.province,
            category: bylaw.category,
            status: bylaw.status,
            tags: bylaw.tags,
            date_enacted: bylaw.date_enacted,
            date_last_amended: bylaw.date_last_amended,
            source_url: bylaw.source_url,
            source_type: bylaw.source_type,
            hash: bylaw.hash,
            created_at: bylaw.created_at,
            updated_at: bylaw.updated_at
          };
          blob = new Blob([JSON.stringify(metadata, null, 2)], { type: 'application/json' });
          filename = `${bylaw.municipality?.name}_${bylaw.number}_metadata.json`;
          break;
          
        default:
          return;
      }

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename.replace(/[^a-zA-Z0-9._-]/g, '_');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="relative">
      <div className="flex items-center space-x-2">
        {/* Source Document Download */}
        <button
          onClick={() => handleDownload('source')}
          disabled={downloading === 'source'}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          title="Download original source document"
        >
          {downloading === 'source' ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          ) : (
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          )}
          {bylaw.source_type.toUpperCase()}
        </button>

        {/* Dropdown for other downloads */}
        <div className="relative">
          <button
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            onClick={() => {
              const dropdown = document.getElementById('download-dropdown');
              if (dropdown) {
                dropdown.classList.toggle('hidden');
              }
            }}
          >
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            More
            <svg className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div
            id="download-dropdown"
            className="hidden absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-10"
          >
            <div className="py-1">
              <button
                onClick={() => handleDownload('content')}
                disabled={downloading === 'content'}
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
              >
                {downloading === 'content' ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                ) : (
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                )}
                Content (TXT)
              </button>
              
              <button
                onClick={() => handleDownload('metadata')}
                disabled={downloading === 'metadata'}
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
              >
                {downloading === 'metadata' ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                ) : (
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                )}
                Metadata (JSON)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};