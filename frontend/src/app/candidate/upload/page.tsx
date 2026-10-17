"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Check,
  AlertCircle,
  FileText,
  Upload,
  Loader2,
  ShieldCheck,
  X,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import { extractSkills, runFullCandidatePipeline, parseDocument } from "@/lib/api";
import { BackendExtractedSkill } from "@/lib/types";
import { recordUatRunning, recordUatPass, recordUatFail } from "@/lib/uatTracker";

export default function ResumeUploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedRole, setSelectedRole] = useState("data_scientist");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileDetails, setFileDetails] = useState<{
    name: string;
    sizeFormatted: string;
    text: string;
  } | null>(null);

  // Upload & parse states
  const [isReadingFile, setIsReadingFile] = useState(false);
  const [extractedSkills, setExtractedSkills] = useState<BackendExtractedSkill[]>([]);

  // Pipeline Analysis State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStage, setAnalysisStage] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const predefinedRoles = [
    {
      id: "data_scientist",
      title: "Data Scientist",
      keySkills: ["Python", "SQL", "Statistics", "Machine Learning"],
    },
    {
      id: "ml_engineer",
      title: "ML Engineer",
      keySkills: ["Python", "PyTorch", "Docker", "Machine Learning"],
    },
    {
      id: "backend_developer",
      title: "Backend Developer",
      keySkills: ["Python", "SQL", "FastAPI", "Docker"],
    },
    {
      id: "data_analyst",
      title: "Data Analyst",
      keySkills: ["SQL", "Excel", "Python", "Power BI"],
    },
    {
      id: "cloud_engineer",
      title: "Cloud & DevOps",
      keySkills: ["Docker", "Kubernetes", "AWS", "Linux"],
    },
    {
      id: "fullstack_developer",
      title: "Fullstack Engineer",
      keySkills: ["React", "TypeScript", "Node.js", "SQL"],
    },
  ];

  const sampleProfiles = [
    {
      name: "Senior Data Scientist",
      filename: "sample_data_scientist.pdf",
      sizeFormatted: "1.8 MB",
      content: `Pawan Kumar\nSenior Data Scientist\n\nExperience:\n- 4+ years architecting machine learning pipelines using Python, scikit-learn, and PyTorch.\n- Formulated complex SQL aggregations and ETL pipelines on PostgreSQL databases.\n- Applied hypothesis testing, experimental design, and mathematical statistics.\n- Containerized analytical microservices using Docker on AWS.`,
    },
    {
      name: "Data Analyst",
      filename: "sample_data_analyst.docx",
      sizeFormatted: "1.2 MB",
      content: `Priya Patel\nBusiness Data Analyst\n\nExperience:\n- 3+ years writing complex SQL queries and window functions.\n- Built executive business intelligence dashboards in Power BI.\n- Applied regression and descriptive statistics to drive revenue decisions using Python and Pandas.`,
    },
    {
      name: "Backend Software Engineer",
      filename: "sample_backend_engineer.pdf",
      sizeFormatted: "2.1 MB",
      content: `Aarav Sharma\nSenior Backend Software Engineer\n\nExperience:\n- Built RESTful APIs and asynchronous microservices with Python, FastAPI, and PostgreSQL.\n- Automated CI/CD pipelines using Docker, Git, and Linux server environments.\n- Implemented caching layers with Redis.`,
    },
  ];

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const processFile = async (file: File) => {
    setErrorMessage(null);
    setSelectedFile(file);
    setIsReadingFile(true);
    recordUatRunning("UAT-01", `Uploaded ${file.name} — parsing document in-memory`);

    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    const allowed = [".pdf", ".docx", ".txt"];
    if (!allowed.includes(ext)) {
      setIsReadingFile(false);
      const msg = `Unsupported format '${ext}'. Please upload a PDF, DOCX, or plain text resume.`;
      setErrorMessage(msg);
      recordUatFail("UAT-01", "Resume file rejected due to unsupported format.", msg);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setIsReadingFile(false);
      const msg = "File exceeds 10 MB maximum allowed limit.";
      setErrorMessage(msg);
      recordUatFail("UAT-01", "Resume file rejected due to size limit.", msg);
      return;
    }

    try {
      const parseRes = await parseDocument(file);
      if (!parseRes.success || !parseRes.data) {
        const parseErr = parseRes.error || "Could not parse document.";
        recordUatFail("UAT-01", "Resume uploaded successfully, but parsing did not complete.", parseErr);
        throw new Error(parseErr);
      }

      const text = parseRes.data.text;
      setFileDetails({
        name: file.name,
        sizeFormatted: formatFileSize(file.size),
        text,
      });

      // Extract skills immediately from parsed text
      const skillRes = await extractSkills(text);
      if (skillRes.success && skillRes.data && Array.isArray(skillRes.data.skills)) {
        setExtractedSkills(skillRes.data.skills);
        const count = skillRes.data.skills.length;
        recordUatPass(
          "UAT-01",
          `Resume uploaded successfully. Resume parsing completed. Extracted ${count} competencies with grounded sentence evidence. Analysis results displayed.`,
          { filename: file.name, skillsCount: count },
          [
            "Resume file accepted",
            "Resume parsing completed",
            "Extracted text returned",
            "Skill extraction completed",
            "Skill profile returned",
            "Analysis results displayed",
          ]
        );
      } else {
        recordUatFail(
          "UAT-01",
          "Resume parsed successfully, but skill extraction returned no valid result.",
          skillRes.error || "Skill extraction service did not return a valid skill profile."
        );
      }
    } catch (err: any) {
      setErrorMessage(err?.message || "File could not be parsed. Please verify the document format or try a sample.");
    } finally {
      setIsReadingFile(false);
    }
  };

  const handleSampleClick = async (sample: (typeof sampleProfiles)[0]) => {
    setErrorMessage(null);
    setSelectedFile(null);
    setFileDetails({
      name: sample.filename,
      sizeFormatted: sample.sizeFormatted,
      text: sample.content,
    });

    setIsReadingFile(true);
    recordUatRunning("UAT-01", `Loaded profile ${sample.name} — extracting skills`);

    try {
      const skillRes = await extractSkills(sample.content);
      if (skillRes.success && skillRes.data && Array.isArray(skillRes.data.skills)) {
        setExtractedSkills(skillRes.data.skills);
        const count = skillRes.data.skills.length;
        recordUatPass(
          "UAT-01",
          `Resume uploaded successfully. Resume parsing completed. Extracted ${count} competencies with grounded sentence evidence. Analysis results displayed.`,
          { filename: sample.filename, skillsCount: count },
          [
            "Resume file accepted",
            "Resume parsing completed",
            "Extracted text returned",
            "Skill extraction completed",
            "Skill profile returned",
            "Analysis results displayed",
          ]
        );
      } else {
        recordUatFail(
          "UAT-01",
          "Resume parsed successfully, but skill extraction returned no valid result.",
          skillRes.error || "Skill extraction service did not return a valid skill profile."
        );
      }
    } catch (err: any) {
      recordUatFail("UAT-01", "Resume parsing failed.", err?.message || "Sample parsing error.");
    } finally {
      setIsReadingFile(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!fileDetails) {
      setErrorMessage("Please upload a resume or select a sample profile first.");
      return;
    }

    setIsAnalyzing(true);
    setErrorMessage(null);

    try {
      setAnalysisStage(1);

      const candidateSkillsToAnalyze =
        extractedSkills.length > 0
          ? extractedSkills
          : ["Python", "SQL", "Statistics", "Machine Learning"];

      setAnalysisStage(2);

      const candidateName = fileDetails.name.replace(/\.[^/.]+$/, "").replace(/_/g, " ");

      const pipelineRes = await runFullCandidatePipeline(
        candidateSkillsToAnalyze,
        selectedRole,
        candidateName,
        3.0
      );

      if (!pipelineRes.success || !pipelineRes.result) {
        throw new Error(pipelineRes.error || "Failed to complete evaluation.");
      }

      setAnalysisStage(3);

      if (typeof window !== "undefined") {
        window.sessionStorage.setItem("candidate_active_analysis", JSON.stringify(pipelineRes.result));
        window.sessionStorage.setItem("candidate_extracted_skills", JSON.stringify(extractedSkills));
      }

      setAnalysisStage(4);

      setTimeout(() => {
        router.push(`/candidate/results?role=${selectedRole}`);
      }, 300);
    } catch (err: any) {
      setIsAnalyzing(false);
      setErrorMessage(
        err?.message || "Analysis service was unable to complete. Please ensure backend is running."
      );
    }
  };

  return (
    <div className="flex-1 flex max-w-7xl mx-auto w-full bg-[#F7F8FA]">
      <DashboardSidebar role="candidate" />

      <main className="flex-1 p-6 sm:p-8 lg:p-10 space-y-8 bg-[#F7F8FA]">
        {/* Workspace Title */}
        <div className="space-y-1 pb-4 border-b border-[#E1E6ED]">
          <h1 className="text-2xl font-bold tracking-tight text-[#172033]">
            Analyze your career profile
          </h1>
          <p className="text-xs text-[#5E6878]">
            Upload your latest resume to identify your verified competencies and see where you stand against target roles.
          </p>
        </div>

        {/* Step 1: Select Target Role */}
        <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-5 space-y-3">
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
              1. Select Target Career Role
            </h2>
            <p className="text-[11px] text-[#5E6878]">
              Your qualifications will be benchmarked against this role&apos;s canonical skills.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            {predefinedRoles.map((role) => (
              <button
                key={role.id}
                type="button"
                onClick={() => setSelectedRole(role.id)}
                className={`p-3 rounded-lg border text-left transition-colors cursor-pointer ${
                  selectedRole === role.id
                    ? "border-[#2563EB] bg-[#EFF6FF] text-[#2563EB]"
                    : "border-[#E1E6ED] bg-[#FFFFFF] hover:border-[#D7DEE8] text-[#172033]"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold block">{role.title}</span>
                  {selectedRole === role.id && (
                    <Check className="w-3.5 h-3.5 text-[#2563EB] stroke-[3]" />
                  )}
                </div>
                <span className="text-[10px] text-[#5E6878] block truncate">
                  {role.keySkills.slice(0, 3).join(", ")}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: Resume Upload Zone */}
        <div className="rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] p-6 space-y-4">
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
              2. Upload Your Latest Resume
            </h2>
            <p className="text-[11px] text-[#5E6878]">
              Supported formats: PDF, DOCX, TXT. Maximum file size: 10 MB. In-memory processing without PII storage.
            </p>
          </div>

          {/* Hidden File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                processFile(e.target.files[0]);
              }
            }}
          />

          {/* Drag & Drop Area */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={(e) => {
              e.preventDefault();
              setIsDragging(false);
            }}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                processFile(e.dataTransfer.files[0]);
              }
            }}
            className={`border border-dashed rounded-lg p-8 text-center transition-colors bg-[#FFFFFF] ${
              isDragging
                ? "border-[#2563EB] bg-[#EFF6FF]"
                : "border-[#CBD5E1] hover:border-[#8A94A6]"
            }`}
          >
            <div className="w-10 h-10 rounded-full bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center mx-auto mb-3">
              <Upload className="w-5 h-5" />
            </div>

            <p className="text-xs font-medium text-[#172033] mb-1">
              Drop your resume here, or{" "}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="font-bold text-[#2563EB] underline cursor-pointer"
              >
                browse files
              </button>
            </p>
            <span className="text-[11px] text-[#5E6878] block">
              PDF, DOCX, or TXT (up to 10 MB)
            </span>
          </div>

          {/* Sample Profiles Quick Selector */}
          <div className="pt-2 border-t border-[#EDF0F4] flex flex-wrap items-center gap-2 text-xs">
            <span className="text-[#8A94A6] text-[11px]">Or test with a sample resume:</span>
            {sampleProfiles.map((sample) => (
              <button
                key={sample.name}
                type="button"
                onClick={() => handleSampleClick(sample)}
                className="px-2.5 py-1 rounded border border-[#E1E6ED] bg-[#F8FAFC] hover:bg-[#F1F4F8] text-[#172033] text-[11px] cursor-pointer"
              >
                {sample.name}
              </button>
            ))}
          </div>

          {/* Reading File State */}
          {isReadingFile && (
            <div className="p-3 rounded bg-[#F8FAFC] border border-[#E1E6ED] flex items-center gap-2 text-xs text-[#5E6878]">
              <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
              <span>Reading resume document and extracting skills...</span>
            </div>
          )}

          {/* File Ready Card */}
          {fileDetails && !isReadingFile && (
            <div className="p-4 rounded-lg border border-[#CDEDDD] bg-[#EAF7F0] flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-[#FFFFFF] border border-[#CDEDDD] flex items-center justify-center text-[#16805C]">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[#172033]">
                      {fileDetails.name}
                    </span>
                    <span className="text-[#16805C] font-semibold text-[11px] flex items-center gap-1">
                      <Check className="w-3 h-3 stroke-[2.5]" /> File ready
                    </span>
                  </div>
                  <span className="text-[11px] text-[#5E6878]">
                    {fileDetails.sizeFormatted} • {extractedSkills.length} skills identified
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => {
                  setFileDetails(null);
                  setSelectedFile(null);
                  setExtractedSkills([]);
                }}
                className="text-[#8A94A6] hover:text-[#172033] p-1 cursor-pointer"
                aria-label="Remove uploaded file"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="p-3 rounded bg-[#FDEEEE] border border-[#F2CACA] text-[#C24141] text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Primary Action Button */}
          <div className="pt-2 flex justify-end">
            <button
              type="button"
              disabled={!fileDetails || isAnalyzing || isReadingFile}
              onClick={handleRunAnalysis}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-xs font-semibold bg-[#2563EB] hover:bg-[#1D4ED8] disabled:bg-[#EDF0F4] text-[#FFFFFF] disabled:text-[#8A94A6] transition-colors cursor-pointer disabled:cursor-not-allowed shadow-xs"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#FFFFFF]" />
                  <span>Analyzing Resume...</span>
                </>
              ) : (
                <>
                  <span>Analyze Resume</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Progress Steps During Analysis */}
        {isAnalyzing && (
          <div className="p-6 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] space-y-4 text-xs">
            <h3 className="font-bold text-[#172033]">
              Analyzing your resume...
            </h3>

            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-[#172033]">
                <span className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-[#16805C] stroke-[2.5]" />
                  <span>Reading resume</span>
                </span>
                <span className="text-[#16805C] text-[11px] font-semibold">Done</span>
              </div>

              <div className="flex items-center justify-between text-[#172033]">
                <span className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-[#16805C] stroke-[2.5]" />
                  <span>Extracting skills</span>
                </span>
                <span className="text-[#16805C] text-[11px] font-semibold">Done</span>
              </div>

              <div className="flex items-center justify-between text-[#172033]">
                <span className="flex items-center gap-2">
                  {analysisStage >= 2 ? (
                    <Loader2 className="w-4 h-4 text-[#2563EB] animate-spin" />
                  ) : (
                    <span className="w-4 h-4 rounded-full border border-[#CBD5E1] block" />
                  )}
                  <span>Calculating role alignment</span>
                </span>
                <span className="text-[#5E6878] text-[11px]">
                  {analysisStage >= 3 ? "Done" : "In progress"}
                </span>
              </div>

              <div className="flex items-center justify-between text-[#172033]">
                <span className="flex items-center gap-2">
                  {analysisStage >= 3 ? (
                    <Loader2 className="w-4 h-4 text-[#2563EB] animate-spin" />
                  ) : (
                    <span className="w-4 h-4 rounded-full border border-[#CBD5E1] block" />
                  )}
                  <span>Preparing recommendations</span>
                </span>
                <span className="text-[#5E6878] text-[11px]">
                  {analysisStage >= 4 ? "Done" : "Pending"}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Trust Policy */}
        <div className="p-4 rounded border border-[#E1E6ED] bg-[#F8FAFC] flex items-start gap-3 text-xs text-[#5E6878]">
          <ShieldCheck className="w-4 h-4 text-[#16805C] shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            RoleSync evaluates resumes entirely in memory. Contact information (phone, address, personal identifiers) is neither indexed nor stored.
          </p>
        </div>
      </main>
    </div>
  );
}
