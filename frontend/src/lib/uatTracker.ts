/**
 * Live UAT State Tracker for RoleSync.
 *
 * Tracks the live, real-time execution status of the 3 canonical workflows:
 * - UAT-01: Resume Analysis and Skill Extraction
 * - UAT-02: Job Match and Skill Gap Analysis
 * - UAT-03: Recruiter Candidate Matching and Shortlisting
 *
 * States: "NOT EXECUTED" | "RUNNING" | "PASS" | "FAIL"
 *
 * Grounded in real user actions. Zero fake PASSes.
 */

export type UATTestId = "UAT-01" | "UAT-02" | "UAT-03";
export type UATStatus = "NOT EXECUTED" | "RUNNING" | "PASS" | "FAIL";

export interface UATExecutionRecord {
  id: UATTestId;
  title: string;
  area: "Candidate" | "Recruiter";
  objective: string;
  preconditions: string[];
  steps: string[];
  expectedResult: string;
  status: UATStatus;
  actualResult?: string;
  failureReason?: string;
  startedAt?: string;
  completedAt?: string;
  durationSeconds?: number;
  metrics?: Record<string, any>;
  logItems?: { timestamp: string; message: string }[];
  passedConditions?: string[];
  failedConditions?: string[];
  linkHref: string;
  linkLabel: string;
}

const STORAGE_KEY = "rolesync_live_uat_store";
const RESET_FLAG_KEY = "rolesync_uat_explicitly_reset";

export const INITIAL_UAT_DEFINITIONS: Record<UATTestId, UATExecutionRecord> = {
  "UAT-01": {
    id: "UAT-01",
    title: "Resume Analysis and Skill Extraction",
    area: "Candidate",
    objective: "Verify that a user can upload a resume and receive an extracted skill profile.",
    preconditions: [
      "User is on the RoleSync Candidate area.",
      "Resume file is available.",
      "Supported file format is used.",
    ],
    steps: [
      "Open Resume Upload.",
      "Upload a supported resume file.",
      "Start resume analysis.",
      "Wait for analysis to complete.",
      "Open the analysis result.",
      "Review extracted skills.",
    ],
    expectedResult:
      "The resume is accepted and processed successfully. The system displays resume/profile information, extracted skills, relevant experience information where available, and analysis result. The user should not remain stuck on an infinite loading state.",
    status: "NOT EXECUTED",
    linkHref: "/candidate/upload",
    linkLabel: "Open Resume Upload",
  },
  "UAT-02": {
    id: "UAT-02",
    title: "Job Match and Skill Gap Analysis",
    area: "Candidate",
    objective:
      "Verify that RoleSync can compare a candidate profile against a target role and identify skill alignment and gaps.",
    preconditions: [
      "Candidate profile/resume has been analyzed.",
      "At least one target role is available.",
    ],
    steps: [
      "Open Match & Results.",
      "Select a target role.",
      "Start the match analysis.",
      "Review the overall match score.",
      "Review matched skills.",
      "Review partial skills.",
      "Review missing skills.",
      "Open the skill gap information.",
    ],
    expectedResult:
      "RoleSync displays overall match/alignment, matched skills, partial/developing skills where supported, missing skills, and skill gap information. The result should be consistent with the existing matching engine.",
    status: "NOT EXECUTED",
    linkHref: "/candidate/results",
    linkLabel: "Open Match & Results",
  },
  "UAT-03": {
    id: "UAT-03",
    title: "Recruiter Candidate Matching and Shortlisting",
    area: "Recruiter",
    objective:
      "Verify that a recruiter can evaluate candidates for a role and shortlist a suitable candidate.",
    preconditions: [
      "Recruiter is logged in.",
      "At least one job/role exists.",
      "Candidate profiles are available.",
    ],
    steps: [
      "Open Recruiter Portal.",
      "Select an existing role.",
      "Open Candidate Matches.",
      "Review candidate match scores.",
      "Open 'Why this candidate?' or the available match explanation.",
      "Review skill alignment/gaps.",
      "Select a suitable candidate.",
      "Add the candidate to the shortlist.",
    ],
    expectedResult:
      "The recruiter can view candidate matches, see candidate alignment, understand the reason for the ranking, review skill gaps, and shortlist a candidate. The shortlisted candidate should appear in the appropriate shortlist/status area if that functionality already exists.",
    status: "NOT EXECUTED",
    linkHref: "/recruiter",
    linkLabel: "Open Recruiter Portal",
  },
};

/**
 * Get current live UAT records from sessionStorage.
 */
export function getLiveUatState(): Record<UATTestId, UATExecutionRecord> {
  if (typeof window === "undefined") {
    return { ...INITIAL_UAT_DEFINITIONS };
  }

  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        "UAT-01": { ...INITIAL_UAT_DEFINITIONS["UAT-01"], ...parsed["UAT-01"] },
        "UAT-02": { ...INITIAL_UAT_DEFINITIONS["UAT-02"], ...parsed["UAT-02"] },
        "UAT-03": { ...INITIAL_UAT_DEFINITIONS["UAT-03"], ...parsed["UAT-03"] },
      };
    }
  } catch {
    // fallback
  }

  return { ...INITIAL_UAT_DEFINITIONS };
}

/**
 * Save live state to sessionStorage.
 */
function saveLiveUatState(state: Record<UATTestId, UATExecutionRecord>): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    window.sessionStorage.removeItem(RESET_FLAG_KEY);
  } catch {
    // ignore
  }
}

/**
 * Record RUNNING state for a test.
 */
export function recordUatRunning(testId: UATTestId, initialLog?: string): void {
  const current = getLiveUatState();
  const now = new Date().toLocaleTimeString();

  current[testId] = {
    ...current[testId],
    status: "RUNNING",
    startedAt: now,
    completedAt: undefined,
    durationSeconds: undefined,
    actualResult: "Workflow currently executing...",
    failureReason: undefined,
    logItems: initialLog ? [{ timestamp: now, message: initialLog }] : [{ timestamp: now, message: "Execution started." }],
  };

  saveLiveUatState(current);
}

/**
 * Record PASS state for a test.
 */
export function recordUatPass(
  testId: UATTestId,
  actualResult: string,
  metrics?: Record<string, any>,
  passedConditions?: string[]
): void {
  const current = getLiveUatState();
  const now = new Date().toLocaleTimeString();
  const startedAt = current[testId].startedAt || now;

  const logs = current[testId].logItems || [];
  logs.push({ timestamp: now, message: "All conditions verified successfully. Workflow PASSED." });

  current[testId] = {
    ...current[testId],
    status: "PASS",
    actualResult,
    failureReason: undefined,
    completedAt: now,
    metrics: metrics || {},
    passedConditions: passedConditions || [],
    failedConditions: [],
    logItems: logs,
  };

  saveLiveUatState(current);
}

/**
 * Record FAIL state for a test with explicit failure reason.
 */
export function recordUatFail(
  testId: UATTestId,
  actualResult: string,
  failureReason: string,
  metrics?: Record<string, any>,
  failedConditions?: string[]
): void {
  const current = getLiveUatState();
  const now = new Date().toLocaleTimeString();

  const logs = current[testId].logItems || [];
  logs.push({ timestamp: now, message: `Workflow failed: ${failureReason}` });

  current[testId] = {
    ...current[testId],
    status: "FAIL",
    actualResult,
    failureReason,
    completedAt: now,
    metrics: metrics || {},
    passedConditions: current[testId].passedConditions || [],
    failedConditions: failedConditions || [failureReason],
    logItems: logs,
  };

  saveLiveUatState(current);
}

/**
 * Reset all 3 UAT tests back to NOT EXECUTED without deleting application data.
 */
export function resetUatState(): Record<UATTestId, UATExecutionRecord> {
  const resetMap: Record<UATTestId, UATExecutionRecord> = {
    "UAT-01": { ...INITIAL_UAT_DEFINITIONS["UAT-01"] },
    "UAT-02": { ...INITIAL_UAT_DEFINITIONS["UAT-02"] },
    "UAT-03": { ...INITIAL_UAT_DEFINITIONS["UAT-03"] },
  };

  if (typeof window !== "undefined") {
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(resetMap));
      window.sessionStorage.setItem(RESET_FLAG_KEY, "true");
    } catch {
      // ignore
    }
  }

  return resetMap;
}

/**
 * Check if UAT was explicitly reset in this session.
 */
export function isUatExplicitlyReset(): boolean {
  if (typeof window === "undefined") return false;
  return window.sessionStorage.getItem(RESET_FLAG_KEY) === "true";
}
