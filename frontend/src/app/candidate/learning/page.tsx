"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ExternalLink,
  Code2,
  Clock,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import { CandidateFullAnalysisResult } from "@/lib/types";

export default function LearningRoadmapPage() {
  const [activeAnalysis, setActiveAnalysis] = useState<CandidateFullAnalysisResult | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = window.sessionStorage.getItem("candidate_active_analysis");
      if (saved) {
        try {
          setActiveAnalysis(JSON.parse(saved));
        } catch {
          // ignore
        }
      }
    }
  }, []);

  const targetRole = activeAnalysis?.targetRole || "Data Scientist";
  const rawRoadmap = activeAnalysis?.roadmap.roadmap || [];

  const defaultTimeline = [
    {
      week: "WEEK 1",
      title: "Statistics Fundamentals",
      skill: "Statistics & Probability",
      description: "Descriptive statistics, distributions, mean/variance, and Central Limit Theorem.",
      course: {
        title: "Introduction to Probability and Statistics",
        provider: "MIT OpenCourseWare",
        hours: 12,
        url: "https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2014/",
        free: true,
      },
    },
    {
      week: "WEEK 2",
      title: "Inferential Hypothesis Testing",
      skill: "Probability & Hypothesis Testing",
      description: "P-values, t-tests, confidence intervals, and experimental significance testing.",
      course: {
        title: "Statistics with Python Specialization",
        provider: "Coursera / Univ of Michigan",
        hours: 10,
        url: "https://www.coursera.org/specializations/statistics-with-python",
        free: false,
      },
    },
    {
      week: "WEEK 3",
      title: "Exploratory Data Visualization",
      skill: "Data Visualization & Analytics",
      description: "Communicating statistical insights clearly using Seaborn and Matplotlib.",
      course: {
        title: "Data Analysis with Python",
        provider: "freeCodeCamp",
        hours: 8,
        url: "https://www.freecodecamp.org/learn/data-analysis-with-python/",
        free: true,
      },
    },
    {
      week: "WEEK 4",
      title: "Business Intelligence & Power BI",
      skill: "Power BI",
      description: "Building interactive dashboards, dimensional modeling, and stakeholder reports.",
      course: {
        title: "Microsoft Power BI Data Analyst",
        provider: "Microsoft Learn",
        hours: 10,
        url: "https://learn.microsoft.com/en-us/credentials/certifications/data-analyst-associate/",
        free: true,
      },
    },
  ];

  return (
    <div className="flex-1 flex max-w-7xl mx-auto w-full bg-[#F7F8FA]">
      <DashboardSidebar role="candidate" />

      <main className="flex-1 p-6 sm:p-8 lg:p-10 space-y-8 bg-[#F7F8FA]">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E1E6ED]">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#172033]">
              Your learning path
            </h1>
            <p className="text-xs text-[#5E6878] mt-1">
              A structured progression timeline designed to bridge skill gaps for{" "}
              <strong className="text-[#172033]">{targetRole}</strong>.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#5E6878]">Estimated duration:</span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded bg-[#F1F4F8] text-[#172033] border border-[#E1E6ED]">
              {rawRoadmap.length > 0 ? `${rawRoadmap.length * 2} weeks` : "4-6 weeks"}
            </span>
          </div>
        </div>

        {/* Structured Timeline Progression */}
        <div className="max-w-3xl space-y-0">
          {rawRoadmap.length > 0 ? (
            rawRoadmap.map((step, idx) => (
              <div key={idx} className="relative pl-8 pb-10 last:pb-0">
                {/* Vertical timeline line */}
                {idx < rawRoadmap.length - 1 && (
                  <div className="absolute left-3.5 top-5 bottom-0 w-0.5 bg-[#CBD5E1]" />
                )}

                {/* Timeline node icon */}
                <div className="absolute left-1.5 top-1.5 w-4 h-4 rounded-full border-2 border-[#2563EB] bg-[#FFFFFF] flex items-center justify-center" />

                <div className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] space-y-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-[#2563EB]">
                      STAGE {idx + 1} • WEEK {idx * 2 + 1}–{idx * 2 + 2}
                    </span>
                    <span className="text-[#5E6878] text-[11px] flex items-center gap-1">
                      <Clock className="w-3 h-3 text-[#8A94A6]" />
                      {step.estimated_duration_weeks || "2 weeks"}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-[#172033]">
                    {step.skill}
                  </h3>

                  <p className="text-[#5E6878] leading-relaxed">
                    {step.reason || "Recommended foundational milestone."}
                  </p>

                  {step.available_learning_resources && step.available_learning_resources.length > 0 && (
                    <div className="pt-2 border-t border-[#EDF0F4] space-y-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#8A94A6] block">
                        Verified Learning Resource
                      </span>
                      {step.available_learning_resources.map((res, rIdx) => (
                        <div
                          key={rIdx}
                          className="p-3 rounded border border-[#E1E6ED] bg-[#F8FAFC] flex items-center justify-between"
                        >
                          <div>
                            <span className="font-semibold text-[#172033] block">
                              {res.title}
                            </span>
                            <span className="text-[11px] text-[#5E6878]">
                              {res.provider} • {res.estimated_hours} hrs • {res.is_free ? "Free" : "Certificate"}
                            </span>
                          </div>
                          {res.url && (
                            <a
                              href={res.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs font-semibold text-[#2563EB] hover:underline flex items-center gap-1"
                            >
                              <span>Open Course</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {step.hands_on_project && (
                    <div className="p-3 rounded bg-[#F8FAFC] border border-[#E1E6ED]">
                      <div className="flex items-center gap-1.5 font-semibold text-[#172033] mb-1">
                        <Code2 className="w-3.5 h-3.5 text-[#2563EB]" />
                        <span>Milestone Challenge</span>
                      </div>
                      <p className="text-[11px] text-[#5E6878]">
                        {step.hands_on_project}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            defaultTimeline.map((item, idx) => (
              <div key={idx} className="relative pl-8 pb-10 last:pb-0">
                {idx < defaultTimeline.length - 1 && (
                  <div className="absolute left-3.5 top-5 bottom-0 w-0.5 bg-[#CBD5E1]" />
                )}

                <div className="absolute left-1.5 top-1.5 w-4 h-4 rounded-full border-2 border-[#2563EB] bg-[#FFFFFF] flex items-center justify-center" />

                <div className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] space-y-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-[#2563EB]">
                      {item.week}
                    </span>
                    <span className="text-[#5E6878] text-[11px] flex items-center gap-1">
                      <Clock className="w-3 h-3 text-[#8A94A6]" />
                      10-12 hours
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-[#172033]">
                    {item.title}
                  </h3>

                  <p className="text-[#5E6878] leading-relaxed">
                    {item.description}
                  </p>

                  <div className="p-3 rounded border border-[#E1E6ED] bg-[#F8FAFC] flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-[#172033] block">
                        {item.course.title}
                      </span>
                      <span className="text-[11px] text-[#5E6878]">
                        {item.course.provider} • {item.course.hours} hrs • {item.course.free ? "Free" : "Certificate"}
                      </span>
                    </div>
                    <a
                      href={item.course.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-semibold text-[#2563EB] hover:underline flex items-center gap-1"
                    >
                      <span>Open Course</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </div>
            ))
          )}

          {/* FINAL CAPSTONE PROJECT */}
          <div className="relative pl-8 pt-2">
            <div className="absolute left-1.5 top-3.5 w-4 h-4 rounded-full bg-[#16805C] flex items-center justify-center" />

            <div className="p-5 rounded-lg border-2 border-[#16805C] bg-[#FFFFFF] space-y-2 text-xs">
              <span className="font-mono text-xs font-bold text-[#16805C]">
                PROJECT CAPSTONE
              </span>
              <h3 className="text-base font-bold text-[#172033]">
                Build a Portfolio Sales Analytics &amp; Prediction Dashboard
              </h3>
              <p className="text-[#5E6878] leading-relaxed">
                Integrate all acquired skills: ingest real-world transactional data, build regression models in Python, create interactive visualizations in Power BI, and write an executive summary report.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
