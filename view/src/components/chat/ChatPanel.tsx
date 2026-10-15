"use client";
import { useEffect, useRef } from "react";
import { Chat } from "@/types";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import SuggestedPrompt from "./SuggestedPrompt";
import Loading from "../common/Loading";
import ErrorMessage from "../common/ErrorMessage";

type Props = { chat?: Chat; loading: boolean; error: string | null; onSend: (t: string) => void };

export default function ChatPanel({ chat, loading, error, onSend }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat?.messages.length, loading]);

  return (
    <section className="flex min-h-0 flex-col bg-slate-50 p-5">
      <p className="text-xs text-slate-500">Asisten karier</p>
      <h1 className="mb-4 mt-1 text-2xl font-semibold leading-snug">
        Ceritakan pekerjaan yang kamu cari.
      </h1>

      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto pr-1">
        {chat?.messages.length === 0 && <SuggestedPrompt onPick={onSend} />}
        {chat?.messages.map((m) => <ChatMessage key={m.id} message={m} />)}
        {loading && <Loading />}
        {error && <ErrorMessage message={error} />}
        <div ref={bottomRef} />
      </div>

      <div className="pt-4">
        <ChatInput onSend={onSend} disabled={loading} />
      </div>
    </section>
  );
}
