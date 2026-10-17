import React from "react";
import { AdjacentRoleItem } from "@/lib/types";
import { ArrowRight, Check, AlertCircle, Compass } from "lucide-react";
import Link from "next/link";

interface RoleMatchCardProps {
  role: AdjacentRoleItem;
}

export function RoleMatchCard({ role }: RoleMatchCardProps) {
  const isHighFeasibility = role.feasibility.includes("Immediate");
  const roundedScore = Math.round(role.alignmentScore);

  return (
    <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-5 shadow-xs transition-colors">
      <div className="flex items-start justify-between gap-3 mb-2.5">
        <div>
          <span className="text-[10px] font-bold text-[#8A94A6] uppercase tracking-wider block">
            {role.category}
          </span>
          <h4 className="text-base font-bold text-[#172033] mt-0.5">
            {role.title}
          </h4>
        </div>

        <div className="text-right shrink-0">
          <div className="text-xl font-bold text-[#2563EB] leading-none">
            {roundedScore}%
          </div>
          <span className="text-[10px] text-[#8A94A6] font-medium">Alignment</span>
        </div>
      </div>

      <div className="mb-3">
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${
            isHighFeasibility
              ? "bg-[#EAF7F0] text-[#16805C] border-[#CDEDDD]"
              : "bg-[#EFF6FF] text-[#2563EB] border-[#D7DEE8]"
          }`}
        >
          {role.feasibility}
        </span>
      </div>

      <p className="text-xs text-[#5E6878] mb-3.5 leading-relaxed">
        {role.rationale}
      </p>

      {/* Skills comparison */}
      <div className="space-y-2 mb-4 text-xs">
        <div>
          <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
            Overlapping Competencies ({role.overlappingSkills.length})
          </span>
          <div className="flex flex-wrap gap-1">
            {role.overlappingSkills.map((skill, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded bg-[#EAF7F0] text-[#16805C] border border-[#CDEDDD] text-[11px] flex items-center gap-1 font-medium"
              >
                <Check className="w-2.5 h-2.5 text-[#16805C] stroke-[2.5]" />
                {skill}
              </span>
            ))}
          </div>
        </div>

        {role.missingBridgeSkills.length > 0 && (
          <div>
            <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
              Top Gaps to Bridge
            </span>
            <div className="flex flex-wrap gap-1">
              {role.missingBridgeSkills.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded bg-[#FFF6DD] text-[#B7791F] border border-[#F2DEAA] text-[11px] flex items-center gap-1 font-medium"
                >
                  <AlertCircle className="w-2.5 h-2.5 text-[#B7791F] stroke-[2.5]" />
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <Link
        href={`/candidate/results?role=${role.id}`}
        className="inline-flex items-center justify-between w-full pt-3 border-t border-[#EDF0F4] text-xs font-semibold text-[#2563EB] hover:text-[#1D4ED8] transition-colors"
      >
        <span>Explore Career Role</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </Link>
    </div>
  );
}
