"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Users,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Award,
  Sparkles,
  ShieldCheck,
  ChevronLeft,
  Loader2,
  FileText,
  Star,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import {
  compareCandidates,
  fetchDemoApplicants,
  shortlistCandidate,
} from "@/lib/api";
import {
  CandidateComparisonResponse,
  CandidateComparisonItem,
} from "@/lib/types";

function CandidateComparisonContent() {
  const searchParams = useSearchParams();
  const idsParam = searchParams.get("ids");
  const roleParam = searchParams.get("role") || "Data Analyst";

  const [comparisonData, setComparisonData] = useState<CandidateComparisonResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [shortlistedSuccess, setShortlistedSuccess] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function loadComparison() {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        let candidateIds: string[] = [];
        if (idsParam) {
          candidateIds = idsParam.split(",").filter(Boolean);
        }

        // If no candidate IDs in URL, default to first 3 demo candidates
        if (candidateIds.length < 2) {
          candidateIds = ["cand_demo_02", "cand_demo_01", "cand_demo_03"];
        }

        const res = await compareCandidates(candidateIds, {
          job_title: roleParam,
          required_skills: ["SQL", "Python", "Excel", "Statistics & Probability"],
          preferred_skills: ["Power BI", "Tableau"],
          target_experience_years: 2.5,
        });

        if (mounted) {
          if (res.success && res.data) {
            setComparisonData(res.data);
          } else {
            setErrorMessage(res.error || "Unable to load candidate comparison.");
          }
        }
      } catch (err) {
        console.error("Comparison load error:", err);
        if (mounted) setErrorMessage("Failed to compare candidate profiles.");
      } finally {
        if (mounted) setIsLoading(false);
      }
    }

    loadComparison();
    return () => {
      mounted = false;
    };
  }, [idsParam, roleParam]);

  const handleShortlistRecommended = async () => {
    if (!comparisonData) return;
    try {
      await shortlistCandidate(comparisonData.recommended_candidate_id, {
        candidate_name: comparisonData.recommended_candidate_name,
        job_title: comparisonData.job_title,
        status: "Shortlisted",
      });
      setShortlistedSuccess(`${comparisonData.recommended_candidate_name} shortlisted!`);
      setTimeout(() => setShortlistedSuccess(null), 3000);
    } catch {
      alert("Failed to shortlist candidate.");
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F8FA] flex flex-col">
      <div className="flex flex-1">
        <DashboardSidebar role="recruiter" />

        <main className="flex-1 p-6 lg:p-8 max-w-6xl mx-auto w-full space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#E1E6ED]">
            <div>
              <div className="flex items-center gap-2 text-xs text-[#5E6878]">
                <Link href="/recruiter" className="hover:text-[#2563EB]">
                  Hiring Intelligence
                </Link>
                <span>/</span>
                <Link href="/recruiter/matches" className="hover:text-[#2563EB]">
                  Candidate Matches
                </Link>
                <span>/</span>
                <span className="text-[#172033] font-semibold">Comparison</span>
              </div>
              <h1 className="text-2xl font-bold text-[#172033] mt-1 tracking-tight">
                Side-by-Side Candidate Comparison
              </h1>
              <p className="text-xs text-[#5E6878] mt-0.5">
                Target Role: <strong className="text-[#172033]">{roleParam}</strong> • Multi-factor objective alignment
              </p>
            </div>

            <Link
              href="/recruiter/matches"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs font-semibold text-[#172033] hover:bg-[#F1F4F8] transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Back to Leaderboard</span>
            </Link>
          </div>

          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center text-center space-y-3 bg-[#FFFFFF] rounded-lg border border-[#E1E6ED]">
              <Loader2 className="w-8 h-8 text-[#2563EB] animate-spin" />
              <h3 className="text-sm font-bold text-[#172033]">Comparing Candidate Profiles...</h3>
            </div>
          ) : errorMessage || !comparisonData ? (
            <div className="p-8 text-center bg-[#FFFFFF] rounded-lg border border-[#E1E6ED] text-xs text-[#C24141]">
              {errorMessage || "Unable to display candidate comparison."}
            </div>
          ) : (
            <div className="space-y-6">
              {/* RECOMMENDED CANDIDATE SPOTLIGHT BANNER */}
              <div className="p-5 rounded-lg border border-[#CDEDDD] bg-[#EAF7F0] shadow-2xs space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-[#16805C] text-[#FFFFFF] flex items-center justify-center font-bold">
                      <Award className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#16805C] block">
                        Recommended Candidate
                      </span>
                      <h2 className="text-base font-bold text-[#172033]">
                        {comparisonData.recommended_candidate_name}
                      </h2>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={handleShortlistRecommended}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-[#16805C] text-[#FFFFFF] hover:bg-[#136B4E] text-xs font-semibold shadow-xs transition-colors"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Shortlist Recommended</span>
                  </button>
                </div>

                <div className="text-xs text-[#172033] bg-[#FFFFFF]/80 p-3 rounded-md border border-[#CDEDDD]">
                  <strong className="text-[#16805C]">Mathematical Rationale: </strong>
                  <span>{comparisonData.recommendation_reason}</span>
                </div>

                {shortlistedSuccess && (
                  <div className="text-xs font-semibold text-[#16805C] animate-in fade-in">
                    ✓ {shortlistedSuccess}
                  </div>
                )}
              </div>

              {/* SIDE-BY-SIDE COMPARISON TABLE */}
              <div className="bg-[#FFFFFF] rounded-lg border border-[#E1E6ED] shadow-2xs overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-[#E1E6ED] bg-[#F7F8FA] text-[#5E6878]">
                        <th className="py-3 px-4 w-44 font-semibold">Attribute</th>
                        {comparisonData.candidates.map((c) => (
                          <th key={c.candidate_id} className="py-3 px-4 font-bold text-[#172033]">
                            <div className="flex flex-col">
                              <span className="text-sm">{c.name}</span>
                              <span className="text-[10px] text-[#8A94A6] font-normal">
                                {c.current_title || "Applicant"}
                              </span>
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E1E6ED]">
                      {/* Overall Match */}
                      <tr>
                        <td className="py-3.5 px-4 font-semibold text-[#5E6878] bg-[#F8FAFC]">
                          Overall Match
                        </td>
                        {comparisonData.candidates.map((c) => (
                          <td key={c.candidate_id} className="py-3.5 px-4">
                            <span
                              className={`text-base font-bold ${
                                c.match_score >= 85
                                  ? "text-[#16805C]"
                                  : c.match_score >= 70
                                  ? "text-[#2563EB]"
                                  : "text-[#B7791F]"
                              }`}
                            >
                              {Math.round(c.match_score)}%
                            </span>
                          </td>
                        ))}
                      </tr>

                      {/* Required Skills Coverage */}
                      <tr>
                        <td className="py-3.5 px-4 font-semibold text-[#5E6878] bg-[#F8FAFC]">
                          Required Skills
                        </td>
                        {comparisonData.candidates.map((c) => (
                          <td key={c.candidate_id} className="py-3.5 px-4">
                            <span className="px-2 py-0.5 rounded font-bold bg-[#EFF6FF] text-[#2563EB]">
                              {c.required_coverage_ratio} Skills
                            </span>
                          </td>
                        ))}
                      </tr>

                      {/* Preferred Skills Coverage */}
                      <tr>
                        <td className="py-3.5 px-4 font-semibold text-[#5E6878] bg-[#F8FAFC]">
                          Preferred Skills
                        </td>
                        {comparisonData.candidates.map((c) => (
                          <td key={c.candidate_id} className="py-3.5 px-4">
                            <span className="px-2 py-0.5 rounded font-medium bg-[#E8F7F4] text-[#0F9F8C]">
                              {c.preferred_coverage_ratio} Bonus
                            </span>
                          </td>
                        ))}
                      </tr>

                      {/* Experience Fit */}
                      <tr>
                        <td className="py-3.5 px-4 font-semibold text-[#5E6878] bg-[#F8FAFC]">
                          Experience Fit
                        </td>
                        {comparisonData.candidates.map((c) => (
                          <td key={c.candidate_id} className="py-3.5 px-4 font-medium text-[#172033]">
                            {c.experience_fit}
                          </td>
                        ))}
                      </tr>

                      {/* Skill Gap Tier */}
                      <tr>
                        <td className="py-3.5 px-4 font-semibold text-[#5E6878] bg-[#F8FAFC]">
                          Skill Gap Tier
                        </td>
                        {comparisonData.candidates.map((c) => (
                          <td key={c.candidate_id} className="py-3.5 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                                c.skill_gap_tier === "Low"
                                  ? "bg-[#EAF7F0] text-[#16805C]"
                                  : c.skill_gap_tier === "Medium"
                                  ? "bg-[#FFF6DD] text-[#B7791F]"
                                  : "bg-[#FDEEEE] text-[#C24141]"
                              }`}
                            >
                              {c.skill_gap_tier}
                            </span>
                          </td>
                        ))}
                      </tr>

                      {/* Hiring Risk */}
                      <tr>
                        <td className="py-3.5 px-4 font-semibold text-[#5E6878] bg-[#F8FAFC]">
                          Hiring Risk
                        </td>
                        {comparisonData.candidates.map((c) => (
                          <td key={c.candidate_id} className="py-3.5 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                c.hiring_risk_level === "LOW RISK"
                                  ? "bg-[#EAF7F0] text-[#16805C] border border-[#CDEDDD]"
                                  : c.hiring_risk_level === "MEDIUM RISK"
                                  ? "bg-[#FFF6DD] text-[#B7791F] border border-[#F2DEAA]"
                                  : "bg-[#FDEEEE] text-[#C24141] border border-[#F2CACA]"
                              }`}
                            >
                              {c.hiring_risk_level}
                            </span>
                          </td>
                        ))}
                      </tr>

                      {/* Resume Evidence Snippets */}
                      <tr>
                        <td className="py-3.5 px-4 font-semibold text-[#5E6878] bg-[#F8FAFC]">
                          Sample Evidence
                        </td>
                        {comparisonData.candidates.map((c) => (
                          <td key={c.candidate_id} className="py-3.5 px-4">
                            {c.key_evidence.length > 0 ? (
                              <p className="text-[11px] text-[#5E6878] italic bg-[#F8FAFC] p-2 rounded border border-[#EDF0F4] leading-relaxed">
                                &quot;{c.key_evidence[0]}&quot;
                              </p>
                            ) : (
                              <span className="text-[11px] text-[#8A94A6] italic">
                                Skill detected, evidence citation uncaptured.
                              </span>
                            )}
                          </td>
                        ))}
                      </tr>

                      {/* Recommendation */}
                      <tr>
                        <td className="py-3.5 px-4 font-semibold text-[#5E6878] bg-[#F8FAFC]">
                          Recommendation
                        </td>
                        {comparisonData.candidates.map((c) => (
                          <td key={c.candidate_id} className="py-3.5 px-4 font-bold text-[#172033]">
                            {c.recommendation}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Ethical Disclaimer */}
              <div className="p-3 rounded-md border border-[#E1E6ED] bg-[#F8FAFC] text-[11px] text-[#5E6878]">
                <strong>Decision Support Notice: </strong>
                {comparisonData.disclaimer}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default function CandidateComparisonPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#F7F8FA] flex items-center justify-center p-8">
          <div className="flex items-center gap-2 text-xs text-[#5E6878]">
            <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
            <span>Loading comparison matrix...</span>
          </div>
        </div>
      }
    >
      <CandidateComparisonContent />
    </Suspense>
  );
}
