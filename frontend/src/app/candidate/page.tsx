"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Check,
  AlertCircle,
  X,
  Clock,
  Target,
  BookOpen,
  FileText,
  UploadCloud,
  Layers,
  Compass,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import { SkillBadge } from "@/components/ui/SkillBadge";
import { mockCandidateProfile } from "@/mock/careerMockData";
import { CandidateFullAnalysisResult } from "@/lib/types";

export default function CandidateDashboardPage() {
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

  const candidateName = activeAnalysis?.candidateName || mockCandidateProfile.name || "Candidate";
  const targetRole = activeAnalysis?.targetRole || "Data Scientist";
  const overallScore = activeAnalysis ? Math.round(activeAnalysis.overallScore) : 79;
  const grade = activeAnalysis?.scoreGrade || "High Alignment";

  const strongSkillList = activeAnalysis?.matching.strong_matches.map((s) => s.skill) || [
    "Python",
    "SQL",
    "Machine Learning",
  ];
  const partialSkillList = activeAnalysis?.matching.partial_matches.map((s) => s.skill) || [
    "Statistics & Probability",
    "Data Visualization",
  ];
  const missingSkillList = activeAnalysis?.matching.missing_skills.map((s) => s.skill) || [
    "Power BI",
  ];

  const totalCoreRequirements = strongSkillList.length + missingSkillList.length;

  return (
    <div className="flex-1 flex max-w-7xl mx-auto w-full bg-[#F7F8FA]">
      <DashboardSidebar role="candidate" />

      <main className="flex-1 p-6 sm:p-8 lg:p-10 space-y-8 bg-[#F7F8FA]">
        {/* Top: Welcome Header & Workspace Meta */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E1E6ED]">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#172033]">
              Welcome back, {candidateName}
            </h1>
            <p className="text-xs text-[#5E6878] mt-1">
              Here&apos;s where your career profile stands today.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/candidate/upload"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md text-xs font-semibold bg-[#2563EB] hover:bg-[#1D4ED8] text-[#FFFFFF] transition-colors"
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Update Resume</span>
            </Link>
          </div>
        </div>

        {/* PROFILE COMPLETENESS RIBBON */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] text-xs">
          <div>
            <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
              Skill Coverage
            </span>
            <span className="text-sm font-bold text-[#172033]">
              {activeAnalysis
                ? `${Math.round(activeAnalysis.matching.required_skill_coverage)}% Core Match`
                : "83% Core Match"}
            </span>
            <p className="text-[11px] text-[#5E6878] mt-0.5">
              {strongSkillList.length} verified competencies
            </p>
          </div>

          <div className="border-t sm:border-t-0 sm:border-l border-[#EDF0F4] pt-3 sm:pt-0 sm:pl-4">
            <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
              Resume Freshness
            </span>
            <span className="text-sm font-bold text-[#16805C]">
              Active • In-Memory Verified
            </span>
            <p className="text-[11px] text-[#5E6878] mt-0.5">
              Zero-PII anonymized evaluation
            </p>
          </div>

          <div className="border-t sm:border-t-0 sm:border-l border-[#EDF0F4] pt-3 sm:pt-0 sm:pl-4">
            <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
              Target Role
            </span>
            <span className="text-sm font-bold text-[#2563EB]">
              {targetRole}
            </span>
            <p className="text-[11px] text-[#5E6878] mt-0.5">
              Benchmark role specifications
            </p>
          </div>
        </div>

        {/* MAIN CAREER ALIGNMENT */}
        <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-6 sm:p-7 space-y-4">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-4 border-b border-[#EDF0F4]">
            <div className="space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#5E6878] block">
                Target Role Alignment
              </span>
              <h2 className="text-2xl font-bold text-[#172033]">
                {targetRole}
              </h2>
              <p className="text-xs text-[#5E6878] max-w-xl leading-relaxed">
                {activeAnalysis?.narrative ||
                  "You possess strong foundations in Python, SQL, and core Machine Learning. Fulfilling the remaining gap in Statistics & Probability will boost your qualification."}
              </p>
            </div>

            {/* Score presentation */}
            <div className="flex items-center gap-4 bg-[#F8FAFC] p-4 rounded-lg border border-[#E1E6ED] shrink-0">
              <div className="text-right">
                <div className="text-3xl font-extrabold text-[#2563EB] leading-none">
                  {overallScore} <span className="text-sm font-normal text-[#8A94A6]">/ 100</span>
                </div>
                <span className="text-xs font-semibold text-[#16805C] block mt-1">
                  {grade}
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-[#5E6878] pt-1">
            <span className="flex items-center gap-1.5 font-medium">
              <Check className="w-4 h-4 text-[#16805C] stroke-[2.5]" />
              {strongSkillList.length} of {totalCoreRequirements || 6} core requirements met
            </span>

            <Link
              href={`/candidate/results?role=${activeAnalysis?.targetRoleId || "data_scientist"}`}
              className="inline-flex items-center gap-1 text-xs font-semibold text-[#2563EB] hover:underline"
            >
              <span>View score breakdown &amp; evidence</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* NEXT BEST ACTION */}
        <div className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#5E6878] block">
              Your Next Best Move
            </span>
            <h3 className="text-sm font-bold text-[#172033]">
              Strengthen Statistics &amp; Probability
            </h3>
            <p className="text-xs text-[#5E6878] max-w-2xl">
              Your target role requires it and it is currently the largest gap affecting your score. Learning this unlocks 3 downstream modeling competencies.
            </p>
          </div>

          <Link
            href="/candidate/learning"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md text-xs font-semibold bg-[#2563EB] hover:bg-[#1D4ED8] text-[#FFFFFF] shrink-0 transition-colors"
          >
            <span>View Learning Path</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* SKILL SNAPSHOT */}
        <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-6 space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#EDF0F4]">
            <div>
              <h3 className="text-sm font-bold text-[#172033]">
                Skill Snapshot
              </h3>
              <p className="text-xs text-[#5E6878]">
                Categorized relative to {targetRole} specifications.
              </p>
            </div>
            <Link
              href="/candidate/gaps"
              className="text-xs font-semibold text-[#2563EB] hover:underline"
            >
              Analyze All Gaps →
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Strong */}
            <div className="space-y-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#16805C] block">
                Strong ({strongSkillList.length})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {strongSkillList.map((name) => (
                  <SkillBadge key={name} name={name} status="strong_match" />
                ))}
              </div>
            </div>

            {/* Developing / Partial */}
            <div className="space-y-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#B7791F] block">
                Developing ({partialSkillList.length})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {partialSkillList.map((name) => (
                  <SkillBadge key={name} name={name} status="partial_match" />
                ))}
              </div>
            </div>

            {/* Missing */}
            <div className="space-y-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#C24141] block">
                Missing ({missingSkillList.length})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {missingSkillList.map((name) => (
                  <SkillBadge key={name} name={name} status="missing" />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* CAREER OPTIONS: YOU MAY ALSO FIT */}
        <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#EDF0F4]">
            <div>
              <h3 className="text-sm font-bold text-[#172033]">
                You May Also Fit
              </h3>
              <p className="text-xs text-[#5E6878]">
                Alternative roles that share verified competencies with your current profile.
              </p>
            </div>
            <Link
              href="/candidate/matches"
              className="text-xs font-semibold text-[#2563EB] hover:underline"
            >
              Explore All Matches →
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { title: "Data Analyst", match: "88%", roleId: "data_analyst", note: "Immediate feasibility • Bridge: Power BI" },
              { title: "ML Engineer", match: "82%", roleId: "ml_engineer", note: "Bridge: PyTorch & Containerization" },
              { title: "Backend Developer", match: "76%", roleId: "backend_developer", note: "Bridge: FastAPI & PostgreSQL" },
            ].map((alt) => (
              <Link
                key={alt.roleId}
                href={`/candidate/results?role=${alt.roleId}`}
                className="p-4 rounded border border-[#E1E6ED] bg-[#F8FAFC] hover:bg-[#F1F4F8] transition-colors group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-[#172033] group-hover:text-[#2563EB] transition-colors">
                    {alt.title}
                  </span>
                  <span className="font-mono text-xs font-bold text-[#2563EB]">
                    {alt.match}
                  </span>
                </div>
                <p className="text-[11px] text-[#5E6878]">
                  {alt.note}
                </p>
              </Link>
            ))}
          </div>
        </div>

        {/* RECENT ACTIVITY */}
        <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-6 space-y-3">
          <h3 className="text-sm font-bold text-[#172033] pb-2 border-b border-[#EDF0F4]">
            Recent Activity
          </h3>
          <div className="divide-y divide-[#EDF0F4] text-xs">
            <div className="py-2.5 flex items-center justify-between">
              <span className="text-[#172033]">Resume analyzed &amp; competencies extracted</span>
              <span className="text-[#8A94A6] text-[11px]">Today</span>
            </div>
            <div className="py-2.5 flex items-center justify-between">
              <span className="text-[#172033]">Target role set to {targetRole}</span>
              <span className="text-[#8A94A6] text-[11px]">Today</span>
            </div>
            <div className="py-2.5 flex items-center justify-between">
              <span className="text-[#172033]">Prerequisite learning roadmap created</span>
              <span className="text-[#8A94A6] text-[11px]">Today</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
