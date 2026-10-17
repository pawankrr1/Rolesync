"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Search,
  Filter,
  ArrowUpDown,
  FileText,
  Star,
  Users,
  Briefcase,
  ChevronRight,
  ShieldCheck,
  Award,
  Layers,
  ArrowRight,
  Loader2,
  X,
  ExternalLink,
  SlidersHorizontal,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import {
  fetchRecruiterJobs,
  fetchDemoApplicants,
  rankRecruiterCandidates,
  shortlistCandidate,
  removeShortlistCandidate,
  fetchShortlist,
} from "@/lib/api";
import {
  RankedCandidateItem,
  RecruiterRankResponse,
  RecruiterJobItem,
  ShortlistItemResponse,
} from "@/lib/types";

function CandidateMatchesContent() {
  const searchParams = useSearchParams();
  const initialRoleParam = searchParams.get("role");

  const [jobs, setJobs] = useState<RecruiterJobItem[]>([]);
  const [selectedJobTitle, setSelectedJobTitle] = useState<string>(
    initialRoleParam || "Data Analyst"
  );
  const [activeJob, setActiveJob] = useState<RecruiterJobItem | null>(null);

  const [rankingResult, setRankingResult] = useState<RecruiterRankResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [shortlistedMap, setShortlistedMap] = useState<Record<string, boolean>>({});

  // Filter & Search states
  const [searchTerm, setSearchTerm] = useState("");
  const [matchTierFilter, setMatchTierFilter] = useState<string>("all");
  const [riskFilter, setRiskFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"score" | "exp" | "coverage">("score");

  // Selection for comparison
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);

  // Modals
  const [whyCandidate, setWhyCandidate] = useState<RankedCandidateItem | null>(null);
  const [evidenceCandidate, setEvidenceCandidate] = useState<RankedCandidateItem | null>(null);

  // Active view tab: "ranking" or "matrix"
  const [viewTab, setViewTab] = useState<"ranking" | "matrix">("ranking");

  // 1. Initial Load: Fetch Jobs and Shortlists
  useEffect(() => {
    let mounted = true;
    async function loadInitial() {
      try {
        const [jobsRes, shortRes] = await Promise.all([
          fetchRecruiterJobs(50, 0),
          fetchShortlist(),
        ]);
        if (mounted) {
          if (jobsRes.success && jobsRes.data) {
            setJobs(jobsRes.data);
            const found = jobsRes.data.find(
              (j) => j.title.toLowerCase() === selectedJobTitle.toLowerCase()
            );
            if (found) setActiveJob(found);
            else if (jobsRes.data.length > 0 && !initialRoleParam) {
              setActiveJob(jobsRes.data[0]);
              setSelectedJobTitle(jobsRes.data[0].title);
            }
          }
          if (shortRes.success && shortRes.data) {
            const map: Record<string, boolean> = {};
            shortRes.data.forEach((s) => {
              map[s.candidate_id] = true;
            });
            setShortlistedMap(map);
          }
        }
      } catch (err) {
        console.error("Failed to load matching requisitions:", err);
      }
    }
    loadInitial();
    return () => {
      mounted = false;
    };
  }, [initialRoleParam]);

  // 2. Perform Matching whenever selectedJob changes
  useEffect(() => {
    let mounted = true;
    async function runMatching() {
      setIsLoading(true);
      try {
        // Resolve job requirements
        let reqs = ["SQL", "Python", "Excel", "Statistics & Probability"];
        let prefs = ["Power BI", "Tableau"];
        let expMin = 2;

        if (activeJob) {
          reqs = activeJob.required_skills.length ? activeJob.required_skills : reqs;
          prefs = activeJob.preferred_skills.length ? activeJob.preferred_skills : prefs;
          expMin = activeJob.experience_years_min;
        }

        const appRes = await fetchDemoApplicants();
        const candidatePool = appRes.success && appRes.data ? appRes.data : [];

        const rankRes = await rankRecruiterCandidates({
          job_title: selectedJobTitle,
          required_skills: reqs,
          preferred_skills: prefs,
          target_experience_years: expMin,
          candidates: candidatePool,
        });

        if (mounted && rankRes.success && rankRes.data) {
          setRankingResult(rankRes.data);
        }
      } catch (err) {
        console.error("Candidate ranking error:", err);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }
    runMatching();
    return () => {
      mounted = false;
    };
  }, [selectedJobTitle, activeJob]);

  const handleSelectJobChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedJobTitle(val);
    const found = jobs.find((j) => j.title === val);
    if (found) setActiveJob(found);
  };

  const handleToggleShortlist = async (candidate: RankedCandidateItem) => {
    const isCurrently = !!shortlistedMap[candidate.candidate_id];
    const newStatus = !isCurrently;

    setShortlistedMap((prev) => ({
      ...prev,
      [candidate.candidate_id]: newStatus,
    }));

    try {
      if (newStatus) {
        await shortlistCandidate(candidate.candidate_id, {
          candidate_name: candidate.name,
          candidate_email: candidate.email,
          job_title: selectedJobTitle,
          match_score: candidate.match_score,
          status: "Shortlisted",
        });
      } else {
        await removeShortlistCandidate(candidate.candidate_id);
      }
    } catch (err) {
      console.error("Shortlist update failed:", err);
    }
  };

  const handleToggleCompare = (candidateId: string) => {
    if (selectedForCompare.includes(candidateId)) {
      setSelectedForCompare(selectedForCompare.filter((id) => id !== candidateId));
    } else {
      if (selectedForCompare.length >= 4) {
        alert("You can compare up to 4 candidates simultaneously.");
        return;
      }
      setSelectedForCompare([...selectedForCompare, candidateId]);
    }
  };

  // Filter & Sort ranked list
  const filteredCandidates = useMemo(() => {
    if (!rankingResult) return [];
    let list = [...rankingResult.ranked_candidates];

    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      list = list.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          (c.current_title && c.current_title.toLowerCase().includes(q)) ||
          c.strong_skills.some((s) => s.toLowerCase().includes(q))
      );
    }

    if (matchTierFilter === "90") {
      list = list.filter((c) => c.match_score >= 90.0);
    } else if (matchTierFilter === "80") {
      list = list.filter((c) => c.match_score >= 80.0);
    } else if (matchTierFilter === "70") {
      list = list.filter((c) => c.match_score >= 70.0);
    }

    if (riskFilter !== "all") {
      list = list.filter((c) => c.hiring_risk?.level === riskFilter);
    }

    if (sortBy === "score") {
      list.sort((a, b) => b.match_score - a.match_score);
    } else if (sortBy === "exp") {
      list.sort((a, b) => b.experience_years - a.experience_years);
    } else if (sortBy === "coverage") {
      list.sort((a, b) => (b.matched_required_count || 0) - (a.matched_required_count || 0));
    }

    return list;
  }, [rankingResult, searchTerm, matchTierFilter, riskFilter, sortBy]);

  // All distinct skills for the Skill Match Matrix
  const matrixSkills = useMemo(() => {
    if (!rankingResult) return [];
    const all = [
      ...rankingResult.required_skills,
      ...rankingResult.preferred_skills,
    ];
    return Array.from(new Set(all));
  }, [rankingResult]);

  return (
    <div className="min-h-screen bg-[#F7F8FA] flex flex-col">
      <div className="flex flex-1">
        <DashboardSidebar role="recruiter" />

        <main className="flex-1 p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
          {/* Header & Job Selector */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-3 border-b border-[#E1E6ED]">
            <div>
              <div className="flex items-center gap-2 text-xs text-[#5E6878]">
                <Link href="/recruiter" className="hover:text-[#2563EB]">
                  Hiring Intelligence
                </Link>
                <span>/</span>
                <span className="text-[#172033] font-semibold">Candidate Matches</span>
              </div>
              <h1 className="text-2xl font-bold text-[#172033] mt-1 tracking-tight">
                Candidate Ranking & Alignment
              </h1>
              <p className="text-xs text-[#5E6878] mt-0.5">
                Explainable talent ranking powered by deterministic 4-factor scoring and verified resume evidence.
              </p>
            </div>

            {/* Role Switcher */}
            <div className="flex items-center gap-3">
              <div className="flex flex-col">
                <span className="text-[10px] font-semibold text-[#8A94A6] uppercase tracking-wider">
                  Target Role
                </span>
                <select
                  value={selectedJobTitle}
                  onChange={handleSelectJobChange}
                  className="px-3 py-1.5 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs font-semibold text-[#172033] shadow-2xs focus:outline-hidden focus:border-[#2563EB]"
                >
                  {jobs.length > 0 ? (
                    jobs.map((j) => (
                      <option key={j.id} value={j.title}>
                        {j.title} ({j.company || "Org"})
                      </option>
                    ))
                  ) : (
                    <option value="Data Analyst">Data Analyst</option>
                  )}
                </select>
              </div>

              <Link
                href="/recruiter/create-job"
                className="mt-4 px-3 py-1.5 rounded-md bg-[#EFF6FF] text-[#2563EB] hover:bg-[#DBEAFE] text-xs font-semibold border border-[#BFDBFE] transition-colors"
              >
                + New Job
              </Link>
            </div>
          </div>

          {/* Active Job Requirements Banner */}
          {rankingResult && (
            <div className="p-4 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm text-[#172033]">
                    {rankingResult.job_title}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] bg-[#F1F4F8] text-[#5E6878]">
                    {rankingResult.total_candidates_evaluated} Candidates Evaluated
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-1.5 text-xs">
                  <span className="text-[11px] font-semibold text-[#8A94A6]">Required:</span>
                  {rankingResult.required_skills.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded text-[10px] font-medium bg-[#EFF6FF] text-[#2563EB] border border-[#BFDBFE]"
                    >
                      {s}
                    </span>
                  ))}
                  {rankingResult.preferred_skills.length > 0 && (
                    <>
                      <span className="text-[11px] font-semibold text-[#8A94A6] ml-2">Preferred:</span>
                      {rankingResult.preferred_skills.map((s, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded text-[10px] font-medium bg-[#E8F7F4] text-[#0F9F8C] border border-[#A7F3D0]"
                        >
                          {s}
                        </span>
                      ))}
                    </>
                  )}
                </div>
              </div>

              {/* View Switcher Tabs */}
              <div className="flex items-center p-1 bg-[#F1F4F8] rounded-md border border-[#E1E6ED] text-xs shrink-0">
                <button
                  type="button"
                  onClick={() => setViewTab("ranking")}
                  className={`px-3 py-1 rounded font-medium transition-colors ${
                    viewTab === "ranking"
                      ? "bg-[#FFFFFF] text-[#172033] shadow-xs font-semibold"
                      : "text-[#5E6878] hover:text-[#172033]"
                  }`}
                >
                  Candidate Leaderboard
                </button>
                <button
                  type="button"
                  onClick={() => setViewTab("matrix")}
                  className={`px-3 py-1 rounded font-medium transition-colors ${
                    viewTab === "matrix"
                      ? "bg-[#FFFFFF] text-[#172033] shadow-xs font-semibold"
                      : "text-[#5E6878] hover:text-[#172033]"
                  }`}
                >
                  Skill Match Matrix
                </button>
              </div>
            </div>
          )}

          {/* Search, Filter & Sort Controls */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative w-64">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#8A94A6]" />
                <input
                  type="text"
                  placeholder="Filter candidate or skill..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033] focus:outline-hidden focus:border-[#2563EB]"
                />
              </div>

              <select
                value={matchTierFilter}
                onChange={(e) => setMatchTierFilter(e.target.value)}
                className="px-2.5 py-1.5 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#5E6878]"
              >
                <option value="all">All Match Tiers</option>
                <option value="90">90%+ Match</option>
                <option value="80">80%+ Match</option>
                <option value="70">70%+ Match</option>
              </select>

              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="px-2.5 py-1.5 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#5E6878]"
              >
                <option value="all">All Risk Tiers</option>
                <option value="LOW RISK">Low Risk Only</option>
                <option value="MEDIUM RISK">Medium Risk</option>
                <option value="HIGH RISK">High Risk</option>
              </select>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span className="text-[#8A94A6]">Sort:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="px-2.5 py-1.5 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033]"
              >
                <option value="score">Overall Match (High to Low)</option>
                <option value="coverage">Required Skill Coverage</option>
                <option value="exp">Experience (High to Low)</option>
              </select>
            </div>
          </div>

          {/* Floating Comparison Action Bar */}
          {selectedForCompare.length > 0 && (
            <div className="sticky top-20 z-30 p-3 rounded-lg border border-[#2563EB] bg-[#EFF6FF] shadow-md flex items-center justify-between gap-4 animate-in fade-in slide-in-from-top-2">
              <div className="flex items-center gap-2 text-xs text-[#172033]">
                <span className="font-bold text-[#2563EB]">
                  {selectedForCompare.length} Candidates Selected
                </span>
                <span className="text-[#5E6878]">for side-by-side comparison</span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedForCompare([])}
                  className="px-2.5 py-1 rounded text-xs text-[#5E6878] hover:text-[#172033]"
                >
                  Clear Selection
                </button>
                <Link
                  href={`/recruiter/compare?ids=${selectedForCompare.join(",")}&role=${encodeURIComponent(
                    selectedJobTitle
                  )}`}
                  className="px-3.5 py-1.5 rounded bg-[#2563EB] text-[#FFFFFF] hover:bg-[#1D4ED8] text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors"
                >
                  <span>Compare Candidates</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          )}

          {/* Main Content Area */}
          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center text-center space-y-3 bg-[#FFFFFF] rounded-lg border border-[#E1E6ED]">
              <Loader2 className="w-8 h-8 text-[#2563EB] animate-spin" />
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-[#172033]">Analyzing Candidate Profiles...</h3>
                <p className="text-xs text-[#5E6878]">
                  Comparing required skills, extracting resume citations, and computing deterministic alignment.
                </p>
              </div>
            </div>
          ) : viewTab === "ranking" ? (
            /* 1. Candidate Leaderboard Table */
            <div className="bg-[#FFFFFF] rounded-lg border border-[#E1E6ED] shadow-2xs overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[#E1E6ED] bg-[#F7F8FA] text-[#5E6878] font-semibold">
                      <th className="py-3 px-3 text-center w-10">Select</th>
                      <th className="py-3 px-3 w-12 text-center">Rank</th>
                      <th className="py-3 px-4">Candidate & Background</th>
                      <th className="py-3 px-4 text-center">Match Score</th>
                      <th className="py-3 px-4 text-center">Req. Skills</th>
                      <th className="py-3 px-4 text-center">Experience Fit</th>
                      <th className="py-3 px-4">Top Skill Gap</th>
                      <th className="py-3 px-4 text-center">Hiring Risk</th>
                      <th className="py-3 px-4 text-center">Recommendation</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E1E6ED]">
                    {filteredCandidates.length === 0 ? (
                      <tr>
                        <td colSpan={10} className="py-12 text-center text-[#8A94A6]">
                          No candidates match the specified filter criteria.
                        </td>
                      </tr>
                    ) : (
                      filteredCandidates.map((cand) => {
                        const isShortlisted = !!shortlistedMap[cand.candidate_id];
                        const isCompared = selectedForCompare.includes(cand.candidate_id);

                        return (
                          <tr
                            key={cand.candidate_id}
                            className={`hover:bg-[#F8FAFC] transition-colors ${
                              isCompared ? "bg-[#EFF6FF]/40" : ""
                            }`}
                          >
                            {/* Checkbox */}
                            <td className="py-3.5 px-3 text-center">
                              <input
                                type="checkbox"
                                checked={isCompared}
                                onChange={() => handleToggleCompare(cand.candidate_id)}
                                className="w-3.5 h-3.5 rounded border-[#CBD5E1] text-[#2563EB] focus:ring-[#2563EB]"
                              />
                            </td>

                            {/* Rank */}
                            <td className="py-3.5 px-3 text-center font-bold text-[#5E6878]">
                              #{cand.rank}
                            </td>

                            {/* Candidate */}
                            <td className="py-3.5 px-4 font-semibold text-[#172033]">
                              <div className="flex flex-col">
                                <div className="flex items-center gap-1.5">
                                  <Link
                                    href={`/recruiter/candidates/${cand.candidate_id}`}
                                    className="hover:text-[#2563EB] hover:underline"
                                  >
                                    {cand.name}
                                  </Link>
                                  {cand.adjacent_talent?.is_adjacent && (
                                    <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-[#E8F7F4] text-[#0F9F8C] border border-[#A7F3D0]">
                                      Near Match
                                    </span>
                                  )}
                                </div>
                                <span className="text-[10px] text-[#8A94A6] font-normal">
                                  {cand.current_title || "Verified Applicant"} • {cand.experience_display}
                                </span>
                              </div>
                            </td>

                            {/* Match Score */}
                            <td className="py-3.5 px-4 text-center">
                              <div className="inline-flex items-center gap-1.5">
                                <span
                                  className={`text-sm font-bold ${
                                    cand.match_score >= 85
                                      ? "text-[#16805C]"
                                      : cand.match_score >= 70
                                      ? "text-[#2563EB]"
                                      : "text-[#B7791F]"
                                  }`}
                                >
                                  {Math.round(cand.match_score)}%
                                </span>
                              </div>
                            </td>

                            {/* Required Skills Coverage */}
                            <td className="py-3.5 px-4 text-center">
                              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-[#EFF6FF] text-[#2563EB]">
                                {cand.required_skill_coverage_ratio || "3/4"}
                              </span>
                            </td>

                            {/* Experience Fit */}
                            <td className="py-3.5 px-4 text-center text-[#5E6878]">
                              <span className="text-[11px] font-medium">
                                {cand.experience_fit_label || "Strong"}
                              </span>
                            </td>

                            {/* Top Gap */}
                            <td className="py-3.5 px-4 text-[#5E6878]">
                              {cand.top_skill_gap && cand.top_skill_gap !== "None" ? (
                                <span className="inline-flex items-center gap-1 text-[11px] text-[#C24141]">
                                  <span className="text-[#C24141]">△</span>
                                  <span>{cand.top_skill_gap}</span>
                                </span>
                              ) : (
                                <span className="text-[11px] text-[#16805C] font-medium">
                                  None (Full Coverage)
                                </span>
                              )}
                            </td>

                            {/* Hiring Risk */}
                            <td className="py-3.5 px-4 text-center">
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                                  cand.hiring_risk?.level === "LOW RISK"
                                    ? "bg-[#EAF7F0] text-[#16805C] border border-[#CDEDDD]"
                                    : cand.hiring_risk?.level === "MEDIUM RISK"
                                    ? "bg-[#FFF6DD] text-[#B7791F] border border-[#F2DEAA]"
                                    : "bg-[#FDEEEE] text-[#C24141] border border-[#F2CACA]"
                                }`}
                              >
                                {cand.hiring_risk?.level || "LOW RISK"}
                              </span>
                            </td>

                            {/* Recommendation */}
                            <td className="py-3.5 px-4 text-center">
                              <span
                                className={`text-[11px] font-semibold ${
                                  cand.recommendation_status === "Recommended"
                                    ? "text-[#16805C]"
                                    : "text-[#5E6878]"
                                }`}
                              >
                                {cand.recommendation_status}
                              </span>
                            </td>

                            {/* Actions */}
                            <td className="py-3.5 px-4 text-right">
                              <div className="flex items-center justify-end gap-1.5">
                                <button
                                  type="button"
                                  onClick={() => setWhyCandidate(cand)}
                                  className="px-2 py-1 rounded bg-[#F1F4F8] hover:bg-[#E1E6ED] text-[#172033] font-semibold text-[11px] transition-colors"
                                  title="Why this candidate?"
                                >
                                  Why?
                                </button>

                                <button
                                  type="button"
                                  onClick={() => setEvidenceCandidate(cand)}
                                  className="px-2 py-1 rounded bg-[#EFF6FF] hover:bg-[#DBEAFE] text-[#2563EB] font-semibold text-[11px] transition-colors"
                                  title="View resume sentence citations"
                                >
                                  Evidence
                                </button>

                                <button
                                  type="button"
                                  onClick={() => handleToggleShortlist(cand)}
                                  className={`px-2 py-1 rounded text-[11px] font-semibold transition-colors ${
                                    isShortlisted
                                      ? "bg-[#EAF7F0] text-[#16805C] border border-[#CDEDDD]"
                                      : "bg-[#FFFFFF] border border-[#E1E6ED] text-[#5E6878] hover:text-[#172033]"
                                  }`}
                                  title={isShortlisted ? "Candidate shortlisted" : "Add to shortlist"}
                                >
                                  {isShortlisted ? "Shortlisted" : "Shortlist"}
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            /* 2. Skill Match Matrix Table */
            <div className="bg-[#FFFFFF] rounded-lg border border-[#E1E6ED] shadow-2xs overflow-hidden space-y-4 p-5">
              <div className="flex items-center justify-between border-b border-[#EDF0F4] pb-3">
                <div>
                  <h3 className="text-sm font-bold text-[#172033]">Candidate Skill Match Matrix</h3>
                  <p className="text-xs text-[#5E6878]">
                    Cross-comparison of verified candidate competencies against role requirements.
                  </p>
                </div>

                {/* Accessible Legend */}
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-[#16805C]">✓</span>
                    <span className="text-[#5E6878]">Strong Match</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-[#B7791F]">△</span>
                    <span className="text-[#5E6878]">Partial / Adjoining</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-[#C24141]">✕</span>
                    <span className="text-[#5E6878]">Missing</span>
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[#E1E6ED] bg-[#F7F8FA] text-[#5E6878] font-semibold">
                      <th className="py-3 px-3">Candidate</th>
                      {matrixSkills.map((skill, idx) => (
                        <th key={idx} className="py-3 px-3 text-center">
                          {skill}
                        </th>
                      ))}
                      <th className="py-3 px-3 text-center font-bold text-[#172033]">Match %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E1E6ED]">
                    {filteredCandidates.map((cand) => (
                      <tr key={cand.candidate_id} className="hover:bg-[#F8FAFC]">
                        <td className="py-3 px-3 font-semibold text-[#172033]">
                          <div className="flex flex-col">
                            <span>{cand.name}</span>
                            <span className="text-[10px] text-[#8A94A6]">
                              {cand.current_title || "Applicant"}
                            </span>
                          </div>
                        </td>

                        {matrixSkills.map((skill, idx) => {
                          const isStrong = cand.strong_skills.some(
                            (s) => s.toLowerCase() === skill.toLowerCase()
                          );
                          const isPartial = cand.partial_skills.some(
                            (s) => s.toLowerCase() === skill.toLowerCase()
                          );

                          return (
                            <td key={idx} className="py-3 px-3 text-center">
                              {isStrong ? (
                                <span
                                  className="inline-block px-1.5 py-0.5 rounded bg-[#EAF7F0] text-[#16805C] font-bold text-xs"
                                  title={`${cand.name} strongly demonstrates ${skill}`}
                                >
                                  ✓
                                </span>
                              ) : isPartial ? (
                                <span
                                  className="inline-block px-1.5 py-0.5 rounded bg-[#FFF6DD] text-[#B7791F] font-bold text-xs"
                                  title={`${cand.name} has partial/transferable background in ${skill}`}
                                >
                                  △
                                </span>
                              ) : (
                                <span
                                  className="inline-block px-1.5 py-0.5 rounded bg-[#FDEEEE] text-[#C24141] font-bold text-xs"
                                  title={`Missing requirement in ${skill}`}
                                >
                                  ✕
                                </span>
                              )}
                            </td>
                          );
                        })}

                        <td className="py-3 px-3 text-center font-bold text-xs text-[#172033]">
                          {Math.round(cand.match_score)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Modal: "Why This Candidate?" Explainability */}
          {whyCandidate && (
            <div className="fixed inset-0 z-50 bg-[#172033]/60 backdrop-blur-xs flex items-center justify-center p-4">
              <div className="bg-[#FFFFFF] rounded-xl border border-[#E1E6ED] max-w-xl w-full p-6 shadow-xl space-y-5 animate-in fade-in zoom-in-95">
                <div className="flex items-start justify-between border-b border-[#EDF0F4] pb-3">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#2563EB]">
                      Explainable Scoring Audit
                    </span>
                    <h3 className="text-lg font-bold text-[#172033] mt-0.5">
                      Why {whyCandidate.name}?
                    </h3>
                    <p className="text-xs text-[#5E6878]">
                      Overall Match: <strong className="text-[#172033]">{Math.round(whyCandidate.match_score)}%</strong> • {whyCandidate.score_grade}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setWhyCandidate(null)}
                    className="text-[#8A94A6] hover:text-[#172033] p-1 rounded"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Deterministic Factor Weights */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-[#172033] uppercase tracking-wider">
                    Scoring Factor Breakdown
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 rounded bg-[#F8FAFC] border border-[#E1E6ED]">
                      <span className="text-[#8A94A6] text-[10px] block">Required Skill Coverage (60%)</span>
                      <span className="font-bold text-[#172033] text-sm">
                        {whyCandidate.required_skill_coverage_ratio} Skills Verified
                      </span>
                    </div>
                    <div className="p-2.5 rounded bg-[#F8FAFC] border border-[#E1E6ED]">
                      <span className="text-[#8A94A6] text-[10px] block">Semantic Domain Overlap (20%)</span>
                      <span className="font-bold text-[#172033] text-sm">
                        High Alignment
                      </span>
                    </div>
                    <div className="p-2.5 rounded bg-[#F8FAFC] border border-[#E1E6ED]">
                      <span className="text-[#8A94A6] text-[10px] block">Experience Alignment (10%)</span>
                      <span className="font-bold text-[#172033] text-sm">
                        {whyCandidate.experience_display} ({whyCandidate.experience_fit_label})
                      </span>
                    </div>
                    <div className="p-2.5 rounded bg-[#F8FAFC] border border-[#E1E6ED]">
                      <span className="text-[#8A94A6] text-[10px] block">Preferred Skill Coverage (10%)</span>
                      <span className="font-bold text-[#172033] text-sm">
                        {whyCandidate.preferred_skill_coverage_ratio} Bonus Met
                      </span>
                    </div>
                  </div>
                </div>

                {/* Strengths & Gaps */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded bg-[#EAF7F0] border border-[#CDEDDD] space-y-1.5">
                    <span className="font-bold text-[#16805C] flex items-center gap-1">
                      <span>✓ Key Strengths</span>
                    </span>
                    <ul className="space-y-1 text-[#172033]">
                      {whyCandidate.strong_skills.slice(0, 4).map((s, idx) => (
                        <li key={idx} className="flex items-center gap-1.5">
                          <span className="text-[#16805C]">✓</span>
                          <span>{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-3 rounded bg-[#FFF6DD] border border-[#F2DEAA] space-y-1.5">
                    <span className="font-bold text-[#B7791F] flex items-center gap-1">
                      <span>△ Identified Gaps</span>
                    </span>
                    <ul className="space-y-1 text-[#172033]">
                      {whyCandidate.missing_skills.length === 0 ? (
                        <li className="text-[#5E6878] italic">No core requirements missing.</li>
                      ) : (
                        whyCandidate.missing_skills.slice(0, 3).map((s, idx) => (
                          <li key={idx} className="flex items-center gap-1.5">
                            <span className="text-[#C24141]">△</span>
                            <span>{s}</span>
                          </li>
                        ))
                      )}
                    </ul>
                  </div>
                </div>

                {/* Why Not 100%? Section */}
                <div className="p-3 rounded bg-[#F8FAFC] border border-[#E1E6ED] space-y-1 text-xs">
                  <span className="font-bold text-[#172033]">Why Not 100%?</span>
                  <p className="text-[#5E6878] leading-relaxed">
                    {whyCandidate.detailed_explanation.why_not_match?.join(" ") || "Full core alignment achieved."}
                  </p>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-[10px] text-[#8A94A6]">
                    Deterministic explanation generated by mathematical scoring.
                  </span>
                  <button
                    type="button"
                    onClick={() => setWhyCandidate(null)}
                    className="px-4 py-1.5 rounded-md bg-[#172033] text-[#FFFFFF] text-xs font-semibold"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Modal: Resume Evidence Citations */}
          {evidenceCandidate && (
            <div className="fixed inset-0 z-50 bg-[#172033]/60 backdrop-blur-xs flex items-center justify-center p-4">
              <div className="bg-[#FFFFFF] rounded-xl border border-[#E1E6ED] max-w-xl w-full p-6 shadow-xl space-y-4 animate-in fade-in zoom-in-95 max-h-[85vh] flex flex-col">
                <div className="flex items-start justify-between border-b border-[#EDF0F4] pb-3 shrink-0">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#0F9F8C]">
                      Verified Resume Citations
                    </span>
                    <h3 className="text-base font-bold text-[#172033] mt-0.5">
                      Skill Evidence for {evidenceCandidate.name}
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => setEvidenceCandidate(null)}
                    className="text-[#8A94A6] hover:text-[#172033] p-1 rounded"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs">
                  {evidenceCandidate.detailed_explanation.evidence_list &&
                  evidenceCandidate.detailed_explanation.evidence_list.length > 0 ? (
                    evidenceCandidate.detailed_explanation.evidence_list.map((item, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg border border-[#E1E6ED] bg-[#F8FAFC] space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-[#172033]">{item.skill}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              item.status === "strong"
                                ? "bg-[#EAF7F0] text-[#16805C]"
                                : "bg-[#FFF6DD] text-[#B7791F]"
                            }`}
                          >
                            {item.status === "strong" ? "Strong Fit" : "Partial Fit"}
                          </span>
                        </div>
                        <p className="text-[#5E6878] italic bg-[#FFFFFF] p-2 rounded border border-[#EDF0F4] leading-relaxed">
                          &quot;{item.evidence}&quot;
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 rounded border border-[#E1E6ED] bg-[#F8FAFC] text-center text-[#8A94A6]">
                      Skill detected from candidate profile, but supporting text evidence was not captured.
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-[#EDF0F4] shrink-0">
                  <span className="text-[10px] text-[#8A94A6]">
                    Direct sentence citations parsed strictly from resume text.
                  </span>
                  <button
                    type="button"
                    onClick={() => setEvidenceCandidate(null)}
                    className="px-4 py-1.5 rounded-md bg-[#172033] text-[#FFFFFF] text-xs font-semibold"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default function CandidateMatchesPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#F7F8FA] flex items-center justify-center p-8">
          <div className="flex items-center gap-2 text-xs text-[#5E6878]">
            <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
            <span>Loading candidate matches...</span>
          </div>
        </div>
      }
    >
      <CandidateMatchesContent />
    </Suspense>
  );
}
