"use client";

import React, { useState } from "react";
import { SkillStatus } from "@/lib/types";
import { Check, AlertCircle, X } from "lucide-react";

interface SkillBadgeProps {
  name: string;
  category?: string;
  status?: SkillStatus;
  confidence?: number;
  confidence_level?: string;
  confidence_note?: string;
  evidence?: string[];
  notes?: string;
  showEvidenceTooltip?: boolean;
}

export function SkillBadge({
  name,
  category,
  status = "strong_match",
  confidence,
  confidence_level,
  confidence_note,
  evidence,
  notes,
  showEvidenceTooltip = true,
}: SkillBadgeProps) {
  const [isOpen, setIsOpen] = useState(false);

  const isLowConfidence =
    (confidence !== undefined && confidence < 0.6) ||
    confidence_level?.toLowerCase() === "low";

  const resolvedConfidenceLevel =
    confidence_level ||
    (confidence !== undefined
      ? confidence >= 0.85
        ? "High"
        : confidence >= 0.6
        ? "Medium"
        : "Low"
      : undefined);

  const resolvedConfidenceNote =
    confidence_note ||
    (isLowConfidence ? "Low extraction confidence — verify manually." : undefined);

  // Exact light skill colors
  const statusConfig = {
    strong_match: {
      badge: "bg-[#EAF7F0] text-[#16805C] border-[#CDEDDD] hover:bg-[#DDF2E7]",
      indicator: "text-[#16805C]",
      icon: <Check className="w-3 h-3 stroke-[2.5]" />,
      label: "Strong",
    },
    partial_match: {
      badge: "bg-[#FFF6DD] text-[#B7791F] border-[#F2DEAA] hover:bg-[#FCEEC5]",
      indicator: "text-[#B7791F]",
      icon: <AlertCircle className="w-3 h-3 stroke-[2.5]" />,
      label: "Developing",
    },
    missing: {
      badge: "bg-[#FDEEEE] text-[#C24141] border-[#F2CACA] hover:bg-[#F9DCDC]",
      indicator: "text-[#C24141]",
      icon: <X className="w-3 h-3 stroke-[2.5]" />,
      label: "Missing",
    },
  }[status];

  const hasPopoverContent =
    showEvidenceTooltip && (evidence?.length || notes || isLowConfidence);

  return (
    <div className="relative inline-block text-left">
      <button
        type="button"
        onClick={() => hasPopoverContent && setIsOpen(!isOpen)}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
          statusConfig.badge
        } ${hasPopoverContent ? "cursor-pointer" : "cursor-default"} ${
          isLowConfidence ? "ring-1 ring-[#B7791F]" : ""
        }`}
        aria-expanded={isOpen}
      >
        <span className={statusConfig.indicator}>{statusConfig.icon}</span>
        <span className="font-semibold text-[#172033]">{name}</span>
        <span className="text-[10px] opacity-80 font-normal ml-0.5">
          ({statusConfig.label})
        </span>

        {confidence !== undefined && (
          <span className="text-[10px] opacity-70 font-mono">
            {Math.round(confidence * 100)}%
          </span>
        )}

        {hasPopoverContent && (
          <span className="text-[10px] opacity-60">
            •
          </span>
        )}
      </button>

      {/* Structured Evidence Popover */}
      {isOpen && hasPopoverContent && (
        <div className="absolute z-40 bottom-full left-0 mb-2 w-80 p-3.5 bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg shadow-lg text-left text-xs">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#E1E6ED]">
            <span className="font-bold text-[#172033]">
              {name}
            </span>
            <div className="flex items-center gap-1.5 text-[10px] text-[#5E6878]">
              {resolvedConfidenceLevel && (
                <span>Confidence: <strong>{resolvedConfidenceLevel}</strong></span>
              )}
              {category && <span>• {category}</span>}
            </div>
          </div>

          {isLowConfidence && resolvedConfidenceNote && (
            <div className="p-2 mb-2 rounded bg-[#FFF6DD] border border-[#F2DEAA] text-[#B7791F] text-[11px] flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              <span>{resolvedConfidenceNote}</span>
            </div>
          )}

          {notes && (
            <p className="text-[#5E6878] mb-2 leading-relaxed">
              {notes}
            </p>
          )}

          {evidence && evidence.length > 0 ? (
            <div>
              <span className="text-[10px] font-semibold text-[#5E6878] uppercase tracking-wider block mb-1">
                Grounded Resume Evidence:
              </span>
              <ul className="space-y-1.5">
                {evidence.map((snippet, idx) => (
                  <li
                    key={idx}
                    className="italic text-[#172033] bg-[#F8FAFC] p-2 rounded border border-[#E1E6ED] text-[11px] leading-relaxed"
                  >
                    &ldquo;{snippet}&rdquo;
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="text-[11px] text-[#8A94A6] italic">
              No direct sentence snippet cited in this section.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
