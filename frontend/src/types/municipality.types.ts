export interface Municipality {
  id: string;
  name: string;
  province: string;
  type: 'city' | 'town' | 'village' | 'county' | 'district' | 'other';
  website_url?: string;
  created_at: Date;
  updated_at: Date;
}

export interface MunicipalityConfig {
  id: string;
  municipality_id: string;
  scraping_enabled: boolean;
  scraping_schedule: string;
  scraping_config: {
    base_url: string;
    selectors: {
      bylaw_links: string;
      title: string;
      number: string;
      content: string;
      date_enacted: string;
    };
    pagination?: {
      enabled: boolean;
      selector: string;
      max_pages: number;
    };
    filters?: {
      bylaw_types: BylawType[];
      keywords: string[];
      date_range?: {
        start: Date;
        end: Date;
      };
    };
  };
  last_scrape_at?: Date;
  last_scrape_status: 'success' | 'error' | 'in_progress' | 'never';
  created_at: Date;
  updated_at: Date;
}

export enum BylawType {
  ADU = 'adu',
  ZONING = 'zoning',
  BUILDING_CODES = 'building_codes',
  PLANNING = 'planning',
  DEVELOPMENT = 'development',
  LICENSING = 'licensing',
  ENVIRONMENTAL = 'environmental',
  HOUSING = 'housing',
  TRAFFIC = 'traffic',
  BYLAW_ENFORCEMENT = 'bylaw_enforcement',
  OTHER = 'other'
}

export interface ScrapingJob {
  id: string;
  municipality_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  type: 'scheduled' | 'manual' | 'retry';
  started_at?: Date;
  completed_at?: Date;
  error_message?: string;
  progress?: {
    current: number;
    total: number;
    stage: string;
  };
  result?: {
    bylaws_found: number;
    bylaws_updated: number;
    bylaws_created: number;
    bylaws_skipped: number;
    errors: string[];
  };
  created_at: Date;
  updated_at: Date;
}

export interface ScrapingJobCreate {
  municipality_id: string;
  type: 'manual' | 'retry';
  config_override?: Partial<MunicipalityConfig['scraping_config']>;
}

export interface DataCorrection {
  id: string;
  municipality_id: string;
  bylaw_id?: string;
  correction_type: 'title' | 'content' | 'date' | 'number' | 'category' | 'delete';
  original_value?: string;
  corrected_value?: string;
  reason: string;
  status: 'pending' | 'applied' | 'rejected';
  created_by: string;
  created_at: Date;
  applied_at?: Date;
  applied_by?: string;
}

export interface ScheduleConfig {
  frequency: 'daily' | 'weekly' | 'monthly' | 'custom';
  cron_expression?: string;
  timezone: string;
  enabled: boolean;
  next_run?: Date;
  last_run?: Date;
}