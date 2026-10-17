import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  title?: string;
  subtitle?: string;
  stepProgress?: string;
}

export function LoadingState({
  title = "Analyzing Skill Signals...",
  subtitle = "Parsing document, extracting canonical skills, and calculating explainable weights.",
  stepProgress = "Stage 4 of 6: Running Weighted Matching Engine",
}: LoadingStateProps) {
  return (
    <div className="w-full min-h-[300px] flex flex-col items-center justify-center p-8 text-center bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg shadow-xs">
      <div className="w-10 h-10 rounded-full bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center mb-4">
        <Loader2 className="w-5 h-5 animate-spin text-[#2563EB]" />
      </div>

      <h3 className="text-base font-bold text-[#172033] mb-1">
        {title}
      </h3>
      <p className="max-w-md text-xs text-[#5E6878] mb-4 leading-relaxed">
        {subtitle}
      </p>

      {stepProgress && (
        <span className="inline-flex items-center px-3 py-1 rounded text-[11px] font-medium bg-[#F1F4F8] text-[#5E6878] border border-[#E1E6ED]">
          {stepProgress}
        </span>
      )}
    </div>
  );
}
