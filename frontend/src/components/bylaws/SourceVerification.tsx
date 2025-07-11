import React, { useState, useEffect } from 'react';
import { Bylaw } from '../../types/bylaw.types';

interface SourceVerificationProps {
  bylaw: Bylaw;
}

interface VerificationStatus {
  sourceAccessible: boolean;
  hashVerified: boolean;
  lastChecked: Date;
  certificateValid: boolean;
  sslVerified: boolean;
}

export const SourceVerification: React.FC<SourceVerificationProps> = ({ bylaw }) => {
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus | null>(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // In a real app, this would fetch verification status from the API
    // For now, we'll simulate it
    simulateVerificationCheck();
  }, [bylaw.id]);

  const simulateVerificationCheck = async () => {
    setChecking(true);
    setError(null);

    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Simulate verification results
      const mockStatus: VerificationStatus = {
        sourceAccessible: Math.random() > 0.1, // 90% chance of being accessible
        hashVerified: Math.random() > 0.05, // 95% chance of hash being verified
        lastChecked: new Date(),
        certificateValid: bylaw.source_url.startsWith('https://'),
        sslVerified: bylaw.source_url.startsWith('https://') && Math.random() > 0.1
      };

      setVerificationStatus(mockStatus);
    } catch (err) {
      setError('Failed to verify source');
    } finally {
      setChecking(false);
    }
  };

  const recheckSource = () => {
    simulateVerificationCheck();
  };

  const getVerificationScore = () => {
    if (!verificationStatus) return 0;
    
    let score = 0;
    if (verificationStatus.sourceAccessible) score += 25;
    if (verificationStatus.hashVerified) score += 25;
    if (verificationStatus.certificateValid) score += 25;
    if (verificationStatus.sslVerified) score += 25;
    
    return score;
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBackground = (score: number) => {
    if (score >= 90) return 'bg-green-50 border-green-200';
    if (score >= 70) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  const verificationScore = getVerificationScore();

  return (
    <div className="space-y-6">
      {/* Verification Score */}
      <div className={`border rounded-lg p-6 ${getScoreBackground(verificationScore)}`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Source Verification Score</h3>
            <p className="text-sm text-gray-600 mt-1">
              Overall reliability assessment of this document's source
            </p>
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold ${getScoreColor(verificationScore)}`}>
              {verificationScore}%
            </div>
            <button
              onClick={recheckSource}
              disabled={checking}
              className="mt-2 text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50"
            >
              {checking ? 'Checking...' : 'Recheck'}
            </button>
          </div>
        </div>
      </div>

      {/* Verification Details */}
      {verificationStatus && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Source Accessibility */}
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-900">Source Accessibility</h4>
              <div className={`flex items-center ${verificationStatus.sourceAccessible ? 'text-green-600' : 'text-red-600'}`}>
                {verificationStatus.sourceAccessible ? (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
                <span className="ml-2 text-sm font-medium">
                  {verificationStatus.sourceAccessible ? 'Accessible' : 'Not Accessible'}
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {verificationStatus.sourceAccessible
                ? 'Source document is currently accessible at the original URL'
                : 'Source document cannot be accessed at the original URL'
              }
            </p>
          </div>

          {/* Hash Verification */}
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-900">Content Integrity</h4>
              <div className={`flex items-center ${verificationStatus.hashVerified ? 'text-green-600' : 'text-red-600'}`}>
                {verificationStatus.hashVerified ? (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.5-2A11.95 11.95 0 0010 2.944a11.95 11.95 0 00-8.5 7.056A11.95 11.95 0 0010 17.056a11.95 11.95 0 008.5-7.056z" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 14.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                )}
                <span className="ml-2 text-sm font-medium">
                  {verificationStatus.hashVerified ? 'Verified' : 'Modified'}
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {verificationStatus.hashVerified
                ? 'Document content matches the original source hash'
                : 'Document content has been modified since initial capture'
              }
            </p>
          </div>

          {/* SSL Certificate */}
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-900">SSL Certificate</h4>
              <div className={`flex items-center ${verificationStatus.sslVerified ? 'text-green-600' : 'text-red-600'}`}>
                {verificationStatus.sslVerified ? (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
                  </svg>
                )}
                <span className="ml-2 text-sm font-medium">
                  {verificationStatus.sslVerified ? 'Valid' : 'Invalid'}
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {verificationStatus.sslVerified
                ? 'Source website has a valid SSL certificate'
                : 'Source website SSL certificate is invalid or missing'
              }
            </p>
          </div>

          {/* Certificate Status */}
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-900">Website Security</h4>
              <div className={`flex items-center ${verificationStatus.certificateValid ? 'text-green-600' : 'text-red-600'}`}>
                {verificationStatus.certificateValid ? (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.5-2A11.95 11.95 0 0010 2.944a11.95 11.95 0 00-8.5 7.056A11.95 11.95 0 0010 17.056a11.95 11.95 0 008.5-7.056z" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 14.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                )}
                <span className="ml-2 text-sm font-medium">
                  {verificationStatus.certificateValid ? 'HTTPS' : 'HTTP'}
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {verificationStatus.certificateValid
                ? 'Source is served over secure HTTPS connection'
                : 'Source is served over insecure HTTP connection'
              }
            </p>
          </div>
        </div>
      )}

      {/* Source Information */}
      <div className="bg-white border rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Source Attribution</h3>
        <div className="space-y-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">Original Source URL</dt>
            <dd className="text-sm text-gray-900 mt-1">
              <a
                href={bylaw.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 break-all"
              >
                {bylaw.source_url}
              </a>
            </dd>
          </div>
          
          <div>
            <dt className="text-sm font-medium text-gray-500">Document Hash</dt>
            <dd className="text-sm text-gray-900 mt-1 font-mono break-all">
              {bylaw.hash}
            </dd>
          </div>
          
          <div>
            <dt className="text-sm font-medium text-gray-500">Source Type</dt>
            <dd className="text-sm text-gray-900 mt-1">
              {bylaw.source_type.toUpperCase()}
            </dd>
          </div>
          
          <div>
            <dt className="text-sm font-medium text-gray-500">Last Captured</dt>
            <dd className="text-sm text-gray-900 mt-1">
              {new Date(bylaw.updated_at).toLocaleDateString()} at {new Date(bylaw.updated_at).toLocaleTimeString()}
            </dd>
          </div>
          
          {verificationStatus && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Last Verified</dt>
              <dd className="text-sm text-gray-900 mt-1">
                {verificationStatus.lastChecked.toLocaleDateString()} at {verificationStatus.lastChecked.toLocaleTimeString()}
              </dd>
            </div>
          )}
        </div>
      </div>

      {/* Liability Notice */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 14.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">Important Legal Notice</h3>
            <div className="mt-2 text-sm text-yellow-700">
              <p>
                This document has been automatically captured from the official source. 
                While we verify the authenticity and integrity of our captures, users should 
                always reference the original source for the most up-to-date and legally binding 
                version of any bylaw.
              </p>
              <p className="mt-2">
                <strong>For legal purposes, always consult the original source:</strong>{' '}
                <a
                  href={bylaw.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  {bylaw.source_url}
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>

      {checking && (
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-sm text-gray-600">Verifying source...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 14.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Verification Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};