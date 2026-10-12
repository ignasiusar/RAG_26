import { NextResponse } from "next/server";
import { mockJobs } from "@/data/mockJobs";
import { Message } from "@/types";

export async function POST(req: Request) {
  const { message, history } = await req.json();

  // 1) Kalau backend RAG (Python/FastAPI) sudah jalan, teruskan ke sana.
  //    Set RAG_API_URL di .env.local, contoh: http://localhost:8000/chat
  if (process.env.RAG_API_URL) {
    const r = await fetch(process.env.RAG_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: message, history }),
    });
    if (!r.ok) return NextResponse.json({ error: "RAG error" }, { status: 502 });
    const data = await r.json();
    // Sesuaikan bentuk respons RAG-mu di sini agar cocok dengan tipe Message
    return NextResponse.json({ message: data as Message });
  }

  // 2) Sementara: jawaban contoh (belum terhubung RAG)
  const q = String(message).toLowerCase();
  const jobs = mockJobs.filter(
    (j) => q.includes(j.location.toLowerCase()) || q.includes("frontend") || q.includes("web")
  );

  const reply: Message = {
    id: crypto.randomUUID(),
    role: "assistant",
    content: jobs.length
      ? `Aku menemukan ${jobs.length} lowongan yang cocok.`
      : "Belum ada lowongan yang cocok. Coba sebutkan lokasi atau skill lain.",
    points: jobs[0]?.requirements,
    sources: jobs.map((j) => ({ id: j.sourceId, title: `Sumber ${j.sourceId}` })),
    jobs,
  };
  return NextResponse.json({ message: reply });
}
