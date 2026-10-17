"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { ChevronLeft, ChevronRight, Check, AlertCircle, X } from "lucide-react";

export interface CandidateProfileItem {
  role: string;
  score: number;
  alignment: string;
  strongSkills: string[];
  skillGaps: { name: string; status: "Partial" | "Missing" }[];
  nextStep: string;
  description: string;
}

export const candidateProfiles: CandidateProfileItem[] = [
  {
    role: "Data Analyst",
    score: 82,
    alignment: "High Alignment",
    strongSkills: ["SQL", "Python", "Excel"],
    skillGaps: [
      { name: "Statistics", status: "Partial" },
      { name: "Power BI", status: "Missing" },
    ],
    nextStep: "Complete Statistics fundamentals",
    description:
      "Build stronger statistical foundations to improve analytical modeling and unlock downstream skills.",
  },
  {
    role: "Frontend Developer",
    score: 89,
    alignment: "Excellent Alignment",
    strongSkills: ["HTML", "CSS", "JavaScript", "React"],
    skillGaps: [
      { name: "TypeScript", status: "Partial" },
      { name: "Testing", status: "Missing" },
    ],
    nextStep: "Strengthen TypeScript and frontend testing",
    description:
      "Build stronger TypeScript and testing skills to become more production-ready.",
  },
  {
    role: "Machine Learning Engineer",
    score: 76,
    alignment: "Good Alignment",
    strongSkills: ["Python", "Machine Learning", "Pandas", "NumPy"],
    skillGaps: [
      { name: "Deep Learning", status: "Partial" },
      { name: "MLOps", status: "Missing" },
    ],
    nextStep: "Learn Deep Learning fundamentals",
    description:
      "Build a stronger foundation in neural networks before moving into production ML systems.",
  },
  {
    role: "Cybersecurity Analyst",
    score: 74,
    alignment: "Good Alignment",
    strongSkills: ["Networking", "Linux", "Python"],
    skillGaps: [
      { name: "Security Tools", status: "Partial" },
      { name: "Threat Analysis", status: "Missing" },
    ],
    nextStep: "Build practical security analysis skills",
    description:
      "Strengthen hands-on security analysis and threat detection capabilities.",
  },
];

export function CandidateProfileCarousel() {
  const [currentProfile, setCurrentProfile] = useState<number>(0);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const touchStartXRef = useRef<number | null>(null);

  const nextProfile = useCallback(() => {
    setCurrentProfile((prev) => (prev + 1) % candidateProfiles.length);
  }, []);

  const previousProfile = useCallback(() => {
    setCurrentProfile(
      (prev) => (prev - 1 + candidateProfiles.length) % candidateProfiles.length
    );
  }, []);

  const goToProfile = (index: number) => {
    setIsPaused(true);
    setCurrentProfile(index);
  };

  const handlePrevClick = () => {
    setIsPaused(true);
    previousProfile();
  };

  const handleNextClick = () => {
    setIsPaused(true);
    nextProfile();
  };

  // Auto-play: 5.5s interval, pauses on user interaction
  useEffect(() => {
    if (isPaused) return;

    const timer = setInterval(() => {
      nextProfile();
    }, 5500);

    return () => clearInterval(timer);
  }, [isPaused, nextProfile]);

  // Touch swipe support for mobile
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartXRef.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartXRef.current === null) return;
    const diff = touchStartXRef.current - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 40) {
      setIsPaused(true);
      if (diff > 0) {
        nextProfile();
      } else {
        previousProfile();
      }
    }
    touchStartXRef.current = null;
  };

  const profile = candidateProfiles[currentProfile];

  return (
    <div
      className="rounded-lg border border-[#DCE6F2] bg-[#FFFFFF] shadow-sm overflow-hidden"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      role="region"
      aria-roledescription="carousel"
      aria-label="Candidate Profile Carousel"
    >
      {/* Window Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-[#F5F9FF] to-[#EFF6FF] border-b border-[#DCE6F2] flex items-center justify-between text-xs">
        <span className="font-semibold text-[#172033]">Candidate Profile</span>
        <span className="text-[11px] font-medium text-[#2563EB] bg-[#DBEAFE]/70 px-2 py-0.5 rounded-full border border-[#DBEAFE]">
          Verified Analysis
        </span>
      </div>

      {/* Carousel Navigation Control Strip */}
      <div className="px-4 py-2 bg-[#FFFFFF] border-b border-[#DCE6F2] flex items-center justify-between text-xs">
        <button
          type="button"
          onClick={handlePrevClick}
          aria-label="Previous candidate profile"
          className="w-7 h-7 rounded-full bg-[#FFFFFF] border border-[#DCE6F2] text-[#2563EB] hover:bg-[#EFF6FF] hover:border-[#2563EB] flex items-center justify-center transition-all duration-200 cursor-pointer shadow-xs focus-visible:outline-2 focus-visible:outline-[#2563EB]"
        >
          <ChevronLeft className="w-4 h-4 stroke-[2.5]" />
        </button>

        <span className="text-[11px] font-medium text-[#5E6878]">
          Candidate {currentProfile + 1} of {candidateProfiles.length}
        </span>

        <button
          type="button"
          onClick={handleNextClick}
          aria-label="Next candidate profile"
          className="w-7 h-7 rounded-full bg-[#FFFFFF] border border-[#DCE6F2] text-[#2563EB] hover:bg-[#EFF6FF] hover:border-[#2563EB] flex items-center justify-center transition-all duration-200 cursor-pointer shadow-xs focus-visible:outline-2 focus-visible:outline-[#2563EB]"
        >
          <ChevronRight className="w-4 h-4 stroke-[2.5]" />
        </button>
      </div>

      {/* Carousel Body with Smooth Slide/Fade Transition */}
      <div
        key={currentProfile}
        className="p-5 space-y-4 text-xs carousel-slide-enter"
        aria-live="polite"
      >
        {/* Top Match Bar */}
        <div className="flex items-center justify-between pb-3 border-b border-[#DCE6F2]">
          <div>
            <span className="text-[10px] uppercase font-bold text-[#8A94A6] block">
              Target Role
            </span>
            <h3 className="text-base font-bold text-[#172033] mt-0.5">
              {profile.role}
            </h3>
          </div>
          <div className="text-right">
            <div className="text-2xl font-extrabold text-[#2563EB] leading-none">
              {profile.score}%
            </div>
            <span className="text-[10px] text-[#16805C] font-semibold">
              {profile.alignment}
            </span>
          </div>
        </div>

        {/* Skills Snapshot */}
        <div className="space-y-3">
          <div>
            <span className="text-[10px] font-bold uppercase text-[#5E6878] block mb-1.5">
              Strong Skills
            </span>
            <div className="flex flex-wrap gap-1.5">
              {profile.strongSkills.map((skill) => (
                <span
                  key={skill}
                  className="px-2 py-0.5 rounded bg-[#EAF7F0] text-[#16805C] border border-[#CDEDDD] text-[11px] font-medium flex items-center gap-1"
                >
                  <Check className="w-3 h-3 text-[#16805C] stroke-[2.5]" />
                  {skill}
                </span>
              ))}
            </div>
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase text-[#5E6878] block mb-1.5">
              Skill Gaps
            </span>
            <div className="flex flex-wrap gap-1.5">
              {profile.skillGaps.map((gap) => (
                <span
                  key={gap.name}
                  className={`px-2 py-0.5 rounded text-[11px] font-medium flex items-center gap-1 border ${
                    gap.status === "Partial"
                      ? "bg-[#FFF6DD] text-[#B7791F] border-[#F2DEAA]"
                      : "bg-[#FDEEEE] text-[#C24141] border-[#F2CACA]"
                  }`}
                >
                  {gap.status === "Partial" ? (
                    <AlertCircle className="w-3 h-3 text-[#B7791F] stroke-[2.5]" />
                  ) : (
                    <X className="w-3 h-3 text-[#C24141] stroke-[2.5]" />
                  )}
                  {gap.name} ({gap.status})
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Next Step Callout */}
        <div
          className="p-3 rounded-md border border-[#DCE6F2] space-y-1"
          style={{
            background:
              "linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%)",
          }}
        >
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#2563EB] block">
            Next Step
          </span>
          <p className="text-xs font-semibold text-[#172033]">
            {profile.nextStep}
          </p>
          <p className="text-[11px] text-[#5E6878] leading-normal">
            {profile.description}
          </p>
        </div>

        {/* Carousel Indicators */}
        <div className="pt-2 flex items-center justify-center gap-2">
          {candidateProfiles.map((item, index) => {
            const isActive = index === currentProfile;
            return (
              <button
                key={item.role}
                type="button"
                onClick={() => goToProfile(index)}
                aria-label={`Go to candidate profile ${index + 1}`}
                aria-current={isActive ? "true" : undefined}
                className={`transition-all duration-200 cursor-pointer rounded-full focus-visible:outline-2 focus-visible:outline-[#2563EB] ${
                  isActive
                    ? "w-3 h-3 bg-[#2563EB] ring-2 ring-[#DBEAFE]"
                    : "w-2.5 h-2.5 bg-[#DBEAFE] hover:bg-[#93C5FD] border border-[#DCE6F2]"
                }`}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
