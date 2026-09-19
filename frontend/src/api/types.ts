export type UserRole = 'OWNER' | 'STAFF' | 'OUTSIDER';

export type StatementStatus = 'PENDING' | 'PROCESSING' | 'CONFIRMED' | 'FLAGGED' | 'REJECTED';

export type Direction = 'IN' | 'OUT';

export type ReviewStatus = 'PENDING' | 'COMPLETED';

export type ReviewDecision = 'APPROVED' | 'REJECTED';

export interface User {
  id: string;
  name: string;
  phone: string;
  is_active: boolean;
  is_phone_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface Shop {
  id: string;
  name: string;
  owner_id: string;
  is_active: boolean;
  role?: UserRole;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: string;
  shop_id: string;
  name: string;
  default_unit: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ShopMember {
  id: string;
  shop_id: string;
  user_id: string;
  role: UserRole;
  status: 'ACTIVE' | 'INACTIVE';
  name?: string;
  phone?: string;
  created_at: string;
  updated_at: string;
}

export interface InventoryItem {
  product_id: string;
  product_name: string;
  default_unit: string;
  current_stock: number | null;
  baseline_quantity: number | null;
  confirmed_in: number;
  confirmed_out: number;
  unit: string | null;
  has_baseline: boolean;
  baseline_date?: string;
}

export interface Statement {
  id: string;
  shop_id: string;
  actor_id: string | null;
  product_id: string | null;
  voice_profile_id: string | null;
  speaker_status: string;
  speaker_confidence: number | null;
  transcript: string | null;
  raw_claim: {
    product?: string;
    quantity?: number;
    unit?: string;
    direction?: string;
    actor?: string;
    event_time?: string | null;
  } | null;
  quantity: number | null;
  unit: string | null;
  direction: Direction | null;
  status: StatementStatus;
  decision: string | null;
  source: string;
  is_overridden: boolean;
  override_reason?: string | null;
  override_at?: string | null;
  created_at: string;
  updated_at: string;
  processing?: {
    trust_score: number | null;
    plausibility_passed: boolean;
    contradiction_detected: boolean;
    decision_explanation: string | null;
    asr_provider: string | null;
    asr_language: string | null;
  };
}

export interface ReviewItem {
  id: string;
  statement_id: string;
  shop_id: string;
  reviewer_id: string | null;
  status: ReviewStatus;
  decision: ReviewDecision | null;
  reason: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  statement?: {
    transcript: string | null;
    speaker_status: string;
    speaker_confidence: number | null;
    product_id: string | null;
    quantity: number | null;
    unit: string | null;
    direction: Direction | null;
    raw_claim: Record<string, unknown> | null;
  };
  processing?: {
    trust_score: number | null;
    plausibility_passed: boolean;
    plausibility_result: Record<string, unknown> | null;
    contradiction_detected: boolean;
    contradiction_result: Record<string, unknown> | null;
    decision_explanation: string | null;
  };
}

export interface VocabularyEntry {
  id: string;
  shop_id: string;
  source_term: string;
  mapping_type: 'PRODUCT_ALIAS' | 'UNIT_ALIAS' | 'UNIT_CONVERSION';
  target_product_id: string | null;
  target_unit: string | null;
  conversion_factor: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface VoiceProfile {
  id: string;
  user_id: string;
  shop_id: string;
  enrollment_status: 'ENROLLED' | 'LOW_QUALITY' | 'FAILED';
  quality_score: number;
  audio_duration_seconds: number;
  model_version: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardData {
  total_products: number;
  inventory_summary: InventoryItem[];
  sales_today: number;
  incoming_today: number;
  pending_reviews: number;
  low_stock_count: number;
  low_stock_products: InventoryItem[];
  recent_activity: Array<{
    id: string;
    direction: Direction | null;
    quantity: number | null;
    unit: string | null;
    status: StatementStatus;
    product_id: string | null;
    transcript: string | null;
    created_at: string;
  }>;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: {
    code: string;
    message: string;
  };
}
