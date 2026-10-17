import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: "/candidate/ats",
        destination: "/candidate/ats-check",
        permanent: false,
      },
      {
        source: "/ats-check",
        destination: "/candidate/ats-check",
        permanent: false,
      },
      {
        source: "/candidate/ats-resume-check",
        destination: "/candidate/ats-check",
        permanent: false,
      },
      {
        source: "/candidate/skill-gaps",
        destination: "/candidate/gaps",
        permanent: false,
      },
      {
        source: "/skill-gaps",
        destination: "/candidate/gaps",
        permanent: false,
      },
      {
        source: "/candidate/career-matches",
        destination: "/candidate/matches",
        permanent: false,
      },
      {
        source: "/career-matches",
        destination: "/candidate/matches",
        permanent: false,
      },
      {
        source: "/candidate/learning-path",
        destination: "/candidate/learning",
        permanent: false,
      },
      {
        source: "/learning-path",
        destination: "/candidate/learning",
        permanent: false,
      },
      {
        source: "/candidate/match-results",
        destination: "/candidate/results",
        permanent: false,
      },
      {
        source: "/match-results",
        destination: "/candidate/results",
        permanent: false,
      },
      {
        source: "/candidate/market-demand",
        destination: "/insights",
        permanent: false,
      },
      {
        source: "/market-demand",
        destination: "/insights",
        permanent: false,
      },
      {
        source: "/candidate/market-insights",
        destination: "/insights",
        permanent: false,
      },
      {
        source: "/market-insights",
        destination: "/insights",
        permanent: false,
      },
      {
        source: "/candidate/market",
        destination: "/insights",
        permanent: false,
      },
      {
        source: "/candidate/resume-upload",
        destination: "/candidate/upload",
        permanent: false,
      },
      {
        source: "/resume-upload",
        destination: "/candidate/upload",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;

