import React from "react";
import { RoadmapMilestoneItem } from "@/lib/types";
import { BookOpen, ExternalLink, Code2, Award, Clock } from "lucide-react";

interface RecommendationCardProps {
  milestone: RoadmapMilestoneItem;
}

export function RecommendationCard({ milestone }: RecommendationCardProps) {
  return (
    <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-5 shadow-xs transition-colors">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-[#EFF6FF] text-[#2563EB] border border-[#E1E6ED]">
            Step {milestone.stepNumber}
          </span>
          <span className="text-xs font-semibold text-[#172033]">
            {milestone.phaseTitle}
          </span>
        </div>
        <span className="text-xs text-[#5E6878] flex items-center gap-1">
          <Clock className="w-3.5 h-3.5 text-[#8A94A6]" />
          <span>{milestone.duration}</span>
        </span>
      </div>

      <h4 className="text-base font-bold text-[#172033] mb-1">
        Focus: {milestone.skillName}
      </h4>
      <p className="text-xs text-[#5E6878] mb-3">
        {milestone.prerequisiteContext}
      </p>

      {/* Grounded Recommendation Rationale */}
      <div className="p-3 mb-3.5 rounded bg-[#F8FAFC] border border-[#E1E6ED] text-[11px] space-y-1">
        <span className="font-semibold text-[#172033] block">
          Strategic Rationale
        </span>
        <p className="text-[#5E6878] leading-relaxed">
          {milestone.why_recommended ||
            `Identified as a critical competency requirement. Recommended to bridge technical gaps with high market relevance.`}
        </p>
      </div>

      {/* Verified Resource Links */}
      {milestone.resources && milestone.resources.length > 0 && (
        <div className="mb-3.5 space-y-2">
          <span className="text-[10px] font-bold text-[#8A94A6] uppercase tracking-wider block">
            Recommended Learning Resource
          </span>
          {milestone.resources.map((res, idx) => {
            const isSafe = res.url && (res.url.startsWith("https://") || res.url.startsWith("http://"));
            return isSafe ? (
              <a
                key={idx}
                href={res.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-2.5 rounded border border-[#E1E6ED] hover:border-[#2563EB] hover:bg-[#F8FAFC] transition-colors group"
              >
                <div className="flex items-center gap-2.5">
                  <BookOpen className="w-4 h-4 text-[#2563EB] shrink-0" />
                  <div>
                    <span className="text-xs font-semibold text-[#172033] block group-hover:text-[#2563EB]">
                      {res.title}
                    </span>
                    <span className="text-[10px] text-[#5E6878]">
                      {res.provider} • {res.estimatedHours} hrs • {res.isFree ? "Free" : "Certificate"}
                    </span>
                  </div>
                </div>
                <ExternalLink className="w-3.5 h-3.5 text-[#8A94A6] group-hover:text-[#2563EB] shrink-0" />
              </a>
            ) : (
              <div
                key={idx}
                className="flex items-center justify-between p-2.5 rounded border border-[#E1E6ED]"
              >
                <div className="flex items-center gap-2.5">
                  <BookOpen className="w-4 h-4 text-[#8A94A6] shrink-0" />
                  <div>
                    <span className="text-xs font-semibold text-[#172033] block">
                      {res.title}
                    </span>
                    <span className="text-[10px] text-[#5E6878]">
                      {res.provider} • {res.estimatedHours} hrs
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Practical Project Challenge */}
      {milestone.projectChallenge && (
        <div className="p-3 bg-[#F8FAFC] rounded border border-[#E1E6ED] mb-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-[#172033] mb-1">
            <Code2 className="w-3.5 h-3.5 text-[#2563EB]" />
            <span>Practical Capstone Application</span>
          </div>
          <p className="text-xs text-[#5E6878] leading-relaxed">
            {milestone.projectChallenge}
          </p>
        </div>
      )}

      {/* Outcomes */}
      {milestone.outcomes && milestone.outcomes.length > 0 && (
        <div className="flex items-start gap-1.5 text-xs text-[#5E6878]">
          <Award className="w-3.5 h-3.5 text-[#16805C] shrink-0 mt-0.5" />
          <span>Outcome: {milestone.outcomes.join(" • ")}</span>
        </div>
      )}
    </div>
  );
}
