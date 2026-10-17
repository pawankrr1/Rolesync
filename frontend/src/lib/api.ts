/**
 * Frontend API Client Configuration.
 * Connects to the FastAPI backend with health monitoring, full candidate workflow endpoints,
 * and safe, user-friendly error envelopes.
 */

import {
  BackendExtractedSkill,
  BackendSkillExtractionResponse,
  BackendMatchingResponse,
  BackendGapResponse,
  BackendRoadmapResponse,
  BackendRoleRecommendationResponse,
  CandidateFullAnalysisResult,
  MatchGrade,
  FactorBreakdownItem,
  RecruiterJobItem,
  CreateJobPayload,
  RecruiterOverviewMetrics,
  CandidateComparisonResponse,
  ShortlistItemResponse,
  RecruiterInsightsResponse,
  RecruiterRankResponse,
  ATSAnalysisResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface BackendHealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  api_prefix?: string;
  latencyMs?: number;
}

export interface ParsedDocumentResponse {
  document_type: string;
  text: string;
  page_count: number;
  metadata: {
    filename: string;
    file_size_bytes: number;
    character_count: number;
    word_count: number;
    content_type: string;
  };
}

/**
 * Sanitizes technical error exceptions into user-friendly, empathetic explanations.
 * Never exposes raw stack traces, database credentials, or internal server codes.
 */
function sanitizeErrorMessage(err: unknown, defaultMessage: string): string {
  if (err instanceof Error) {
    const msg = err.message.toLowerCase();
    if (msg.includes("failed to fetch") || msg.includes("networkerror") || msg.includes("econnrefused")) {
      return "Unable to reach the RoleSync backend. Please verify your connection or ensure the local server is running.";
    }
    if (msg.includes("413") || msg.includes("file size")) {
      return "The uploaded document exceeds the maximum allowed file size (10 MB). Please upload a smaller file.";
    }
    if (msg.includes("415") || msg.includes("unsupported")) {
      return "The file format is not supported. Please upload a PDF, DOCX, or plain text resume.";
    }
    if (msg.includes("timeout")) {
      return "The analysis request took longer than expected. Please try again in a few moments.";
    }
  }
  return defaultMessage;
}

// ---------------------------------------------------------------------------
// 1. Backend Health Check
// ---------------------------------------------------------------------------

export async function checkBackendHealth(): Promise<{
  isOnline: boolean;
  data?: BackendHealthResponse;
  error?: string;
}> {
  const startTime = Date.now();
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/health`, {
      method: "GET",
      cache: "no-store",
    });
    const latencyMs = Date.now() - startTime;
    if (!res.ok) {
      return {
        isOnline: false,
        error: `Backend health responded with status ${res.status}`,
      };
    }
    const data = await res.json();
    return {
      isOnline: true,
      data: { ...data, latencyMs },
    };
  } catch (err: unknown) {
    return {
      isOnline: false,
      error: sanitizeErrorMessage(err, "Unable to establish communication with the intelligence backend."),
    };
  }
}

// ---------------------------------------------------------------------------
// 2. Parse Document (PDF, DOCX, TXT)
// ---------------------------------------------------------------------------

export async function parseDocument(file: File): Promise<{
  success: boolean;
  data?: ParsedDocumentResponse;
  error?: string;
}> {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE_URL}/api/v1/documents/parse`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      const detail = errorJson?.detail || "Document parsing was unsuccessful.";
      return {
        success: false,
        error: detail,
      };
    }

    const data: ParsedDocumentResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Failed to parse document. Please check the file and try again."),
    };
  }
}

// ---------------------------------------------------------------------------
// 3. Extract Skills from Resume Text
// ---------------------------------------------------------------------------

export async function extractSkills(
  resumeText: string,
  jobDescriptionText?: string
): Promise<{
  success: boolean;
  data?: BackendSkillExtractionResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/skills/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume_text: resumeText,
        job_description_text: jobDescriptionText || null,
        min_confidence: 0.5,
      }),
    });

    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errorJson?.detail || "Skill extraction service encountered an issue.",
      };
    }

    const data: BackendSkillExtractionResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Skill extraction failed. Please retry."),
    };
  }
}

// ---------------------------------------------------------------------------
// 4. Candidate Matching Analysis (POST /api/v1/matching/analyze)
// ---------------------------------------------------------------------------

export async function analyzeCandidateMatching(payload: {
  candidate_skills: (string | BackendExtractedSkill | Record<string, any>)[];
  target_role?: string;
  job_description_text?: string;
  candidate_experience_years?: number;
}): Promise<{
  success: boolean;
  data?: BackendMatchingResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/matching/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errorJson?.detail || "Candidate matching service is currently unavailable.",
      };
    }

    const data: BackendMatchingResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Failed to analyze candidate match score."),
    };
  }
}

// ---------------------------------------------------------------------------
// 5. Skill Gap Analysis (POST /api/v1/gap/analyze)
// ---------------------------------------------------------------------------

export async function analyzeSkillGaps(payload: {
  candidate_skills: (string | BackendExtractedSkill | Record<string, any>)[];
  target_role?: string;
}): Promise<{
  success: boolean;
  data?: BackendGapResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/gap/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errorJson?.detail || "Gap analysis service is currently unavailable.",
      };
    }

    const data: BackendGapResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Failed to compute skill gap analysis."),
    };
  }
}

// ---------------------------------------------------------------------------
// 6. Learning Roadmap Generator (POST /api/v1/recommendations/roadmap)
// ---------------------------------------------------------------------------

export async function generateLearningRoadmap(payload: {
  candidate_skills: (string | BackendExtractedSkill | Record<string, any>)[];
  target_role?: string;
  missing_skills?: any[];
  partial_skills?: any[];
  candidate_experience_years?: number;
}): Promise<{
  success: boolean;
  data?: BackendRoadmapResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recommendations/roadmap`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errorJson?.detail || "Roadmap generation service is currently unavailable.",
      };
    }

    const data: BackendRoadmapResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Failed to generate learning roadmap."),
    };
  }
}

// ---------------------------------------------------------------------------
// 7. Role Recommendations (POST /api/v1/recommendations/roles)
// ---------------------------------------------------------------------------

export async function getRoleRecommendations(payload: {
  candidate_skills: (string | BackendExtractedSkill | Record<string, any>)[];
  current_role?: string;
  top_n?: number;
}): Promise<{
  success: boolean;
  data?: BackendRoleRecommendationResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recommendations/roles`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errorJson?.detail || "Career recommendation service is currently unavailable.",
      };
    }

    const data: BackendRoleRecommendationResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Failed to fetch alternative career paths."),
    };
  }
}

// ---------------------------------------------------------------------------
// 8. Full Orchestrated Candidate Workflow Engine
// ---------------------------------------------------------------------------

/**
 * Runs the complete intelligence workflow:
 * 1. Matching Engine (Score, Strong, Partial, Missing, Explanation)
 * 2. Gap Analysis Engine (Readiness, DAG Priorities)
 * 3. Learning Roadmap Engine (Milestones, Seeded Courses, Projects)
 * 4. Career Recommendations Engine (Alternative Paths)
 */
export async function runFullCandidatePipeline(
  candidateSkills: (string | BackendExtractedSkill)[],
  targetRole: string = "data_scientist",
  candidateName: string = "Candidate",
  experienceYears: number = 2.0
): Promise<{
  success: boolean;
  result?: CandidateFullAnalysisResult;
  error?: string;
}> {
  try {
    // 1. Fast unified candidate intelligence pipeline (1 roundtrip instead of 4)
    let matchingData: any = null;
    let gapData: any = null;
    let roadmapData: any = null;
    let rolesData: any = null;

    try {
      const unifiedRes = await fetch(`${API_BASE_URL}/matching/candidate-pipeline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_skills: candidateSkills,
          target_role: targetRole,
          candidate_experience_years: experienceYears,
          candidate_name: candidateName,
        }),
      });
      if (unifiedRes.ok) {
        const payload = await unifiedRes.json();
        matchingData = payload.matching;
        gapData = payload.gap_analysis;
        roadmapData = payload.roadmap;
        rolesData = payload.recommendations;
      }
    } catch {
      // Fallback to legacy parallel calls if unified endpoint is unavailable
    }

    if (!matchingData) {
      const [matchingRes, gapRes, roadmapRes, rolesRes] = await Promise.all([
        analyzeCandidateMatching({
          candidate_skills: candidateSkills,
          target_role: targetRole,
          candidate_experience_years: experienceYears,
        }),
        analyzeSkillGaps({
          candidate_skills: candidateSkills,
          target_role: targetRole,
        }),
        generateLearningRoadmap({
          candidate_skills: candidateSkills,
          target_role: targetRole,
          candidate_experience_years: experienceYears,
        }),
        getRoleRecommendations({
          candidate_skills: candidateSkills,
          current_role: targetRole,
          top_n: 5,
        }),
      ]);

      if (!matchingRes.success || !matchingRes.data) {
        return {
          success: false,
          error: matchingRes.error || "Unable to calculate match score for the selected role.",
        };
      }
      matchingData = matchingRes.data;
      gapData = gapRes.data;
      roadmapData = roadmapRes.data;
      rolesData = rolesRes.data;
    }

    gapData = gapData || {
      target_role_title: matchingData.target_role_title,
      gap_score: 100 - matchingData.final_match_score,
      readiness_percentage: matchingData.final_match_score,
      strong_skills: [],
      partial_skills: [],
      missing_skills: [],
      priority_order: [],
    };

    roadmapData = roadmapData || {
      target_role: matchingData.target_role_title,
      target_role_id: targetRole,
      total_estimated_weeks: 6,
      total_milestones: 0,
      readiness_before: matchingData.final_match_score,
      projected_readiness_after: 100,
      pedagogical_strategy: "Progressive skill acquisition following prerequisite hierarchy.",
      roadmap: [],
    };

    rolesData = rolesData || {
      recommended_roles: [],
      adjacent_roles: [],
    };

    // Calculate score grade
    const score = matchingData.final_match_score;
    let scoreGrade: MatchGrade = "Needs Upskilling";
    if (score >= 85) scoreGrade = "Exceptional Match";
    else if (score >= 70) scoreGrade = "High Alignment";
    else if (score >= 50) scoreGrade = "Moderate Potential";

    // Build standard 4-factor breakdown items
    const weights = matchingData.weights_used || {
      required_coverage: 0.6,
      semantic_similarity: 0.2,
      experience_alignment: 0.1,
      preferred_coverage: 0.1,
    };

    const factors: FactorBreakdownItem[] = [
      {
        name: "Required Skill Coverage",
        rawScore: matchingData.required_skill_coverage,
        weight: weights.required_coverage,
        weightedScore: (matchingData.required_skill_coverage * weights.required_coverage),
        maxPoints: weights.required_coverage * 100,
        explanation: `Matches ${(matchingData.strong_matches || []).filter((m: { is_required?: boolean }) => m.is_required).length} core role requirements with demonstrated competency.`,
      },
      {
        name: "Semantic Domain Overlap",
        rawScore: matchingData.semantic_similarity,
        weight: weights.semantic_similarity,
        weightedScore: (matchingData.semantic_similarity * weights.semantic_similarity),
        maxPoints: weights.semantic_similarity * 100,
        explanation: "Evaluates contextual and architectural domain alignment with the target role.",
      },
      {
        name: "Experience & Evidence Depth",
        rawScore: matchingData.experience_alignment,
        weight: weights.experience_alignment,
        weightedScore: (matchingData.experience_alignment * weights.experience_alignment),
        maxPoints: weights.experience_alignment * 100,
        explanation: `Reflects practical experience depth and verified sentence citations.`,
      },
      {
        name: "Preferred Skill Coverage",
        rawScore: matchingData.preferred_skill_coverage,
        weight: weights.preferred_coverage,
        weightedScore: (matchingData.preferred_skill_coverage * weights.preferred_coverage),
        maxPoints: weights.preferred_coverage * 100,
        explanation: `Assesses bonus skills and adjacent technical capabilities.`,
      },
    ];

    // Normalize extracted skills list
    const extractedList: BackendExtractedSkill[] = candidateSkills.map((s) => {
      if (typeof s === "string") {
        return {
          name: s,
          canonical_name: s,
          canonical_id: s.toLowerCase().replace(/[^a-z0-9]/g, "_"),
          confidence: 0.95,
          confidence_level: "High",
          evidence: `${s} detected in verified profile.`,
          source: "resume",
          category: "Technical Skill",
        };
      }
      const conf = s.confidence ?? 0.8;
      const confLevel = s.confidence_level || (conf >= 0.85 ? "High" : conf >= 0.60 ? "Medium" : "Low");
      const confNote = s.confidence_note || (conf < 0.60 ? "Possible skill detected — review recommended." : undefined);
      return {
        ...s,
        confidence: conf,
        confidence_level: confLevel,
        confidence_note: confNote,
      };
    });

    const narrative =
      matchingData.explainability_narrative ||
      `Overall match score of ${score.toFixed(1)}% for ${matchingData.target_role_title} is derived from transparent, measurable signals rather than arbitrary keyword filtering.`;

    const fullResult: CandidateFullAnalysisResult = {
      candidateName,
      targetRole: matchingData.target_role_title,
      targetRoleId: targetRole,
      overallScore: score,
      scoreGrade,
      whyScore: matchingData.why_score,
      systemDisclaimer:
        matchingData.system_disclaimer?.replace(/Career Intelligence/g, "RoleSync") ||
        "RoleSync provides decision support based on the available profile and dataset. It does not guarantee employment, hiring outcomes or career success.",
      extractedSkills: extractedList,
      matching: matchingData,
      gaps: gapData,
      roadmap: roadmapData,
      recommendations: rolesData,
      narrative,
      factors,
      timestamp: new Date().toISOString(),
    };

    return {
      success: true,
      result: fullResult,
    };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Failed to complete candidate evaluation pipeline."),
    };
  }
}

// ---------------------------------------------------------------------------
// 9. Recruiter Workflow APIs (POST /recruiter/parse-jd, POST /recruiter/rank)
// ---------------------------------------------------------------------------

export interface ParseJDResponse {
  job_title: string;
  required_skills: string[];
  preferred_skills: string[];
  total_skills_extracted: number;
}

export async function parseJobDescription(
  jobDescriptionText: string,
  jobTitle: string = "Target Role"
): Promise<{
  success: boolean;
  data?: ParseJDResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/parse-jd`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_description_text: jobDescriptionText,
        job_title: jobTitle,
      }),
    });

    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errorJson?.detail || "Failed to extract skills from job description.",
      };
    }

    const data: ParseJDResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to reach job description parsing service."),
    };
  }
}

export async function rankRecruiterCandidates(payload: {
  job_title?: string;
  job_description_text?: string;
  required_skills?: string[];
  preferred_skills?: string[];
  target_experience_years?: number;
  candidates: any[];
}): Promise<{
  success: boolean;
  data?: any;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/rank`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errorJson?.detail || "Candidate ranking service is currently unavailable.",
      };
    }

    const data = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Failed to rank candidates against job requirements."),
    };
  }
}

export async function fetchDemoApplicants(): Promise<{
  success: boolean;
  data?: any[];
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/demo-candidates`, {
      method: "GET",
    });

    if (!res.ok) {
      return { success: false, error: "Failed to fetch demo candidates." };
    }

    const data = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to load demo candidates from backend."),
    };
  }
}

// ---------------------------------------------------------------------------
// 10. Market Intelligence Dashboard API (GET /insights/market-intelligence)
// ---------------------------------------------------------------------------

export async function fetchMarketIntelligence(options?: {
  topN?: number;
  roleId?: string;
}): Promise<{
  success: boolean;
  data?: import("./types").MarketIntelligenceResponse;
  error?: string;
}> {
  try {
    const params = new URLSearchParams();
    if (options?.topN) params.append("top_n_skills", options.topN.toString());
    if (options?.roleId) params.append("role_id", options.roleId);

    const qs = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${API_BASE_URL}/api/v1/insights/market-intelligence${qs}`, {
      method: "GET",
      cache: "no-store",
    });

    if (!res.ok) {
      return {
        success: false,
        error: `Market intelligence API responded with status ${res.status}`,
      };
    }

    const data: import("./types").MarketIntelligenceResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(
        err,
        "Unable to fetch market intelligence analytics from backend."
      ),
    };
  }
}

// ---------------------------------------------------------------------------
// 11. Recruiter Hiring Intelligence APIs
// ---------------------------------------------------------------------------

export async function fetchRecruiterMetrics(): Promise<{
  success: boolean;
  data?: RecruiterOverviewMetrics;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/overview-metrics`, {
      method: "GET",
      cache: "no-store",
    });
    if (!res.ok) {
      return { success: false, error: "Failed to fetch recruiter overview metrics." };
    }
    const data: RecruiterOverviewMetrics = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to load recruiter metrics."),
    };
  }
}

export async function fetchRecruiterJobs(limit: number = 50, offset: number = 0): Promise<{
  success: boolean;
  data?: RecruiterJobItem[];
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/jobs?limit=${limit}&offset=${offset}`, {
      method: "GET",
      cache: "no-store",
    });
    if (!res.ok) {
      return { success: false, error: "Failed to load recruiter jobs." };
    }
    const data: RecruiterJobItem[] = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to load recruiter requisitions."),
    };
  }
}

export async function createRecruiterJob(payload: CreateJobPayload): Promise<{
  success: boolean;
  data?: RecruiterJobItem;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errJson?.detail || "Failed to create and persist job.",
      };
    }
    const data: RecruiterJobItem = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to save job requisition to database."),
    };
  }
}

export async function updateRecruiterJob(
  jobId: string,
  payload: Partial<CreateJobPayload>
): Promise<{
  success: boolean;
  data?: RecruiterJobItem;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/jobs/${jobId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errJson?.detail || "Failed to update job requisition.",
      };
    }
    const data: RecruiterJobItem = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to update job requisition."),
    };
  }
}

export async function deleteRecruiterJob(jobId: string): Promise<{
  success: boolean;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/jobs/${jobId}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      return { success: false, error: "Failed to delete job." };
    }
    return { success: true };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to delete job."),
    };
  }
}

export async function fetchRecruiterJob(jobId: string): Promise<{
  success: boolean;
  data?: RecruiterJobItem;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/jobs/${jobId}`, {
      method: "GET",
      cache: "no-store",
    });
    if (!res.ok) {
      return { success: false, error: "Failed to load job details." };
    }
    const data: RecruiterJobItem = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to retrieve job details."),
    };
  }
}

export async function analyzeRecruiterJob(jobId: string): Promise<{
  success: boolean;
  data?: RecruiterRankResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/jobs/${jobId}/analyze`, {
      method: "POST",
    });
    if (!res.ok) {
      const errJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errJson?.detail || "Failed to analyze candidates against job.",
      };
    }
    const data: RecruiterRankResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to run job candidate analysis."),
    };
  }
}

export async function fetchCandidateProfile(candidateId: string): Promise<{
  success: boolean;
  data?: any;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/candidates/${candidateId}`, {
      method: "GET",
      cache: "no-store",
    });
    if (!res.ok) {
      return { success: false, error: "Candidate profile not found." };
    }
    const data = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to load candidate profile."),
    };
  }
}

export async function fetchTalentPool(filters?: {
  search?: string;
  skill?: string;
  role?: string;
  min_exp?: number;
  max_exp?: number;
  page?: number;
  page_size?: number;
}): Promise<{
  success: boolean;
  data?: {
    total_count: number;
    page: number;
    page_size: number;
    candidates: any[];
    filters_applied: any;
  };
  error?: string;
}> {
  try {
    const params = new URLSearchParams();
    if (filters?.search) params.append("search", filters.search);
    if (filters?.skill) params.append("skill", filters.skill);
    if (filters?.role) params.append("role", filters.role);
    if (filters?.min_exp !== undefined) params.append("min_exp", filters.min_exp.toString());
    if (filters?.max_exp !== undefined) params.append("max_exp", filters.max_exp.toString());
    if (filters?.page) params.append("page", filters.page.toString());
    if (filters?.page_size) params.append("page_size", filters.page_size.toString());

    const qs = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/talent-pool${qs}`, {
      method: "GET",
      cache: "no-store",
    });
    if (!res.ok) {
      return { success: false, error: "Failed to retrieve talent pool data." };
    }
    const data = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to load talent pool candidates."),
    };
  }
}

export async function compareCandidates(
  candidateIds: string[],
  jobSpec: {
    job_title: string;
    required_skills: string[];
    preferred_skills: string[];
    target_experience_years?: number;
  }
): Promise<{
  success: boolean;
  data?: CandidateComparisonResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate_ids: candidateIds,
        job_title: jobSpec.job_title,
        required_skills: jobSpec.required_skills,
        preferred_skills: jobSpec.preferred_skills,
        target_experience_years: jobSpec.target_experience_years || 3.0,
      }),
    });
    if (!res.ok) {
      const errJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errJson?.detail || "Candidate comparison failed.",
      };
    }
    const data: CandidateComparisonResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to complete candidate comparison."),
    };
  }
}

export async function shortlistCandidate(
  candidateId: string,
  payload: {
    candidate_name: string;
    candidate_email?: string;
    job_id?: string;
    job_title?: string;
    match_score?: number;
    status?: string;
    notes?: string;
  }
): Promise<{
  success: boolean;
  data?: ShortlistItemResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/candidates/${candidateId}/shortlist`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate_id: candidateId,
        ...payload,
      }),
    });
    if (!res.ok) {
      return { success: false, error: "Failed to shortlist candidate." };
    }
    const data: ShortlistItemResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to update candidate shortlist."),
    };
  }
}

export async function removeShortlistCandidate(
  candidateId: string,
  jobId?: string
): Promise<{
  success: boolean;
  error?: string;
}> {
  try {
    const qs = jobId ? `?job_id=${encodeURIComponent(jobId)}` : "";
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/candidates/${candidateId}/shortlist${qs}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      return { success: false, error: "Failed to remove candidate from shortlist." };
    }
    return { success: true };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to update shortlist status."),
    };
  }
}

export async function fetchShortlist(jobId?: string): Promise<{
  success: boolean;
  data?: ShortlistItemResponse[];
  error?: string;
}> {
  try {
    const qs = jobId ? `?job_id=${encodeURIComponent(jobId)}` : "";
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/shortlist${qs}`, {
      method: "GET",
      cache: "no-store",
    });
    if (!res.ok) {
      return { success: false, error: "Failed to load shortlisted candidates." };
    }
    const data: ShortlistItemResponse[] = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to load shortlist."),
    };
  }
}

export async function updateShortlistStatus(
  shortlistId: string,
  status: string,
  notes?: string
): Promise<{
  success: boolean;
  data?: ShortlistItemResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/shortlist/${shortlistId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, notes }),
    });
    if (!res.ok) {
      return { success: false, error: "Failed to update review status." };
    }
    const data: ShortlistItemResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to update review status."),
    };
  }
}

export async function fetchRecruiterInsights(
  jobId?: string,
  roleTitle: string = "Data Analyst"
): Promise<{
  success: boolean;
  data?: RecruiterInsightsResponse;
  error?: string;
}> {
  try {
    const params = new URLSearchParams();
    if (jobId) params.append("job_id", jobId);
    if (roleTitle) params.append("role_title", roleTitle);

    const qs = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${API_BASE_URL}/api/v1/recruiter/insights${qs}`, {
      method: "GET",
      cache: "no-store",
    });
    if (!res.ok) {
      return { success: false, error: "Failed to retrieve recruiter hiring insights." };
    }
    const data: RecruiterInsightsResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Unable to compute hiring insights."),
    };
  }
}

// ---------------------------------------------------------------------------
// 15. ATS Resume Checker APIs
// ---------------------------------------------------------------------------

export async function analyzeATS(payload: {
  resume_text: string;
  filename?: string;
  file_size_bytes?: number;
  page_count?: number;
  check_type?: "general" | "job_specific";
  job_description_text?: string;
  target_job_title?: string;
}): Promise<{
  success: boolean;
  data?: ATSAnalysisResponse;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/ats/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errJson?.detail || "ATS readiness evaluation service failed. Please try again.",
      };
    }

    const data: ATSAnalysisResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Network issue while evaluating ATS readiness."),
    };
  }
}

export async function uploadAndAnalyzeATS(
  file: File,
  checkType: "general" | "job_specific" = "general",
  jobDescriptionText?: string,
  targetJobTitle?: string
): Promise<{
  success: boolean;
  data?: ATSAnalysisResponse;
  error?: string;
}> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("check_type", checkType);
    if (jobDescriptionText) {
      formData.append("job_description_text", jobDescriptionText);
    }
    if (targetJobTitle) {
      formData.append("target_job_title", targetJobTitle);
    }

    const res = await fetch(`${API_BASE_URL}/api/v1/ats/upload-and-analyze`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => null);
      return {
        success: false,
        error: errJson?.detail || "Failed to process resume file for ATS check.",
      };
    }

    const data: ATSAnalysisResponse = await res.json();
    return { success: true, data };
  } catch (err: unknown) {
    return {
      success: false,
      error: sanitizeErrorMessage(err, "Failed to upload and analyze resume document."),
    };
  }
}



