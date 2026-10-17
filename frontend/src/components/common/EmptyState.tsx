import React from "react";
import Link from "next/link";
import { FolderSearch, Plus } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  actionHref?: string;
  onActionClick?: () => void;
  icon?: React.ReactNode;
}

export function EmptyState({
  title,
  description,
  actionText,
  actionHref,
  onActionClick,
  icon,
}: EmptyStateProps) {
  return (
    <div className="w-full min-h-[280px] flex flex-col items-center justify-center p-8 text-center bg-[#FFFFFF] border border-dashed border-[#CBD5E1] rounded-lg">
      <div className="w-12 h-12 rounded-lg bg-[#F8FAFC] text-[#5E6878] flex items-center justify-center mb-3.5 border border-[#E1E6ED]">
        {icon || <FolderSearch className="w-6 h-6 stroke-[1.8]" />}
      </div>

      <h3 className="text-base font-bold text-[#172033] mb-1">
        {title}
      </h3>
      <p className="max-w-md text-xs text-[#5E6878] mb-5 leading-relaxed">
        {description}
      </p>

      {actionText && actionHref && (
        <Link
          href={actionHref}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold bg-[#2563EB] hover:bg-[#1D4ED8] text-[#FFFFFF] shadow-xs transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>{actionText}</span>
        </Link>
      )}

      {actionText && !actionHref && onActionClick && (
        <button
          type="button"
          onClick={onActionClick}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold bg-[#2563EB] hover:bg-[#1D4ED8] text-[#FFFFFF] shadow-xs transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>{actionText}</span>
        </button>
      )}
    </div>
  );
}
