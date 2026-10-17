"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  Loader2,
  CheckCircle2,
  Layers,
  Sparkles,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import { fetchRecruiterJobs, fetchRecruiterInsights } from "@/lib/api";
import { RecruiterInsightsResponse, RecruiterJobItem } from "@/lib/types";

export default function RecruiterInsightsPage() {
  const [jobs, setJobs] = useState<RecruiterJobItem[]>([]);
  const [selectedRole, setSelectedRole] = useState("Data Analyst");
  const [selectedJobId, setSelectedJobId] = useState<string | undefined>(undefined);
  const [insights, setInsights] = useState<RecruiterInsightsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function loadJobs() {
      try {
        const res = await fetchRecruiterJobs(20, 0);
        if (mounted && res.success && res.data && res.data.length > 0) {
          setJobs(res.data);
          setSelectedRole(res.data[0].title);
          setSelectedJobId(res.data[0].id);
        }
      } catch (err) {
        console.error("Failed to load jobs for insights:", err);
      }
    }
    loadJobs();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    async function loadInsights() {
      setIsLoading(true);
      try {
        const res = await fetchRecruiterInsights(selectedJobId, selectedRole);
        if (mounted && res.success && res.data) {
          setInsights(res.data);
        }
      } catch (err) {
        console.error("Failed to load recruiter insights:", err);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }
    loadInsights();
    return () => {
      mounted = false;
    };
  }, [selectedJobId, selectedRole]);

  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedRole(val);
    const found = jobs.find((j) => j.title === val);
    setSelectedJobId(found ? found.id : undefined);
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
                <span className="text-[#172033] font-semibold">Hiring Insights</span>
              </div>
              <h1 className="text-2xl font-bold text-[#172033] mt-1 tracking-tight">
                Applicant Pool Skill Shortages & Coverage
              </h1>
              <p className="text-xs text-[#5E6878] mt-0.5">
                Understand applicant skill gaps to adjust hiring criteria, interview benchmarks, or upskilling paths.
              </p>
            </div>

            {/* Target Role Selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[#8A94A6]">Position:</span>
              <select
                value={selectedRole}
                onChange={handleRoleChange}
                className="px-3 py-1.5 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs font-semibold text-[#172033]"
              >
                {jobs.map((j) => (
                  <option key={j.id} value={j.title}>
                    {j.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center text-center space-y-3 bg-[#FFFFFF] rounded-lg border border-[#E1E6ED]">
              <Loader2 className="w-8 h-8 text-[#2563EB] animate-spin" />
              <h3 className="text-sm font-bold text-[#172033]">Analyzing Applicant Pool Data...</h3>
            </div>
          ) : !insights ? (
            <div className="p-8 text-center bg-[#FFFFFF] rounded-lg border border-[#E1E6ED] text-xs text-[#8A94A6]">
              Unable to load insights for this position.
            </div>
          ) : (
            <div className="space-y-6">
              {/* TALENT SHORTAGE INSIGHT BANNER */}
              <div className="p-5 rounded-lg border border-[#F2DEAA] bg-[#FFF6DD] shadow-2xs space-y-2">
                <div className="flex items-center gap-2 text-[#B7791F]">
                  <AlertTriangle className="w-5 h-5 shrink-0" />
                  <h2 className="text-sm font-bold text-[#172033]">
                    Critical Talent Shortage Alert
                  </h2>
                </div>
                <p className="text-xs text-[#172033] leading-relaxed">
                  {insights.shortage_insight_narrative}
                </p>
                {insights.market_trend_linkage && (
                  <p className="text-xs text-[#5E6878] pt-1 border-t border-[#F2DEAA]/60">
                    <strong>Macro Context: </strong>
                    {insights.market_trend_linkage}
                  </p>
                )}
              </div>

              {/* SKILL COVERAGE BREAKDOWN */}
              <div className="p-6 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs space-y-4">
                <div className="flex items-center justify-between border-b border-[#EDF0F4] pb-2">
                  <h3 className="text-sm font-bold text-[#172033]">
                    Skill Coverage Across Applicant Pool ({insights.total_applicants_evaluated} Candidates Evaluated)
                  </h3>
                  <span className="text-[11px] text-[#8A94A6]">
                    % of applicants possessing verified competency
                  </span>
                </div>

                <div className="space-y-3">
                  {insights.skill_coverage.map((item, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-[#172033]">{item.skill}</span>
                          <span
                            className={`px-1.5 py-0.2 rounded text-[10px] font-medium ${
                              item.is_required
                                ? "bg-[#EFF6FF] text-[#2563EB]"
                                : "bg-[#E8F7F4] text-[#0F9F8C]"
                            }`}
                          >
                            {item.is_required ? "Required" : "Preferred"}
                          </span>
                        </div>
                        <span className="font-bold text-[#172033]">
                          {item.coverage_percentage}% ({item.applicant_count}/{item.total_applicants})
                        </span>
                      </div>

                      {/* Progress Track */}
                      <div className="h-2 w-full rounded-full bg-[#E1E6ED] overflow-hidden">
                        <div
                          className={`h-full transition-all duration-500 ${
                            item.coverage_percentage >= 70
                              ? "bg-[#16805C]"
                              : item.coverage_percentage >= 40
                              ? "bg-[#2563EB]"
                              : "bg-[#B7791F]"
                          }`}
                          style={{ width: `${item.coverage_percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* BRIDGE TO MARKET INTELLIGENCE */}
              <div className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-[#2563EB]" />
                    <h3 className="text-sm font-bold text-[#172033]">
                      National Labor Market Intelligence
                    </h3>
                  </div>
                  <p className="text-xs text-[#5E6878]">
                    Explore macro supply-demand indices across 50+ benchmark roles, emerging technical skills, and transition feasibility.
                  </p>
                </div>

                <Link
                  href="/insights"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-[#2563EB] text-[#FFFFFF] hover:bg-[#1D4ED8] text-xs font-semibold shadow-xs shrink-0 transition-colors"
                >
                  <span>Open Market Intelligence</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Data Notice */}
              <div className="p-3 rounded-md border border-[#E1E6ED] bg-[#F8FAFC] text-[11px] text-[#5E6878]">
                <strong>Dataset Integrity: </strong>
                {insights.disclaimer}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
