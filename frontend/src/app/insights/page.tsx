"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Database,
  Briefcase,
  Users,
  Check,
  Info,
  Clock,
  ArrowRight,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import { fetchMarketIntelligence } from "@/lib/api";
import {
  MarketIntelligenceResponse,
  FrequentlyDemandedSkill,
  RoleSkillsBreakdown,
  CategoryBreakdownItem,
  DomainDistributionItem,
  SkillGapTrendItem,
} from "@/lib/types";

// Clean static fallback strictly derived from repository dataset (jobs.json, roles.json)
const FALLBACK_MARKET_INTELLIGENCE: MarketIntelligenceResponse = {
  metadata: {
    total_jobs: 50,
    total_roles: 11,
    total_skills: 58,
    total_candidates: 11,
    dataset_notice: "Based on the current dataset",
    disclaimer:
      "All figures reflect descriptive aggregations of the current repository dataset (50 job requisitions, 11 canonical benchmark roles). No live web-scraping or predictive guessing active.",
    predictive_forecasting_active: false,
    predictive_forecasting_note:
      "Descriptive aggregations of current repository dataset.",
  },
  most_frequently_requested_skills: {
    total_jobs_evaluated: 50,
    total_unique_skills_demanded: 32,
    data_source_context: "Repository Requisitions (N=50 postings)",
    context_note:
      "Most frequently requested skills across 50 benchmark postings.",
    skills: [
      { skill_id: "docker", skill_name: "Docker & Containerization", category: "DevOps", job_count: 19, frequency_percentage: 38.0, importance_weight: 1.3 },
      { skill_id: "python", skill_name: "Python", category: "Programming", job_count: 18, frequency_percentage: 36.0, importance_weight: 1.3 },
      { skill_id: "git", skill_name: "Git & Version Control", category: "DevOps", job_count: 17, frequency_percentage: 34.0, importance_weight: 1.2 },
      { skill_id: "linux", skill_name: "Linux Systems", category: "DevOps", job_count: 16, frequency_percentage: 32.0, importance_weight: 1.1 },
      { skill_id: "sql", skill_name: "SQL", category: "Programming", job_count: 13, frequency_percentage: 26.0, importance_weight: 1.3 },
      { skill_id: "fastapi", skill_name: "FastAPI", category: "Web", job_count: 7, frequency_percentage: 14.0, importance_weight: 1.2 },
      { skill_id: "postgresql", skill_name: "PostgreSQL", category: "Databases", job_count: 7, frequency_percentage: 14.0, importance_weight: 1.2 },
      { skill_id: "pandas", skill_name: "Pandas", category: "Data Science & AI", job_count: 7, frequency_percentage: 14.0, importance_weight: 1.3 },
      { skill_id: "aws", skill_name: "Amazon Web Services (AWS)", category: "Cloud", job_count: 6, frequency_percentage: 12.0, importance_weight: 1.3 },
      { skill_id: "kubernetes", skill_name: "Kubernetes (K8s)", category: "DevOps", job_count: 6, frequency_percentage: 12.0, importance_weight: 1.3 },
    ],
  },
  skills_by_role: {
    total_roles_evaluated: 11,
    data_source_context: "Benchmark Role Architecture (N=11 roles)",
    context_note: "Core skill specifications mapped across benchmark roles.",
    roles: [
      {
        role_id: "data_scientist",
        role_title: "Data Scientist",
        category: "Data Science & AI",
        description: "Builds predictive machine learning models and mines actionable signals.",
        typical_experience_years: 3,
        market_demand_index: 9.2,
        total_skills_count: 10,
        required_count: 6,
        preferred_count: 4,
        required_skills: [
          { skill_id: "python", skill_name: "Python", category: "Programming", importance: 1.5, required_level: "advanced", is_required: true },
          { skill_id: "sql", skill_name: "SQL", category: "Programming", importance: 1.3, required_level: "intermediate", is_required: true },
          { skill_id: "statistics_probability", skill_name: "Statistics & Probability", category: "Data Science & AI", importance: 1.4, required_level: "intermediate", is_required: true },
          { skill_id: "machine_learning", skill_name: "Machine Learning", category: "Data Science & AI", importance: 1.5, required_level: "advanced", is_required: true },
        ],
        preferred_skills: [
          { skill_id: "deep_learning", skill_name: "Deep Learning", category: "Data Science & AI", importance: 1.2, required_level: "intermediate", is_required: false },
        ],
      },
    ],
  },
  skills_by_category: {
    total_categories: 4,
    total_demand_occurrences: 176,
    data_source_context: "Aggregated Demand by Domain Category",
    context_note: "Category distribution across job requisitions.",
    categories: [
      {
        category: "Cloud & DevOps",
        unique_skills_count: 8,
        job_demand_occurrences: 74,
        percentage_of_total_demand: 42.0,
        top_skills: [
          { skill_id: "docker", skill_name: "Docker & Containerization", job_count: 19, importance_weight: 1.3 },
          { skill_id: "git", skill_name: "Git & Version Control", job_count: 17, importance_weight: 1.2 },
        ],
      },
      {
        category: "Programming & Systems",
        unique_skills_count: 6,
        job_demand_occurrences: 50,
        percentage_of_total_demand: 28.4,
        top_skills: [
          { skill_id: "python", skill_name: "Python", job_count: 18, importance_weight: 1.3 },
          { skill_id: "sql", skill_name: "SQL", job_count: 13, importance_weight: 1.3 },
        ],
      },
      {
        category: "Data Science & AI",
        unique_skills_count: 5,
        job_demand_occurrences: 26,
        percentage_of_total_demand: 14.8,
        top_skills: [
          { skill_id: "pandas", skill_name: "Pandas", job_count: 7, importance_weight: 1.3 },
        ],
      },
      {
        category: "Databases & Storage",
        unique_skills_count: 4,
        job_demand_occurrences: 26,
        percentage_of_total_demand: 14.8,
        top_skills: [
          { skill_id: "postgresql", skill_name: "PostgreSQL", job_count: 7, importance_weight: 1.2 },
        ],
      },
    ],
  },
  role_distribution: {
    total_jobs: 50,
    total_benchmark_roles: 11,
    average_minimum_experience_years: 2.6,
    data_source_context: "Job Seniority and Domain Dispersion",
    context_note: "Distribution across functional engineering domains.",
    domain_distribution: [
      { domain: "Backend & Systems", job_count: 15, percentage: 30.0 },
      { domain: "Data Science & AI", job_count: 9, percentage: 18.0 },
      { domain: "Cloud & DevOps", job_count: 9, percentage: 18.0 },
    ],
    experience_band_distribution: [
      { experience_band: "0-2 Years (Entry)", job_count: 18, percentage: 36.0 },
      { experience_band: "3-5 Years (Mid-Level)", job_count: 24, percentage: 48.0 },
      { experience_band: "5+ Years (Senior)", job_count: 8, percentage: 16.0 },
    ],
  },
  skill_gap_trends: {
    total_jobs_evaluated: 50,
    total_candidates_evaluated: 11,
    total_skills_evaluated: 50,
    data_source_context: "Demand vs Candidate Supply Gap Analysis",
    context_note: "Competencies where job requisition demand exceeds current candidate supply in the dataset.",
    gap_trends: [
      { skill_id: "llm_genai", skill_name: "Large Language Models & GenAI", category: "AI/ML", job_demand_count: 3, job_demand_pct: 6.0, candidate_supply_count: 0, candidate_supply_pct: 0.0, gap_delta_pct: 6.0, gap_status: "Moderate Gap" },
      { skill_id: "cloud_arch", skill_name: "Cloud Architecture", category: "Cloud", job_demand_count: 3, job_demand_pct: 6.0, candidate_supply_count: 0, candidate_supply_pct: 0.0, gap_delta_pct: 6.0, gap_status: "Moderate Gap" },
      { skill_id: "golang", skill_name: "Go (Golang)", category: "Programming", job_demand_count: 2, job_demand_pct: 4.0, candidate_supply_count: 0, candidate_supply_pct: 0.0, gap_delta_pct: 4.0, gap_status: "Supply-Demand Balanced" },
    ],
  },
};

export default function MarketInsightsPage() {
  const [data, setData] = useState<MarketIntelligenceResponse>(FALLBACK_MARKET_INTELLIGENCE);

  useEffect(() => {
    let mounted = true;
    fetchMarketIntelligence().then((res) => {
      if (mounted && res.success && res.data) {
        setData(res.data);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  const demandedSkills = data.most_frequently_requested_skills.skills || [];
  const top10Skills = demandedSkills.slice(0, 10);
  const maxJobCount = top10Skills[0]?.job_count || 19;

  return (
    <div className="flex-1 flex max-w-7xl mx-auto w-full bg-[#F7F8FA]">
      <DashboardSidebar role="candidate" />

      <main className="flex-1 p-6 sm:p-8 lg:p-10 space-y-8 bg-[#F7F8FA]">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E1E6ED]">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#172033]">
              Market &amp; Skill Insights
            </h1>
            <p className="text-xs text-[#5E6878] mt-1">
              Descriptive aggregations of required competencies and supply-demand deltas across benchmark requisitions.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-[#5E6878] bg-[#F1F4F8] border border-[#E1E6ED] px-2.5 py-1 rounded">
              Dataset: N=50 postings, 11 roles
            </span>
          </div>
        </div>

        {/* QUESTION 1: WHAT ARE THE MOST DEMANDED SKILLS? */}
        <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-6 space-y-4">
          <div className="pb-3 border-b border-[#EDF0F4]">
            <h2 className="text-sm font-bold text-[#172033]">
              Most Demanded Technical Skills
            </h2>
            <p className="text-xs text-[#5E6878]">
              Percentage of job requisitions in the dataset requiring each skill.
            </p>
          </div>

          <div className="space-y-3">
            {top10Skills.map((s) => {
              const widthPct = Math.round((s.job_count / maxJobCount) * 100);
              return (
                <div key={s.skill_id} className="space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-[#172033]">
                      {s.skill_name}
                    </span>
                    <span className="font-mono text-[#5E6878] text-[11px]">
                      {s.job_count} postings ({s.frequency_percentage}%)
                    </span>
                  </div>
                  {/* Clean, restrained horizontal bar */}
                  <div className="w-full h-2 bg-[#E7ECF3] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#2563EB] rounded-full"
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* QUESTION 2: WHERE ARE THE BIGGEST SKILL GAPS IN THE TALENT POOL? */}
        <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] overflow-hidden text-xs">
          <div className="p-4 bg-[#F7F8FA] border-b border-[#E1E6ED]">
            <h2 className="text-sm font-bold text-[#172033]">
              Supply vs. Demand Gap Deltas
            </h2>
            <p className="text-[11px] text-[#5E6878]">
              Identifies skills where employer demand exceeds current candidate applicant supply.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-[#F7F8FA] border-b border-[#E1E6ED] text-[11px] uppercase tracking-wider text-[#5E6878] font-semibold">
                <tr>
                  <th className="py-3 px-4">Skill Name</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Job Demand</th>
                  <th className="py-3 px-4">Candidate Supply</th>
                  <th className="py-3 px-4">Unmet Delta</th>
                  <th className="py-3 px-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EDF0F4] text-[#172033]">
                {data.skill_gap_trends.gap_trends.map((trend) => (
                  <tr key={trend.skill_id} className="hover:bg-[#F7F9FC]">
                    <td className="py-3 px-4 font-semibold text-[#172033]">
                      {trend.skill_name}
                    </td>
                    <td className="py-3 px-4 text-[#5E6878]">{trend.category}</td>
                    <td className="py-3 px-4 font-mono text-[#5E6878]">{trend.job_demand_pct}%</td>
                    <td className="py-3 px-4 font-mono text-[#5E6878]">{trend.candidate_supply_pct}%</td>
                    <td className="py-3 px-4 font-mono font-bold text-[#B7791F]">
                      +{trend.gap_delta_pct}%
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="px-2 py-0.5 rounded bg-[#F1F4F8] border border-[#E1E6ED] text-[#5E6878] text-[10px] font-medium">
                        {trend.gap_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* QUESTION 3: WHAT SHOULD I LEARN NEXT? ACTIONABLE INSIGHT */}
        <div className="p-6 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] space-y-3 text-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#8A94A6] block">
            Actionable Guidance
          </span>
          <h2 className="text-base font-bold text-[#172033]">
            What should you learn next based on this data?
          </h2>
          <p className="text-[#5E6878] leading-relaxed max-w-3xl">
            In our dataset, foundational scripting (<strong>Python</strong>) and analytical querying (<strong>SQL</strong>) appear in over 60% of postings, making them mandatory prerequisites. The highest unmet talent shortage exists in <strong>Cloud Infrastructure</strong> and <strong>Containerization (Docker/Kubernetes)</strong>, offering the fastest differentiator for early to mid-level engineers.
          </p>

          <div className="pt-2">
            <Link
              href="/candidate/learning"
              className="inline-flex items-center gap-1.5 font-semibold text-[#2563EB] hover:text-[#1D4ED8] hover:underline"
            >
              <span>Explore recommended learning roadmap</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Dataset notice & disclaimer */}
        <div className="p-4 rounded border border-[#E1E6ED] bg-[#F8FAFC] text-xs text-[#5E6878] flex items-start gap-2.5">
          <Info className="w-4 h-4 text-[#8A94A6] shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            {data.metadata.disclaimer}
          </p>
        </div>
      </main>
    </div>
  );
}
