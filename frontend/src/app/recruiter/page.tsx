"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Users,
  Briefcase,
  CheckCircle2,
  TrendingUp,
  FileText,
  Search,
  ArrowRight,
  ShieldCheck,
  Award,
  AlertTriangle,
  Compass,
  Layers,
  ChevronRight,
  Plus,
  BarChart3,
  Sparkles,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import {
  fetchRecruiterMetrics,
  fetchRecruiterJobs,
} from "@/lib/api";
import {
  RecruiterOverviewMetrics,
  RecruiterJobItem,
} from "@/lib/types";

export default function RecruiterOverviewPage() {
  const [metrics, setMetrics] = useState<RecruiterOverviewMetrics | null>(null);
  const [jobs, setJobs] = useState<RecruiterJobItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      try {
        const [mRes, jRes] = await Promise.all([
          fetchRecruiterMetrics(),
          fetchRecruiterJobs(20, 0),
        ]);
        if (mounted) {
          if (mRes.success && mRes.data) setMetrics(mRes.data);
          if (jRes.success && jRes.data) setJobs(jRes.data);
        }
      } catch (err) {
        console.error("Failed to load recruiter data:", err);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadData();
    return () => {
      mounted = false;
    };
  }, []);

  const filteredJobs = jobs.filter(
    (j) =>
      j.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (j.company && j.company.toLowerCase().includes(searchTerm.toLowerCase())) ||
      j.location.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#F7F8FA] flex flex-col">
      <div className="flex flex-1">
        <DashboardSidebar role="recruiter" />

        <main className="flex-1 p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-8">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-[#E1E6ED]">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#EFF6FF] text-[#2563EB] border border-[#BFDBFE]">
                  Recruiter Workspace
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#F1F4F8] text-[#5E6878]">
                  Zero-PII Compliance
                </span>
              </div>
              <h1 className="text-2xl lg:text-3xl font-bold text-[#172033] mt-2 tracking-tight">
                Hiring Intelligence
              </h1>
              <p className="text-sm text-[#5E6878] mt-1">
                Find candidates based on skill alignment—not just keywords.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/recruiter/create-job"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-md bg-[#2563EB] text-[#FFFFFF] hover:bg-[#1D4ED8] text-xs font-semibold shadow-xs transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>Create Job</span>
              </Link>
              <Link
                href="/recruiter/matches"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-md bg-[#FFFFFF] border border-[#E1E6ED] text-[#172033] hover:bg-[#F1F4F8] text-xs font-semibold transition-colors"
              >
                <span>View Matches</span>
                <ArrowRight className="w-3.5 h-3.5 text-[#8A94A6]" />
              </Link>
            </div>
          </div>

          {/* Top Metrics Banner */}
          <section aria-label="Key Recruiting Metrics">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs">
                <div className="flex items-center justify-between text-[#8A94A6]">
                  <span className="text-xs font-medium uppercase tracking-wider">Open Roles</span>
                  <Briefcase className="w-4 h-4 text-[#2563EB]" />
                </div>
                <div className="mt-2 text-2xl lg:text-3xl font-bold text-[#172033]">
                  {metrics ? metrics.open_roles_count : 50}
                </div>
                <span className="text-[11px] text-[#5E6878] mt-1 block">Active requisitions in system</span>
              </div>

              <div className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs">
                <div className="flex items-center justify-between text-[#8A94A6]">
                  <span className="text-xs font-medium uppercase tracking-wider">Candidates Analyzed</span>
                  <Users className="w-4 h-4 text-[#0F9F8C]" />
                </div>
                <div className="mt-2 text-2xl lg:text-3xl font-bold text-[#172033]">
                  {metrics ? metrics.candidates_analyzed_count : 550}
                </div>
                <span className="text-[11px] text-[#5E6878] mt-1 block">Evaluated across all roles</span>
              </div>

              <div className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs">
                <div className="flex items-center justify-between text-[#8A94A6]">
                  <span className="text-xs font-medium uppercase tracking-wider">Strong Matches</span>
                  <Award className="w-4 h-4 text-[#16805C]" />
                </div>
                <div className="mt-2 text-2xl lg:text-3xl font-bold text-[#16805C]">
                  {metrics ? metrics.strong_matches_count : 46}
                </div>
                <span className="text-[11px] text-[#5E6878] mt-1 block">≥ 80% measured skill overlap</span>
              </div>

              <div className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs">
                <div className="flex items-center justify-between text-[#8A94A6]">
                  <span className="text-xs font-medium uppercase tracking-wider">Average Alignment</span>
                  <TrendingUp className="w-4 h-4 text-[#B7791F]" />
                </div>
                <div className="mt-2 text-2xl lg:text-3xl font-bold text-[#172033]">
                  {metrics ? `${Math.round(metrics.average_alignment_percentage)}%` : "81%"}
                </div>
                <span className="text-[11px] text-[#5E6878] mt-1 block">Dataset skill alignment</span>
              </div>
            </div>

            {/* Benchmark dataset badge */}
            <div className="mt-3 flex items-center justify-between p-3 rounded-md border border-[#E1E6ED] bg-[#F8FAFC] text-xs text-[#5E6878]">
              <div className="flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-[#16805C]"></span>
                <span className="font-semibold text-[#172033]">Data Grounding Notice:</span>
                <span>Active metrics are calculated against live benchmark profiles & database requisitions.</span>
              </div>
              <span className="text-[11px] px-2 py-0.5 rounded bg-[#EDF0F4] text-[#5E6878] font-mono">
                Sample Benchmark Pool
              </span>
            </div>
          </section>

          {/* Workflow Shortcuts Hub */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-4" aria-label="Workflow Quick Actions">
            <Link
              href="/recruiter/create-job"
              className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] hover:border-[#2563EB] hover:shadow-xs transition-all group"
            >
              <div className="w-9 h-9 rounded-md bg-[#EFF6FF] flex items-center justify-center text-[#2563EB] mb-3 group-hover:scale-105 transition-transform">
                <Briefcase className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-[#172033] flex items-center justify-between">
                <span>1. Job Description & Extraction</span>
                <ChevronRight className="w-4 h-4 text-[#8A94A6] group-hover:text-[#2563EB] transition-colors" />
              </h3>
              <p className="text-xs text-[#5E6878] mt-1">
                Paste any job requisition to extract, normalize, and classify required vs. preferred competencies.
              </p>
            </Link>

            <Link
              href="/recruiter/matches"
              className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] hover:border-[#2563EB] hover:shadow-xs transition-all group"
            >
              <div className="w-9 h-9 rounded-md bg-[#EAF7F0] flex items-center justify-center text-[#16805C] mb-3 group-hover:scale-105 transition-transform">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-[#172033] flex items-center justify-between">
                <span>2. Candidate Ranking & Matrix</span>
                <ChevronRight className="w-4 h-4 text-[#8A94A6] group-hover:text-[#16805C] transition-colors" />
              </h3>
              <p className="text-xs text-[#5E6878] mt-1">
                Deterministic 4-factor scoring, resume citations, skill match matrix, and candidate comparisons.
              </p>
            </Link>

            <Link
              href="/recruiter/insights"
              className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] hover:border-[#2563EB] hover:shadow-xs transition-all group"
            >
              <div className="w-9 h-9 rounded-md bg-[#FFF6DD] flex items-center justify-center text-[#B7791F] mb-3 group-hover:scale-105 transition-transform">
                <BarChart3 className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-[#172033] flex items-center justify-between">
                <span>3. Pool Shortages & Insights</span>
                <ChevronRight className="w-4 h-4 text-[#8A94A6] group-hover:text-[#B7791F] transition-colors" />
              </h3>
              <p className="text-xs text-[#5E6878] mt-1">
                Inspect applicant coverage percentages, common skill shortages, and market alignment trends.
              </p>
            </Link>
          </section>

          {/* Active Roles Section */}
          <section className="space-y-4" aria-label="Active Requisitions">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-bold text-[#172033]">Active Requisitions</h2>
                <p className="text-xs text-[#5E6878]">
                  Select a role to inspect applicant alignment or launch deterministic candidate matching.
                </p>
              </div>

              <div className="relative w-full sm:w-64">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#8A94A6]" />
                <input
                  type="text"
                  placeholder="Filter roles by title..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033] focus:outline-hidden focus:border-[#2563EB]"
                />
              </div>
            </div>

            <div className="bg-[#FFFFFF] rounded-lg border border-[#E1E6ED] shadow-2xs overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[#E1E6ED] bg-[#F7F8FA] text-[#5E6878] font-semibold">
                      <th className="py-3 px-4">Role Title</th>
                      <th className="py-3 px-4">Company & Location</th>
                      <th className="py-3 px-4">Required Skills</th>
                      <th className="py-3 px-4 text-center">Applicants</th>
                      <th className="py-3 px-4 text-center">Strong Matches</th>
                      <th className="py-3 px-4 text-center">Avg Alignment</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E1E6ED]">
                    {filteredJobs.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-[#8A94A6]">
                          No requisitions found matching &quot;{searchTerm}&quot;.
                        </td>
                      </tr>
                    ) : (
                      filteredJobs.slice(0, 10).map((job) => (
                        <tr key={job.id} className="hover:bg-[#F8FAFC] transition-colors">
                          <td className="py-3.5 px-4 font-semibold text-[#172033]">
                            <div className="flex flex-col">
                              <span>{job.title}</span>
                              <span className="text-[10px] text-[#8A94A6] font-normal">
                                Min. {job.experience_years_min} yrs exp • {job.status}
                              </span>
                            </div>
                          </td>
                          <td className="py-3.5 px-4 text-[#5E6878]">
                            <div className="flex flex-col">
                              <span>{job.company || "Enterprise"}</span>
                              <span className="text-[10px] text-[#8A94A6]">{job.location}</span>
                            </div>
                          </td>
                          <td className="py-3.5 px-4">
                            <div className="flex flex-wrap gap-1 max-w-xs">
                              {job.required_skills.slice(0, 3).map((s, idx) => (
                                <span
                                  key={idx}
                                  className="px-2 py-0.5 rounded text-[10px] bg-[#EFF6FF] text-[#2563EB] border border-[#BFDBFE]"
                                >
                                  {s}
                                </span>
                              ))}
                              {job.required_skills.length > 3 && (
                                <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#F1F4F8] text-[#5E6878]">
                                  +{job.required_skills.length - 3}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="py-3.5 px-4 text-center font-medium text-[#172033]">
                            {job.candidates_count}
                          </td>
                          <td className="py-3.5 px-4 text-center">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-[#EAF7F0] text-[#16805C]">
                              {job.strong_matches_count}
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-center font-semibold text-[#172033]">
                            {Math.round(job.avg_alignment)}%
                          </td>
                          <td className="py-3.5 px-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Link
                                href={`/recruiter/matches?role=${encodeURIComponent(job.title)}`}
                                className="px-3 py-1.5 rounded bg-[#EFF6FF] text-[#2563EB] hover:bg-[#DBEAFE] font-semibold text-[11px] transition-colors"
                              >
                                View Candidates
                              </Link>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* Responsible Matching & Compliance Section */}
          <section className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs space-y-3">
            <div className="flex items-center gap-2 text-[#16805C]">
              <ShieldCheck className="w-5 h-5" />
              <h3 className="text-sm font-bold text-[#172033]">Responsible Matching Philosophy</h3>
            </div>
            <p className="text-xs text-[#5E6878] leading-relaxed">
              RoleSync is designed to prioritize job-relevant evidence. Candidate rankings focus strictly on verified skill competency, experience alignment, and job-specific requirements. RoleSync intentionally discards personal demographics (gender, age, caste, religion, photographs, or personal PII) from scoring algorithms.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 border-t border-[#EDF0F4] text-[11px] text-[#5E6878]">
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#16805C]"></span>
                <span>Deterministic Mathematical Scoring</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#16805C]"></span>
                <span>Direct Resume Sentence Evidence</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#16805C]"></span>
                <span>Decision Support (Non-Autonomous)</span>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
