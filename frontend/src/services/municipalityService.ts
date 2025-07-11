import { apiClient } from './apiService'
import { Municipality, MunicipalityConfig } from '../types/municipality.types'

export class MunicipalityService {
  // Get all municipalities
  static async getMunicipalities(): Promise<Municipality[]> {
    try {
      const result = await apiClient.get<Municipality[]>('/api/municipalities')
      return result
    } catch (error) {
      console.error('Get municipalities error:', error)
      throw error
    }
  }

  // Get a single municipality by ID
  static async getMunicipalityById(id: string): Promise<Municipality> {
    try {
      const result = await apiClient.get<Municipality>(`/api/municipalities/${id}`)
      return result
    } catch (error) {
      console.error('Get municipality error:', error)
      throw error
    }
  }

  // Get municipalities by province
  static async getMunicipalitiesByProvince(province: string): Promise<Municipality[]> {
    try {
      const result = await apiClient.get<Municipality[]>('/api/municipalities', { province })
      return result
    } catch (error) {
      console.error('Get municipalities by province error:', error)
      throw error
    }
  }

  // Get all provinces
  static async getProvinces(): Promise<string[]> {
    try {
      const result = await apiClient.get<string[]>('/api/municipalities/provinces')
      return result
    } catch (error) {
      console.error('Get provinces error:', error)
      throw error
    }
  }

  // Create a new municipality (admin only)
  static async createMunicipality(municipality: Omit<Municipality, 'id' | 'created_at' | 'updated_at'>): Promise<Municipality> {
    try {
      const result = await apiClient.post<Municipality>('/api/municipalities', municipality)
      return result
    } catch (error) {
      console.error('Create municipality error:', error)
      throw error
    }
  }

  // Update a municipality (admin only)
  static async updateMunicipality(id: string, updates: Partial<Municipality>): Promise<Municipality> {
    try {
      const result = await apiClient.put<Municipality>(`/api/municipalities/${id}`, updates)
      return result
    } catch (error) {
      console.error('Update municipality error:', error)
      throw error
    }
  }

  // Delete a municipality (admin only)
  static async deleteMunicipality(id: string): Promise<void> {
    try {
      await apiClient.delete<void>(`/api/municipalities/${id}`)
    } catch (error) {
      console.error('Delete municipality error:', error)
      throw error
    }
  }

  // Get municipality configuration
  static async getMunicipalityConfig(municipalityId: string): Promise<MunicipalityConfig | null> {
    try {
      const result = await apiClient.get<MunicipalityConfig>(`/api/municipalities/${municipalityId}/config`)
      return result
    } catch (error) {
      console.error('Get municipality config error:', error)
      return null
    }
  }

  // Update municipality configuration (admin only)
  static async updateMunicipalityConfig(
    municipalityId: string, 
    config: Omit<MunicipalityConfig, 'id' | 'municipality_id' | 'created_at' | 'updated_at'>
  ): Promise<MunicipalityConfig> {
    try {
      const result = await apiClient.put<MunicipalityConfig>(`/api/municipalities/${municipalityId}/config`, config)
      return result
    } catch (error) {
      console.error('Update municipality config error:', error)
      throw error
    }
  }
}