/**
 * Frontend Test Suite: Validates routes, components, and TypeScript definitions.
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

console.log("=== RUNNING FRONTEND TEST SUITE ===");

// 1. Verify required routes exist
const requiredRoutes = [
  "src/app/page.tsx",
  "src/app/candidate/page.tsx",
  "src/app/candidate/upload/page.tsx",
  "src/app/candidate/results/page.tsx",
  "src/app/recruiter/page.tsx",
  "src/app/insights/page.tsx",
];

for (const route of requiredRoutes) {
  const fullPath = path.resolve(__dirname, "..", route);
  if (!fs.existsSync(fullPath)) {
    console.error(`❌ Missing required route: ${route}`);
    process.exit(1);
  }
  console.log(`✓ Route verified: ${route}`);
}

// 2. Verify required reusable components exist
const requiredComponents = [
  "src/components/ui/MatchScore.tsx",
  "src/components/ui/SkillBadge.tsx",
  "src/components/ui/SkillGroup.tsx",
  "src/components/ui/SkillGapCard.tsx",
  "src/components/ui/RecommendationCard.tsx",
  "src/components/ui/RoleMatchCard.tsx",
  "src/components/ui/UploadZone.tsx",
  "src/components/ui/ProgressIndicator.tsx",
  "src/components/ui/ExplanationPanel.tsx",
  "src/components/layout/Navbar.tsx",
  "src/components/layout/Footer.tsx",
  "src/components/layout/DashboardSidebar.tsx",
  "src/components/common/LoadingState.tsx",
  "src/components/common/EmptyState.tsx",
  "src/components/common/ErrorState.tsx",
];

for (const comp of requiredComponents) {
  const fullPath = path.resolve(__dirname, "..", comp);
  if (!fs.existsSync(fullPath)) {
    console.error(`❌ Missing required component: ${comp}`);
    process.exit(1);
  }
  console.log(`✓ Component verified: ${comp}`);
}

// 3. Verify TypeScript check
try {
  console.log("Running TypeScript compilation check (tsc --noEmit)...");
  execSync("npx tsc --noEmit", { stdio: "inherit", cwd: path.resolve(__dirname, "..") });
  console.log("✓ TypeScript check passed with 0 errors!");
} catch (error) {
  console.error("❌ TypeScript compilation failed!");
  process.exit(1);
}

// 4. Verify Candidate Workflow End-to-End
try {
  console.log("\nRunning Candidate Workflow E2E Integration Suite...");
  execSync("node scripts/test-candidate-workflow.mjs", { stdio: "inherit", cwd: path.resolve(__dirname, "..") });
  console.log("✓ Candidate Workflow E2E Suite passed!");
} catch (error) {
  console.error("❌ Candidate Workflow E2E Suite failed!");
  process.exit(1);
}

// 5. Verify Recruiter Workflow End-to-End
try {
  console.log("\nRunning Recruiter Workflow E2E Integration Suite...");
  execSync("node scripts/test-recruiter-workflow.mjs", { stdio: "inherit", cwd: path.resolve(__dirname, "..") });
  console.log("✓ Recruiter Workflow E2E Suite passed!");
} catch (error) {
  console.error("❌ Recruiter Workflow E2E Suite failed!");
  process.exit(1);
}

// 6. Verify Market Intelligence Dashboard End-to-End
try {
  console.log("\nRunning Market Intelligence E2E Integration Suite...");
  execSync("node scripts/test-market-intelligence.mjs", { stdio: "inherit", cwd: path.resolve(__dirname, "..") });
  console.log("✓ Market Intelligence E2E Suite passed!");
} catch (error) {
  console.error("❌ Market Intelligence E2E Suite failed!");
  process.exit(1);
}

console.log("\n✅ ALL FRONTEND VERIFICATION & E2E TESTS PASSED!\n");


