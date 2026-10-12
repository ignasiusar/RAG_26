"use client";
import { useState } from "react";

export default function ChatInput({ onSend, disabled }: { onSend: (t: string) => void; disabled?: boolean }) {
  const [value, setValue] = useState("");

  const submit = () => {
    if (!value.trim() || disabled) return;
    onSend(value.trim());
    setValue("");
  };

  return (
    <div className="flex items-end gap-2 rounded-xl border border-slate-200 bg-white p-3">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        rows={2}
        placeholder="Bandingkan persyaratannya…"
        className="flex-1 resize-none text-sm outline-none"
      />
      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        aria-label="Kirim"
        className="h-9 w-9 rounded-lg bg-emerald-800 text-white disabled:opacity-40"
      >
        ↑
      </button>
    </div>
  );
}
