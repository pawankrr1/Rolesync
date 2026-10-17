"use client";

import React from "react";
import { Check } from "lucide-react";

interface ProgressIndicatorProps {
  currentStep?: number; // 1 to 6
  interactive?: boolean;
  onStepClick?: (step: number) => void;
}

const steps = [
  { number: 1, name: "Ingest", label: "CV & JD" },
  { number: 2, name: "Extract", label: "NLP Skills" },
  { number: 3, name: "Normalize", label: "Taxonomy" },
  { number: 4, name: "Match", label: "Scoring" },
  { number: 5, name: "Gap", label: "Priority DAG" },
  { number: 6, name: "Recommend", label: "Action Roadmap" },
];

export function ProgressIndicator({
  currentStep = 4,
  interactive = false,
  onStepClick,
}: ProgressIndicatorProps) {
  return (
    <div className="w-full py-2">
      <div className="flex items-center justify-between relative">
        {/* Continuous track */}
        <div className="absolute top-4 left-0 right-0 h-0.5 bg-[#E1E6ED] -translate-y-1/2 z-0" />

        {/* Progress fill */}
        <div
          className="absolute top-4 left-0 h-0.5 bg-[#2563EB] -translate-y-1/2 z-0 transition-all duration-300"
          style={{
            width: `${((Math.max(1, currentStep) - 1) / (steps.length - 1)) * 100}%`,
          }}
        />

        {steps.map((s) => {
          const isCompleted = s.number < currentStep;
          const isCurrent = s.number === currentStep;

          return (
            <div
              key={s.number}
              onClick={() => interactive && onStepClick?.(s.number)}
              className={`relative z-10 flex flex-col items-center group ${
                interactive ? "cursor-pointer" : ""
              }`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs transition-colors ${
                  isCompleted
                    ? "bg-[#16805C] text-[#FFFFFF]"
                    : isCurrent
                    ? "bg-[#FFFFFF] border-2 border-[#2563EB] text-[#2563EB] font-bold"
                    : "bg-[#FFFFFF] border border-[#CBD5E1] text-[#8A94A6]"
                }`}
              >
                {isCompleted ? <Check className="w-3.5 h-3.5 stroke-[2.5]" /> : s.number}
              </div>

              <div className="mt-1.5 text-center">
                <span
                  className={`text-xs font-medium block leading-tight ${
                    isCurrent
                      ? "text-[#2563EB] font-semibold"
                      : isCompleted
                      ? "text-[#172033]"
                      : "text-[#8A94A6]"
                  }`}
                >
                  {s.name}
                </span>
                <span className="text-[10px] text-[#5E6878] hidden sm:block">
                  {s.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
