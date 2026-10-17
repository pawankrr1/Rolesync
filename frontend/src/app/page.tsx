"use client";

import React from "react";
import Link from "next/link";
import {
  ArrowRight,
  Check,
  ShieldCheck,
} from "lucide-react";
import { CandidateProfileCarousel } from "@/components/home/CandidateProfileCarousel";

export default function LandingPage() {
  return (
    <div className="flex flex-col bg-[#F5F9FF] text-[#172033]">
      {/* ------------------------------------------------------------- */}
      {/* SECTION 2 — HERO                                              */}
      {/* ------------------------------------------------------------- */}
      <section
        className="pt-16 pb-20 sm:pt-24 sm:pb-28 border-b border-[#DCE6F2]"
        style={{
          background:
            "linear-gradient(135deg, #F5F9FF 0%, #EFF6FF 50%, #DBEAFE 100%)",
        }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-10 items-center">
            {/* Left Column: Clear Value Proposition */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-[#EFF6FF] border border-[#DBEAFE] text-xs font-semibold text-[#2563EB] shadow-xs">
                <span className="px-1.5 py-0.5 rounded bg-[#2563EB] text-white text-[10px] font-bold tracking-wider uppercase">CODE YUDH</span>
                <span className="font-mono">MATCH → GAP → LEARN → GROW</span>
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-[#172033] leading-[1.15]">
                Turn your resume into a career plan.
              </h1>

              <p className="text-base sm:text-lg text-[#5E6878] max-w-xl leading-relaxed">
                RoleSync shows how your skills align with real career paths, where your gaps are, and what to learn next.
              </p>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <Link
                  href="/candidate/upload"
                  className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-md text-sm font-semibold text-[#FFFFFF] shadow-sm hover:opacity-95 hover:shadow transition-all duration-200"
                  style={{
                    background:
                      "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
                  }}
                >
                  <span>Analyze My Resume</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>

                <Link
                  href="/candidate/matches"
                  className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-md text-sm font-semibold bg-[#FFFFFF] border border-[#DCE6F2] text-[#2563EB] hover:bg-[#EFF6FF] hover:border-[#2563EB] transition-colors"
                >
                  <span>Explore Career Paths</span>
                </Link>
              </div>

              {/* Trust & Principles */}
              <div className="pt-4 flex flex-wrap items-center gap-6 text-xs text-[#5E6878]">
                <div className="flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-[#16805C] stroke-[2.5]" />
                  <span>Explainable 4-Factor Matching</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Check className="w-4 h-4 text-[#16805C] stroke-[2.5]" />
                  <span>Prerequisite-Ordered Learning</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#16805C]" />
                  <span>Zero-PII Storage Policy</span>
                </div>
              </div>
            </div>

            {/* Right Column: Interactive Candidate Profile Carousel */}
            <div className="lg:col-span-5">
              <CandidateProfileCarousel />
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 3 — HOW IT WORKS                                      */}
      {/* ------------------------------------------------------------- */}
      <section className="py-20 border-b border-[#DCE6F2] bg-[#FFFFFF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mb-14">
            <span className="text-xs font-bold uppercase tracking-wider text-[#5E6878] block mb-1">
              Methodology
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#172033]">
              How RoleSync Works
            </h2>
            <p className="text-sm text-[#5E6878] mt-2">
              A transparent four-phase process designed to provide genuine career clarity without black-box filtering.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="space-y-3">
              <span className="font-mono text-sm font-bold text-[#2563EB] block">
                01
              </span>
              <h3 className="text-base font-bold text-[#172033]">
                MATCH
              </h3>
              <p className="text-xs text-[#5E6878] leading-relaxed">
                See where your current skills fit. RoleSync extracts verified competencies from your resume and compares them against canonical role taxonomies.
              </p>
            </div>

            <div className="space-y-3">
              <span className="font-mono text-sm font-bold text-[#2563EB] block">
                02
              </span>
              <h3 className="text-base font-bold text-[#172033]">
                GAP
              </h3>
              <p className="text-xs text-[#5E6878] leading-relaxed">
                Understand what you are missing. See which unmet requirements are core deal-breakers versus secondary preferences, ordered by prerequisite dependencies.
              </p>
            </div>

            <div className="space-y-3">
              <span className="font-mono text-sm font-bold text-[#2563EB] block">
                03
              </span>
              <h3 className="text-base font-bold text-[#172033]">
                LEARN
              </h3>
              <p className="text-xs text-[#5E6878] leading-relaxed">
                Get prioritized learning recommendations. Receive a sequenced roadmap with verified course materials, realistic duration, and hands-on projects.
              </p>
            </div>

            <div className="space-y-3">
              <span className="font-mono text-sm font-bold text-[#2563EB] block">
                04
              </span>
              <h3 className="text-base font-bold text-[#172033]">
                GROW
              </h3>
              <p className="text-xs text-[#5E6878] leading-relaxed">
                Move toward the next career opportunity. Discover adjacent roles you qualify for immediately or with minimal bridge skills.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 4 — EXPLAINABLE MATCHING                              */}
      {/* ------------------------------------------------------------- */}
      <section className="py-20 border-b border-[#DCE6F2] bg-[#F5F9FF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-6 space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-[#5E6878] block">
                Transparency
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-[#172033]">
                Every score has an explanation.
              </h2>
              <p className="text-sm text-[#5E6878] leading-relaxed">
                Black-box applicant tracking systems reject qualified candidates with zero feedback. RoleSync constructs scores transparently from 4 defined signals so you know exactly where you stand.
              </p>

              <div className="space-y-2 pt-2 text-xs">
                <div className="p-3 rounded border border-[#DCE6F2] bg-[#FFFFFF] flex items-center justify-between">
                  <span className="font-semibold text-[#172033]">Required Skill Coverage</span>
                  <span className="font-mono font-bold text-[#2563EB]">60% Weight</span>
                </div>
                <div className="p-3 rounded border border-[#DCE6F2] bg-[#FFFFFF] flex items-center justify-between">
                  <span className="font-semibold text-[#172033]">Semantic Domain Overlap</span>
                  <span className="font-mono font-bold text-[#2563EB]">20% Weight</span>
                </div>
                <div className="p-3 rounded border border-[#DCE6F2] bg-[#FFFFFF] flex items-center justify-between">
                  <span className="font-semibold text-[#172033]">Experience &amp; Evidence Depth</span>
                  <span className="font-mono font-bold text-[#2563EB]">10% Weight</span>
                </div>
                <div className="p-3 rounded border border-[#DCE6F2] bg-[#FFFFFF] flex items-center justify-between">
                  <span className="font-semibold text-[#172033]">Preferred Skill Coverage</span>
                  <span className="font-mono font-bold text-[#2563EB]">10% Weight</span>
                </div>
              </div>
            </div>

            {/* Example Breakdown Table */}
            <div className="lg:col-span-6">
              <div className="rounded-lg border border-[#DCE6F2] bg-[#FFFFFF] p-6 space-y-4 shadow-xs">
                <div className="flex items-center justify-between pb-3 border-b border-[#EFF6FF]">
                  <div>
                    <h3 className="text-sm font-bold text-[#172033]">
                      Data Analyst
                    </h3>
                    <span className="text-xs text-[#5E6878]">Benchmark Role Evaluation</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xl font-bold text-[#2563EB]">82%</span>
                    <span className="text-[10px] text-[#5E6878] block">Overall Match</span>
                  </div>
                </div>

                <div className="divide-y divide-[#EFF6FF] text-xs">
                  <div className="py-2 flex items-center justify-between">
                    <span className="font-medium text-[#172033]">Python</span>
                    <span className="text-[#16805C] font-semibold flex items-center gap-1">
                      <Check className="w-3 h-3 stroke-[2.5]" /> Strong
                    </span>
                  </div>
                  <div className="py-2 flex items-center justify-between">
                    <span className="font-medium text-[#172033]">SQL</span>
                    <span className="text-[#16805C] font-semibold flex items-center gap-1">
                      <Check className="w-3 h-3 stroke-[2.5]" /> Strong
                    </span>
                  </div>
                  <div className="py-2 flex items-center justify-between">
                    <span className="font-medium text-[#172033]">Excel</span>
                    <span className="text-[#16805C] font-semibold flex items-center gap-1">
                      <Check className="w-3 h-3 stroke-[2.5]" /> Strong
                    </span>
                  </div>
                  <div className="py-2 flex items-center justify-between">
                    <span className="font-medium text-[#172033]">Statistics</span>
                    <span className="text-[#B7791F] font-semibold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#B7791F]" /> Partial
                    </span>
                  </div>
                  <div className="py-2 flex items-center justify-between">
                    <span className="font-medium text-[#172033]">Power BI</span>
                    <span className="text-[#C24141] font-semibold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#C24141]" /> Missing
                    </span>
                  </div>
                </div>

                <div className="pt-2 text-[11px] text-[#5E6878] italic">
                  Grounded evidence: Verified in 4 resume sentence citations without hallucination.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 5 — SKILL GAP                                         */}
      {/* ------------------------------------------------------------- */}
      <section className="py-20 border-b border-[#DCE6F2] bg-[#FFFFFF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mb-12">
            <span className="text-xs font-bold uppercase tracking-wider text-[#5E6878] block mb-1">
              Prerequisite DAG
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#172033]">
              You don&apos;t need to learn everything.
            </h2>
            <p className="text-sm text-[#5E6878] mt-2">
              RoleSync maps technical dependencies so you prioritize the skills that unlock downstream requirements first.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
            <div className="p-5 rounded-lg border border-[#DCE6F2] bg-[#F5F9FF] space-y-1.5">
              <span className="text-[10px] font-bold uppercase text-[#8A94A6] block">Current Skills</span>
              <p className="text-sm font-bold text-[#172033]">Python, SQL, Excel</p>
              <p className="text-[11px] text-[#5E6878]">Demonstrated competency in analytical querying.</p>
            </div>

            <div className="p-5 rounded-lg border border-[#DCE6F2] bg-[#F5F9FF] space-y-1.5">
              <span className="text-[10px] font-bold uppercase text-[#8A94A6] block">Target Role</span>
              <p className="text-sm font-bold text-[#172033]">Data Analyst</p>
              <p className="text-[11px] text-[#5E6878]">Requires business intelligence &amp; probability.</p>
            </div>

            <div className="p-5 rounded-lg border border-[#DCE6F2] bg-[#F5F9FF] space-y-1.5">
              <span className="text-[10px] font-bold uppercase text-[#8A94A6] block">Priority Gaps</span>
              <p className="text-sm font-bold text-[#B7791F]">Statistics (P1)</p>
              <p className="text-[11px] text-[#5E6878]">Highest leverage skill to raise qualification.</p>
            </div>

            <div className="p-5 rounded-lg border border-[#DCE6F2] bg-[#F5F9FF] space-y-1.5">
              <span className="text-[10px] font-bold uppercase text-[#8A94A6] block">Recommended Action</span>
              <p className="text-sm font-bold text-[#172033]">Khan Academy / MIT OCW</p>
              <p className="text-[11px] text-[#5E6878]">Estimated 3 weeks to complete.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 6 — CAREER PATH                                       */}
      {/* ------------------------------------------------------------- */}
      <section className="py-20 border-b border-[#DCE6F2] bg-[#F5F9FF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mb-12">
            <span className="text-xs font-bold uppercase tracking-wider text-[#5E6878] block mb-1">
              Lateral Mobility
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#172033]">
              Discover adjacent career paths.
            </h2>
            <p className="text-sm text-[#5E6878] mt-2">
              See what alternative roles share your existing skill foundations, and how small additions open lateral moves.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-lg border border-[#DCE6F2] bg-[#FFFFFF] space-y-2 shadow-xs">
              <span className="text-xs font-bold text-[#172033] block">
                Data Analyst
              </span>
              <span className="text-xl font-bold text-[#2563EB] block">88%</span>
              <p className="text-[11px] text-[#5E6878]">Immediate feasibility • Overlap in SQL, Python, Excel.</p>
            </div>

            <div className="p-5 rounded-lg border border-[#DCE6F2] bg-[#FFFFFF] space-y-2 shadow-xs">
              <span className="text-xs font-bold text-[#172033] block">
                ML Engineer
              </span>
              <span className="text-xl font-bold text-[#2563EB] block">82%</span>
              <p className="text-[11px] text-[#5E6878]">Moderate bridge • Requires PyTorch &amp; Docker.</p>
            </div>

            <div className="p-5 rounded-lg border border-[#DCE6F2] bg-[#FFFFFF] space-y-2 shadow-xs">
              <span className="text-xs font-bold text-[#172033] block">
                Backend Developer
              </span>
              <span className="text-xl font-bold text-[#2563EB] block">76%</span>
              <p className="text-[11px] text-[#5E6878]">Moderate bridge • Requires FastAPI &amp; PostgreSQL.</p>
            </div>

            <div className="p-5 rounded-lg border border-[#DCE6F2] bg-[#FFFFFF] space-y-2 shadow-xs">
              <span className="text-xs font-bold text-[#172033] block">
                Data Scientist
              </span>
              <span className="text-xl font-bold text-[#2563EB] block">79%</span>
              <p className="text-[11px] text-[#5E6878]">Target role • Requires Statistics &amp; Probability.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 7 — FOR RECRUITERS                                    */}
      {/* ------------------------------------------------------------- */}
      <section className="py-20 border-b border-[#DCE6F2] bg-[#FFFFFF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-6 space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-[#5E6878] block">
                Recruiter Screening
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-[#172033]">
                Objective ranking. Zero PII storage.
              </h2>
              <p className="text-sm text-[#5E6878] leading-relaxed">
                Parse job descriptions, rank multiple candidate resumes against required versus preferred competencies, and inspect transparent reason codes without risking bias.
              </p>

              <div className="space-y-3 pt-2 text-xs">
                <div className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-[#16805C] shrink-0 mt-0.5" />
                  <span className="text-[#172033]">
                    <strong>Upload Job Description</strong> — Extracts required and preferred skills automatically.
                  </span>
                </div>
                <div className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-[#16805C] shrink-0 mt-0.5" />
                  <span className="text-[#172033]">
                    <strong>Rank Candidates</strong> — Evaluates skill coverage and experience depth.
                  </span>
                </div>
                <div className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-[#16805C] shrink-0 mt-0.5" />
                  <span className="text-[#172033]">
                    <strong>Understand Skill Alignment</strong> — Inspect exactly what matched, partial, or missing.
                  </span>
                </div>
                <div className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-[#16805C] shrink-0 mt-0.5" />
                  <span className="text-[#172033]">
                    <strong>Shortlist Confidently</strong> — Share objective reason codes with hiring managers.
                  </span>
                </div>
              </div>

              <div className="pt-2">
                <Link
                  href="/recruiter"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2563EB] hover:underline"
                >
                  <span>Open Recruiter Screening Workspace</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Recruiter Preview Table */}
            <div className="lg:col-span-6">
              <div className="rounded-lg border border-[#DCE6F2] bg-[#FFFFFF] overflow-hidden text-xs shadow-xs">
                <div className="p-4 bg-gradient-to-r from-[#F5F9FF] to-[#EFF6FF] border-b border-[#DCE6F2] flex items-center justify-between">
                  <div>
                    <span className="font-bold text-[#172033] block">
                      Senior Data Scientist Requisition
                    </span>
                    <span className="text-[11px] text-[#5E6878]">4 Candidates Evaluated</span>
                  </div>
                  <span className="text-[11px] font-mono text-[#16805C] font-semibold bg-[#EAF7F0] px-2 py-0.5 rounded border border-[#CDEDDD]">
                    Zero-PII Mode
                  </span>
                </div>

                <div className="divide-y divide-[#EFF6FF]">
                  <div className="p-3.5 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-[#172033] block">Pawan Kumar</span>
                      <span className="text-[11px] text-[#5E6878]">4.0 yrs • Required: 5/5 matched</span>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-[#172033]">84%</span>
                      <span className="text-[10px] text-[#16805C] block font-semibold">Strong</span>
                    </div>
                  </div>

                  <div className="p-3.5 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-[#172033] block">Priya Patel</span>
                      <span className="text-[11px] text-[#5E6878]">3.0 yrs • Required: 4/5 matched</span>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-[#172033]">62%</span>
                      <span className="text-[10px] text-[#B7791F] block font-semibold">Review</span>
                    </div>
                  </div>

                  <div className="p-3.5 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-[#172033] block">Aarav Sharma</span>
                      <span className="text-[11px] text-[#5E6878]">4.5 yrs • Required: 3/5 matched</span>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-[#172033]">47%</span>
                      <span className="text-[10px] text-[#5E6878] block">Review</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION 8 — FINAL CTA                                         */}
      {/* ------------------------------------------------------------- */}
      <section
        className="py-20 border-t border-[#DCE6F2]"
        style={{
          background:
            "linear-gradient(135deg, #F5F9FF 0%, #EFF6FF 50%, #DBEAFE 100%)",
        }}
      >
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#172033] tracking-tight">
            Know your next move.
          </h2>
          <p className="text-sm sm:text-base text-[#5E6878] max-w-xl mx-auto leading-relaxed">
            Upload your resume to see your role matches, discover priority gaps, and start your structured learning path today.
          </p>
          <div className="pt-2">
            <Link
              href="/candidate/upload"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-md text-sm font-semibold text-[#FFFFFF] shadow-sm hover:opacity-95 hover:shadow transition-all duration-200"
              style={{
                background:
                  "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
              }}
            >
              <span>Analyze My Resume</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
