import type { RunSummary } from "./models";

export const sampleRuns: RunSummary[] = [
  {
    id: "run-001",
    productName: "Sustainable packaging subscription",
    region: "India",
    marketDefinition: "B2B recurring packaging for small food businesses",
    createdAt: "2026-10-12T09:30:00Z",
    updatedAt: "2026-10-15T15:45:00Z",
    status: "completed",
    evidenceCount: 42,
    reportAvailable: true,
    warnings: [],
  },
  {
    id: "run-002",
    productName: "Regional telehealth platform",
    region: "Maharashtra, India",
    marketDefinition: "Affordable primary-care video consultations",
    createdAt: "2026-10-14T08:10:00Z",
    updatedAt: "2026-10-16T11:20:00Z",
    status: "partial",
    evidenceCount: 18,
    reportAvailable: true,
    warnings: [
      {
        stage: "Customer feedback",
        source: "Public review source",
        message: "The source could not be reached. The report uses market and competitor evidence only.",
      },
    ],
  },
  {
    id: "run-003",
    productName: "Inventory assistant for independent retailers",
    region: "United Kingdom",
    marketDefinition: "Cloud inventory management for small retailers",
    createdAt: "2026-10-16T06:15:00Z",
    updatedAt: "2026-10-16T06:17:00Z",
    status: "running",
    evidenceCount: 0,
    reportAvailable: false,
    warnings: [],
  },
];
