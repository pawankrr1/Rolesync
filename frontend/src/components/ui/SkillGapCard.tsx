import React from "react";
import { SkillGapItem } from "@/lib/types";
import { Clock, Unlock, ShieldAlert, ArrowRight, BookOpen } from "lucide-react";
import Link from "next/link";

interface SkillGapCardProps {
  gap: SkillGapItem;
  onSelectAction?: (skillName: string) => void;
}

export function SkillGapCard({ gap, onSelectAction }: SkillGapCardProps) {
  const isP1 = gap.priorityTier.startsWith("P1") || gap.priorityTier.includes("HIGH");
  const isP2 = gap.priorityTier.startsWith("P2") || gap.priorityTier.includes("MEDIUM");

  const tierBadgeColor = isP1
    ? "bg-[#FDEEEE] text-[#C24141] border-[#F2CACA]"
    : isP2
    ? "bg-[#FFF6DD] text-[#B7791F] border-[#F2DEAA]"
    : "bg-[#F1F4F8] text-[#5E6878] border-[#E1E6ED]";

  const tierLabel = isP1 ? "HIGH PRIORITY" : isP2 ? "MEDIUM PRIORITY" : "LOW PRIORITY";

  return (
    <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-5 shadow-xs transition-colors">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-5 h-5 rounded bg-[#F1F4F8] text-[#172033] font-bold text-xs flex items-center justify-center">
              #{gap.priorityRank}
            </span>
            <h4 className="text-base font-bold text-[#172033]">
              {gap.name}
            </h4>
          </div>
          <span className="text-xs text-[#5E6878]">
            {gap.category}
          </span>
        </div>

        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${tierBadgeColor}`}>
          {tierLabel}
        </span>
      </div>

      {/* Why it matters & Reasoning */}
      <div className="space-y-2 mb-3.5 text-xs">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#8A94A6] block mb-0.5">
            Why It Matters
          </span>
          <p className="text-[#172033] leading-relaxed">
            {gap.reasoning}
          </p>
        </div>

        {/* Explainability: Why is this missing? */}
        <div className="p-2.5 rounded bg-[#F8FAFC] border border-[#E1E6ED] text-[11px] space-y-0.5">
          <span className="font-semibold text-[#172033] block">
            Evidence Context
          </span>
          <p className="text-[#5E6878] leading-normal">
            {gap.why_missing ||
              `Required by target role specifications, but not detected in the parsed resume.`}
          </p>
        </div>
      </div>

      {/* Meta indicators */}
      <div className="grid grid-cols-2 gap-2 pt-3 border-t border-[#EDF0F4] text-xs">
        <div className="flex items-center gap-1.5 text-[#5E6878]">
          <Clock className="w-3.5 h-3.5 text-[#8A94A6]" />
          <span>Effort: <strong className="text-[#172033] font-medium">{gap.learningEffortWeeks}</strong></span>
        </div>

        <div className="flex items-center gap-1.5 text-[#5E6878]">
          <ShieldAlert className="w-3.5 h-3.5 text-[#8A94A6]" />
          <span>
            Prereqs:{" "}
            <strong className={gap.prerequisitesMet ? "text-[#16805C] font-medium" : "text-[#B7791F] font-medium"}>
              {gap.prerequisitesMet ? "Satisfied" : "Pending"}
            </strong>
          </span>
        </div>

        {gap.unblocksSkills && gap.unblocksSkills.length > 0 && (
          <div className="col-span-2 flex items-center gap-1.5 text-[#5E6878] pt-1">
            <Unlock className="w-3.5 h-3.5 text-[#2563EB] shrink-0" />
            <span>
              Unblocks:{" "}
              <strong className="text-[#172033] font-medium">
                {gap.unblocksSkills.join(", ")}
              </strong>
            </span>
          </div>
        )}
      </div>

      {/* Action Link */}
      <div className="mt-3.5 pt-3 border-t border-[#EDF0F4] flex justify-end">
        <a
          href="#roadmap-section"
          onClick={() => onSelectAction?.(gap.name)}
          className="inline-flex items-center gap-1 text-xs font-semibold text-[#2563EB] hover:text-[#1D4ED8] transition-colors"
        >
          <span>View in Learning Roadmap</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </a>
      </div>
    </div>
  );
}
