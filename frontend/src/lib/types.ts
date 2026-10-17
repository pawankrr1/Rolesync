/**
 * Core Domain TypeScript Definitions for Career Intelligence.
 * Shared across UI components, mock data, and API services.
 */

export type MatchGrade =
  | "Exceptional Match"
  | "High Alignment"
  | "Moderate Potential"
  | "Needs Upskilling";

export type SkillStatus = "strong_match" | "partial_match" | "missing";

export type PriorityTier =
  | "P1 - Foundational (Learn First)"
  | "P2 - Core Competency"
  | "P3 - Advanced / Capstone";

export type TransitionFeasibility =
  | "Immediate / High Feasibility"
  | "Moderate Bridge Required"
  | "Long-term Pivot";

export interface SkillItem {
  id: string;
  name: string;
  category: string;
  confidence?: number;
  confidence_level?: "High" | "Medium" | "Low" | string;
  confidence_note?: string;
  frequency?: number;
  status?: SkillStatus;
  evidence?: string[];
  notes?: string;
}

export interface FactorBreakdownItem {
  name: string;
  rawScore: number;
  weight: number;
  weightedScore: number;
  maxPoints: number;
  explanation: string;
}

export interface SkillGapItem {
  id: string;
  name: string;
  category: string;
  status: SkillStatus;
  priorityRank: number;
  priorityTier: PriorityTier;
  priorityScore: number;
  prerequisitesMet: boolean;
  unmetPrerequisites: string[];
  unblocksSkills: string[];
  learningEffortWeeks: string;
  reasoning: string;
  why_missing?: string;
}

export interface LearningResource {
  title: string;
  provider: string;
  type: string;
  estimatedHours: number;
  url: string;
  isFree: boolean;
  rating: number;
}

export interface RoadmapMilestoneItem {
  stepNumber: number;
  phaseTitle: string;
  skillName: string;
  category: string;
  duration: string;
  prerequisiteContext: string;
  resources: LearningResource[];
  projectChallenge: string;
  outcomes: string[];
  why_recommended?: string;
}

export interface AdjacentRoleItem {
  id: string;
  title: string;
  category: string;
  alignmentScore: number;
  scoreGrade: MatchGrade;
  overlappingSkills: string[];
  missingBridgeSkills: string[];
  feasibility: TransitionFeasibility;
  rationale: string;
  why_recommended?: string;
}

export interface CandidateAnalysisSummary {
  candidateName: string;
  targetRole: string;
  overallScore: number;
  scoreGrade: MatchGrade;
  totalSkillsDetected: number;
  requiredCoveragePct: number;
  factors: FactorBreakdownItem[];
  matchedSkills: SkillItem[];
  partialSkills: SkillItem[];
  missingSkills: SkillItem[];
  prioritizedGaps: SkillGapItem[];
  milestones: RoadmapMilestoneItem[];
  adjacentRoles: AdjacentRoleItem[];
  narrative: string;
}

export interface RecruiterApplicantItem {
  id: string;
  name: string;
  filename: string;
  score: number;
  grade: MatchGrade;
  requiredCoverage: number;
  matchedCount: number;
  missingKeySkills: string[];
  topSkills: string[];
  experienceYears: number;
  status: "Reviewed" | "Shortlisted" | "Under Review";
}

export interface MarketInsightMetric {
  title: string;
  value: string;
  trend: string;
  isPositive: boolean;
  description: string;
}

// ============================================================================
// Real Backend API Intelligence Types
// ============================================================================

export interface BackendExtractedSkill {
  name: string;
  canonical_name: string;
  canonical_id: string;
  confidence: number;
  evidence: string;
  source: string;
  category: string;
  frequency?: number;
  evidence_snippets?: string[];
  confidence_level?: "High" | "Medium" | "Low" | string;
  confidence_note?: string;
}

export interface BackendSkillExtractionResponse {
  skills: BackendExtractedSkill[];
  extraction_metadata: {
    total_detected: number;
    total_canonical_unique: number;
    average_confidence: number;
    categories_detected: string[];
    processing_time_ms?: number;
  };
  system_disclaimer?: string;
}

export interface BackendMatchItem {
  skill: string;
  status: "matched" | "partial" | "missing" | string;
  contribution: number;
  evidence: string;
  category?: string;
  is_required?: boolean;
  why_missing?: string;
}

export interface BackendDetailedSkillMatch {
  skill_id: string;
  canonical_name: string;
  category: string;
  status: "strong_match" | "partial_match" | "missing" | string;
  is_required: boolean;
  confidence: number;
  evidence: string[];
  notes?: string;
  why_missing?: string;
}

export interface BackendMatchingResponse {
  candidate_id?: string;
  target_role_title: string;
  final_match_score: number;
  overall_match_score?: number;
  score_grade: string;
  why_score?: string;
  system_disclaimer?: string;
  required_skill_coverage: number;
  preferred_skill_coverage: number;
  semantic_similarity: number;
  experience_alignment: number;
  strong_matches: BackendMatchItem[];
  partial_matches: BackendMatchItem[];
  missing_skills: BackendMatchItem[];
  detailed_skill_matches?: BackendDetailedSkillMatch[];
  why_match: string[];
  why_not_match: string[];
  top_strengths: string[];
  top_gaps: string[];
  explainability_narrative?: string;
  weights_used?: {
    required_coverage: number;
    semantic_similarity: number;
    experience_alignment: number;
    preferred_coverage: number;
  };
}

export interface BackendGapItem {
  skill: string;
  skill_id: string;
  canonical_name: string;
  category: string;
  classification: "STRONG" | "PARTIAL" | "MISSING" | string;
  priority: "HIGH" | "MEDIUM" | "LOW" | string;
  importance: string;
  importance_score?: number;
  priority_score?: number;
  reason: string;
  reasoning?: string;
  why_missing?: string;
  recommended_next_action?: string;
  learning_effort_weeks: string;
  prerequisites: string[];
  unblocks: string[];
  is_required: boolean;
  gap_status?: string;
}

export interface BackendGapResponse {
  target_role_title: string;
  target_role_id?: string;
  gap_score: number;
  readiness_percentage: number;
  strong_skills: BackendGapItem[];
  partial_skills: BackendGapItem[];
  missing_skills: BackendGapItem[];
  priority_order: BackendGapItem[];
  system_disclaimer?: string;
}

export interface BackendCourseResource {
  title: string;
  provider: string;
  type: string;
  url: string | null;
  estimated_hours: number;
  is_free: boolean;
  rating: number;
}

export interface BackendRoadmapItem {
  skill: string;
  skill_id: string;
  priority: "HIGH" | "MEDIUM" | "LOW" | string;
  reason: string;
  why_recommended?: string;
  prerequisites: string[];
  prerequisite?: string | null;
  recommended_sequence: number;
  estimated_learning_stage: string;
  estimated_duration_weeks: string;
  available_learning_resources: BackendCourseResource[];
  hands_on_project: string;
  learning_outcomes: string[];
  step_number?: number;
  stage_phase?: string;
  skill_name?: string;
}

export interface BackendRoadmapResponse {
  target_role: string;
  target_role_id: string;
  total_estimated_weeks: number;
  total_milestones: number;
  readiness_before: number;
  projected_readiness_after: number;
  pedagogical_strategy: string;
  roadmap: BackendRoadmapItem[];
  prioritized_learning_plan?: BackendRoadmapItem[];
  system_disclaimer?: string;
}

export interface BackendRecommendedRole {
  role: string;
  role_id: string;
  category?: string;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  reason: string;
  why_recommended?: string;
  next_skills_to_learn: string[];
  vector_similarity?: number;
  skill_coverage?: number;
  experience_compatibility?: string;
  market_demand_index?: number;
}

export interface BackendAdjacentRole {
  role_id: string;
  role_title: string;
  category: string;
  alignment_score: number;
  score_grade: string;
  overlapping_skills: string[];
  missing_bridge_skills: string[];
  transition_feasibility: string;
  why_recommended: string;
}

export interface BackendRoleRecommendationResponse {
  target_role?: string;
  recommended_roles: BackendRecommendedRole[];
  adjacent_roles: BackendAdjacentRole[];
  system_disclaimer?: string;
}

export interface CandidateFullAnalysisResult {
  candidateName: string;
  targetRole: string;
  targetRoleId: string;
  overallScore: number;
  scoreGrade: MatchGrade;
  whyScore?: string;
  systemDisclaimer?: string;
  extractedSkills: BackendExtractedSkill[];
  matching: BackendMatchingResponse;
  gaps: BackendGapResponse;
  roadmap: BackendRoadmapResponse;
  recommendations: BackendRoleRecommendationResponse;
  narrative: string;
  factors: FactorBreakdownItem[];
  timestamp: string;
}

// ============================================================================
// Recruiter Screening & Talent Ranking Types
// ============================================================================

export interface RecruiterCandidateInput {
  id?: string;
  name: string;
  email?: string;
  filename?: string;
  current_title?: string;
  location?: string;
  resume_text?: string;
  candidate_skills?: (string | BackendExtractedSkill | Record<string, any>)[];
  experience_years?: number;
  education?: any;
}

export interface SkillEvidenceItem {
  skill: string;
  status: "strong" | "partial" | "missing";
  evidence: string;
  has_direct_quote: boolean;
}

export interface HiringRiskAssessment {
  level: "LOW RISK" | "MEDIUM RISK" | "HIGH RISK";
  badge_variant: "success" | "warning" | "error";
  indicators: string[];
  rationale: string;
}

export interface AdjacentTalentInfo {
  is_adjacent: boolean;
  source_role?: string;
  near_match_label?: string;
  bridge_skills?: string[];
  rationale?: string;
}

export interface CandidateDetailedExplanation {
  match_score_display: string;
  matched: string[];
  partial: string[];
  missing: string[];
  matched_details?: BackendMatchItem[];
  partial_details?: BackendMatchItem[];
  missing_details?: BackendMatchItem[];
  why_match?: string[];
  why_not_match?: string[];
  top_strengths?: string[];
  top_gaps?: string[];
  factor_breakdown?: Record<string, number>;
  evidence_list?: SkillEvidenceItem[];
}

export interface RankedCandidateItem {
  rank: number;
  candidate_id: string;
  name: string;
  email?: string;
  current_title?: string;
  filename: string;
  match_score: number;
  score_grade: string;
  required_skill_coverage_ratio?: string;
  required_skills_count?: number;
  matched_required_count?: number;
  preferred_skill_coverage_ratio?: string;
  strong_skills: string[];
  partial_skills: string[];
  missing_skills: string[];
  experience_years: number;
  experience_display: string;
  experience_fit_label?: string;
  top_skill_gap?: string;
  recommendation_status?: "Recommended" | "Review" | "Consider Bridge" | string;
  hiring_risk?: HiringRiskAssessment;
  adjacent_talent?: AdjacentTalentInfo;
  reason: string;
  alignment_statement: string;
  detailed_explanation: CandidateDetailedExplanation;
  resume_text?: string;
}

export interface RecruiterRankResponse {
  job_title: string;
  required_skills: string[];
  preferred_skills: string[];
  total_candidates_evaluated: number;
  ranked_candidates: RankedCandidateItem[];
  top_candidate_statement: string;
  disclaimer: string;
  responsible_matching?: string;
}

export interface RecruiterJobItem {
  id: string;
  title: string;
  company?: string;
  location: string;
  experience_years_min: number;
  description: string;
  required_skills: string[];
  preferred_skills: string[];
  candidates_count: number;
  strong_matches_count: number;
  avg_alignment: number;
  status: string;
  created_at?: string;
}

export interface CreateJobPayload {
  title: string;
  company?: string;
  location?: string;
  experience_years_min?: number;
  description: string;
  required_skills: string[];
  preferred_skills: string[];
  employment_type?: string;
}

export interface RecruiterOverviewMetrics {
  open_roles_count: number;
  candidates_analyzed_count: number;
  strong_matches_count: number;
  average_alignment_percentage: number;
  is_sample_dataset: boolean;
  notice: string;
}

export interface CandidateComparisonItem {
  candidate_id: string;
  name: string;
  current_title?: string;
  match_score: number;
  required_coverage_ratio: string;
  preferred_coverage_ratio: string;
  experience_fit: string;
  skill_gap_tier: "Low" | "Medium" | "High" | string;
  top_gaps: string[];
  hiring_risk_level: string;
  recommendation: string;
  key_evidence: string[];
}

export interface CandidateComparisonResponse {
  job_title: string;
  required_skills: string[];
  preferred_skills: string[];
  candidates: CandidateComparisonItem[];
  recommended_candidate_id: string;
  recommended_candidate_name: string;
  recommendation_reason: string;
  disclaimer: string;
}

export interface ShortlistItemResponse {
  id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email?: string;
  job_id?: string;
  job_title?: string;
  match_score?: number;
  status: "Shortlisted" | "Review" | "Interview" | "Rejected" | string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ApplicantSkillCoverageItem {
  skill: string;
  is_required: boolean;
  applicant_count: number;
  total_applicants: number;
  coverage_percentage: number;
}

export interface RecruiterInsightsResponse {
  job_title: string;
  total_applicants_evaluated: number;
  skill_coverage: ApplicantSkillCoverageItem[];
  most_common_gap_skill?: string;
  most_common_gap_percentage?: number;
  shortage_insight_narrative: string;
  market_trend_linkage?: string;
  is_sample_dataset: boolean;
  disclaimer: string;
}

// ============================================================================
// Market Intelligence Dashboard Types
// ============================================================================

export interface FrequentlyDemandedSkill {
  skill_id: string;
  skill_name: string;
  category: string;
  job_count: number;
  frequency_percentage: number;
  importance_weight: number;
}

export interface RoleSkillItem {
  skill_id: string;
  skill_name: string;
  category: string;
  importance: number;
  required_level: string;
  is_required: boolean;
}

export interface RoleSkillsBreakdown {
  role_id: string;
  role_title: string;
  category: string;
  description: string;
  typical_experience_years: number;
  market_demand_index: number;
  required_skills: RoleSkillItem[];
  preferred_skills: RoleSkillItem[];
  total_skills_count: number;
  required_count: number;
  preferred_count: number;
}

export interface CategoryBreakdownItem {
  category: string;
  unique_skills_count: number;
  job_demand_occurrences: number;
  percentage_of_total_demand: number;
  top_skills: {
    skill_id: string;
    skill_name: string;
    job_count: number;
    importance_weight: number;
  }[];
}

export interface DomainDistributionItem {
  domain: string;
  job_count: number;
  percentage: number;
}

export interface ExperienceBandItem {
  experience_band: string;
  job_count: number;
  percentage: number;
}

export interface SkillGapTrendItem {
  skill_id: string;
  skill_name: string;
  category: string;
  job_demand_count: number;
  job_demand_pct: number;
  candidate_supply_count: number;
  candidate_supply_pct: number;
  gap_delta_pct: number;
  gap_status: "High Unmet Demand" | "Moderate Gap" | "Supply-Demand Balanced" | "High Candidate Supply";
}

export interface MarketIntelligenceMetadata {
  total_jobs: number;
  total_roles: number;
  total_skills: number;
  total_candidates: number;
  dataset_notice: string;
  disclaimer: string;
  predictive_forecasting_active: boolean;
  predictive_forecasting_note: string;
}

export interface MarketIntelligenceResponse {
  metadata: MarketIntelligenceMetadata;
  most_frequently_requested_skills: {
    total_jobs_evaluated: number;
    total_unique_skills_demanded: number;
    skills: FrequentlyDemandedSkill[];
    data_source_context: string;
    context_note: string;
  };
  skills_by_role: {
    total_roles_evaluated: number;
    roles: RoleSkillsBreakdown[];
    data_source_context: string;
    context_note: string;
  };
  skills_by_category: {
    total_categories: number;
    total_demand_occurrences: number;
    categories: CategoryBreakdownItem[];
    data_source_context: string;
    context_note: string;
  };
  role_distribution: {
    total_jobs: number;
    total_benchmark_roles: number;
    average_minimum_experience_years: number;
    domain_distribution: DomainDistributionItem[];
    experience_band_distribution: ExperienceBandItem[];
    data_source_context: string;
    context_note: string;
  };
  skill_gap_trends: {
    total_jobs_evaluated: number;
    total_candidates_evaluated: number;
    total_skills_evaluated: number;
    gap_trends: SkillGapTrendItem[];
    data_source_context: string;
    context_note: string;
  };
}

// ---------------------------------------------------------------------------
// ATS Resume Checker Types
// ---------------------------------------------------------------------------

export interface ATSCategoryScore {
  category_id: string;
  name: string;
  score: number;
  max_score: number;
  percentage: number;
  status: "Strong" | "Good" | "Needs Improvement" | "Needs Attention" | string;
}

export interface ATSChecklistItem {
  label: string;
  status: "pass" | "warning" | "fail";
  detail: string;
}

export interface ATSRecommendation {
  priority: "HIGH" | "MEDIUM" | "LOW" | string;
  title: string;
  description: string;
  category: string;
}

export interface ATSMatchedSkill {
  name: string;
  canonical_name: string;
  category: string;
  evidence?: string | null;
}

export interface ATSMissingSkill {
  name: string;
  canonical_name: string;
  category: string;
}

export interface ATSAnalysisResponse {
  overall_score: number;
  rating: "Excellent" | "Strong" | "Good" | "Needs Improvement" | "Needs Attention" | string;
  check_type: "general" | "job_specific";
  target_job_title?: string | null;
  category_scores: ATSCategoryScore[];
  whats_working: string[];
  needs_attention: string[];
  resume_health: {
    parseability: string;
    content: string;
    skills: string;
    impact: string;
    formatting: string;
    job_alignment?: number;
  };
  matched_skills: ATSMatchedSkill[];
  missing_skills: ATSMissingSkill[];
  recommendations: ATSRecommendation[];
  checklist: ATSChecklistItem[];
  job_alignment_percentage?: number | null;
  total_jd_skills: number;
  matched_jd_skills_count: number;
  parse_confidence: "High" | "Medium" | "Low" | string;
  word_count: number;
  character_count: number;
  page_count: number;
  disclaimer: string;
}




