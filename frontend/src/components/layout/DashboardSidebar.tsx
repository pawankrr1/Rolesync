"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FileText,
  FileCheck,
  UploadCloud,
  CheckCircle2,
  TrendingUp,
  BookOpen,
  BarChart3,
  Users,
  Briefcase,
  Layers,
  Compass,
} from "lucide-react";

interface SidebarProps {
  role?: "candidate" | "recruiter";
}

export function DashboardSidebar({ role = "candidate" }: SidebarProps) {
  const pathname = usePathname();

  const candidateLinks = [
    { href: "/candidate", label: "Overview", icon: Layers },
    { href: "/candidate/upload", label: "Resume Upload", icon: UploadCloud },
    { href: "/candidate/ats-check", label: "ATS Resume Check", icon: FileCheck },
    { href: "/candidate/results", label: "Match & Results", icon: CheckCircle2 },
    { href: "/candidate/matches", label: "Career Matches", icon: Compass },
    { href: "/candidate/gaps", label: "Skill Gaps", icon: TrendingUp },
    { href: "/candidate/learning", label: "Learning Path", icon: BookOpen },
    { href: "/insights", label: "Market Insights", icon: BarChart3 },
  ];

  const recruiterLinks = [
    { href: "/recruiter", label: "Recruiter Overview", icon: Users },
    { href: "/recruiter/create-job", label: "Create Job", icon: Briefcase },
    { href: "/recruiter/matches", label: "Candidate Matches", icon: CheckCircle2 },
    { href: "/recruiter/talent-pool", label: "Talent Pool", icon: FileText },
    { href: "/recruiter/shortlist", label: "Shortlisted", icon: CheckCircle2 },
    { href: "/recruiter/insights", label: "Hiring Insights", icon: BarChart3 },
  ];

  const links = role === "candidate" ? candidateLinks : recruiterLinks;

  return (
    <aside className="w-56 shrink-0 hidden lg:block border-r border-[#DCE6F2] bg-[#FFFFFF] p-5 space-y-6">
      <div>
        <span className="text-[10px] font-bold uppercase tracking-wider text-[#8A94A6] block mb-3 px-2">
          {role === "candidate" ? "Candidate Workspace" : "Recruiter Workspace"}
        </span>
        <nav className="space-y-0.5" aria-label="Sidebar Navigation">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive =
              pathname === link.href ||
              (link.href !== "/candidate" &&
                link.href !== "/recruiter" &&
                !link.href.includes("#") &&
                pathname.startsWith(link.href));

            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-2.5 px-2.5 py-2 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-[#EFF6FF] text-[#2563EB] font-semibold"
                    : "text-[#5E6878] hover:text-[#2563EB] hover:bg-[#EFF6FF]"
                }`}
              >
                <Icon
                  className={`w-4 h-4 ${
                    isActive ? "text-[#2563EB]" : "text-[#8A94A6]"
                  }`}
                />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* RoleSync Method note */}
      <div className="p-3 rounded border border-[#DCE6F2] bg-[#F5F9FF] text-[11px] space-y-1">
        <span className="font-semibold text-[#172033] block">
          Methodology
        </span>
        <p className="text-[#5E6878] leading-normal">
          {role === "candidate"
            ? "MATCH → GAP → LEARN → GROW. Scores are mathematical and explainable."
            : "Zero-PII compliant candidate evaluation with objective skill coverage criteria."}
        </p>
      </div>
    </aside>
  );
}
