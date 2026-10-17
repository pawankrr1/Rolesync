"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Users,
  CheckCircle2,
  Trash2,
  ExternalLink,
  ChevronRight,
  Loader2,
  Clock,
  Briefcase,
  AlertCircle,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import {
  fetchShortlist,
  updateShortlistStatus,
  removeShortlistCandidate,
} from "@/lib/api";
import { ShortlistItemResponse } from "@/lib/types";

export default function ShortlistPage() {
  const [shortlist, setShortlist] = useState<ShortlistItemResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const loadShortlist = async () => {
    setIsLoading(true);
    try {
      const res = await fetchShortlist();
      if (res.success && res.data) {
        setShortlist(res.data);
      }
    } catch (err) {
      console.error("Failed to load shortlist:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadShortlist();
  }, []);

  const handleStatusChange = async (shortlistId: string, newStatus: string) => {
    setUpdatingId(shortlistId);
    try {
      const res = await updateShortlistStatus(shortlistId, newStatus);
      if (res.success && res.data) {
        setShortlist((prev) =>
          prev.map((item) =>
            item.id === shortlistId ? { ...item, status: newStatus } : item
          )
        );
      }
    } catch (err) {
      console.error("Failed to update status:", err);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleRemove = async (candidateId: string) => {
    try {
      await removeShortlistCandidate(candidateId);
      setShortlist((prev) => prev.filter((item) => item.candidate_id !== candidateId));
    } catch (err) {
      console.error("Failed to remove shortlist item:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F8FA] flex flex-col">
      <div className="flex flex-1">
        <DashboardSidebar role="recruiter" />

        <main className="flex-1 p-6 lg:p-8 max-w-6xl mx-auto w-full space-y-6">
          {/* Header */}
          <div className="pb-3 border-b border-[#E1E6ED]">
            <div className="flex items-center gap-2 text-xs text-[#5E6878]">
              <Link href="/recruiter" className="hover:text-[#2563EB]">
                Hiring Intelligence
              </Link>
              <span>/</span>
              <span className="text-[#172033] font-semibold">Shortlisted Candidates</span>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mt-2">
              <div>
                <h1 className="text-2xl font-bold text-[#172033] tracking-tight">
                  Shortlisted Talent Pipeline
                </h1>
                <p className="text-xs text-[#5E6878] mt-0.5">
                  Track candidates across review, interview, and decision stages with full database persistence.
                </p>
              </div>

              <div className="text-xs font-semibold px-3 py-1 rounded bg-[#EAF7F0] text-[#16805C] border border-[#CDEDDD] self-start sm:self-auto">
                {shortlist.length} In Pipeline
              </div>
            </div>
          </div>

          {/* Shortlist Table */}
          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center text-center space-y-3 bg-[#FFFFFF] rounded-lg border border-[#E1E6ED]">
              <Loader2 className="w-8 h-8 text-[#2563EB] animate-spin" />
              <h3 className="text-sm font-bold text-[#172033]">Loading Shortlist Pipeline...</h3>
            </div>
          ) : shortlist.length === 0 ? (
            <div className="p-12 text-center bg-[#FFFFFF] rounded-lg border border-[#E1E6ED] space-y-3">
              <Users className="w-8 h-8 text-[#8A94A6] mx-auto" />
              <h3 className="text-sm font-bold text-[#172033]">No candidates shortlisted yet.</h3>
              <p className="text-xs text-[#5E6878] max-w-md mx-auto">
                Evaluate candidates against active job descriptions and click &quot;Shortlist&quot; to populate your hiring pipeline.
              </p>
              <Link
                href="/recruiter/matches"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-[#2563EB] text-[#FFFFFF] text-xs font-semibold shadow-xs hover:bg-[#1D4ED8] transition-colors"
              >
                <span>Browse Candidate Matches</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : (
            <div className="bg-[#FFFFFF] rounded-lg border border-[#E1E6ED] shadow-2xs overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[#E1E6ED] bg-[#F7F8FA] text-[#5E6878] font-semibold">
                      <th className="py-3 px-4">Candidate</th>
                      <th className="py-3 px-4">Role Requisition</th>
                      <th className="py-3 px-4 text-center">Match Score</th>
                      <th className="py-3 px-4">Date Shortlisted</th>
                      <th className="py-3 px-4">Pipeline Stage</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E1E6ED]">
                    {shortlist.map((item) => (
                      <tr key={item.id} className="hover:bg-[#F8FAFC] transition-colors">
                        <td className="py-3.5 px-4 font-semibold text-[#172033]">
                          <Link
                            href={`/recruiter/candidates/${item.candidate_id}`}
                            className="hover:text-[#2563EB] hover:underline"
                          >
                            {item.candidate_name}
                          </Link>
                        </td>

                        <td className="py-3.5 px-4 text-[#5E6878]">
                          {item.job_title || "General Pool"}
                        </td>

                        <td className="py-3.5 px-4 text-center">
                          {item.match_score ? (
                            <span className="font-bold text-[#16805C]">
                              {Math.round(item.match_score)}%
                            </span>
                          ) : (
                            <span className="text-[#8A94A6]">—</span>
                          )}
                        </td>

                        <td className="py-3.5 px-4 text-[#8A94A6]">
                          {item.created_at || "Recent"}
                        </td>

                        <td className="py-3.5 px-4">
                          <select
                            value={item.status}
                            onChange={(e) => handleStatusChange(item.id, e.target.value)}
                            disabled={updatingId === item.id}
                            className="px-2.5 py-1 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs font-semibold text-[#172033] focus:outline-hidden focus:border-[#2563EB]"
                          >
                            <option value="Shortlisted">Shortlisted</option>
                            <option value="Review">Review</option>
                            <option value="Interview">Interview</option>
                            <option value="Rejected">Rejected</option>
                          </select>
                        </td>

                        <td className="py-3.5 px-4 text-right">
                          <button
                            type="button"
                            onClick={() => handleRemove(item.candidate_id)}
                            className="p-1.5 rounded text-[#8A94A6] hover:text-[#C24141] hover:bg-[#FDEEEE] transition-colors"
                            title="Remove from shortlist"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
