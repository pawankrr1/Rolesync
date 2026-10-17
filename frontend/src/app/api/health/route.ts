import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const backendApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  return NextResponse.json(
    {
      status: "healthy",
      service: "career-intelligence-frontend",
      version: "1.0.0",
      timestamp: new Date().toISOString(),
      configured_backend_url: backendApiUrl,
      environment: process.env.NODE_ENV || "development",
    },
    { status: 200 }
  );
}
