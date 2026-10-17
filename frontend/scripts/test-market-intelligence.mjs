/**
 * E2E Integration Test: Market Intelligence Dashboard
 * Validates:
 * 1. Most frequently requested skills
 * 2. Skills by role
 * 3. Skills by category
 * 4. Role distribution
 * 5. Skill-gap trends within available dataset
 * 6. Explicit data source context on every view
 * 7. "Based on the current dataset" notices
 * 8. Predictive workforce forecasting is disabled
 * 9. Frontend /insights route is accessible
 */

import assert from "assert";

const BACKEND_BASE = "http://127.0.0.1:8000";
const FRONTEND_BASE = "http://127.0.0.1:3000";

async function runMarketIntelligenceTests() {
  console.log("==================================================================");
  console.log("📊 STARTING E2E MARKET INTELLIGENCE VERIFICATION TEST");
  console.log(`Backend Target: ${BACKEND_BASE}`);
  console.log(`Frontend Target: ${FRONTEND_BASE}`);
  console.log("==================================================================\n");

  // Step 0: Verify Frontend Route
  console.log("▶ Step 0: Verify Market Intelligence Dashboard route (/insights)");
  const frontRes = await fetch(`${FRONTEND_BASE}/insights`);
  assert.strictEqual(frontRes.status, 200, "Frontend /insights must return 200 OK");
  console.log("  ✓ Market Intelligence route is live and accessible (200 OK).\n");

  // Step 1: Query Backend Master Market Intelligence API
  console.log("▶ Step 1: Query Market Intelligence Master API (GET /api/v1/insights/market-intelligence)");
  const apiRes = await fetch(`${BACKEND_BASE}/api/v1/insights/market-intelligence?top_n_skills=15`);
  assert.strictEqual(apiRes.status, 200, "Backend /insights/market-intelligence must return 200 OK");
  const data = await apiRes.json();
  assert.ok(data.metadata, "Metadata must be present");
  console.log(`  ✓ Retrieved intelligence compiled across ${data.metadata.total_jobs} seeded jobs, ${data.metadata.total_roles} roles, and ${data.metadata.total_skills} skills.\n`);

  // Step 2: Validate 1. Most Frequently Requested Skills
  console.log("▶ Step 2: Validate Most Frequently Requested Skills");
  const reqSkills = data.most_frequently_requested_skills;
  assert.ok(reqSkills.skills.length > 0, "Frequently requested skills list must not be empty");
  assert.ok(reqSkills.data_source_context.includes("data/jobs.json"), "Must cite data/jobs.json source context");
  assert.ok(reqSkills.context_note.includes("Based on the current dataset"), "Must include 'Based on the current dataset'");
  console.log(`  ✓ Data Source Context: ${reqSkills.data_source_context}`);
  console.log(`  ✓ Top 3 Demanded Skills in Dataset:`);
  reqSkills.skills.slice(0, 3).forEach((s, i) => {
    console.log(`     #${i + 1} ${s.skill_name} (${s.category}): ${s.job_count} jobs (${s.frequency_percentage}%)`);
  });
  console.log("");

  // Step 3: Validate 2. Skills by Role
  console.log("▶ Step 3: Validate Skills by Role");
  const byRole = data.skills_by_role;
  assert.ok(byRole.roles.length > 0, "Roles list must not be empty");
  assert.ok(byRole.data_source_context.includes("data/roles.json"), "Must cite data/roles.json source context");
  assert.ok(byRole.context_note.includes("Based on the current dataset"), "Must include 'Based on the current dataset'");
  const sampleRole = byRole.roles[0];
  assert.ok(sampleRole.required_skills.length > 0, "Role must have required skills");
  console.log(`  ✓ Evaluated ${byRole.total_roles_evaluated} benchmark roles. Sample: ${sampleRole.role_title} (${sampleRole.required_count} required, ${sampleRole.preferred_count} preferred skills)`);
  console.log("");

  // Step 4: Validate 3. Skills by Category
  console.log("▶ Step 4: Validate Skills by Category");
  const byCat = data.skills_by_category;
  assert.ok(byCat.categories.length > 0, "Categories list must not be empty");
  assert.ok(byCat.data_source_context.includes("skills.json") && byCat.data_source_context.includes("jobs.json"), "Must cite skills and jobs source context");
  assert.ok(byCat.context_note.includes("Based on the current dataset"), "Must include 'Based on the current dataset'");
  console.log(`  ✓ Breakdown across ${byCat.total_categories} functional categories:`);
  byCat.categories.slice(0, 4).forEach((c) => {
    console.log(`     • ${c.category}: ${c.job_demand_occurrences} demand mentions (${c.percentage_of_total_demand}% of total)`);
  });
  console.log("");

  // Step 5: Validate 4. Role Distribution
  console.log("▶ Step 5: Validate Role Distribution");
  const roleDist = data.role_distribution;
  assert.ok(roleDist.domain_distribution.length > 0, "Domain distribution must not be empty");
  assert.ok(roleDist.experience_band_distribution.length > 0, "Experience band distribution must not be empty");
  assert.ok(roleDist.data_source_context.includes("data/jobs.json"), "Must cite data/jobs.json source context");
  assert.ok(roleDist.context_note.includes("Based on the current dataset"), "Must include 'Based on the current dataset'");
  console.log(`  ✓ Total Jobs: ${roleDist.total_jobs}, Avg Minimum Exp: ${roleDist.average_minimum_experience_years} years`);
  roleDist.domain_distribution.slice(0, 3).forEach((d) => {
    console.log(`     • Domain: ${d.domain} - ${d.job_count} jobs (${d.percentage}%)`);
  });
  console.log("");

  // Step 6: Validate 5. Skill-Gap Trends Within Available Dataset
  console.log("▶ Step 6: Validate Skill-Gap Trends Within Available Dataset");
  const gapTrends = data.skill_gap_trends;
  assert.ok(gapTrends.gap_trends.length > 0, "Gap trends list must not be empty");
  assert.ok(gapTrends.data_source_context.includes("data/jobs.json") && gapTrends.data_source_context.includes("demo_candidates.json"), "Must cite jobs vs candidates source context");
  assert.ok(gapTrends.context_note.includes("Based on the current dataset"), "Must include 'Based on the current dataset'");
  console.log(`  ✓ Evaluated ${gapTrends.gap_trends.length} skill-gap vectors:`);
  gapTrends.gap_trends.slice(0, 4).forEach((g) => {
    console.log(`     • ${g.skill_name} (${g.category}): Demand=${g.job_demand_pct}%, Supply=${g.candidate_supply_pct}%, Gap Delta=${g.gap_delta_pct > 0 ? "+" : ""}${g.gap_delta_pct}% [${g.gap_status}]`);
  });
  console.log("");

  // Step 7: Verify Constraints (No predictive forecasting, explicit dataset notices)
  console.log("▶ Step 7: Verify Methodological Constraints");
  assert.strictEqual(data.metadata.predictive_forecasting_active, false, "Predictive forecasting must be disabled");
  assert.ok(data.metadata.dataset_notice.includes("Based on the current dataset"), "Dataset notice must be present");
  assert.ok(data.metadata.disclaimer.includes("Do not present sample/demo data as live market statistics"), "Disclaimer must prevent demo data presentation as live market stats");
  console.log("  ✓ Predictive forecasting confirmed disabled.");
  console.log("  ✓ Data notice verified: 'Based on the current dataset'");
  console.log("  ✓ Regulatory disclaimer verified: Sample/demo data not presented as live market statistics.");
  console.log("");

  console.log("==================================================================");
  console.log("🎉 ALL MARKET INTELLIGENCE DASHBOARD REQUIREMENTS FULLY VERIFIED!");
  console.log("==================================================================\n");
}

runMarketIntelligenceTests().catch((err) => {
  console.error("❌ Market Intelligence Test failed:", err);
  process.exit(1);
});
