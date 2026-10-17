import React from "react";
import { SkillItem } from "@/lib/types";
import { SkillBadge } from "./SkillBadge";

interface SkillGroupProps {
  title: string;
  skills: SkillItem[];
  emptyMessage?: string;
}

export function SkillGroup({
  title,
  skills,
  emptyMessage = "No skills detected in this group.",
}: SkillGroupProps) {
  return (
    <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-4 shadow-xs">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-[#EDF0F4]">
        <h4 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
          {title}
        </h4>
        <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-[#F1F4F8] text-[#5E6878]">
          {skills.length}
        </span>
      </div>

      {skills.length === 0 ? (
        <p className="text-xs text-[#8A94A6] italic py-2">
          {emptyMessage}
        </p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {skills.map((skill) => (
            <SkillBadge
              key={skill.id}
              name={skill.name}
              category={skill.category}
              status={skill.status}
              confidence={skill.confidence}
              evidence={skill.evidence}
              notes={skill.notes}
            />
          ))}
        </div>
      )}
    </div>
  );
}
