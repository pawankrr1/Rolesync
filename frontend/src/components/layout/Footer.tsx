import React from "react";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-[#E1E6ED] bg-[#172033] py-12 text-[#B8C0CD] text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand & Purpose */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-[#2563EB] flex items-center justify-center text-[#FFFFFF] text-xs font-bold">
                RS
              </div>
              <span className="font-bold text-sm text-[#FFFFFF]">
                RoleSync
              </span>
            </div>
            <p className="max-w-md text-xs leading-relaxed text-[#B8C0CD]">
              A transparent career intelligence platform that helps professionals understand their competencies,
              quantifies role alignment, identifies skill gaps, and recommends focused learning pathways.
            </p>
            <div className="flex items-center gap-2 text-[11px] text-[#B8C0CD]">
              <ShieldCheck className="w-4 h-4 text-[#16805C] shrink-0" />
              <span>Zero-PII Storage • In-Memory Document Stream Processing</span>
            </div>
          </div>

          {/* Candidate Workflow Links */}
          <div>
            <h4 className="font-semibold text-[#FFFFFF] mb-3 text-xs uppercase tracking-wider">
              For Candidates
            </h4>
            <ul className="space-y-2">
              <li>
                <Link href="/candidate" className="hover:text-[#FFFFFF] transition-colors">
                  Overview Workspace
                </Link>
              </li>
              <li>
                <Link href="/candidate/upload" className="hover:text-[#FFFFFF] transition-colors">
                  Analyze Resume
                </Link>
              </li>
              <li>
                <Link href="/candidate/matches" className="hover:text-[#FFFFFF] transition-colors">
                  Career Matches
                </Link>
              </li>
              <li>
                <Link href="/candidate/gaps" className="hover:text-[#FFFFFF] transition-colors">
                  Skill Gaps
                </Link>
              </li>
              <li>
                <Link href="/candidate/learning" className="hover:text-[#FFFFFF] transition-colors">
                  Learning Roadmap
                </Link>
              </li>
              <li>
                <Link href="/insights" className="hover:text-[#FFFFFF] transition-colors">
                  Market Skill Trends
                </Link>
              </li>
            </ul>
          </div>

          {/* Recruiter & System Links */}
          <div>
            <h4 className="font-semibold text-[#FFFFFF] mb-3 text-xs uppercase tracking-wider">
              For Recruiters
            </h4>
            <ul className="space-y-2">
              <li>
                <Link href="/recruiter" className="hover:text-[#FFFFFF] transition-colors">
                  Recruiter Overview
                </Link>
              </li>
              <li>
                <Link href="/recruiter#create-job" className="hover:text-[#FFFFFF] transition-colors">
                  Create Job &amp; Parse JD
                </Link>
              </li>
              <li>
                <Link href="/recruiter#rankings" className="hover:text-[#FFFFFF] transition-colors">
                  Candidate Comparison Table
                </Link>
              </li>
              <li>
                <Link href="/recruiter#talent-pool" className="hover:text-[#FFFFFF] transition-colors">
                  Talent Pool
                </Link>
              </li>
              <li>
                <Link href="/insights" className="hover:text-[#FFFFFF] transition-colors">
                  Hiring &amp; Market Insights
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-[#2D3748] flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-[#B8C0CD]">
          <p>© {new Date().getFullYear()} RoleSync. Professional Career Intelligence.</p>
          <p className="text-center sm:text-right">
            Decision support platform. Objective skill match engine without black-box filtering.
          </p>
        </div>
      </div>
    </footer>
  );
}
