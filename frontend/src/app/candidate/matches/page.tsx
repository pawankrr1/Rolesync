"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import { CandidateFullAnalysisResult } from "@/lib/types";

export default function CareerMatchesPage() {
  const [activeAnalysis, setActiveAnalysis] = useState<CandidateFullAnalysisResult | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = window.sessionStorage.getItem("candidate_active_analysis");
      if (saved) {
        try {
          setActiveAnalysis(JSON.parse(saved));
        } catch {
          // ignore
        }
      }
    }
  }, []);

  const roles = [
    {
      roleId: "data_analyst",
      title: "Data Analyst",
      category: "Analytics",
      match: 88,
      strongSkills: ["SQL", "Excel", "Python"],
      topGap: "Power BI",
      experienceFit: "Immediate (3+ yrs)",
      nextAction: "Explore Role",
    },
    {
      roleId: "ml_engineer",
      title: "Machine Learning Engineer",
      category: "AI & Systems",
      match: 82,
      strongSkills: ["Python", "Machine Learning", "PyTorch"],
      topGap: "Docker & Containerization",
      experienceFit: "Moderate Bridge (2-3 yrs)",
      nextAction: "Explore Role",
    },
    {
      roleId: "data_scientist",
      title: "Data Scientist",
      category: "Data Science & AI",
      match: 79,
      strongSkills: ["Python", "SQL", "Scikit-Learn"],
      topGap: "Statistics & Probability",
      experienceFit: "Current Target",
      nextAction: "View Gaps",
    },
    {
      roleId: "backend_developer",
      title: "Backend Software Engineer",
      category: "Web & Platforms",
      match: 76,
      strongSkills: ["Python", "SQL", "FastAPI"],
      topGap: "PostgreSQL & Redis",
      experienceFit: "Moderate Bridge (3+ yrs)",
      nextAction: "Explore Role",
    },
    {
      roleId: "cloud_engineer",
      title: "Cloud & DevOps Engineer",
      category: "Infrastructure",
      match: 64,
      strongSkills: ["Linux", "Git", "Python"],
      topGap: "Kubernetes & AWS",
      experienceFit: "Long-term Pivot",
      nextAction: "Explore Role",
    },
  ];

  return (
    <div className="flex-1 flex max-w-7xl mx-auto w-full bg-[#F7F8FA]">
      <DashboardSidebar role="candidate" />

      <main className="flex-1 p-6 sm:p-8 lg:p-10 space-y-8 bg-[#F7F8FA]">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E1E6ED]">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#172033]">
              Career matches
            </h1>
            <p className="text-xs text-[#5E6878] mt-1">
              Roles that align with your current verified skill profile.
            </p>
          </div>

          <Link
            href="/candidate/upload"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md text-xs font-semibold bg-[#2563EB] hover:bg-[#1D4ED8] text-[#FFFFFF] transition-colors"
          >
            <span>Update Resume</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Structured Comparison Table */}
        <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] overflow-hidden text-xs">
          <div className="p-4 bg-[#F7F8FA] border-b border-[#E1E6ED] flex items-center justify-between">
            <span className="font-semibold text-[#172033]">
              Benchmark Role Comparisons ({roles.length})
            </span>
            <span className="text-[11px] text-[#5E6878]">
              Sorted by alignment percentage
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-[#F7F8FA] border-b border-[#E1E6ED] text-[11px] uppercase tracking-wider text-[#5E6878] font-semibold">
                <tr>
                  <th className="py-3 px-4">Role Name</th>
                  <th className="py-3 px-4">Match %</th>
                  <th className="py-3 px-4">Strong Skills</th>
                  <th className="py-3 px-4">Top Gap</th>
                  <th className="py-3 px-4">Experience Fit</th>
                  <th className="py-3 px-4 text-right">Next Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EDF0F4] text-[#172033]">
                {roles.map((r) => (
                  <tr key={r.roleId} className="hover:bg-[#F7F9FC]">
                    <td className="py-3.5 px-4">
                      <span className="font-bold text-[#172033] block">
                        {r.title}
                      </span>
                      <span className="text-[11px] text-[#5E6878]">{r.category}</span>
                    </td>
                    <td className="py-3.5 px-4 font-mono">
                      <span className="font-bold text-[#2563EB] text-sm">
                        {r.match}%
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex flex-wrap gap-1">
                        {r.strongSkills.map((s, idx) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 rounded bg-[#EAF7F0] text-[#16805C] border border-[#CDEDDD] text-[10px] font-medium"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="text-[#B7791F] font-medium flex items-center gap-1">
                        <AlertCircle className="w-3 h-3 text-[#B7791F]" />
                        {r.topGap}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-[#5E6878] text-[11px]">
                      {r.experienceFit}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/candidate/results?role=${r.roleId}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold bg-[#EFF6FF] hover:bg-[#DBEAFE] text-[#2563EB] transition-colors"
                      >
                        <span>{r.nextAction}</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
