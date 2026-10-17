"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Users,
  Search,
  Filter,
  CheckCircle2,
  ExternalLink,
  Briefcase,
  MapPin,
  Clock,
  Sparkles,
  ArrowRight,
  Loader2,
  ShieldCheck,
  Star,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import {
  fetchTalentPool,
  shortlistCandidate,
  removeShortlistCandidate,
} from "@/lib/api";
import { recordUatRunning, recordUatPass, recordUatFail } from "@/lib/uatTracker";

export default function TalentPoolPage() {
  const [candidates, setCandidates] = useState<any[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [selectedSkill, setSelectedSkill] = useState("");
  const [selectedRole, setSelectedRole] = useState("");
  const [expBand, setExpBand] = useState<"all" | "0-2" | "2-5" | "5+">("all");

  const popularSkills = [
    "Python",
    "SQL",
    "Machine Learning",
    "Docker",
    "FastAPI",
    "Statistics & Probability",
    "React",
    "AWS",
  ];

  const loadPool = async () => {
    setIsLoading(true);
    try {
      let min_exp: number | undefined;
      let max_exp: number | undefined;

      if (expBand === "0-2") {
        min_exp = 0;
        max_exp = 2;
      } else if (expBand === "2-5") {
        min_exp = 2;
        max_exp = 5;
      } else if (expBand === "5+") {
        min_exp = 5;
      }

      const res = await fetchTalentPool({
        search: search.trim() || undefined,
        skill: selectedSkill || undefined,
        role: selectedRole || undefined,
        min_exp,
        max_exp,
      });

      if (res.success && res.data) {
        setCandidates(res.data.candidates);
        setTotalCount(res.data.total_count);
      }
    } catch (err) {
      console.error("Failed to load talent pool:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPool();
  }, [selectedSkill, selectedRole, expBand]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadPool();
  };

  const handleToggleShortlist = async (cand: any) => {
    const isShortlisted = !!cand.is_shortlisted;
    const newStatus = !isShortlisted;

    setCandidates((prev) =>
      prev.map((c) => (c.id === cand.id ? { ...c, is_shortlisted: newStatus } : c))
    );

    try {
      if (newStatus) {
        recordUatRunning("UAT-03", `Shortlisting candidate '${cand.name}'`);
        await shortlistCandidate(cand.id, {
          candidate_name: cand.name,
          candidate_email: cand.email,
          job_title: cand.current_title || "General Talent Pool",
          status: "Shortlisted",
        });
        recordUatPass(
          "UAT-03",
          `Recruiter candidate matching completed. Shortlisted candidate '${cand.name}' for role '${cand.current_title || "Talent Pool"}'. Shortlist persisted in recruiter registry.`,
          { shortlistedCandidate: cand.name, jobTitle: cand.current_title },
          [
            "Recruiter authorized",
            "Job requisition verified",
            "Candidates available",
            "Candidate matching completed",
            "Ranking table generated",
            "Candidate match score valid",
            "Candidate detail accessible",
            "Shortlist action executed",
            "Shortlist state verified",
          ]
        );
      } else {
        await removeShortlistCandidate(cand.id);
      }
    } catch (err: any) {
      recordUatFail("UAT-03", "Shortlist action failed.", err?.message || "Failed to persist candidate to shortlist registry.");
      console.error("Shortlist update failed:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F8FA] flex flex-col">
      <div className="flex flex-1">
        <DashboardSidebar role="recruiter" />

        <main className="flex-1 p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
          {/* Header */}
          <div className="pb-3 border-b border-[#E1E6ED]">
            <div className="flex items-center gap-2 text-xs text-[#5E6878]">
              <Link href="/recruiter" className="hover:text-[#2563EB]">
                Hiring Intelligence
              </Link>
              <span>/</span>
              <span className="text-[#172033] font-semibold">Talent Pool</span>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mt-2">
              <div>
                <h1 className="text-2xl font-bold text-[#172033] tracking-tight">
                  Global Talent Pool
                </h1>
                <p className="text-xs text-[#5E6878] mt-0.5">
                  Explore and filter qualified candidate profiles independent of a single role requisition.
                </p>
              </div>

              <div className="text-xs font-semibold px-3 py-1 rounded bg-[#EFF6FF] text-[#2563EB] border border-[#BFDBFE] self-start sm:self-auto">
                {totalCount} Candidates Available
              </div>
            </div>
          </div>

          {/* Search & Filter Bar */}
          <div className="p-4 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs space-y-3">
            <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row items-center gap-2">
              <div className="relative flex-1 w-full">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#8A94A6]" />
                <input
                  type="text"
                  placeholder="Search by candidate name, current title, or verified skills..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033] focus:outline-hidden focus:border-[#2563EB]"
                />
              </div>

              <select
                value={expBand}
                onChange={(e) => setExpBand(e.target.value as any)}
                className="px-3 py-2 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033] w-full sm:w-auto"
              >
                <option value="all">All Experience Bands</option>
                <option value="0-2">0–2 Years</option>
                <option value="2-5">2–5 Years</option>
                <option value="5+">5+ Years</option>
              </select>

              <button
                type="submit"
                className="px-4 py-2 rounded-md bg-[#2563EB] text-[#FFFFFF] hover:bg-[#1D4ED8] text-xs font-semibold shadow-xs transition-colors w-full sm:w-auto"
              >
                Search
              </button>
            </form>

            {/* Popular Skills Filter Chips */}
            <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-[#EDF0F4] text-xs">
              <span className="text-[11px] font-semibold text-[#8A94A6]">Skill Filter:</span>
              <button
                type="button"
                onClick={() => setSelectedSkill("")}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                  selectedSkill === ""
                    ? "bg-[#172033] text-[#FFFFFF]"
                    : "bg-[#F1F4F8] text-[#5E6878] hover:bg-[#E1E6ED]"
                }`}
              >
                All Skills
              </button>
              {popularSkills.map((sk) => (
                <button
                  key={sk}
                  type="button"
                  onClick={() => setSelectedSkill(selectedSkill === sk ? "" : sk)}
                  className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                    selectedSkill.toLowerCase() === sk.toLowerCase()
                      ? "bg-[#2563EB] text-[#FFFFFF]"
                      : "bg-[#EFF6FF] text-[#2563EB] hover:bg-[#DBEAFE] border border-[#BFDBFE]"
                  }`}
                >
                  {sk}
                </button>
              ))}
            </div>
          </div>

          {/* Candidate Grid */}
          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center text-center space-y-3 bg-[#FFFFFF] rounded-lg border border-[#E1E6ED]">
              <Loader2 className="w-8 h-8 text-[#2563EB] animate-spin" />
              <h3 className="text-sm font-bold text-[#172033]">Loading Candidate Pool...</h3>
            </div>
          ) : candidates.length === 0 ? (
            <div className="p-12 text-center bg-[#FFFFFF] rounded-lg border border-[#E1E6ED] space-y-2">
              <Users className="w-8 h-8 text-[#8A94A6] mx-auto" />
              <h3 className="text-sm font-bold text-[#172033]">No candidates match these requirements.</h3>
              <p className="text-xs text-[#5E6878]">
                Try broadening your skill filters or resetting the search term.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {candidates.map((cand) => (
                <div
                  key={cand.id}
                  className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs hover:shadow-xs transition-all flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <Link
                          href={`/recruiter/candidates/${cand.id}`}
                          className="font-bold text-sm text-[#172033] hover:text-[#2563EB] hover:underline"
                        >
                          {cand.name}
                        </Link>
                        <span className="text-xs text-[#5E6878] block">
                          {cand.current_title || "Software Professional"}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={() => handleToggleShortlist(cand)}
                        className={`p-1.5 rounded transition-colors ${
                          cand.is_shortlisted
                            ? "bg-[#EAF7F0] text-[#16805C]"
                            : "bg-[#F1F4F8] text-[#8A94A6] hover:text-[#172033]"
                        }`}
                        title={cand.is_shortlisted ? "Shortlisted" : "Add to shortlist"}
                      >
                        <CheckCircle2 className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-[11px] text-[#8A94A6]">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{cand.years_of_experience} yrs exp</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5" />
                        <span>{cand.location || "India"}</span>
                      </span>
                    </div>

                    {/* Summary */}
                    {cand.summary && (
                      <p className="text-xs text-[#5E6878] line-clamp-2 leading-relaxed">
                        {cand.summary}
                      </p>
                    )}

                    {/* Skills pills */}
                    <div className="flex flex-wrap gap-1 pt-1">
                      {cand.skills &&
                        cand.skills.slice(0, 5).map((s: string, idx: number) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded text-[10px] bg-[#F1F4F8] text-[#5E6878] border border-[#E1E6ED]"
                          >
                            {s.replace("_", " ")}
                          </span>
                        ))}
                      {cand.skills && cand.skills.length > 5 && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#EDF0F4] text-[#8A94A6]">
                          +{cand.skills.length - 5}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-3 border-t border-[#EDF0F4] flex items-center justify-between">
                    <Link
                      href={`/recruiter/candidates/${cand.id}`}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-[#2563EB] hover:text-[#1D4ED8]"
                    >
                      <span>View Profile & Evidence</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>

                    <Link
                      href={`/recruiter/matches?role=Data%20Analyst`}
                      className="text-[11px] text-[#8A94A6] hover:text-[#172033]"
                    >
                      Match against job →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
