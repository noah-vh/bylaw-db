import { apiClient } from './apiService'
import { Bylaw, BylawVersion, BylawSearchFilters, BylawSearchResult } from '../types/bylaw.types'

export class BylawService {
  // Search bylaws with filters and pagination
  static async searchBylaws(
    filters: BylawSearchFilters = {},
    page: number = 1,
    perPage: number = 20
  ): Promise<BylawSearchResult> {
    try {
      const params: Record<string, any> = {
        page,
        per_page: perPage,
        ...filters
      }

      // Convert dates to ISO strings
      if (filters.date_enacted_from) {
        params.date_enacted_from = filters.date_enacted_from.toISOString()
      }
      if (filters.date_enacted_to) {
        params.date_enacted_to = filters.date_enacted_to.toISOString()
      }

      const result = await apiClient.get<BylawSearchResult>('/api/bylaws/search', params)
      return result
    } catch (error) {
      console.error('Search bylaws error:', error)
      throw error
    }
  }

  // Get a single bylaw by ID
  static async getBylawById(id: string): Promise<Bylaw> {
    try {
      const result = await apiClient.get<Bylaw>(`/api/bylaws/${id}`)
      return result
    } catch (error) {
      console.error('Get bylaw error:', error)
      throw error
    }
  }

  // Get bylaw versions
  static async getBylawVersions(bylawId: string): Promise<BylawVersion[]> {
    try {
      const result = await apiClient.get<BylawVersion[]>(`/api/bylaws/${bylawId}/versions`)
      return result
    } catch (error) {
      console.error('Get bylaw versions error:', error)
      throw error
    }
  }

  // Get bylaw categories
  static async getBylawCategories(): Promise<string[]> {
    try {
      const result = await apiClient.get<string[]>('/api/bylaws/categories')
      return result
    } catch (error) {
      console.error('Get bylaw categories error:', error)
      throw error
    }
  }

  // Get all unique tags
  static async getBylawTags(): Promise<string[]> {
    try {
      const result = await apiClient.get<string[]>('/api/bylaws/tags')
      return result
    } catch (error) {
      console.error('Get bylaw tags error:', error)
      throw error
    }
  }

  // Create a new bylaw (admin only)
  static async createBylaw(bylaw: Omit<Bylaw, 'id' | 'created_at' | 'updated_at'>): Promise<Bylaw> {
    try {
      const result = await apiClient.post<Bylaw>('/api/bylaws', bylaw)
      return result
    } catch (error) {
      console.error('Create bylaw error:', error)
      throw error
    }
  }

  // Update a bylaw (admin only)
  static async updateBylaw(id: string, updates: Partial<Bylaw>): Promise<Bylaw> {
    try {
      const result = await apiClient.put<Bylaw>(`/api/bylaws/${id}`, updates)
      return result
    } catch (error) {
      console.error('Update bylaw error:', error)
      throw error
    }
  }

  // Delete a bylaw (admin only)
  static async deleteBylaw(id: string): Promise<void> {
    try {
      await apiClient.delete<void>(`/api/bylaws/${id}`)
    } catch (error) {
      console.error('Delete bylaw error:', error)
      throw error
    }
  }

  // Download bylaw document
  static async downloadBylaw(id: string, filename?: string): Promise<void> {
    try {
      await apiClient.downloadFile(`/api/bylaws/${id}/download`, filename)
    } catch (error) {
      console.error('Download bylaw error:', error)
      throw error
    }
  }

  // Check property compliance
  static async checkPropertyCompliance(address: string, requirements: string[]): Promise<any> {
    try {
      const result = await apiClient.post<any>('/api/compliance/check', {
        address,
        requirements
      })
      return result
    } catch (error) {
      console.error('Check compliance error:', error)
      throw error
    }
  }

  // Geocode address
  static async geocodeAddress(address: string): Promise<any> {
    try {
      const result = await apiClient.get<any>('/api/geocode', { address })
      return result
    } catch (error) {
      console.error('Geocode error:', error)
      throw error
    }
  }

  // Verify source document
  static async verifySourceDocument(id: string): Promise<any> {
    try {
      const result = await apiClient.post<any>(`/api/bylaws/${id}/verify-source`)
      return result
    } catch (error) {
      console.error('Verify source error:', error)
      throw error
    }
  }

  // Get source verification status
  static async getSourceVerificationStatus(id: string): Promise<any> {
    try {
      const result = await apiClient.get<any>(`/api/bylaws/${id}/verification-status`)
      return result
    } catch (error) {
      console.error('Get verification status error:', error)
      throw error
    }
  }

  // Extract ADU requirements
  static async extractADURequirements(id: string): Promise<any> {
    try {
      const result = await apiClient.post<any>(`/api/bylaws/${id}/extract-adu-requirements`)
      return result
    } catch (error) {
      console.error('Extract ADU requirements error:', error)
      throw error
    }
  }

  // Get ADU requirements
  static async getADURequirements(id: string): Promise<any> {
    try {
      const result = await apiClient.get<any>(`/api/bylaws/${id}/adu-requirements`)
      return result
    } catch (error) {
      console.error('Get ADU requirements error:', error)
      throw error
    }
  }

  // Download source document
  static async downloadSourceDocument(id: string, filename?: string): Promise<void> {
    try {
      await apiClient.downloadFile(`/api/bylaws/${id}/download-source`, filename)
    } catch (error) {
      console.error('Download source document error:', error)
      throw error
    }
  }

  // Get document content as different formats
  static async getDocumentContent(id: string, format: 'text' | 'html' | 'json' = 'text'): Promise<any> {
    try {
      const result = await apiClient.get<any>(`/api/bylaws/${id}/content`, { format })
      return result
    } catch (error) {
      console.error('Get document content error:', error)
      throw error
    }
  }

  // Get document metadata
  static async getDocumentMetadata(id: string): Promise<any> {
    try {
      const result = await apiClient.get<any>(`/api/bylaws/${id}/metadata`)
      return result
    } catch (error) {
      console.error('Get document metadata error:', error)
      throw error
    }
  }
}