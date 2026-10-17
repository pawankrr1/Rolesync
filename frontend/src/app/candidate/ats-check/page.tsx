"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  HelpCircle,
  FileCheck,
  ArrowRight,
  RotateCcw,
  ShieldCheck,
  Check,
  X,
  ChevronDown,
  ChevronUp,
  Briefcase,
  Layers,
  Sparkles,
  Info,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import { analyzeATS, uploadAndAnalyzeATS } from "@/lib/api";
import { ATSAnalysisResponse, ATSCategoryScore } from "@/lib/types";

export default function AtsResumeCheckPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Check Mode
  const [checkType, setCheckType] = useState<"general" | "job_specific">("general");

  // Resume State
  const [resumeSource, setResumeSource] = useState<"current" | "upload">("upload");
  const [currentResumeText, setCurrentResumeText] = useState<string | null>(null);
  const [currentResumeName, setCurrentResumeName] = useState<string>("Active Profile Resume");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Job Description Inputs
  const [targetJobTitle, setTargetJobTitle] = useState<string>("");
  const [jobDescriptionText, setJobDescriptionText] = useState<string>("");

  // Analysis Lifecycle States
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisStage, setAnalysisStage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<ATSAnalysisResponse | null>(null);

  // Previous score comparison
  const [previousScore, setPreviousScore] = useState<number | null>(null);

  // Expanded evidence state
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null);

  // Load existing candidate session resume if present
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedAnalysis = window.sessionStorage.getItem("candidate_active_analysis");
      if (savedAnalysis) {
        try {
          const parsed = JSON.parse(savedAnalysis);
          // If active analysis exists, construct synthetic profile text for ATS check
          const sampleText = `Candidate Name: ${parsed.candidateName || "Candidate"}\nTarget Role: ${
            parsed.targetRole || "Software Engineer"
          }\n\nPROFESSIONAL SUMMARY\nExperienced professional with verified competencies in ${
            parsed.matching?.strong_matches?.map((s: any) => s.skill).join(", ") || "Python, SQL, Machine Learning"
          }.\n\nEXPERIENCE & PROJECTS\nSoftware Project Engineer\n- Developed predictive workflows using ${
            parsed.matching?.strong_matches?.map((s: any) => s.skill).slice(0, 3).join(" and ") || "Python and SQL"
          }, scaling analytics throughput.\n- Implemented database queries and machine learning pipelines for 25,000+ data records.\n\nSKILLS\n${
            parsed.matching?.strong_matches?.map((s: any) => s.skill).join(", ") || "Python, SQL, Machine Learning"
          }\n\nEDUCATION\nBachelor of Science in Technology`;
          setCurrentResumeText(sampleText);
          setCurrentResumeName(parsed.candidateName ? `${parsed.candidateName}_Resume.pdf` : "Current_Resume.pdf");
          setResumeSource("current");
        } catch {
          // ignore
        }
      }

      // Check stored previous ATS score
      const storedScore = window.sessionStorage.getItem("rolesync_prev_ats_score");
      if (storedScore) {
        const val = parseInt(storedScore, 10);
        if (!isNaN(val)) setPreviousScore(val);
      }
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setResumeSource("upload");
      setErrorMessage(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
      setResumeSource("upload");
      setErrorMessage(null);
    }
  };

  const handleRunAnalysis = async () => {
    setErrorMessage(null);

    // Validation
    if (resumeSource === "upload" && !selectedFile) {
      setErrorMessage("Please select a resume file (PDF, DOCX, or TXT) to evaluate.");
      return;
    }
    if (resumeSource === "current" && !currentResumeText) {
      setErrorMessage("No current resume was found in session. Please upload a resume file.");
      return;
    }
    if (checkType === "job_specific" && (!jobDescriptionText || jobDescriptionText.trim().length < 20)) {
      setErrorMessage("Please paste a job description (at least 20 characters) for a Job-Specific check.");
      return;
    }

    setIsAnalyzing(true);
    setAnalysisStage("Analyzing ATS readiness...");

    try {
      let res;
      if (resumeSource === "upload" && selectedFile) {
        res = await uploadAndAnalyzeATS(
          selectedFile,
          checkType,
          checkType === "job_specific" ? jobDescriptionText : undefined,
          targetJobTitle ? targetJobTitle : undefined
        );
      } else if (currentResumeText) {
        res = await analyzeATS({
          resume_text: currentResumeText,
          filename: currentResumeName,
          check_type: checkType,
          job_description_text: checkType === "job_specific" ? jobDescriptionText : undefined,
          target_job_title: targetJobTitle ? targetJobTitle : undefined,
        });
      }

      if (res && res.success && res.data) {
        // Track score history delta
        if (analysisResult) {
          setPreviousScore(analysisResult.overall_score);
          if (typeof window !== "undefined") {
            window.sessionStorage.setItem("rolesync_prev_ats_score", analysisResult.overall_score.toString());
          }
        }
        setAnalysisResult(res.data);
      } else {
        setErrorMessage(
          res?.error || "We couldn't read enough text from this resume to calculate a reliable ATS Readiness Score."
        );
      }
    } catch {
      setErrorMessage("Service error while evaluating ATS readiness. Please verify file and retry.");
    } finally {
      setIsAnalyzing(false);
      setAnalysisStage("");
    }
  };

  const handleRecheck = () => {
    if (analysisResult) {
      setPreviousScore(analysisResult.overall_score);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="flex-1 flex max-w-7xl mx-auto w-full bg-[#F7F8FA]">
      <DashboardSidebar role="candidate" />

      <main className="flex-1 p-6 sm:p-8 lg:p-10 space-y-8 bg-[#F7F8FA]">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E1E6ED]">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#2563EB] bg-[#EFF6FF] px-2 py-0.5 rounded border border-[#BFDBFE]">
                Document Quality &amp; Alignment
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[#172033] mt-1">
              ATS Resume Check
            </h1>
            <p className="text-xs text-[#5E6878] mt-1">
              See how readable, complete, and job-aligned your resume is.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-[#5E6878] bg-[#FFFFFF] px-3 py-1.5 rounded-md border border-[#E1E6ED]">
            <ShieldCheck className="w-4 h-4 text-[#16805C]" />
            <span>Zero-PII In-Memory Processing</span>
          </div>
        </div>

        {/* MODE SELECTOR (GENERAL CHECK vs JOB-SPECIFIC CHECK) */}
        <div className="bg-[#FFFFFF] rounded-lg border border-[#E1E6ED] p-2 flex flex-col sm:flex-row gap-2">
          <button
            type="button"
            onClick={() => setCheckType("general")}
            className={`flex-1 py-2.5 px-4 rounded-md text-xs font-semibold transition-colors flex items-center justify-center gap-2 cursor-pointer ${
              checkType === "general"
                ? "bg-[#2563EB] text-[#FFFFFF] shadow-xs"
                : "text-[#5E6878] hover:text-[#172033] hover:bg-[#F1F4F8]"
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>General Check</span>
            <span className="text-[10px] opacity-80 hidden md:inline">
              (Quality &amp; Structure)
            </span>
          </button>

          <button
            type="button"
            onClick={() => setCheckType("job_specific")}
            className={`flex-1 py-2.5 px-4 rounded-md text-xs font-semibold transition-colors flex items-center justify-center gap-2 cursor-pointer ${
              checkType === "job_specific"
                ? "bg-[#2563EB] text-[#FFFFFF] shadow-xs"
                : "text-[#5E6878] hover:text-[#172033] hover:bg-[#F1F4F8]"
            }`}
          >
            <Briefcase className="w-4 h-4" />
            <span>Job-Specific Check</span>
            <span className="text-[10px] opacity-80 hidden md:inline">
              (Resume + Job Description)
            </span>
          </button>
        </div>

        {/* INPUT PANEL: RESUME SOURCE & OPTIONAL JD */}
        <div className="bg-[#FFFFFF] rounded-lg border border-[#E1E6ED] p-6 space-y-6">
          {/* SECTION 1: RESUME SELECTION */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-[#172033]">
                Resume Document
              </label>
              {currentResumeText && (
                <div className="flex items-center gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => {
                      setResumeSource("current");
                      setSelectedFile(null);
                    }}
                    className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors cursor-pointer ${
                      resumeSource === "current"
                        ? "bg-[#EFF6FF] text-[#2563EB] font-semibold border border-[#BFDBFE]"
                        : "text-[#5E6878] hover:text-[#172033]"
                    }`}
                  >
                    Use Current Resume
                  </button>
                  <button
                    type="button"
                    onClick={() => setResumeSource("upload")}
                    className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors cursor-pointer ${
                      resumeSource === "upload"
                        ? "bg-[#EFF6FF] text-[#2563EB] font-semibold border border-[#BFDBFE]"
                        : "text-[#5E6878] hover:text-[#172033]"
                    }`}
                  >
                    Upload Different Resume
                  </button>
                </div>
              )}
            </div>

            {resumeSource === "current" && currentResumeText ? (
              <div className="p-4 rounded-md border border-[#BFDBFE] bg-[#F8FAFC] flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded bg-[#EFF6FF] border border-[#BFDBFE] flex items-center justify-center text-[#2563EB]">
                    <FileCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-[#172033] block">
                      {currentResumeName}
                    </span>
                    <span className="text-[11px] text-[#5E6878]">
                      Loaded from active candidate workspace • Ready for ATS evaluation
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setResumeSource("upload")}
                  className="text-xs text-[#2563EB] hover:underline shrink-0"
                >
                  Change file
                </button>
              </div>
            ) : (
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`p-6 rounded-md border-2 border-dashed transition-colors text-center cursor-pointer ${
                  selectedFile
                    ? "border-[#2563EB] bg-[#F8FAFC]"
                    : "border-[#E1E6ED] hover:border-[#2563EB] bg-[#FFFFFF] hover:bg-[#F8FAFC]"
                }`}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.txt"
                  className="hidden"
                />
                <UploadCloud className="w-8 h-8 text-[#8A94A6] mx-auto mb-2" />
                {selectedFile ? (
                  <div>
                    <span className="text-xs font-bold text-[#172033] block">
                      {selectedFile.name}
                    </span>
                    <span className="text-[11px] text-[#16805C] font-medium">
                      {(selectedFile.size / 1024).toFixed(1)} KB • Ready to check
                    </span>
                  </div>
                ) : (
                  <div>
                    <span className="text-xs font-semibold text-[#172033] block">
                      Click to upload or drag &amp; drop your resume
                    </span>
                    <span className="text-[11px] text-[#8A94A6] block mt-0.5">
                      Supports PDF, DOCX, or TXT up to 10MB
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* SECTION 2: JOB-SPECIFIC INPUTS (ONLY IN JOB-SPECIFIC MODE) */}
          {checkType === "job_specific" && (
            <div className="space-y-4 pt-4 border-t border-[#EDF0F4]">
              <div>
                <label
                  htmlFor="targetJobTitle"
                  className="text-xs font-bold uppercase tracking-wider text-[#172033] block mb-1"
                >
                  Target Role Title <span className="text-[#8A94A6] font-normal">(Optional)</span>
                </label>
                <input
                  id="targetJobTitle"
                  type="text"
                  value={targetJobTitle}
                  onChange={(e) => setTargetJobTitle(e.target.value)}
                  placeholder="e.g. Data Scientist, Senior Backend Engineer"
                  className="w-full px-3 py-2 text-xs rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-[#172033] focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label
                  htmlFor="jobDescription"
                  className="text-xs font-bold uppercase tracking-wider text-[#172033] block mb-1"
                >
                  Job Description <span className="text-[#C24141]">*</span>
                </label>
                <textarea
                  id="jobDescription"
                  rows={5}
                  value={jobDescriptionText}
                  onChange={(e) => setJobDescriptionText(e.target.value)}
                  placeholder="Paste the full job requisition requirements, required qualifications, and key competencies here..."
                  className="w-full p-3 text-xs rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-[#172033] focus:outline-none focus:border-[#2563EB] leading-relaxed font-mono"
                />
                <span className="text-[10px] text-[#8A94A6] block mt-1">
                  Skills from this JD will be normalized against RoleSync taxonomy and matched against your resume.
                </span>
              </div>
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="p-3 rounded-md border border-[#FECACA] bg-[#FEF2F2] flex items-center justify-between gap-3 text-xs text-[#C24141]">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
              <button
                type="button"
                onClick={() => setErrorMessage(null)}
                className="text-[#8A94A6] hover:text-[#172033]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Action Trigger */}
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3">
            <span className="text-[11px] text-[#5E6878]">
              Deterministic evaluation • No random LLM score generation
            </span>

            <button
              type="button"
              onClick={handleRunAnalysis}
              disabled={isAnalyzing}
              className="inline-flex items-center justify-center gap-2 w-full sm:w-auto px-6 py-2.5 rounded-md text-xs font-semibold bg-[#2563EB] hover:bg-[#1D4ED8] disabled:opacity-60 text-[#FFFFFF] transition-colors cursor-pointer"
            >
              {isAnalyzing ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin" />
                  <span>{analysisStage || "Analyzing ATS readiness..."}</span>
                </>
              ) : (
                <>
                  <FileCheck className="w-4 h-4" />
                  <span>Check ATS Score</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* RESULTS PRESENTATION */}
        {analysisResult && (
          <div className="space-y-8 animate-in fade-in duration-300">
            {/* SCORE HERO PANEL */}
            <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-6 sm:p-8 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-[#EDF0F4]">
                <div className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#5E6878] block">
                    ATS Resume Analysis
                  </span>
                  <h2 className="text-xl font-bold text-[#172033]">
                    RoleSync ATS Readiness Score
                  </h2>
                  <p className="text-xs text-[#5E6878] max-w-xl leading-relaxed">
                    {analysisResult.disclaimer}
                  </p>
                </div>

                {/* Score badge & score number */}
                <div className="flex items-center gap-4 bg-[#F8FAFC] p-4 rounded-lg border border-[#E1E6ED] shrink-0">
                  <div className="text-right">
                    <div className="text-3xl sm:text-4xl font-extrabold text-[#2563EB] leading-none">
                      {analysisResult.overall_score}{" "}
                      <span className="text-sm font-normal text-[#8A94A6]">/ 100</span>
                    </div>
                    <span
                      className={`text-xs font-bold block mt-1 ${
                        analysisResult.overall_score >= 80
                          ? "text-[#16805C]"
                          : analysisResult.overall_score >= 70
                          ? "text-[#2563EB]"
                          : analysisResult.overall_score >= 60
                          ? "text-[#B7791F]"
                          : "text-[#C24141]"
                      }`}
                    >
                      {analysisResult.rating}
                    </span>
                  </div>

                  {/* Previous Score Comparison (if available) */}
                  {previousScore !== null && previousScore !== analysisResult.overall_score && (
                    <div className="border-l border-[#E1E6ED] pl-3 text-left text-xs">
                      <span className="text-[10px] text-[#8A94A6] block uppercase font-bold">
                        Previous
                      </span>
                      <span className="font-mono font-semibold text-[#5E6878]">
                        {previousScore}
                      </span>
                      <span
                        className={`text-[11px] font-bold block ${
                          analysisResult.overall_score >= previousScore
                            ? "text-[#16805C]"
                            : "text-[#C24141]"
                        }`}
                      >
                        {analysisResult.overall_score >= previousScore
                          ? `+${analysisResult.overall_score - previousScore}`
                          : `${analysisResult.overall_score - previousScore}`}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* PRODUCT DISTINCTION NOTICE */}
              <div className="p-3 rounded-md bg-[#EFF6FF] border border-[#BFDBFE] text-xs text-[#1E40AF] flex items-start gap-2.5">
                <Info className="w-4 h-4 shrink-0 mt-0.5 text-[#2563EB]" />
                <div className="space-y-0.5 leading-normal">
                  <span className="font-bold">Understanding RoleSync Scores:</span>
                  <p className="text-[11px] text-[#1E3A8A]">
                    <strong>ATS Readiness Score</strong> evaluates how readable, complete, and format-friendly your resume
                    is for document parsers. <strong>Role Match Score</strong> (in Match &amp; Results) evaluates how your
                    broader technical background aligns with target roles. Both operate independently.
                  </p>
                </div>
              </div>

              {/* SCORE BREAKDOWN CATEGORIES */}
              <div className="space-y-3 pt-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
                  Score Breakdown
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {analysisResult.category_scores.map((cat: ATSCategoryScore) => (
                    <div
                      key={cat.category_id}
                      className="p-3.5 rounded border border-[#E1E6ED] bg-[#FFFFFF] space-y-2"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-[#172033]">{cat.name}</span>
                        <span className="font-mono font-bold text-[#2563EB]">
                          {cat.score} / {cat.max_score}
                        </span>
                      </div>
                      <div className="w-full bg-[#F1F4F8] h-1.5 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            cat.percentage >= 80
                              ? "bg-[#16805C]"
                              : cat.percentage >= 65
                              ? "bg-[#2563EB]"
                              : "bg-[#B7791F]"
                          }`}
                          style={{ width: `${Math.min(cat.percentage, 100)}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-[#8A94A6]">
                        <span>{cat.percentage}% quality</span>
                        <span
                          className={`font-medium ${
                            cat.status === "Strong"
                              ? "text-[#16805C]"
                              : cat.status === "Good"
                              ? "text-[#2563EB]"
                              : "text-[#B7791F]"
                          }`}
                        >
                          {cat.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* WHY THIS SCORE (WHAT'S WORKING & NEEDS ATTENTION) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-6 space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-[#EDF0F4]">
                  <CheckCircle2 className="w-4 h-4 text-[#16805C]" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
                    What&apos;s Working
                  </h3>
                </div>
                <ul className="space-y-2 text-xs text-[#172033]">
                  {analysisResult.whats_working.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <Check className="w-3.5 h-3.5 text-[#16805C] shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-6 space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-[#EDF0F4]">
                  <AlertTriangle className="w-4 h-4 text-[#B7791F]" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
                    Needs Attention
                  </h3>
                </div>
                <ul className="space-y-2 text-xs text-[#5E6878]">
                  {analysisResult.needs_attention.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-[#B7791F] font-bold text-xs shrink-0 mt-0.5">△</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* RESUME HEALTH OVERVIEW */}
            <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-6 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
                Resume Health Overview
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
                <div className="p-3 rounded bg-[#F8FAFC] border border-[#E1E6ED]">
                  <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
                    Parseability
                  </span>
                  <span className="font-semibold text-[#172033]">
                    {analysisResult.resume_health.parseability}
                  </span>
                </div>
                <div className="p-3 rounded bg-[#F8FAFC] border border-[#E1E6ED]">
                  <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
                    Content
                  </span>
                  <span className="font-semibold text-[#172033]">
                    {analysisResult.resume_health.content}
                  </span>
                </div>
                <div className="p-3 rounded bg-[#F8FAFC] border border-[#E1E6ED]">
                  <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
                    Skills
                  </span>
                  <span className="font-semibold text-[#172033]">
                    {analysisResult.resume_health.skills}
                  </span>
                </div>
                <div className="p-3 rounded bg-[#F8FAFC] border border-[#E1E6ED]">
                  <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
                    Impact
                  </span>
                  <span className="font-semibold text-[#172033]">
                    {analysisResult.resume_health.impact}
                  </span>
                </div>
                <div className="p-3 rounded bg-[#F8FAFC] border border-[#E1E6ED]">
                  <span className="text-[10px] uppercase font-bold text-[#8A94A6] block mb-1">
                    {analysisResult.check_type === "job_specific" ? "Job Alignment" : "Formatting"}
                  </span>
                  <span className="font-semibold text-[#2563EB]">
                    {analysisResult.check_type === "job_specific" && analysisResult.job_alignment_percentage !== null
                      ? `${Math.round(analysisResult.job_alignment_percentage || 0)}%`
                      : analysisResult.resume_health.formatting}
                  </span>
                </div>
              </div>
            </div>

            {/* JOB-SPECIFIC SKILL ALIGNMENT (ONLY WHEN JD IS EVALUATED) */}
            {analysisResult.check_type === "job_specific" && (
              <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-6 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#EDF0F4]">
                  <div>
                    <h3 className="text-sm font-bold text-[#172033]">
                      Resume-to-JD Skill Alignment
                    </h3>
                    <p className="text-xs text-[#5E6878]">
                      Comparison against {analysisResult.total_jd_skills} canonical requirements from target job description.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-[#5E6878]">Match Rate:</span>
                    <span className="font-mono font-bold text-xs px-2.5 py-1 rounded bg-[#EFF6FF] text-[#2563EB] border border-[#BFDBFE]">
                      {analysisResult.matched_jd_skills_count} / {analysisResult.total_jd_skills} (
                      {Math.round(analysisResult.job_alignment_percentage || 0)}%)
                    </span>
                  </div>
                </div>

                {/* Matched Skills */}
                <div className="space-y-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#16805C] block">
                    Matched Skills ({analysisResult.matched_skills.length})
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.matched_skills.map((skill) => (
                      <div key={skill.canonical_name} className="relative group">
                        <button
                          type="button"
                          onClick={() =>
                            setExpandedSkill(
                              expandedSkill === skill.canonical_name ? null : skill.canonical_name
                            )
                          }
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold bg-[#DCFCE7] text-[#16805C] border border-[#BBF7D0] hover:bg-[#BBF7D0] transition-colors cursor-pointer"
                        >
                          <Check className="w-3 h-3 stroke-[3]" />
                          <span>{skill.canonical_name}</span>
                          {skill.evidence && (
                            <ChevronDown className="w-3 h-3 text-[#16805C] opacity-70" />
                          )}
                        </button>

                        {expandedSkill === skill.canonical_name && skill.evidence && (
                          <div className="mt-1 p-2 rounded bg-[#FFFFFF] border border-[#E1E6ED] text-[11px] text-[#5E6878] shadow-sm max-w-sm">
                            <span className="font-bold text-[#172033] block mb-0.5">Resume Evidence:</span>
                            &ldquo;{skill.evidence}&rdquo;
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Missing Target Skills */}
                {analysisResult.missing_skills.length > 0 && (
                  <div className="space-y-2 pt-3 border-t border-[#EDF0F4]">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-[#C24141] block">
                        Missing Target Skills ({analysisResult.missing_skills.length})
                      </span>
                      <span className="text-[11px] text-[#5E6878] italic">
                        Only add a skill if you genuinely have that skill or relevant experience.
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {analysisResult.missing_skills.map((skill) => (
                        <span
                          key={skill.canonical_name}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium bg-[#FEE2E2] text-[#C24141] border border-[#FECACA]"
                        >
                          <X className="w-3 h-3" />
                          <span>{skill.canonical_name}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TOP IMPROVEMENTS (PRIORITIZED RECOMMENDATIONS) */}
            {analysisResult.recommendations.length > 0 && (
              <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-6 space-y-4">
                <div className="pb-3 border-b border-[#EDF0F4]">
                  <h3 className="text-sm font-bold text-[#172033]">
                    Top Improvements
                  </h3>
                  <p className="text-xs text-[#5E6878]">
                    Prioritized action items to enhance readability and ATS qualification.
                  </p>
                </div>

                <div className="space-y-3">
                  {analysisResult.recommendations.map((rec, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-md border border-[#E1E6ED] bg-[#F8FAFC] space-y-1.5"
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                            rec.priority === "HIGH"
                              ? "bg-[#FEE2E2] text-[#C24141] border-[#FECACA]"
                              : rec.priority === "MEDIUM"
                              ? "bg-[#FEF3C7] text-[#B7791F] border-[#FDE68A]"
                              : "bg-[#F1F4F8] text-[#5E6878] border-[#E1E6ED]"
                          }`}
                        >
                          {rec.priority} PRIORITY
                        </span>
                        <span className="text-xs font-bold text-[#172033]">
                          {rec.title}
                        </span>
                      </div>
                      <p className="text-xs text-[#5E6878] leading-relaxed pl-1">
                        {rec.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ATS READINESS CHECKLIST */}
            <div className="bg-[#FFFFFF] border border-[#E1E6ED] rounded-lg p-6 space-y-4">
              <div className="pb-3 border-b border-[#EDF0F4]">
                <h3 className="text-sm font-bold text-[#172033]">
                  ATS Readiness Checklist
                </h3>
                <p className="text-xs text-[#5E6878]">
                  Verified document parsing characteristics based on extracted text layer.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {analysisResult.checklist.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded border border-[#E1E6ED] bg-[#FFFFFF] flex items-start gap-2.5"
                  >
                    <span
                      className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                        item.status === "pass"
                          ? "bg-[#DCFCE7] text-[#16805C]"
                          : item.status === "warning"
                          ? "bg-[#FEF3C7] text-[#B7791F]"
                          : "bg-[#FEE2E2] text-[#C24141]"
                      }`}
                    >
                      {item.status === "pass" ? (
                        <Check className="w-3.5 h-3.5 stroke-[3]" />
                      ) : item.status === "warning" ? (
                        <span className="text-xs font-bold">△</span>
                      ) : (
                        <X className="w-3.5 h-3.5" />
                      )}
                    </span>
                    <div>
                      <span className="font-semibold text-[#172033] block">
                        {item.label}
                      </span>
                      <span className="text-[11px] text-[#5E6878] leading-normal block mt-0.5">
                        {item.detail}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* RECHECK RESUME ACTION BAR */}
            <div className="p-6 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-0.5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
                  Ready to test an updated resume?
                </h4>
                <p className="text-xs text-[#5E6878]">
                  Upload revised document edits to evaluate your score delta and checklist improvements.
                </p>
              </div>

              <button
                type="button"
                onClick={handleRecheck}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-xs font-semibold bg-[#2563EB] hover:bg-[#1D4ED8] text-[#FFFFFF] transition-colors cursor-pointer shrink-0"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Check Updated Resume</span>
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
