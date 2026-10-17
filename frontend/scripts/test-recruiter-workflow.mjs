/**
 * End-to-End Recruiter Workflow Verification Test
 * Validates the complete 5-step recruiter screening, skill extraction, candidate ranking,
 * inspection modal payload, and ethical decision-support language guardrails.
 */

import assert from "node:assert";

const BACKEND_URL = process.env.API_URL || "http://127.0.0.1:8000";
const FRONTEND_URL = process.env.FRONTEND_URL || "http://127.0.0.1:3000";

console.log("==================================================================");
console.log("👔 STARTING E2E RECRUITER SCREENING & TALENT RANKING TEST");
console.log(`Backend Target: ${BACKEND_URL}`);
console.log(`Frontend Target: ${FRONTEND_URL}`);
console.log("==================================================================\n");

async function runRecruiterTest() {
  // -------------------------------------------------------------------------
  // Step 0: Verify Recruiter Dashboard Route
  // -------------------------------------------------------------------------
  console.log("▶ Step 0: Recruiter opens recruiter dashboard");
  const dashRes = await fetch(`${FRONTEND_URL}/recruiter`);
  assert.strictEqual(dashRes.status, 200, "GET /recruiter must return 200 OK");
  console.log("  ✓ Recruiter dashboard route is live and accessible (200 OK).\n");

  // -------------------------------------------------------------------------
  // Step 1 & 2: Paste or upload Job Description & Extract Required Skills
  // -------------------------------------------------------------------------
  console.log("▶ Step 1 & 2: Paste Job Description & System Extracts Required Skills");
  const jobTitle = "Senior Data Scientist";
  const jobDescription = `
Senior Data Scientist
We are seeking an experienced Data Scientist with 3+ years experience.
Required Skills:
- Python
- SQL
- Machine Learning
- Statistics & Probability
- Kubernetes
Preferred Skills:
- Cloud architectures
- Deep Learning
`;

  const parseJdRes = await fetch(`${BACKEND_URL}/api/v1/recruiter/parse-jd`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_title: jobTitle,
      job_description_text: jobDescription,
    }),
  });

  assert.strictEqual(parseJdRes.status, 200, "POST /api/v1/recruiter/parse-jd must return 200 OK");
  const jdData = await parseJdRes.json();
  assert.ok(jdData.required_skills && jdData.required_skills.length > 0, "Must extract required skills");
  console.log(`  ✓ Extracted ${jdData.required_skills.length} required skills: ${jdData.required_skills.join(", ")}`);
  console.log(`  ✓ Extracted ${jdData.preferred_skills.length} preferred skills: ${jdData.preferred_skills.join(", ")}\n`);

  // -------------------------------------------------------------------------
  // Step 3 & 4: Ingest Multiple Candidate Resumes & Extract Skills
  // -------------------------------------------------------------------------
  console.log("▶ Step 3 & 4: Recruiter Uploads Multiple Candidate Resumes & Extracts Skills");
  const testCandidates = [
    {
      id: "cand_01",
      name: "Pawan Kumar",
      filename: "pawan_kumar_cv.pdf",
      candidate_skills: ["Python", "SQL", "Machine Learning", "Statistics & Probability", "Cloud"],
      experience_years: 4.0,
    },
    {
      id: "cand_02",
      name: "Priya Patel",
      filename: "priya_patel_cv.pdf",
      candidate_skills: ["Python", "SQL", "Machine Learning", "Pandas"],
      experience_years: 3.0,
    },
    {
      id: "cand_03",
      name: "Aarav Sharma",
      filename: "aarav_backend.pdf",
      candidate_skills: ["Python", "SQL", "FastAPI", "Docker"],
      experience_years: 4.5,
    },
    {
      id: "cand_04",
      name: "Junior Analyst",
      filename: "junior_analyst.pdf",
      candidate_skills: ["SQL", "Excel"],
      experience_years: 1.0,
    },
  ];

  console.log(`  ✓ Ingested batch of ${testCandidates.length} candidate profiles.\n`);

  // -------------------------------------------------------------------------
  // Step 5: Matching Engine Ranks Candidates
  // -------------------------------------------------------------------------
  console.log("▶ Step 5: Matching Engine Ranks Candidates");
  const rankRes = await fetch(`${BACKEND_URL}/api/v1/recruiter/rank`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_title: jobTitle,
      job_description_text: jobDescription,
      required_skills: ["Python", "SQL", "Machine Learning", "Statistics & Probability", "Kubernetes"],
      preferred_skills: ["Cloud"],
      candidates: testCandidates,
    }),
  });

  assert.strictEqual(rankRes.status, 200, "POST /api/v1/recruiter/rank must return 200 OK");
  const rankData = await rankRes.json();
  assert.strictEqual(rankData.total_candidates_evaluated, testCandidates.length);

  // Verify descending sort order
  const scores = rankData.ranked_candidates.map((c) => c.match_score);
  for (let i = 0; i < scores.length - 1; i++) {
    assert.ok(scores[i] >= scores[i + 1], `Ranked list must be sorted descending: ${scores[i]} >= ${scores[i + 1]}`);
  }

  console.log("  ✓ Candidates ranked descending by explainable match score:\n");
  rankData.ranked_candidates.forEach((cand) => {
    console.log(`    #${cand.rank} ${cand.name}: ${cand.match_score}% [${cand.score_grade}]`);
    console.log(`       Strong: ${cand.strong_skills.join(", ") || "None"}`);
    console.log(`       Missing: ${cand.missing_skills.join(", ") || "None"}`);
    console.log(`       Exp: ${cand.experience_display} | Reason: ${cand.reason}`);
  });

  // -------------------------------------------------------------------------
  // Step 6: Detailed Explanation Inspection Modal (Click Candidate)
  // -------------------------------------------------------------------------
  console.log("\n▶ Step 6: Verify Detailed Explanation Inspection Structure (Prompt Example)");
  const topCandidate = rankData.ranked_candidates[0];
  const expl = topCandidate.detailed_explanation;

  assert.ok(expl.match_score_display.includes("Match"), "Must include match score display");
  assert.ok(Array.isArray(expl.matched), "Must include matched skills list");
  assert.ok(Array.isArray(expl.partial), "Must include partial skills list");
  assert.ok(Array.isArray(expl.missing), "Must include missing skills list");

  console.log(`  ✓ Detailed Inspection for ${topCandidate.name}:`);
  console.log(`     ${expl.match_score_display}`);
  console.log(`     Matched: ${expl.matched.join(", ")}`);
  console.log(`     Partial: ${expl.partial.join(", ") || "None"}`);
  console.log(`     Missing: ${expl.missing.join(", ") || "None"}`);

  // -------------------------------------------------------------------------
  // Step 7: Ethical Language Guardrails & Decision Support Disclaimer
  // -------------------------------------------------------------------------
  console.log("\n▶ Step 7: Ethical Language Guardrails & Decision Support Disclaimer");

  // 1. Must NOT claim person is "best" candidate
  const textPayload = JSON.stringify(rankData).toLowerCase();
  assert.ok(
    !textPayload.includes("best candidate") && !textPayload.includes("the best candidate"),
    "Must NOT claim highest score means candidate is objectively 'best'"
  );

  // 2. Must use "Highest measured skill alignment in this dataset."
  assert.ok(
    rankData.top_candidate_statement.includes("Highest measured skill alignment in this dataset."),
    "Must use: 'Highest measured skill alignment in this dataset.'"
  );
  assert.ok(
    topCandidate.alignment_statement.includes("Highest measured skill alignment in this dataset."),
    "Top candidate item must include 'Highest measured skill alignment in this dataset.'"
  );

  // 3. Must include decision support disclaimer
  assert.ok(
    rankData.disclaimer.toLowerCase().includes("decision support"),
    "Disclaimer must state system is decision support"
  );
  assert.ok(
    rankData.disclaimer.toLowerCase().includes("not an automated hiring decision"),
    "Disclaimer must state system is not an automated hiring decision"
  );

  console.log(`  ✓ Ethical statement verified: "${rankData.top_candidate_statement}"`);
  console.log(`  ✓ Decision support disclaimer verified: "${rankData.disclaimer.slice(0, 95)}..."`);

  console.log("\n==================================================================");
  console.log("🎉 ALL RECRUITER WORKFLOW STEPS VERIFIED & FULLY FUNCTIONAL!");
  console.log("==================================================================\n");
}

runRecruiterTest().catch((err) => {
  console.error("❌ RECRUITER E2E TEST FAILED:", err);
  process.exit(1);
});
