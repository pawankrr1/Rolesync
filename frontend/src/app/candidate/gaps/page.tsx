"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import { CandidateFullAnalysisResult } from "@/lib/types";

export default function SkillGapsPage() {
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

  const targetRole = activeAnalysis?.targetRole || "Data Scientist";
  const rawGaps = activeAnalysis?.gaps.priority_order || [];

  const highGaps = rawGaps.filter((g) => g.priority === "HIGH");
  const mediumGaps = rawGaps.filter((g) => g.priority === "MEDIUM");
  const lowGaps = rawGaps.filter((g) => g.priority === "LOW");

  const defaultHighGaps = [
    {
      skill: "Statistics & Probability",
      category: "Data Science & AI",
      reason: "Required by 6 target roles. Foundation for predictive modeling and hypothesis testing.",
      currentLevel: "Developing",
      targetLevel: "Proficient",
      effort: "3-4 weeks",
      unblocks: ["Machine Learning", "A/B Testing", "Deep Learning"],
    },
  ];

  const defaultMediumGaps = [
    {
      skill: "Power BI",
      category: "Analytics & BI",
      reason: "Demanded across executive reporting workflows and stakeholder dashboards.",
      currentLevel: "Missing",
      targetLevel: "Intermediate",
      effort: "2 weeks",
      unblocks: ["Business Reporting"],
    },
  ];

  const defaultLowGaps = [
    {
      skill: "Cloud Architecture (AWS)",
      category: "Infrastructure",
      reason: "Preferred for production deployments; secondary to core modeling skills.",
      currentLevel: "Missing",
      targetLevel: "Basic",
      effort: "1-2 weeks",
      unblocks: ["Cloud Deployments"],
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
              Your skill gaps
            </h1>
            <p className="text-xs text-[#5E6878] mt-1">
              Focus on the skills that will have the biggest impact on your readiness for{" "}
              <strong className="text-[#172033]">{targetRole}</strong>.
            </p>
          </div>

          <Link
            href="/candidate/learning"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md text-xs font-semibold bg-[#2563EB] hover:bg-[#1D4ED8] text-[#FFFFFF] transition-colors"
          >
            <span>View Learning Roadmap</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* HIGH PRIORITY */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#C24141]" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#C24141]">
              High Priority (Learn First)
            </h2>
          </div>

          <div className="space-y-3">
            {(highGaps.length > 0 ? highGaps : defaultHighGaps).map((gap, idx) => (
              <div
                key={idx}
                className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] text-xs space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-base font-bold text-[#172033]">
                      {gap.skill}
                    </h3>
                    <span className="text-[11px] text-[#5E6878]">
                      {gap.category}
                    </span>
                  </div>

                  <Link
                    href="/candidate/learning"
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs font-semibold bg-[#2563EB] text-[#FFFFFF] hover:bg-[#1D4ED8] transition-colors shrink-0"
                  >
                    <span>Start Learning</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>

                <div className="p-3 rounded bg-[#F8FAFC] border border-[#E1E6ED] space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#8A94A6] block">
                    Why It Matters
                  </span>
                  <p className="text-[#172033] leading-relaxed">
                    {gap.reason}
                  </p>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-[#5E6878] border-t border-[#EDF0F4] text-[11px]">
                  <div>
                    <span className="text-[#8A94A6] block text-[10px]">Your Current Level:</span>
                    <strong className="text-[#B7791F] font-semibold">Developing</strong>
                  </div>
                  <div>
                    <span className="text-[#8A94A6] block text-[10px]">Target Level:</span>
                    <strong className="text-[#172033] font-semibold">Proficient</strong>
                  </div>
                  <div>
                    <span className="text-[#8A94A6] block text-[10px]">Estimated Effort:</span>
                    <span className="font-medium text-[#172033]">
                      {"learning_effort_weeks" in gap ? gap.learning_effort_weeks : (gap as any).effort}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#8A94A6] block text-[10px]">Downstream Impact:</span>
                    <span className="font-medium text-[#172033]">
                      Unblocks 3 modeling skills
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* MEDIUM PRIORITY */}
        <div className="space-y-4 pt-4 border-t border-[#E1E6ED]">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#B7791F]" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#B7791F]">
              Medium Priority (Core Competencies)
            </h2>
          </div>

          <div className="space-y-3">
            {(mediumGaps.length > 0 ? mediumGaps : defaultMediumGaps).map((gap, idx) => (
              <div
                key={idx}
                className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] text-xs space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-base font-bold text-[#172033]">
                      {gap.skill}
                    </h3>
                    <span className="text-[11px] text-[#5E6878]">
                      {gap.category}
                    </span>
                  </div>

                  <Link
                    href="/candidate/learning"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-[#2563EB] hover:underline"
                  >
                    <span>View in Roadmap</span>
                    <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>

                <p className="text-[#5E6878] leading-relaxed">
                  {gap.reason}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* LOW PRIORITY */}
        <div className="space-y-4 pt-4 border-t border-[#E1E6ED]">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#8A94A6]" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#5E6878]">
              Low Priority (Advanced / Bonus)
            </h2>
          </div>

          <div className="space-y-3">
            {(lowGaps.length > 0 ? lowGaps : defaultLowGaps).map((gap, idx) => (
              <div
                key={idx}
                className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] text-xs space-y-2"
              >
                <h3 className="text-sm font-bold text-[#172033]">
                  {gap.skill}
                </h3>
                <p className="text-[#5E6878] leading-relaxed">
                  {gap.reason}
                </p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
