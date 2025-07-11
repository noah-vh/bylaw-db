export interface Bylaw {
  id: string;
  municipality_id: string;
  title: string;
  number: string;
  description?: string;
  content: string;
  status: 'active' | 'repealed' | 'superseded' | 'draft';
  category: string;
  tags: string[];
  date_enacted: Date;
  date_last_amended?: Date;
  date_repealed?: Date;
  source_url: string;
  source_type: 'pdf' | 'html' | 'docx' | 'txt';
  hash: string;
  created_at: Date;
  updated_at: Date;
  municipality?: Municipality;
  versions?: BylawVersion[];
}

export interface AuditTrail {
  id: string;
  action: 'created' | 'updated' | 'deleted' | 'verified';
  timestamp: Date;
  user_id: string;
  details?: Record<string, any>;
}

export interface BylawVersion {
  id: string;
  bylaw_id: string;
  version_number: number;
  content: string;
  hash: string;
  change_summary: string;
  created_at: Date;
  created_by: string;
  source_url: string;
  audit_trail?: AuditTrail[];
}

export interface BylawSearchFilters {
  municipality_id?: string;
  category?: string;
  tags?: string[];
  status?: string;
  date_enacted_from?: Date;
  date_enacted_to?: Date;
  search_text?: string;
  property_address?: string;
  adu_categories?: string[];
  height_restrictions?: boolean;
  setback_requirements?: boolean;
  lot_size_requirements?: boolean;
  parking_requirements?: boolean;
  design_guidelines?: boolean;
}

export interface BylawSearchResult {
  bylaws: Bylaw[];
  total_count: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface Municipality {
  id: string;
  name: string;
  province: string;
  type: 'city' | 'town' | 'village' | 'county' | 'district' | 'other';
  website_url?: string;
  created_at: Date;
  updated_at: Date;
}