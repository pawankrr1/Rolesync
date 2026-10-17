/**
 * Frontend Foundation Smoke Test
 * Verifies mock data integrity and basic component contracts.
 */

import assert from "node:assert";
import {
  mockWorkflowSteps,
  mockCandidateProfile,
  mockAnalysisResult,
  mockRecruiterApplicants,
  mockMarketInsights,
} from "../src/mock/careerMockData.js";

console.log("Running frontend smoke tests...");

// 1. Verify 6-step workflow definition
assert.strictEqual(mockWorkflowSteps.length, 6, "Expected 6 workflow steps");
assert.strictEqual(mockWorkflowSteps[0].title, "Ingest");
assert.strictEqual(mockWorkflowSteps[5].title, "Recommend");
console.log("✓ 6-step workflow structure validated");

// 2. Verify candidate profile mock
assert.ok(mockCandidateProfile.name, "Candidate name must be present");
assert.ok(mockCandidateProfile.extractedSkills.length >= 5, "Extracted skills should have at least 5 items");
console.log("✓ Candidate mock profile validated");

// 3. Verify analysis result breakdown
assert.strictEqual(mockAnalysisResult.factors.length, 4, "Must have 4 mathematical factor contributions");
assert.strictEqual(mockAnalysisResult.milestones.length, 3, "Must have 3 roadmap milestones");
assert.ok(mockAnalysisResult.overallScore >= 0 && mockAnalysisResult.overallScore <= 100, "Score within 0-100");
console.log("✓ Analysis result & 4-factor scoring validated");

// 4. Verify recruiter applicants
assert.ok(mockRecruiterApplicants.length >= 3, "Recruiter applicants must have sample entries");
assert.strictEqual(mockRecruiterApplicants[0].grade, "Exceptional Match");
console.log("✓ Recruiter leaderboard mock validated");

// 5. Verify market insights
assert.strictEqual(mockMarketInsights.length, 4, "Expected 4 national market insight cards");
console.log("✓ Market insight metrics validated");

console.log("\nALL FRONTEND SMOKE TESTS PASSED SUCCESSFULLY! 🚀");
