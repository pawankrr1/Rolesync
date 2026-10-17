"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Menu,
  X,
  ArrowRight,
  Briefcase,
  User,
} from "lucide-react";
import { checkBackendHealth } from "@/lib/api";

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<{
    online: boolean;
    latency?: number;
    checked: boolean;
  }>({
    online: false,
    checked: false,
  });

  useEffect(() => {
    let mounted = true;
    checkBackendHealth().then((res) => {
      if (mounted) {
        setBackendStatus({
          online: res.isOnline,
          latency: res.data?.latencyMs,
          checked: true,
        });
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  const isRecruiterPath = pathname.startsWith("/recruiter");

  const candidateNav = [
    { href: "/candidate", label: "Overview" },
    { href: "/candidate/upload", label: "Resume Upload" },
    { href: "/candidate/ats-check", label: "ATS Resume Check" },
    { href: "/candidate/results", label: "Match & Results" },
    { href: "/candidate/matches", label: "Career Matches" },
    { href: "/candidate/gaps", label: "Skill Gaps" },
    { href: "/candidate/learning", label: "Learning Path" },
    { href: "/insights", label: "Market Insights" },
  ];

  const recruiterNav = [
    { href: "/recruiter", label: "Overview" },
    { href: "/recruiter/create-job", label: "Create Job" },
    { href: "/recruiter/matches", label: "Candidate Matches" },
    { href: "/recruiter/talent-pool", label: "Talent Pool" },
    { href: "/recruiter/shortlist", label: "Shortlisted" },
    { href: "/recruiter/insights", label: "Hiring Insights" },
  ];

  const activeNavLinks = isRecruiterPath ? recruiterNav : candidateNav;

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#DCE6F2] bg-[#FFFFFF]/95 backdrop-blur-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand & Identity */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-[#172033] flex items-center justify-center text-[#FFFFFF] font-bold text-sm tracking-tight shadow-xs">
              RS
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold tracking-tight text-[#172033] leading-none">
                RoleSync
              </span>
              <span className="text-[10px] font-medium text-[#5E6878] mt-0.5">
                Career Intelligence
              </span>
            </div>
          </Link>

          {/* Workflow Mode Switcher */}
          <div className="hidden lg:flex items-center p-0.5 bg-[#EFF6FF] rounded-md text-xs border border-[#DCE6F2]">
            <Link
              href="/candidate"
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded font-medium transition-colors ${
                !isRecruiterPath
                  ? "bg-[#FFFFFF] text-[#2563EB] shadow-xs font-semibold"
                  : "text-[#5E6878] hover:text-[#2563EB]"
              }`}
            >
              <User className="w-3.5 h-3.5" />
              <span>For Candidates</span>
            </Link>
            <Link
              href="/recruiter"
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded font-medium transition-colors ${
                isRecruiterPath
                  ? "bg-[#FFFFFF] text-[#2563EB] shadow-xs font-semibold"
                  : "text-[#5E6878] hover:text-[#2563EB]"
              }`}
            >
              <Briefcase className="w-3.5 h-3.5" />
              <span>For Recruiters</span>
            </Link>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-1" aria-label="Main Navigation">
          {activeNavLinks.map((link) => {
            const isActive =
              link.href === "/candidate"
                ? pathname === "/candidate"
                : link.href === "/recruiter"
                ? pathname === "/recruiter"
                : pathname === link.href || (link.href.startsWith("/candidate") && pathname.startsWith(link.href));

            return (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-[#EFF6FF] text-[#2563EB] font-semibold shadow-2xs"
                    : "text-[#5E6878] hover:text-[#2563EB] hover:bg-[#EFF6FF]"
                }`}
              >
                {link.label}
              </Link>
            );
          })}

          <div className="h-4 w-px bg-[#DCE6F2] mx-1" />

          <Link
            href="/uat"
            className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
              pathname === "/uat"
                ? "bg-[#EFF6FF] text-[#2563EB] font-semibold shadow-2xs"
                : "text-[#5E6878] hover:text-[#2563EB] hover:bg-[#EFF6FF]"
            }`}
          >
            UAT
          </Link>
        </nav>

        {/* Action Controls & Health */}
        <div className="hidden sm:flex items-center gap-3">
          {/* Health indicator */}
          <div
            className="flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-medium text-[#5E6878] border border-[#DCE6F2] bg-[#F5F9FF]"
            title={
              backendStatus.checked
                ? backendStatus.online
                  ? `Backend connected (${backendStatus.latency || "<10"}ms)`
                  : "Backend offline"
                : "Checking backend..."
            }
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                backendStatus.checked
                  ? backendStatus.online
                    ? "bg-[#16805C]"
                    : "bg-[#C24141]"
                  : "bg-[#B7791F]"
              }`}
            />
            <span className="text-[10px]">
              {backendStatus.checked
                ? backendStatus.online
                  ? "Connected"
                  : "Offline"
                : "Connecting"}
            </span>
          </div>

          <Link
            href="/candidate/upload"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold text-[#FFFFFF] shadow-sm hover:opacity-95 hover:shadow transition-all duration-200"
            style={{
              background: "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
            }}
          >
            <span>Analyze Resume</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Mobile menu trigger */}
        <div className="flex md:hidden items-center gap-2">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-md text-[#5E6878] hover:bg-[#EFF6FF] hover:text-[#2563EB]"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-[#DCE6F2] bg-[#FFFFFF] px-4 pt-3 pb-5 space-y-3">
          <div className="flex items-center p-1 bg-[#EFF6FF] rounded-md text-xs border border-[#DCE6F2]">
            <Link
              href="/candidate"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex-1 text-center py-1.5 rounded font-medium ${
                !isRecruiterPath
                  ? "bg-[#FFFFFF] text-[#2563EB] font-semibold shadow-xs"
                  : "text-[#5E6878]"
              }`}
            >
              For Candidates
            </Link>
            <Link
              href="/recruiter"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex-1 text-center py-1.5 rounded font-medium ${
                isRecruiterPath
                  ? "bg-[#FFFFFF] text-[#2563EB] font-semibold shadow-xs"
                  : "text-[#5E6878]"
              }`}
            >
              For Recruiters
            </Link>
          </div>

          <div className="space-y-1">
            {activeNavLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-xs font-medium text-[#5E6878] hover:bg-[#EFF6FF] hover:text-[#2563EB]"
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="pt-2 border-t border-[#DCE6F2] space-y-2">
            <Link
              href="/uat"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                pathname === "/uat"
                  ? "bg-[#EFF6FF] text-[#2563EB] font-semibold"
                  : "text-[#5E6878] hover:bg-[#EFF6FF] hover:text-[#2563EB]"
              }`}
            >
              UAT
            </Link>

            <Link
              href="/candidate/upload"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center justify-center gap-2 w-full py-2.5 rounded-md text-xs font-semibold text-[#FFFFFF] shadow-sm hover:opacity-95"
              style={{
                background: "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
              }}
            >
              <span>Analyze Resume</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
