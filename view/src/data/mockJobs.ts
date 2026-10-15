import { Job } from "@/types";

export const mockJobs: Job[] = [
  {
    id: "1",
    title: "Junior Frontend Developer",
    company: "Nusa Digital",
    location: "Malang",
    mode: "Hybrid",
    type: "Full-time",
    salary: "Rp5–7 juta / bulan",
    match: "Sesuai preferensimu: React, lokasi Malang, fresh graduate.",
    requirements: ["Menerima fresh graduate", "React termasuk keterampilan yang diminta"],
    sourceId: 1,
    checkedAt: "12 Okt 2026",
  },
  {
    id: "2",
    title: "Web Developer",
    company: "Ruang Karya",
    location: "Malang",
    mode: "On-site",
    experience: "0–1 tahun",
    requirements: ["HTML, CSS, JavaScript"],
    sourceId: 2,
    checkedAt: "12 Okt 2026",
  },
];
