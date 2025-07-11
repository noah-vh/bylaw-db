import { apiClient } from './apiService'
import { ScrapingJob, ScrapingJobCreate, DataCorrection, ScheduleConfig } from '../types/municipality.types'

export class ScrapingService {
  // Get all scraping jobs
  static async getScrapingJobs(municipalityId?: string): Promise<ScrapingJob[]> {
    try {
      const params = municipalityId ? { municipality_id: municipalityId } : {}
      const result = await apiClient.get<ScrapingJob[]>('/api/scraping/jobs', params)
      return result || []
    } catch (error) {
      console.error('Get scraping jobs error:', error)
      return []
    }
  }

  // Get a specific scraping job
  static async getScrapingJob(jobId: string): Promise<ScrapingJob> {
    try {
      const result = await apiClient.get<ScrapingJob>(`/api/scraping/jobs/${jobId}`)
      return result
    } catch (error) {
      console.error('Get scraping job error:', error)
      throw error
    }
  }

  // Create a new scraping job
  static async createScrapingJob(job: ScrapingJobCreate): Promise<ScrapingJob> {
    try {
      const result = await apiClient.post<ScrapingJob>('/api/scraping/jobs', {
        ...job,
        status: 'pending'
      })
      return result
    } catch (error) {
      console.error('Create scraping job error:', error)
      throw error
    }
  }

  // Cancel a scraping job
  static async cancelScrapingJob(jobId: string): Promise<void> {
    try {
      await apiClient.put<void>(`/api/scraping/jobs/${jobId}`, { status: 'cancelled' })
    } catch (error) {
      console.error('Cancel scraping job error:', error)
      throw error
    }
  }

  // Get scraping job statistics
  static async getScrapingStats(municipalityId?: string): Promise<{
    total_jobs: number;
    running_jobs: number;
    completed_jobs: number;
    failed_jobs: number;
    success_rate: number;
  }> {
    try {
      const params = municipalityId ? { municipality_id: municipalityId } : {}
      const result = await apiClient.get<{
        total_jobs: number;
        running_jobs: number;
        completed_jobs: number;
        failed_jobs: number;
        success_rate: number;
      }>('/api/scraping/stats', params)
      return result
    } catch (error) {
      console.error('Get scraping stats error:', error)
      return {
        total_jobs: 0,
        running_jobs: 0,
        completed_jobs: 0,
        failed_jobs: 0,
        success_rate: 0
      }
    }
  }

  // Test scraping configuration
  static async testScrapingConfig(municipalityId: string, configOverride?: any): Promise<{
    success: boolean;
    message: string;
    test_results?: {
      url_accessible: boolean;
      selectors_found: boolean;
      sample_data: any;
    };
  }> {
    try {
      // This would call a backend endpoint to test the configuration
      const response = await fetch(`/api/scraping/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          municipality_id: municipalityId,
          config_override: configOverride
        })
      })

      if (!response.ok) {
        throw new Error('Failed to test scraping configuration')
      }

      return await response.json()
    } catch (error) {
      console.error('Error testing scraping config:', error)
      throw error
    }
  }

  // Data Corrections
  static async getDataCorrections(municipalityId?: string): Promise<DataCorrection[]> {
    try {
      const params = municipalityId ? { municipality_id: municipalityId } : {}
      const result = await apiClient.get<DataCorrection[]>('/api/data-corrections', params)
      return result || []
    } catch (error) {
      console.error('Get data corrections error:', error)
      return []
    }
  }

  // Create data correction
  static async createDataCorrection(correction: Omit<DataCorrection, 'id' | 'created_at' | 'applied_at' | 'applied_by'>): Promise<DataCorrection> {
    try {
      const result = await apiClient.post<DataCorrection>('/api/data-corrections', {
        ...correction,
        status: 'pending'
      })
      return result
    } catch (error) {
      console.error('Create data correction error:', error)
      throw error
    }
  }

  // Apply data correction
  static async applyDataCorrection(correctionId: string): Promise<void> {
    try {
      await apiClient.put<void>(`/api/data-corrections/${correctionId}`, { status: 'applied' })
    } catch (error) {
      console.error('Apply data correction error:', error)
      throw error
    }
  }

  // Reject data correction
  static async rejectDataCorrection(correctionId: string): Promise<void> {
    try {
      await apiClient.put<void>(`/api/data-corrections/${correctionId}`, { status: 'rejected' })
    } catch (error) {
      console.error('Reject data correction error:', error)
      throw error
    }
  }

  // Schedule Configuration
  static async updateScheduleConfig(municipalityId: string, config: ScheduleConfig): Promise<void> {
    try {
      // Convert schedule config to cron expression
      let cronExpression = config.cron_expression

      if (config.frequency !== 'custom') {
        switch (config.frequency) {
          case 'daily':
            cronExpression = '0 2 * * *' // 2 AM daily
            break
          case 'weekly':
            cronExpression = '0 2 * * 0' // 2 AM every Sunday
            break
          case 'monthly':
            cronExpression = '0 2 1 * *' // 2 AM on 1st of month
            break
        }
      }

      await apiClient.put<void>(`/api/municipalities/${municipalityId}/schedule`, {
        scraping_schedule: cronExpression,
        scraping_enabled: config.enabled
      })
    } catch (error) {
      console.error('Update schedule config error:', error)
      throw error
    }
  }

  // Get next scheduled run time
  static async getNextScheduledRun(municipalityId: string): Promise<Date | null> {
    try {
      const result = await apiClient.get<{ next_run: string | null }>(`/api/scraping/schedule/next-run/${municipalityId}`)
      return result.next_run ? new Date(result.next_run) : null
    } catch (error) {
      console.error('Error getting next scheduled run:', error)
      return null
    }
  }
}