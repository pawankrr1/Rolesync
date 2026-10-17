/**
 * End-to-End Candidate Workflow Verification Script
 * Validates all 14 steps of the complete candidate workflow against the live backend API
 * and frontend data contracts.
 */

import assert from "node:assert";

const BACKEND_URL = process.env.API_URL || "http://127.0.0.1:8000";
const FRONTEND_URL = process.env.FRONTEND_URL || "http://127.0.0.1:3000";

console.log("==================================================================");
console.log("🚀 STARTING E2E CANDIDATE WORKFLOW INTELLIGENCE VERIFICATION TEST");
console.log(`Backend Target: ${BACKEND_URL}`);
console.log(`Frontend Target: ${FRONTEND_URL}`);
console.log("==================================================================\n");

async function runTest() {
  // -------------------------------------------------------------------------
  // Step 1 & 2: Upload and Parse Resume
  // -------------------------------------------------------------------------
  console.log("▶ Step 1 & 2: Upload & In-Memory Parse Resume");
  const sampleResumeContent = `
Pawan Kumar
Senior AI & Distributed Systems Engineer
Email: pawan.kumar@example.com

Professional Summary:
Full-stack software engineer with 4+ years of experience in distributed systems, RESTful microservices, and machine learning models.

Core Technical Competencies:
- Programming Languages: Python, SQL, JavaScript, TypeScript
- AI & Data Science: Machine Learning, Deep Learning, Statistics & Probability, Scikit-learn, PyTorch, Pandas
- Backend & Frameworks: FastAPI, PostgreSQL, Docker, Kubernetes, AWS, Git

Experience:
- Architected production microservices in Python with FastAPI and PostgreSQL handling 2M+ daily requests.
- Trained predictive machine learning models with 92% cross-validated accuracy.
- Containerized applications using Docker and automated CI/CD pipelines.
`;

  const boundary = "----WebKitFormBoundaryE2ETestWorkflow";
  const bodyParts = [
    `--${boundary}\r\n`,
    `Content-Disposition: form-data; name="file"; filename="pawan_resume.txt"\r\n`,
    `Content-Type: text/plain\r\n\r\n`,
    sampleResumeContent.trim(),
    `\r\n--${boundary}--\r\n`,
  ];
  const payloadBuffer = Buffer.from(bodyParts.join(""), "utf-8");

  const parseRes = await fetch(`${BACKEND_URL}/api/v1/documents/parse`, {
    method: "POST",
    headers: {
      "Content-Type": `multipart/form-data; boundary=${boundary}`,
    },
    body: payloadBuffer,
  });

  assert.strictEqual(parseRes.status, 200, "POST /api/v1/documents/parse should return 200 OK");
  const parseData = await parseRes.json();
  assert.ok(parseData.text && parseData.text.length > 50, "Extracted text must not be empty");
  assert.strictEqual(parseData.document_type, "txt", "Document type must be detected as txt");
  console.log(`  ✓ Resume parsed successfully: ${parseData.metadata.word_count} words extracted in-memory.\n`);

  // -------------------------------------------------------------------------
  // Step 3: Extract Skills
  // -------------------------------------------------------------------------
  console.log("▶ Step 3: Extract Verified Canonical Skills with Contextual Evidence");
  const extractRes = await fetch(`${BACKEND_URL}/api/v1/skills/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_text: parseData.text,
      min_confidence: 0.5,
    }),
  });

  assert.strictEqual(extractRes.status, 200, "POST /api/v1/skills/extract should return 200 OK");
  const extractData = await extractRes.json();
  assert.ok(extractData.skills && extractData.skills.length >= 5, "Extracted skills should have at least 5 skills");

  const extractedSkillNames = extractData.skills.map((s) => s.canonical_name);
  console.log(`  ✓ Detected ${extractData.skills.length} canonical skills: ${extractedSkillNames.slice(0, 6).join(", ")}...`);

  // -------------------------------------------------------------------------
  // Step 4: Display Skill Profile
  // -------------------------------------------------------------------------
  console.log("▶ Step 4: Display Candidate Skill Profile Structure");
  for (const s of extractData.skills) {
    assert.ok(s.canonical_name, "Each skill must have a canonical_name");
    assert.ok(s.category, "Each skill must have a category");
    assert.ok(typeof s.confidence === "number", "Each skill must have numerical confidence");
    assert.ok(s.evidence && s.evidence.length > 0, "Each skill must include sentence-level evidence");
  }
  console.log("  ✓ Candidate skill profile verified with categories, confidence, and sentence citations.\n");

  // -------------------------------------------------------------------------
  // Step 5: Select Target Role
  // -------------------------------------------------------------------------
  const targetRole = "data_scientist";
  console.log(`▶ Step 5: Selected Target Role: '${targetRole}'\n`);

  // -------------------------------------------------------------------------
  // Step 6 & 7: Analyze Match & Show Score
  // -------------------------------------------------------------------------
  console.log("▶ Step 6 & 7: Analyze Match & Compute Explainable MATCH SCORE");
  const candidateSkillPayload = extractData.skills.map((s) => s.canonical_name);

  const matchRes = await fetch(`${BACKEND_URL}/api/v1/matching/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate_skills: candidateSkillPayload,
      target_role: targetRole,
      candidate_experience_years: 3.0,
    }),
  });

  assert.strictEqual(matchRes.status, 200, "POST /api/v1/matching/analyze should return 200 OK");
  const matchData = await matchRes.json();
  assert.ok(typeof matchData.final_match_score === "number", "Match score must be a number");
  assert.ok(matchData.final_match_score >= 0 && matchData.final_match_score <= 100, "Score within 0-100");
  assert.ok(matchData.score_grade, "Score grade must be present");
  console.log(`  ✓ MATCH SCORE: ${matchData.final_match_score}% (${matchData.score_grade})`);

  // -------------------------------------------------------------------------
  // Step 8, 9, 10: Show Matched, Partial, and Missing Skills
  // -------------------------------------------------------------------------
  console.log("▶ Step 8, 9, 10: Show Matched Skills, Partial Skills, and Skill Gaps");
  assert.ok(Array.isArray(matchData.strong_matches), "strong_matches must be an array");
  assert.ok(Array.isArray(matchData.partial_matches), "partial_matches must be an array");
  assert.ok(Array.isArray(matchData.missing_skills), "missing_skills must be an array");

  console.log(`  ✓ Strong Match (${matchData.strong_matches.length}): ${matchData.strong_matches.map(m => m.skill).join(", ")}`);
  console.log(`  ✓ Partial Match (${matchData.partial_matches.length}): ${matchData.partial_matches.map(m => m.skill).join(", ") || "None"}`);
  console.log(`  ✓ Skill Gaps (${matchData.missing_skills.length}): ${matchData.missing_skills.map(m => m.skill).join(", ") || "None"}\n`);

  // -------------------------------------------------------------------------
  // Step 11: Show Explanation ("WHY THIS SCORE?")
  // -------------------------------------------------------------------------
  console.log("▶ Step 11: Show 4-Factor Explanation ('WHY THIS SCORE?')");
  assert.ok(matchData.why_match && matchData.why_match.length > 0, "why_match list must exist");
  assert.ok(matchData.why_not_match !== undefined, "why_not_match list must exist");
  assert.ok(matchData.weights_used, "weights_used must exist for 4-factor transparency");
  assert.strictEqual(matchData.weights_used.required_coverage, 0.6, "Default required coverage weight = 60%");
  assert.strictEqual(matchData.weights_used.semantic_similarity, 0.2, "Default semantic similarity weight = 20%");
  assert.strictEqual(matchData.weights_used.experience_alignment, 0.1, "Default experience alignment weight = 10%");
  assert.strictEqual(matchData.weights_used.preferred_coverage, 0.1, "Default preferred coverage weight = 10%");
  console.log(`  ✓ 4-Factor Weights Breakdown: Required (60%), Semantic (20%), Experience (10%), Preferred (10%)`);
  console.log(`  ✓ Key Strengths Cited: ${matchData.why_match[0]}`);

  // -------------------------------------------------------------------------
  // Step 12: Show Skill-Gap Priorities ("WHAT SHOULD I LEARN NEXT?")
  // -------------------------------------------------------------------------
  console.log("\n▶ Step 12: Show Skill-Gap Priorities");
  const gapRes = await fetch(`${BACKEND_URL}/api/v1/gap/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate_skills: candidateSkillPayload,
      target_role: targetRole,
    }),
  });

  assert.strictEqual(gapRes.status, 200, "POST /api/v1/gap/analyze should return 200 OK");
  const gapData = await gapRes.json();
  assert.ok(Array.isArray(gapData.priority_order), "priority_order must be an array");
  console.log(`  ✓ Ranked ${gapData.priority_order.length} skill gaps by prerequisite DAG priority.`);

  // -------------------------------------------------------------------------
  // Step 13: Show Career Recommendations ("ALTERNATIVE CAREER PATHS")
  // -------------------------------------------------------------------------
  console.log("\n▶ Step 13: Show Career Recommendations ('ALTERNATIVE CAREER PATHS')");
  const rolesRes = await fetch(`${BACKEND_URL}/api/v1/recommendations/roles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate_skills: candidateSkillPayload,
      current_role: targetRole,
      top_n: 5,
    }),
  });

  assert.strictEqual(rolesRes.status, 200, "POST /api/v1/recommendations/roles should return 200 OK");
  const rolesData = await rolesRes.json();
  assert.ok(rolesData.recommended_roles && rolesData.recommended_roles.length > 0, "Must return recommended roles");
  for (const r of rolesData.recommended_roles) {
    assert.ok(r.role, "Each recommended role must have a title");
    assert.ok(typeof r.match_score === "number", "Each role must have a match_score");
    assert.ok(Array.isArray(r.matched_skills), "Must include matched_skills list");
    assert.ok(r.reason, "Must include recommendation reason");
  }
  console.log(`  ✓ Generated ${rolesData.recommended_roles.length} alternative career paths:`);
  rolesData.recommended_roles.slice(0, 3).forEach((r) => {
    console.log(`    • ${r.role} (${Math.round(r.match_score)}% fit) - Bridge: ${r.missing_skills.join(", ") || "None"}`);
  });

  // -------------------------------------------------------------------------
  // Step 14: Show Learning Roadmap
  // -------------------------------------------------------------------------
  console.log("\n▶ Step 14: Show Dependency-Aware Learning Roadmap");
  const roadmapRes = await fetch(`${BACKEND_URL}/api/v1/recommendations/roadmap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate_skills: candidateSkillPayload,
      target_role: targetRole,
      missing_skills: ["Statistics", "Deep Learning", "Cloud"],
    }),
  });

  assert.strictEqual(roadmapRes.status, 200, "POST /api/v1/recommendations/roadmap should return 200 OK");
  const roadmapData = await roadmapRes.json();
  assert.ok(roadmapData.roadmap && roadmapData.roadmap.length > 0, "Must return roadmap items");

  for (const item of roadmapData.roadmap) {
    assert.ok(item.skill, "Roadmap item must specify skill");
    assert.ok(item.priority in { HIGH: 1, MEDIUM: 1, LOW: 1 }, "Priority must be HIGH, MEDIUM, or LOW");
    assert.ok(item.reason, "Roadmap item must include grounded reason");
    assert.ok(item.estimated_learning_stage, "Roadmap item must specify learning stage");
    assert.ok(typeof item.recommended_sequence === "number", "Roadmap item must have sequence number");
    assert.ok(Array.isArray(item.available_learning_resources), "Resources must be a list");
  }

  console.log(`  ✓ Roadmap structured into ${roadmapData.roadmap.length} sequenced milestones.`);
  roadmapData.roadmap.forEach((item) => {
    console.log(`    ${item.recommended_sequence}. ${item.skill} [${item.priority}] - ${item.estimated_learning_stage}`);
    if (item.available_learning_resources[0]) {
      const res = item.available_learning_resources[0];
      console.log(`       Resource: "${res.title}" via ${res.provider} (URL: ${res.url ? res.url : "Demo learning resource"})`);
    }
  });

  // -------------------------------------------------------------------------
  // Frontend HTTP Smoke Validation
  // -------------------------------------------------------------------------
  console.log("\n▶ Checking Live Frontend HTTP Status");
  const frontUploadRes = await fetch(`${FRONTEND_URL}/candidate/upload`);
  assert.strictEqual(frontUploadRes.status, 200, "Frontend /candidate/upload must respond with 200 OK");
  console.log("  ✓ Frontend /candidate/upload: 200 OK");

  const frontResultsRes = await fetch(`${FRONTEND_URL}/candidate/results?role=data_scientist`);
  assert.strictEqual(frontResultsRes.status, 200, "Frontend /candidate/results: 200 OK");
  console.log("  ✓ Frontend /candidate/results: 200 OK");

  console.log("\n==================================================================");
  console.log("🎉 ALL 14 STEPS OF CANDIDATE WORKFLOW COMPLETED & VERIFIED!");
  console.log("==================================================================\n");
}

runTest().catch((err) => {
  console.error("❌ E2E TEST FAILED:", err);
  process.exit(1);
});
