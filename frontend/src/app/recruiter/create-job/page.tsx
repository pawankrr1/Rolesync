"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Briefcase,
  Sparkles,
  ArrowRight,
  Plus,
  X,
  ArrowLeftRight,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileText,
} from "lucide-react";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import { parseJobDescription, createRecruiterJob } from "@/lib/api";

export default function CreateJobPage() {
  const router = useRouter();

  const [title, setTitle] = useState("Data Analyst");
  const [company, setCompany] = useState("RetailPulse Analytics (Demo)");
  const [location, setLocation] = useState("Pune, Maharashtra");
  const [experienceMin, setExperienceMin] = useState(2);
  const [employmentType, setEmploymentType] = useState("Full-time");
  const [jdText, setJdText] = useState(
    "We are looking for a Data Analyst with strong SQL, Python, Excel, and statistical analysis skills. Experience with Power BI and Tableau for executive dashboarding is preferred."
  );

  const [requiredSkills, setRequiredSkills] = useState<string[]>([
    "SQL",
    "Python",
    "Excel",
    "Statistics & Probability",
  ]);
  const [preferredSkills, setPreferredSkills] = useState<string[]>([
    "Power BI",
    "Tableau",
  ]);

  const [isExtracting, setIsExtracting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [newSkillInput, setNewSkillInput] = useState("");
  const [skillTargetType, setSkillTargetType] = useState<"required" | "preferred">("required");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const presetTemplates: Record<string, { title: string; text: string; reqs: string[]; prefs: string[]; exp: number }> = {
    "Data Analyst": {
      title: "Data Analyst",
      text: "We are looking for a Data Analyst with strong SQL, Python, Excel, and statistical analysis skills. Experience with Power BI and Tableau for executive dashboarding is preferred.",
      reqs: ["SQL", "Python", "Excel", "Statistics & Probability"],
      prefs: ["Power BI", "Tableau"],
      exp: 2,
    },
    "Machine Learning Specialist": {
      title: "Machine Learning Specialist",
      text: "Seeking a Machine Learning Engineer to design scalable deep learning models. Required: Python, Machine Learning, PyTorch, Scikit-Learn, and Docker. Experience with Kubernetes, LLMs, and AWS cloud pipelines is preferred.",
      reqs: ["Python", "Machine Learning", "PyTorch", "Scikit-Learn", "Docker"],
      prefs: ["Kubernetes", "AWS", "LLMs"],
      exp: 3,
    },
    "Senior Backend Engineer": {
      title: "Senior Backend Engineer",
      text: "Architect high-performance payment APIs and distributed microservices. Required: Python, FastAPI, PostgreSQL, and Docker. Experience with Redis, Kubernetes, and Linux CI/CD is preferred.",
      reqs: ["Python", "FastAPI", "PostgreSQL", "Docker"],
      prefs: ["Redis", "Kubernetes", "Linux"],
      exp: 4,
    },
  };

  const handleApplyPreset = (key: string) => {
    const p = presetTemplates[key];
    if (p) {
      setTitle(p.title);
      setJdText(p.text);
      setRequiredSkills(p.reqs);
      setPreferredSkills(p.prefs);
      setExperienceMin(p.exp);
      setErrorMessage(null);
    }
  };

  const handleExtractSkills = async () => {
    if (!jdText.trim()) {
      setErrorMessage("Please paste job description text before extracting skills.");
      return;
    }
    setIsExtracting(true);
    setErrorMessage(null);
    try {
      const res = await parseJobDescription(jdText, title);
      if (res.success && res.data) {
        setRequiredSkills(res.data.required_skills);
        setPreferredSkills(res.data.preferred_skills);
      } else {
        setErrorMessage(res.error || "Unable to extract skills from this job description.");
      }
    } catch {
      setErrorMessage("An unexpected error occurred during skill extraction.");
    } finally {
      setIsExtracting(false);
    }
  };

  const handleRemoveRequired = (skill: string) => {
    setRequiredSkills(requiredSkills.filter((s) => s !== skill));
  };

  const handleRemovePreferred = (skill: string) => {
    setPreferredSkills(preferredSkills.filter((s) => s !== skill));
  };

  const handleMoveToPreferred = (skill: string) => {
    handleRemoveRequired(skill);
    if (!preferredSkills.includes(skill)) {
      setPreferredSkills([...preferredSkills, skill]);
    }
  };

  const handleMoveToRequired = (skill: string) => {
    handleRemovePreferred(skill);
    if (!requiredSkills.includes(skill)) {
      setRequiredSkills([...requiredSkills, skill]);
    }
  };

  const handleAddManualSkill = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = newSkillInput.trim();
    if (!clean) return;

    if (skillTargetType === "required") {
      if (!requiredSkills.includes(clean)) {
        setRequiredSkills([...requiredSkills, clean]);
      }
    } else {
      if (!preferredSkills.includes(clean)) {
        setPreferredSkills([...preferredSkills, clean]);
      }
    }
    setNewSkillInput("");
  };

  const handleSaveJob = async () => {
    if (!title.trim()) {
      setErrorMessage("Job title is required.");
      return;
    }
    if (!jdText.trim()) {
      setErrorMessage("Job description is required.");
      return;
    }
    if (requiredSkills.length === 0) {
      setErrorMessage("Please specify at least one required skill.");
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    try {
      const res = await createRecruiterJob({
        title,
        company,
        location,
        experience_years_min: Number(experienceMin),
        description: jdText,
        required_skills: requiredSkills,
        preferred_skills: preferredSkills,
        employment_type: employmentType,
      });

      if (res.success && res.data) {
        setSuccessMessage(`Role "${title}" created and persisted to database!`);
        setTimeout(() => {
          router.push(`/recruiter/matches?role=${encodeURIComponent(title)}`);
        }, 1200);
      } else {
        setErrorMessage(res.error || "Failed to persist job requisition.");
      }
    } catch {
      setErrorMessage("An unexpected network error occurred while saving the role.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F8FA] flex flex-col">
      <div className="flex flex-1">
        <DashboardSidebar role="recruiter" />

        <main className="flex-1 p-6 lg:p-8 max-w-5xl mx-auto w-full space-y-6">
          {/* Header */}
          <div className="pb-3 border-b border-[#E1E6ED]">
            <div className="flex items-center gap-2 text-xs text-[#5E6878]">
              <Link href="/recruiter" className="hover:text-[#2563EB]">
                Hiring Intelligence
              </Link>
              <span>/</span>
              <span className="text-[#172033] font-semibold">Create Job</span>
            </div>
            <h1 className="text-2xl font-bold text-[#172033] mt-2 tracking-tight">
              Create New Role Requisition
            </h1>
            <p className="text-xs text-[#5E6878] mt-1">
              Paste your complete job description to automatically extract, normalize, and classify required vs. preferred skills.
            </p>
          </div>

          {/* Feedback messages */}
          {errorMessage && (
            <div className="p-3 rounded-md border border-[#F2CACA] bg-[#FDEEEE] text-xs text-[#C24141] flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div className="p-3 rounded-md border border-[#CDEDDD] bg-[#EAF7F0] text-xs text-[#16805C] flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMessage} Redirecting to candidate matching...</span>
            </div>
          )}

          {/* Job Details Card */}
          <div className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs space-y-4">
            <h2 className="text-sm font-bold text-[#172033] border-b border-[#EDF0F4] pb-2">
              Role Specification
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-[#172033] mb-1">
                  Job Title *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Senior Data Analyst"
                  className="w-full px-3 py-2 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033] focus:outline-hidden focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#172033] mb-1">
                  Company / Organization
                </label>
                <input
                  type="text"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="e.g. Acme Tech Solutions"
                  className="w-full px-3 py-2 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033] focus:outline-hidden focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#172033] mb-1">
                  Location
                </label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Bengaluru / Remote"
                  className="w-full px-3 py-2 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033] focus:outline-hidden focus:border-[#2563EB]"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-[#172033] mb-1">
                    Min. Experience (Yrs)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={20}
                    value={experienceMin}
                    onChange={(e) => setExperienceMin(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033] focus:outline-hidden focus:border-[#2563EB]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#172033] mb-1">
                    Employment Type
                  </label>
                  <select
                    value={employmentType}
                    onChange={(e) => setEmploymentType(e.target.value)}
                    className="w-full px-3 py-2 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033] focus:outline-hidden focus:border-[#2563EB]"
                  >
                    <option value="Full-time">Full-time</option>
                    <option value="Contract">Contract</option>
                    <option value="Internship">Internship</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Job Description Input & Extraction */}
          <div className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#EDF0F4] pb-2">
              <h2 className="text-sm font-bold text-[#172033]">
                Job Description Text
              </h2>
              <div className="flex items-center gap-1.5 text-xs text-[#5E6878]">
                <span className="text-[11px]">Quick Templates:</span>
                {Object.keys(presetTemplates).map((key) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => handleApplyPreset(key)}
                    className="px-2 py-0.5 rounded text-[10px] bg-[#F1F4F8] hover:bg-[#E1E6ED] text-[#172033] transition-colors"
                  >
                    {key}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <textarea
                rows={5}
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the full job description or requisition here..."
                className="w-full p-3 rounded-md border border-[#E1E6ED] bg-[#F8FAFC] text-xs text-[#172033] font-mono leading-relaxed focus:outline-hidden focus:border-[#2563EB]"
              />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[11px] text-[#8A94A6]">
                Our hybrid NLP & taxonomy engine will parse and extract verified skills.
              </span>
              <button
                type="button"
                onClick={handleExtractSkills}
                disabled={isExtracting}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-[#EFF6FF] border border-[#BFDBFE] text-[#2563EB] hover:bg-[#DBEAFE] text-xs font-semibold transition-colors disabled:opacity-50"
              >
                {isExtracting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Extracting Requirements...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Extract Skills</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Role Requirements & Editable Skills */}
          <div className="p-5 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] shadow-2xs space-y-5">
            <div className="flex items-center justify-between border-b border-[#EDF0F4] pb-2">
              <h2 className="text-sm font-bold text-[#172033]">
                Role Skill Requirements
              </h2>
              <span className="text-[11px] text-[#5E6878]">
                Total Skills: {requiredSkills.length + preferredSkills.length}
              </span>
            </div>

            {/* Required Skills */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#2563EB]"></span>
                  <span className="text-xs font-bold text-[#172033]">
                    Required Skills (Core Competencies)
                  </span>
                  <span className="text-[11px] text-[#8A94A6]">
                    ({requiredSkills.length})
                  </span>
                </div>
                <span className="text-[10px] text-[#8A94A6]">Weighted at 60% in match engine</span>
              </div>

              <div className="flex flex-wrap gap-2 p-3 rounded-md border border-[#E1E6ED] bg-[#F8FAFC] min-h-[50px]">
                {requiredSkills.length === 0 ? (
                  <span className="text-xs text-[#8A94A6] italic">
                    No required skills defined. Use &quot;Extract Skills&quot; or add manually.
                  </span>
                ) : (
                  requiredSkills.map((skill) => (
                    <div
                      key={skill}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#EFF6FF] text-[#2563EB] border border-[#BFDBFE] text-xs font-medium"
                    >
                      <span>{skill}</span>
                      <button
                        type="button"
                        onClick={() => handleMoveToPreferred(skill)}
                        title="Move to Preferred Skills"
                        className="text-[#3B82F6] hover:text-[#1D4ED8] p-0.5"
                      >
                        <ArrowLeftRight className="w-3 h-3" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleRemoveRequired(skill)}
                        title="Remove skill"
                        className="text-[#93C5FD] hover:text-[#DC2626] p-0.5"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Preferred Skills */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#0F9F8C]"></span>
                  <span className="text-xs font-bold text-[#172033]">
                    Preferred Skills (Bonus / Complementary)
                  </span>
                  <span className="text-[11px] text-[#8A94A6]">
                    ({preferredSkills.length})
                  </span>
                </div>
                <span className="text-[10px] text-[#8A94A6]">Weighted at 10% in match engine</span>
              </div>

              <div className="flex flex-wrap gap-2 p-3 rounded-md border border-[#E1E6ED] bg-[#F8FAFC] min-h-[50px]">
                {preferredSkills.length === 0 ? (
                  <span className="text-xs text-[#8A94A6] italic">
                    No preferred skills defined.
                  </span>
                ) : (
                  preferredSkills.map((skill) => (
                    <div
                      key={skill}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#E8F7F4] text-[#0F9F8C] border border-[#A7F3D0] text-xs font-medium"
                    >
                      <span>{skill}</span>
                      <button
                        type="button"
                        onClick={() => handleMoveToRequired(skill)}
                        title="Move to Required Skills"
                        className="text-[#059669] hover:text-[#047857] p-0.5"
                      >
                        <ArrowLeftRight className="w-3 h-3" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleRemovePreferred(skill)}
                        title="Remove skill"
                        className="text-[#6EE7B7] hover:text-[#DC2626] p-0.5"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Add Skill Manually Form */}
            <form onSubmit={handleAddManualSkill} className="flex flex-col sm:flex-row items-center gap-2 pt-2">
              <div className="flex-1 w-full">
                <input
                  type="text"
                  placeholder="Add another skill (e.g. Scikit-Learn, Docker, Pandas)..."
                  value={newSkillInput}
                  onChange={(e) => setNewSkillInput(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033] focus:outline-hidden focus:border-[#2563EB]"
                />
              </div>
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <select
                  value={skillTargetType}
                  onChange={(e) => setSkillTargetType(e.target.value as "required" | "preferred")}
                  className="px-2.5 py-1.5 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-xs text-[#172033]"
                >
                  <option value="required">As Required</option>
                  <option value="preferred">As Preferred</option>
                </select>
                <button
                  type="submit"
                  className="px-3 py-1.5 rounded-md bg-[#172033] text-[#FFFFFF] hover:bg-[#2A374E] text-xs font-semibold flex items-center gap-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Skill</span>
                </button>
              </div>
            </form>
          </div>

          {/* Action Footer */}
          <div className="flex items-center justify-between pt-2">
            <Link
              href="/recruiter"
              className="px-4 py-2 rounded-md border border-[#E1E6ED] bg-[#FFFFFF] text-[#5E6878] hover:text-[#172033] text-xs font-medium transition-colors"
            >
              Cancel
            </Link>

            <button
              type="button"
              onClick={handleSaveJob}
              disabled={isSaving}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-[#2563EB] text-[#FFFFFF] hover:bg-[#1D4ED8] text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Persisting Requisition...</span>
                </>
              ) : (
                <>
                  <span>Create Role & Analyze Candidates</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}
