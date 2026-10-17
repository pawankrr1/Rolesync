import React, { useState } from "react";
import { FactorBreakdownItem, BackendMatchItem, BackendExtractedSkill } from "@/lib/types";
import {
  Info,
  Check,
  AlertCircle,
  HelpCircle,
  Shield,
  FileText,
  Lock,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

export interface ExplanationPanelProps {
  whyScore?: string;
  factors: FactorBreakdownItem[];
  narrative?: string;
  strongMatches?: BackendMatchItem[];
  partialMatches?: BackendMatchItem[];
  missingSkills?: BackendMatchItem[];
  extractedSkills?: BackendExtractedSkill[];
  systemDisclaimer?: string;
}

const DEFAULT_SYSTEM_DISCLAIMER =
  "RoleSync provides decision support based on the available profile and dataset. It does not guarantee employment, hiring outcomes or career success.";

export function ExplanationPanel({
  whyScore,
  factors,
  narrative,
  strongMatches = [],
  partialMatches = [],
  missingSkills = [],
  extractedSkills = [],
  systemDisclaimer = DEFAULT_SYSTEM_DISCLAIMER,
}: ExplanationPanelProps) {
  const [showAllEvidence, setShowAllEvidence] = useState(false);

  // Collect skills that have evidence snippets
  const evidenceItems = extractedSkills.length > 0
    ? extractedSkills
        .filter((s) => Boolean(s.evidence))
        .map((s) => ({
          name: s.name,
          category: s.category || "Skill",
          evidence: s.evidence || "",
          confidence: s.confidence,
          confidence_level: s.confidence_level || (s.confidence && s.confidence >= 0.85 ? "High" : s.confidence && s.confidence >= 0.6 ? "Medium" : "Low"),
          confidence_note: s.confidence_note || (s.confidence && s.confidence < 0.6 ? "Possible skill detected — review recommended." : undefined),
        }))
    : strongMatches
        .concat(partialMatches)
        .filter((m) => Boolean(m.evidence))
        .map((m) => ({
          name: m.skill,
          category: m.is_required ? "Core Requirement" : "Preferred Skill",
          evidence: m.evidence || "",
          confidence: m.contribution ? Math.min(1, m.contribution + 0.7) : 0.85,
          confidence_level: "High",
          confidence_note: undefined,
        }));

  const visibleEvidence = showAllEvidence ? evidenceItems : evidenceItems.slice(0, 4);

  return (
    <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-6 sm:p-7 shadow-xs space-y-6 transition-colors">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b border-[#EDF0F4]">
        <div className="p-2 rounded bg-[#EFF6FF] text-[#2563EB]">
          <Info className="w-4 h-4 stroke-[2.2]" />
        </div>
        <div>
          <h3 className="text-base font-bold text-[#172033]">
            Score Transparency & Grounded Evidence
          </h3>
          <p className="text-xs text-[#5E6878]">
            Every match score and skill gap is mathematically constructed from 4 weighted factors with citation back to your resume.
          </p>
        </div>
      </div>

      {/* 1. WHY THIS SCORE? Summary Banner */}
      {whyScore && (
        <div className="p-4 rounded-lg bg-[#F8FAFC] border border-[#E1E6ED] space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#2563EB] block">
            Why this score?
          </span>
          <p className="text-xs font-medium text-[#172033] leading-relaxed">
            &ldquo;{whyScore}&rdquo;
          </p>
        </div>
      )}

      {/* Narrative */}
      {narrative && (
        <p className="text-xs text-[#5E6878] leading-relaxed">
          {narrative}
        </p>
      )}

      {/* 2. 4-Factor Mathematical Breakdown Table */}
      <div>
        <span className="text-[11px] font-bold uppercase tracking-wider text-[#8A94A6] block mb-3">
          4-Factor Weight Construction
        </span>
        <div className="overflow-x-auto rounded-lg border border-[#E1E6ED]">
          <table className="w-full text-left text-xs bg-[#FFFFFF]">
            <thead className="bg-[#F7F8FA] border-b border-[#E1E6ED] text-[11px] uppercase tracking-wider text-[#5E6878] font-semibold">
              <tr>
                <th className="py-2.5 px-3">Factor</th>
                <th className="py-2.5 px-3">Weight</th>
                <th className="py-2.5 px-3">Score Achieved</th>
                <th className="py-2.5 px-3 hidden md:table-cell">Basis / Method</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EDF0F4] text-[#172033]">
              {factors.map((f, idx) => (
                <tr key={idx} className="hover:bg-[#F7F9FC]">
                  <td className="py-2.5 px-3 font-semibold text-[#172033]">
                    {f.name}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[#5E6878]">
                    {Math.round(f.weight * 100)}%
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="font-bold text-[#2563EB] font-mono">
                      {f.weightedScore.toFixed(1)}
                    </span>
                    <span className="text-[#8A94A6] text-[10px]"> / {f.maxPoints} pts</span>
                  </td>
                  <td className="py-2.5 px-3 hidden md:table-cell text-[#5E6878] text-[11px] max-w-xs truncate">
                    {f.explanation}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Verified Sentence-Level Evidence Quotes */}
      {evidenceItems.length > 0 && (
        <div className="pt-2 border-t border-[#EDF0F4]">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#8A94A6]">
                Grounded Sentence Citations ({evidenceItems.length})
              </h4>
              <p className="text-[11px] text-[#5E6878]">
                Extracted verbatim from the submitted resume without generative hallucination.
              </p>
            </div>

            {evidenceItems.length > 4 && (
              <button
                type="button"
                onClick={() => setShowAllEvidence(!showAllEvidence)}
                className="text-xs font-semibold text-[#2563EB] hover:underline flex items-center gap-1"
              >
                <span>{showAllEvidence ? "Show less" : `View all (${evidenceItems.length})`}</span>
                {showAllEvidence ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {visibleEvidence.map((item, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg border border-[#E1E6ED] bg-[#F8FAFC] text-xs space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#172033]">
                    {item.name}
                  </span>
                  <span className="text-[10px] text-[#8A94A6]">
                    {item.category}
                  </span>
                </div>
                <p className="text-[11px] italic text-[#172033] bg-[#FFFFFF] p-2 rounded border border-[#E1E6ED] leading-relaxed">
                  &ldquo;{item.evidence}&rdquo;
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Decision Support Disclaimer */}
      <div className="pt-3 border-t border-[#EDF0F4] flex items-start gap-2 text-[11px] text-[#8A94A6]">
        <Shield className="w-4 h-4 text-[#8A94A6] shrink-0 mt-0.5" />
        <p className="leading-normal">{systemDisclaimer}</p>
      </div>
    </div>
  );
}
