"use client";

import React, { useState, useRef } from "react";
import {
  UploadCloud,
  FileText,
  Check,
  AlertCircle,
  Loader2,
  X,
  FileCode,
  FileCheck,
} from "lucide-react";

export interface ParsedDocumentData {
  document_type: string;
  text: string;
  page_count: number;
  metadata: {
    filename: string;
    file_size_bytes: number;
    character_count: number;
    word_count: number;
    content_type: string;
  };
}

export type UploadStatus = "idle" | "uploading" | "parsing" | "success" | "failure";

interface UploadZoneProps {
  onFileSelect?: (file: File) => void;
  onSampleSelect?: (sampleName: string) => void;
  onParsed?: (data: ParsedDocumentData) => void;
  acceptedFormats?: string[];
  maxSizeMB?: number;
  isProcessing?: boolean;
}

export function UploadZone({
  onFileSelect,
  onSampleSelect,
  onParsed,
  acceptedFormats = [".pdf", ".docx", ".txt"],
  maxSizeMB = 10,
  isProcessing = false,
}: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [parsedData, setParsedData] = useState<ParsedDocumentData | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sampleProfiles = [
    {
      name: "Senior Data Scientist",
      desc: "Python, SQL, ML, Deep Learning, Statistics",
      content: `Pawan Kumar\nSenior Data Scientist\npawan@example.com\n\nExperience:\n- 4+ years architecting predictive machine learning pipelines in Python, scikit-learn, and PyTorch.\n- Designed complex PostgreSQL analytical queries and ETL data pipelines for high-throughput transactional records.\n- Applied hypothesis testing, experimental design, and mathematical statistics to optimize product conversion rates by 22%.\n- Containerized analytical microservices using Docker and orchestrated model deployments on AWS.`,
    },
    {
      name: "Backend Software Engineer",
      desc: "Python, FastAPI, PostgreSQL, Docker, Redis",
      content: `Aarav Sharma\nSenior Backend Software Engineer\naarav@example.com\n\nExperience:\n- Built low-latency RESTful APIs and asynchronous microservices with Python, FastAPI, and PostgreSQL.\n- Automated CI/CD deployment pipelines using Docker, Git, and Linux server environments.\n- Implemented caching layers with Redis and designed relational database schemas.`,
    },
    {
      name: "Data Analyst",
      desc: "SQL, Excel, Python, Power BI, Statistics",
      content: `Priya Patel\nBusiness Data Analyst\npriya@example.com\n\nExperience:\n- 3+ years writing complex SQL joins, aggregations, and window functions to query multi-million row business datasets.\n- Built executive business intelligence dashboards in Power BI and conducted exploratory data analysis using Python and Pandas.\n- Applied regression and descriptive statistics to drive revenue decisions.`,
    },
  ];

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const uploadAndParseFile = async (file: File) => {
    setErrorMessage(null);
    setParsedData(null);
    setSelectedFile(file);
    onFileSelect?.(file);

    // Extension validation
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!acceptedFormats.includes(ext)) {
      setUploadStatus("failure");
      setErrorMessage(`Unsupported format '${ext}'. Please upload a ${acceptedFormats.join(", ")} document.`);
      return;
    }

    // Size validation
    if (file.size > maxSizeMB * 1024 * 1024) {
      setUploadStatus("failure");
      const actualMB = (file.size / (1024 * 1024)).toFixed(1);
      setErrorMessage(`File size (${actualMB} MB) exceeds maximum allowed limit of ${maxSizeMB} MB.`);
      return;
    }

    if (file.size === 0) {
      setUploadStatus("failure");
      setErrorMessage("The selected file is empty (0 bytes).");
      return;
    }

    setUploadStatus("uploading");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_BASE}/api/v1/documents/parse`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errDetail = `Server returned status ${response.status}`;
        try {
          const json = await response.json();
          errDetail = json.detail || errDetail;
        } catch {
          // ignore json parse error
        }
        throw new Error(errDetail);
      }

      const data: ParsedDocumentData = await response.json();
      setParsedData(data);
      setUploadStatus("success");
      onParsed?.(data);
    } catch (err: any) {
      setUploadStatus("failure");
      setErrorMessage(
        err?.message || "Unable to read document. Please verify the document format or try a sample profile."
      );
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadAndParseFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      uploadAndParseFile(e.target.files[0]);
    }
  };

  const handleSampleClick = async (sample: (typeof sampleProfiles)[0]) => {
    setErrorMessage(null);
    const mockFile = new File([sample.content], `${sample.name.toLowerCase().replace(/\s+/g, "_")}.txt`, {
      type: "text/plain",
    });
    setSelectedFile(mockFile);
    onSampleSelect?.(sample.name);
    uploadAndParseFile(mockFile);
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setParsedData(null);
    setUploadStatus("idle");
    setErrorMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-lg p-8 sm:p-10 text-center transition-colors ${
          isDragging
            ? "border-[#2563EB] bg-[#EFF6FF]"
            : "border-[#CBD5E1] bg-[#FFFFFF] hover:border-[#2563EB]"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedFormats.join(",")}
          onChange={handleFileInputChange}
          className="hidden"
          id="resume-file-input"
        />

        <div className="max-w-md mx-auto flex flex-col items-center">
          <div className="w-12 h-12 rounded-lg bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center mb-4">
            <UploadCloud className="w-6 h-6 stroke-[1.8]" />
          </div>

          <h3 className="text-base font-semibold text-[#172033] mb-1">
            Upload your resume
          </h3>
          <p className="text-xs text-[#5E6878] mb-5">
            Drop your resume here, or{" "}
            <label
              htmlFor="resume-file-input"
              className="text-[#2563EB] hover:text-[#1D4ED8] font-semibold cursor-pointer hover:underline"
            >
              browse files
            </label>
          </p>

          <div className="flex items-center gap-3 text-[11px] text-[#8A94A6]">
            <span>Supported formats: PDF, DOCX, TXT</span>
            <span>•</span>
            <span>Up to {maxSizeMB} MB</span>
          </div>
        </div>
      </div>

      {/* Selected File State */}
      {selectedFile && (
        <div className="p-4 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-[#172033] truncate">
                {selectedFile.name}
              </p>
              <div className="flex items-center gap-2 text-xs text-[#5E6878]">
                <span>{formatFileSize(selectedFile.size)}</span>
                <span>•</span>
                {uploadStatus === "uploading" && (
                  <span className="flex items-center gap-1 text-[#2563EB]">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Reading document...
                  </span>
                )}
                {uploadStatus === "success" && (
                  <span className="flex items-center gap-1 text-[#16805C] font-medium">
                    <Check className="w-3 h-3 stroke-[3]" />
                    File ready
                  </span>
                )}
                {uploadStatus === "failure" && (
                  <span className="flex items-center gap-1 text-[#C24141] font-medium">
                    <AlertCircle className="w-3 h-3" />
                    Error reading file
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={clearSelection}
            className="p-1.5 rounded text-[#8A94A6] hover:text-[#172033] hover:bg-[#F1F4F8] transition-colors"
            title="Remove file"
            aria-label="Remove file"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="p-3.5 rounded-lg bg-[#FDEEEE] border border-[#F2CACA] text-[#C24141] text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[#C24141]" />
          <div className="space-y-0.5">
            <span className="font-semibold block">Upload Failed</span>
            <p className="leading-relaxed">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Quick Test: Sample Profiles */}
      <div className="pt-2">
        <span className="text-[11px] font-bold text-[#8A94A6] uppercase tracking-wider block mb-2.5">
          Or test with a sample profile
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          {sampleProfiles.map((sample) => (
            <button
              key={sample.name}
              type="button"
              onClick={() => handleSampleClick(sample)}
              className="text-left p-3 rounded-lg border border-[#E1E6ED] bg-[#FFFFFF] hover:border-[#CBD5E1] hover:bg-[#F8FAFC] transition-colors"
            >
              <span className="text-xs font-semibold text-[#172033] block">
                {sample.name}
              </span>
              <span className="text-[11px] text-[#5E6878] block mt-0.5 truncate">
                {sample.desc}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
