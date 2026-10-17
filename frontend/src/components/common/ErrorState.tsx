import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Something went wrong",
  message = "Failed to complete evaluation. Please verify file integrity and backend connectivity.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="w-full min-h-[240px] flex flex-col items-center justify-center p-8 text-center bg-[#FDEEEE] border border-[#F2CACA] rounded-lg">
      <div className="w-10 h-10 rounded-lg bg-[#FFFFFF] text-[#C24141] border border-[#F2CACA] flex items-center justify-center mb-3">
        <AlertCircle className="w-5 h-5 stroke-[2]" />
      </div>

      <h3 className="text-base font-bold text-[#172033] mb-1">
        {title}
      </h3>
      <p className="max-w-md text-xs text-[#5E6878] mb-4 leading-relaxed">
        {message}
      </p>

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold bg-[#FFFFFF] border border-[#D7DEE8] text-[#172033] hover:bg-[#F1F4F8] transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Try Again</span>
        </button>
      )}
    </div>
  );
}
