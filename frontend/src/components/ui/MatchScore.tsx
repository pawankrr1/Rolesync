"use client";

import React from "react";
import { MatchGrade } from "@/lib/types";

interface MatchScoreProps {
  score: number;
  grade: MatchGrade;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

export function MatchScore({
  score,
  grade,
  size = "md",
  showLabel = true,
}: MatchScoreProps) {
  const rounded = Math.round(score);

  // Professional color theme
  const getTheme = () => {
    if (rounded >= 80) {
      return {
        stroke: "#16805C",
        text: "text-[#16805C]",
        bg: "bg-[#EAF7F0] text-[#16805C] border-[#CDEDDD]",
      };
    }
    if (rounded >= 65) {
      return {
        stroke: "#2563EB",
        text: "text-[#2563EB]",
        bg: "bg-[#EFF6FF] text-[#2563EB] border-[#D7DEE8]",
      };
    }
    if (rounded >= 50) {
      return {
        stroke: "#B7791F",
        text: "text-[#B7791F]",
        bg: "bg-[#FFF6DD] text-[#B7791F] border-[#F2DEAA]",
      };
    }
    return {
      stroke: "#C24141",
      text: "text-[#C24141]",
      bg: "bg-[#FDEEEE] text-[#C24141] border-[#F2CACA]",
    };
  };

  const theme = getTheme();

  const dimensions = {
    sm: { box: 60, strokeWidth: 4, radius: 25, scoreText: "text-base", denomText: "text-[10px]" },
    md: { box: 96, strokeWidth: 6, radius: 41, scoreText: "text-2xl", denomText: "text-xs" },
    lg: { box: 124, strokeWidth: 7, radius: 53, scoreText: "text-3xl", denomText: "text-xs" },
  }[size];

  const circumference = 2 * Math.PI * dimensions.radius;
  const strokeDashoffset = circumference - (circumference * rounded) / 100;

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative inline-flex items-center justify-center">
        <svg
          width={dimensions.box}
          height={dimensions.box}
          className="transform -rotate-90"
        >
          {/* Track circle */}
          <circle
            cx={dimensions.box / 2}
            cy={dimensions.box / 2}
            r={dimensions.radius}
            stroke="#E7ECF3"
            strokeWidth={dimensions.strokeWidth}
            fill="transparent"
          />
          {/* Calibrated progress indicator */}
          <circle
            cx={dimensions.box / 2}
            cy={dimensions.box / 2}
            r={dimensions.radius}
            stroke={theme.stroke}
            strokeWidth={dimensions.strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Crisp ratio display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className={`font-bold tracking-tight text-[#172033] ${dimensions.scoreText} leading-none`}>
            {rounded}
          </span>
          <span className={`text-[#8A94A6] font-medium ${dimensions.denomText} mt-0.5`}>
            / 100
          </span>
        </div>
      </div>

      {showLabel && (
        <span
          className={`mt-2.5 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${theme.bg}`}
        >
          {grade}
        </span>
      )}
    </div>
  );
}
