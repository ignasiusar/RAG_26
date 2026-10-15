"use client";
import Header from "./Header";
import Sidebar from "./Sidebar";
import ChatPanel from "../chat/ChatPanel";
import JobResults from "../jobs/JobResults";
import { useChats } from "@/hooks/useChats";

export default function MainLayout() {
  const { chats, activeChat, activeId, loading, error, ready, createChat, selectChat, deleteChat, send } = useChats();

  // Lowongan = hasil dari balasan asisten terakhir di chat yang aktif
  const lastJobs =
    [...(activeChat?.messages ?? [])].reverse().find((m) => m.role === "assistant" && m.jobs)?.jobs ?? [];

  if (!ready) return null;

  return (
    <div className="flex h-screen flex-col">
      <Header />
      <div className="grid min-h-0 flex-1 grid-cols-1 md:grid-cols-[240px_1fr] lg:grid-cols-[240px_380px_1fr]">
        <Sidebar chats={chats} activeId={activeId} onNew={createChat} onSelect={selectChat} onDelete={deleteChat} />
        <ChatPanel chat={activeChat} loading={loading} error={error} onSend={send} />
        <div className="hidden min-h-0 lg:block">
          <JobResults jobs={lastJobs} />
        </div>
      </div>
    </div>
  );
}
