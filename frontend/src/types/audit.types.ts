export interface AuditTrail {
  id: string;
  bylaw_id: string;
  action: 'created' | 'updated' | 'deleted' | 'scraped' | 'manual_edit';
  changes: Record<string, { old: any; new: any }>;
  source: 'scraper' | 'admin' | 'api';
  user_id?: string;
  ip_address?: string;
  user_agent?: string;
  metadata?: Record<string, any>;
  created_at: Date;
}

export interface ScrapingJob {
  id: string;
  municipality_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at?: Date;
  completed_at?: Date;
  error_message?: string;
  stats: {
    bylaws_found: number;
    bylaws_new: number;
    bylaws_updated: number;
    bylaws_failed: number;
  };
  created_at: Date;
  updated_at: Date;
}