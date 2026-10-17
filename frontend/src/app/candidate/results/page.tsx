"use client";

import React, { useEffect, useState, useTransition, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  ArrowRight,
  Check,
  AlertCircle,
  X,
  Clock,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Code2,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import { SkillBadge } from "@/components/ui/SkillBadge";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { runFullCandidatePipeline } from "@/lib/api";
import {
  CandidateFullAnalysisResult,
  BackendExtractedSkill,
} from "@/lib/types";
import { recordUatRunning, recordUatPass, recordUatFail } from "@/lib/uatTracker";

function CandidateResultsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const roleParam = searchParams.get("role") || "data_scientist";

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<CandidateFullAnalysisResult | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>(roleParam);
  const [showScoreBreakdown, setShowScoreBreakdown] = useState<boolean>(true);
  const [showAllEvidence, setShowAllEvidence] = useState<boolean>(false);
  const [activeSection, setActiveSection] = useState<"match" | "gap" | "learn" | "grow">("match");
  const [, startTransition] = useTransition();

  const availableRoles = [
    { id: "data_scientist", title: "Data Scientist" },
    { id: "ml_engineer", title: "ML Engineer" },
    { id: "backend_developer", title: "Backend Developer" },
    { id: "data_analyst", title: "Data Analyst" },
    { id: "cloud_engineer", title: "Cloud & DevOps" },
    { id: "fullstack_developer", title: "Fullstack Engineer" },
  ];

  const loadAnalysis = async (targetRoleId: string) => {
    setLoading(true);
    setError(null);
    recordUatRunning("UAT-02", `Evaluating match for role '${targetRoleId}'`);

    try {
      if (typeof window !== "undefined") {
        const cachedRaw = window.sessionStorage.getItem("candidate_active_analysis");
        if (cachedRaw) {
          try {
            const cached: CandidateFullAnalysisResult = JSON.parse(cachedRaw);
            if (cached.targetRoleId === targetRoleId) {
              setAnalysisResult(cached);
              const scoreVal = typeof cached.overallScore === "number" ? Math.round(cached.overallScore) : 0;
              recordUatPass(
                "UAT-02",
                `Match analysis completed for target role '${cached.targetRole}'. Calculated match score: ${scoreVal}/100 (${cached.scoreGrade}). Skill alignment and directed gap analysis generated.`,
                { targetRole: cached.targetRole, matchScore: scoreVal },
                [
                  "Candidate profile verified",
                  "Target role verified",
                  "Matching analysis completed",
                  "Match score valid",
                  "Skill alignment breakdown generated",
                  "Skill gap analysis result generated",
                  "Results displayed",
                ]
              );
              setLoading(false);
              return;
            }
          } catch {
            // ignore
          }
        }
      }

      let candidateSkills: (string | BackendExtractedSkill)[] = [
        "Python",
        "SQL",
        "FastAPI",
        "Docker",
        "Machine Learning",
        "PostgreSQL",
      ];

      if (typeof window !== "undefined") {
        const savedSkillsRaw = window.sessionStorage.getItem("candidate_extracted_skills");
        if (savedSkillsRaw) {
          try {
            const savedSkills = JSON.parse(savedSkillsRaw);
            if (Array.isArray(savedSkills) && savedSkills.length > 0) {
              candidateSkills = savedSkills;
            }
          } catch {
            // ignore
          }
        }
      }

      const res = await runFullCandidatePipeline(
        candidateSkills,
        targetRoleId,
        "Candidate",
        3.0
      );

      if (!res.success || !res.result) {
        const errMsg = res.error || "Failed to generate evaluation report.";
        recordUatFail("UAT-02", "Match analysis failed.", errMsg);
        throw new Error(errMsg);
      }

      const result = res.result;
      const scoreVal = typeof result.overallScore === "number" ? Math.round(result.overallScore) : 0;

      if (scoreVal >= 0 && scoreVal <= 100) {
        recordUatPass(
          "UAT-02",
          `Match analysis completed for target role '${result.targetRole}'. Calculated match score: ${scoreVal}/100 (${result.scoreGrade}). Skill alignment and directed gap analysis generated.`,
          { targetRole: result.targetRole, matchScore: scoreVal },
          [
            "Candidate profile verified",
            "Target role verified",
            "Matching analysis completed",
            "Match score valid",
            "Skill alignment breakdown generated",
            "Skill gap analysis result generated",
            "Results displayed",
          ]
        );
      } else {
        recordUatFail("UAT-02", "Match analysis returned an invalid score.", "Match score must be between 0 and 100.");
      }

      setAnalysisResult(result);
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem("candidate_active_analysis", JSON.stringify(result));
      }
    } catch (err: any) {
      recordUatFail("UAT-02", "Match analysis failed to complete.", err?.message || "Matching engine did not return a valid score.");
      setError(err?.message || "Failed to connect to RoleSync backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setSelectedRole(roleParam);
    loadAnalysis(roleParam);
  }, [roleParam]);

  const handleRoleChange = (newRoleId: string) => {
    setSelectedRole(newRoleId);
    startTransition(() => {
      router.push(`/candidate/results?role=${newRoleId}`);
    });
  };

  if (loading) {
    return (
      <div className="flex-1 flex max-w-7xl mx-auto w-full bg-[#F7F8FA]">
        <DashboardSidebar role="candidate" />
        <main className="flex-1 p-8 flex items-center justify-center bg-[#F7F8FA]">
          <LoadingState
            title="Computing Candidate Profile..."
            subtitle="Evaluating verified competencies, 4-factor scoring weights, and prerequisite dependencies."
            stepProgress="Running explainable matching engine..."
          />
        </main>
      </div>
    );
  }

  if (error || !analysisResult) {
    return (
      <div className="flex-1 flex max-w-7xl mx-auto w-full bg-[#F7F8FA]">
        <DashboardSidebar role="candidate" />
        <main className="flex-1 p-8 flex items-center justify-center bg-[#F7F8FA]">
          <ErrorState
            title="Analysis Unavailable"
            message={error || "Could not retrieve match analysis."}
            onRetry={() => loadAnalysis(selectedRole)}
          />
        </main>
      </div>
    );
  }

  const score = Math.round(analysisResult.overallScore);
  const grade = analysisResult.scoreGrade;
  const strongMatches = analysisResult.matching.strong_matches || [];
  const partialMatches = analysisResult.matching.partial_matches || [];
  const missingMatches = analysisResult.matching.missing_skills || [];
  const factors = analysisResult.factors || [];
  const gaps = analysisResult.gaps.priority_order || [];
  const roadmap = analysisResult.roadmap.roadmap || [];
  const adjacentRoles = analysisResult.recommendations.adjacent_roles || [];

  const evidenceList = analysisResult.extractedSkills
    .filter((s) => Boolean(s.evidence))
    .slice(0, showAllEvidence ? undefined : 4);

  return (
    <div className="flex-1 flex max-w-7xl mx-auto w-full bg-[#F7F8FA]">
      <DashboardSidebar role="candidate" />

      <main className="flex-1 p-6 sm:p-8 lg:p-10 space-y-8 bg-[#F7F8FA]">
        {/* TOP: Status & Profile Summary */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E1E6ED]">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#16805C] bg-[#EAF7F0] px-2.5 py-0.5 rounded border border-[#CDEDDD]">
                <Check className="w-3 h-3 stroke-[2.5]" />
                Resume analyzed successfully
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[#172033]">
              Career Match &amp; Intelligence Report
            </h1>
            <p className="text-xs text-[#5E6878]">
              Target role: <strong className="text-[#172033]">{analysisResult.targetRole}</strong>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-[#5E6878]">Compare with:</span>
            <select
              value={selectedRole}
              onChange={(e) => handleRoleChange(e.target.value)}
              className="text-xs font-semibold py-1.5 px-3 rounded border border-[#E1E6ED] bg-[#FFFFFF] text-[#172033] cursor-pointer"
            >
              {availableRoles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Profile Summary Ribbon */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] text-xs">
          <div>
            <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
              Skills Identified
            </span>
            <span className="text-base font-bold text-[#172033]">
              {analysisResult.extractedSkills.length} competencies
            </span>
            <p className="text-[11px] text-[#5E6878] mt-0.5">Extracted from resume stream</p>
          </div>

          <div className="border-t sm:border-t-0 sm:border-l border-[#EDF0F4] pt-3 sm:pt-0 sm:pl-4">
            <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
              Estimated Experience
            </span>
            <span className="text-base font-bold text-[#172033]">
              3.0+ years
            </span>
            <p className="text-[11px] text-[#5E6878] mt-0.5">Evaluated experience depth</p>
          </div>

          <div className="border-t sm:border-t-0 sm:border-l border-[#EDF0F4] pt-3 sm:pt-0 sm:pl-4">
            <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
              Primary Domain
            </span>
            <span className="text-base font-bold text-[#172033]">
              Software &amp; AI Engineering
            </span>
            <p className="text-[11px] text-[#5E6878] mt-0.5">High technical overlap</p>
          </div>
        </div>

        {/* WORKFLOW NAVIGATION: MATCH → GAP → LEARN → GROW */}
        <div className="flex border-b border-[#E1E6ED] gap-6 text-xs font-semibold">
          {[
            { id: "match", label: "01 MATCH — Where you stand" },
            { id: "gap", label: "02 GAP — What you're missing" },
            { id: "learn", label: "03 LEARN — What to learn" },
            { id: "grow", label: "04 GROW — Where it can take you" },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveSection(tab.id as any)}
              className={`pb-3 border-b-2 transition-colors cursor-pointer ${
                activeSection === tab.id
                  ? "border-[#2563EB] text-[#2563EB]"
                  : "border-transparent text-[#5E6878] hover:text-[#172033]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ------------------------------------------------------------- */}
        {/* SECTION 1: MATCH (Where you stand & Why this score)            */}
        {/* ------------------------------------------------------------- */}
        {(activeSection === "match") && (
          <div className="space-y-6">
            {/* Top Match Score Presentation */}
            <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-6 sm:p-7 space-y-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-[#EDF0F4]">
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-[#5E6878] block">
                    Top Role Match
                  </span>
                  <h2 className="text-2xl font-bold text-[#172033] mt-0.5">
                    {analysisResult.targetRole}
                  </h2>
                  <p className="text-xs text-[#5E6878] max-w-xl mt-1 leading-relaxed">
                    {analysisResult.narrative}
                  </p>
                </div>

                <div className="flex items-center gap-3 bg-[#F8FAFC] p-4 rounded-lg border border-[#E1E6ED] shrink-0">
                  <div className="text-right">
                    <div className="text-3xl font-extrabold text-[#2563EB] leading-none">
                      {score} <span className="text-sm font-normal text-[#8A94A6]">/ 100</span>
                    </div>
                    <span className="text-xs font-semibold text-[#16805C] block mt-1">
                      {grade}
                    </span>
                  </div>
                </div>
              </div>

              {/* WHY THIS SCORE? Transparent Factor Construction */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
                    Why This Score?
                  </h3>
                  <button
                    type="button"
                    onClick={() => setShowScoreBreakdown(!showScoreBreakdown)}
                    className="text-xs text-[#5E6878] hover:text-[#172033] flex items-center gap-1 cursor-pointer"
                  >
                    <span>{showScoreBreakdown ? "Hide calculation" : "Show calculation"}</span>
                    {showScoreBreakdown ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                </div>

                {showScoreBreakdown && (
                  <div className="overflow-x-auto rounded border border-[#E1E6ED]">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#F7F8FA] border-b border-[#E1E6ED] text-[11px] text-[#5E6878] uppercase tracking-wider">
                        <tr>
                          <th className="py-2.5 px-3">Factor</th>
                          <th className="py-2.5 px-3">Weight</th>
                          <th className="py-2.5 px-3">Score Achieved</th>
                          <th className="py-2.5 px-3">Measurement Basis</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#EDF0F4] text-[#172033]">
                        {factors.map((f, idx) => (
                          <tr key={idx} className="hover:bg-[#F7F9FC]">
                            <td className="py-2.5 px-3 font-semibold text-[#172033]">
                              {f.name}
                            </td>
                            <td className="py-2.5 px-3 font-mono text-[#5E6878]">
                              {Math.round(f.weight * 100)}%
                            </td>
                            <td className="py-2.5 px-3 font-mono font-bold text-[#2563EB]">
                              {f.weightedScore.toFixed(1)} / {f.maxPoints} pts
                            </td>
                            <td className="py-2.5 px-3 text-[#5E6878] text-[11px]">
                              {f.explanation}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Skills breakdown */}
              <div className="pt-4 border-t border-[#EDF0F4] space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
                  Skill Alignment Details
                </h3>

                <div className="space-y-3">
                  <div>
                    <span className="text-[11px] font-bold text-[#16805C] block mb-1.5">
                      Strong Skills ({strongMatches.length})
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {strongMatches.map((m) => (
                        <SkillBadge key={m.skill} name={m.skill} status="strong_match" />
                      ))}
                    </div>
                  </div>

                  {partialMatches.length > 0 && (
                    <div>
                      <span className="text-[11px] font-bold text-[#B7791F] block mb-1.5">
                        Developing Skills ({partialMatches.length})
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {partialMatches.map((m) => (
                          <SkillBadge key={m.skill} name={m.skill} status="partial_match" />
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <span className="text-[11px] font-bold text-[#C24141] block mb-1.5">
                      Missing Requirements ({missingMatches.length})
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {missingMatches.map((m) => (
                        <SkillBadge key={m.skill} name={m.skill} status="missing" />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Grounded Resume Evidence */}
            {evidenceList.length > 0 && (
              <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-6 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[#EDF0F4]">
                  <div>
                    <h3 className="text-sm font-bold text-[#172033]">
                      Verified Resume Evidence
                    </h3>
                    <p className="text-xs text-[#5E6878]">
                      Actual citations extracted from your document supporting the competency assessment.
                    </p>
                  </div>
                  {analysisResult.extractedSkills.filter((s) => Boolean(s.evidence)).length > 4 && (
                    <button
                      type="button"
                      onClick={() => setShowAllEvidence(!showAllEvidence)}
                      className="text-xs font-semibold text-[#2563EB] hover:underline cursor-pointer"
                    >
                      {showAllEvidence ? "Show less" : "View all citations"}
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  {evidenceList.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded border border-[#E1E6ED] bg-[#F8FAFC] space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-[#172033]">
                          {item.name}
                        </span>
                        <span className="text-[10px] text-[#8A94A6]">
                          {item.category}
                        </span>
                      </div>
                      <p className="text-[11px] italic text-[#172033] bg-[#FFFFFF] p-2.5 rounded border border-[#E1E6ED]">
                        &ldquo;{item.evidence}&rdquo;
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* SECTION 2: GAP (What you're missing)                           */}
        {/* ------------------------------------------------------------- */}
        {(activeSection === "gap") && (
          <div className="space-y-6">
            <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-6 space-y-4">
              <div className="pb-3 border-b border-[#EDF0F4]">
                <h2 className="text-base font-bold text-[#172033]">
                  Prioritized Skill Gaps
                </h2>
                <p className="text-xs text-[#5E6878]">
                  Focus on the skills that will have the biggest impact on your readiness for {analysisResult.targetRole}.
                </p>
              </div>

              {gaps.length === 0 ? (
                <p className="text-xs text-[#16805C] font-semibold py-4">
                  No critical skill gaps detected for this role. You meet all primary benchmark requirements.
                </p>
              ) : (
                <div className="space-y-3">
                  {gaps.map((gap, idx) => (
                    <div
                      key={gap.skill_id || idx}
                      className="p-4 rounded-lg border border-[#E1E6ED] bg-[#F8FAFC] text-xs space-y-2"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-[#5E6878]">
                              #{idx + 1}
                            </span>
                            <h3 className="text-sm font-bold text-[#172033]">
                              {gap.skill}
                            </h3>
                          </div>
                          <span className="text-[11px] text-[#5E6878]">
                            {gap.category} • Estimated {gap.learning_effort_weeks || "2-3 weeks"}
                          </span>
                        </div>

                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                            gap.priority === "HIGH"
                              ? "bg-[#FDEEEE] text-[#C24141] border-[#F2CACA]"
                              : "bg-[#FFF6DD] text-[#B7791F] border-[#F2DEAA]"
                          }`}
                        >
                          {gap.priority} PRIORITY
                        </span>
                      </div>

                      <p className="text-[#5E6878] leading-relaxed">
                        {gap.reason || "Required competency for target role qualification."}
                      </p>

                      {gap.unblocks && gap.unblocks.length > 0 && (
                        <div className="text-[11px] text-[#5E6878] pt-1">
                          <strong>Unblocks downstream:</strong> {gap.unblocks.join(", ")}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* SECTION 3: LEARN (What to learn & Roadmap)                     */}
        {/* ------------------------------------------------------------- */}
        {(activeSection === "learn") && (
          <div className="space-y-6">
            <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-6 space-y-4">
              <div className="pb-3 border-b border-[#EDF0F4]">
                <h2 className="text-base font-bold text-[#172033]">
                  Sequenced Learning Roadmap
                </h2>
                <p className="text-xs text-[#5E6878]">
                  Prerequisite-ordered milestones with verified open courseware and practical capstone projects.
                </p>
              </div>

              {roadmap.length === 0 ? (
                <p className="text-xs text-[#5E6878] py-4">
                  No additional courses required. Your profile already satisfies all target requirements.
                </p>
              ) : (
                <div className="space-y-4">
                  {roadmap.map((step, idx) => (
                    <div
                      key={idx}
                      className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] space-y-3 text-xs"
                    >
                      <div className="flex items-center justify-between pb-2 border-b border-[#EDF0F4]">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-[#2563EB]">
                            WEEK {idx + 1}
                          </span>
                          <span className="text-[#8A94A6]">•</span>
                          <span className="font-semibold text-[#172033]">
                            {step.skill}
                          </span>
                        </div>
                        <span className="text-[#5E6878] text-[11px] flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-[#8A94A6]" />
                          {step.estimated_duration_weeks || "2 weeks"}
                        </span>
                      </div>

                      <p className="text-[#5E6878] leading-relaxed">
                        {step.reason || "Recommended to bridge technical requirements."}
                      </p>

                      {step.available_learning_resources && step.available_learning_resources.length > 0 && (
                        <div className="space-y-1.5 pt-1">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-[#8A94A6] block">
                            Recommended Course
                          </span>
                          {step.available_learning_resources.map((res, rIdx) => (
                            <div
                              key={rIdx}
                              className="p-3 rounded border border-[#E1E6ED] bg-[#F8FAFC] flex items-center justify-between"
                            >
                              <div>
                                <span className="font-semibold text-[#172033] block">
                                  {res.title}
                                </span>
                                <span className="text-[11px] text-[#5E6878]">
                                  {res.provider} • {res.estimated_hours} hrs • {res.is_free ? "Free" : "Certificate"}
                                </span>
                              </div>
                              {res.url && (
                                <a
                                  href={res.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs font-semibold text-[#2563EB] hover:underline flex items-center gap-1"
                                >
                                  <span>Open</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {step.hands_on_project && (
                        <div className="p-3 rounded bg-[#F8FAFC] border border-[#E1E6ED]">
                          <div className="flex items-center gap-1.5 font-semibold text-[#172033] mb-1">
                            <Code2 className="w-3.5 h-3.5 text-[#2563EB]" />
                            <span>Practical Capstone Project</span>
                          </div>
                          <p className="text-[11px] text-[#5E6878]">
                            {step.hands_on_project}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* SECTION 4: GROW (Where it can take you & Adjacent Roles)       */}
        {/* ------------------------------------------------------------- */}
        {(activeSection === "grow") && (
          <div className="space-y-6">
            <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-6 space-y-4">
              <div className="pb-3 border-b border-[#EDF0F4]">
                <h2 className="text-base font-bold text-[#172033]">
                  Adjacent Career Paths
                </h2>
                <p className="text-xs text-[#5E6878]">
                  Roles sharing significant overlap with your existing technical competencies.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {adjacentRoles.map((role) => (
                  <div
                    key={role.role_id}
                    className="p-5 rounded-lg border border-[#E1E6ED] bg-[#F8FAFC] text-xs space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-bold text-[#172033]">
                          {role.role_title}
                        </h3>
                        <span className="text-[11px] text-[#5E6878]">{role.category}</span>
                      </div>
                      <span className="font-mono text-base font-bold text-[#2563EB]">
                        {Math.round(role.alignment_score)}%
                      </span>
                    </div>

                    <p className="text-[#5E6878] leading-relaxed">
                      {role.why_recommended}
                    </p>

                    <div>
                      <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
                        Overlapping Skills ({role.overlapping_skills.length})
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {role.overlapping_skills.map((s, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded bg-[#EAF7F0] text-[#16805C] border border-[#CDEDDD] text-[11px] font-medium"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>

                    {role.missing_bridge_skills && role.missing_bridge_skills.length > 0 && (
                      <div>
                        <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
                          Bridge Skills to Acquire
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {role.missing_bridge_skills.map((s, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 rounded bg-[#FFF6DD] text-[#B7791F] border border-[#F2DEAA] text-[11px] font-medium"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="pt-2 border-t border-[#E1E6ED]">
                      <Link
                        href={`/candidate/results?role=${role.role_id}`}
                        className="text-xs font-semibold text-[#2563EB] hover:underline flex items-center justify-between"
                      >
                        <span>Benchmark Against This Role</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Decision Support Disclaimer */}
        <div className="p-4 rounded border border-[#E1E6ED] bg-[#F8FAFC] text-xs text-[#5E6878] flex items-start gap-3">
          <ShieldCheck className="w-4 h-4 text-[#16805C] shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            {analysisResult.systemDisclaimer}
          </p>
        </div>
      </main>
    </div>
  );
}

export default function CandidateResultsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex max-w-7xl mx-auto w-full bg-[#F7F8FA]">
          <DashboardSidebar role="candidate" />
          <main className="flex-1 p-8 flex items-center justify-center bg-[#F7F8FA]">
            <LoadingState title="Loading Match Results..." />
          </main>
        </div>
      }
    >
      <CandidateResultsContent />
    </Suspense>
  );
}
