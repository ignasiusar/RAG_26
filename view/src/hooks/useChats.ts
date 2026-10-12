"use client";
import { useCallback, useEffect, useState } from "react";
import { Chat, Message } from "@/types";
import { sendMessage } from "@/services/chatService";

const KEY = "temukerja.chats";

const newChatObj = (): Chat => ({
  id: crypto.randomUUID(),
  title: "Chat baru",
  createdAt: Date.now(),
  messages: [],
});

export function useChats() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  // Muat riwayat dari localStorage (hanya di client, supaya tidak error hydration)
  useEffect(() => {
    try {
      const saved: Chat[] = JSON.parse(localStorage.getItem(KEY) || "[]");
      if (saved.length) {
        setChats(saved);
        setActiveId(saved[0].id);
      } else {
        const c = newChatObj();
        setChats([c]);
        setActiveId(c.id);
      }
    } catch {
      const c = newChatObj();
      setChats([c]);
      setActiveId(c.id);
    }
    setReady(true);
  }, []);

  // Simpan setiap ada perubahan
  useEffect(() => {
    if (ready) localStorage.setItem(KEY, JSON.stringify(chats));
  }, [chats, ready]);

  const activeChat = chats.find((c) => c.id === activeId);

  const createChat = useCallback(() => {
    // Kalau chat aktif masih kosong, tidak perlu bikin baru
    if (activeChat && activeChat.messages.length === 0) return;
    const c = newChatObj();
    setChats((prev) => [c, ...prev]);
    setActiveId(c.id);
    setError(null);
  }, [activeChat]);

  const selectChat = (id: string) => {
    setActiveId(id);
    setError(null);
  };

  const deleteChat = (id: string) => {
    setChats((prev) => {
      const rest = prev.filter((c) => c.id !== id);
      if (rest.length === 0) {
        const c = newChatObj();
        setActiveId(c.id);
        return [c];
      }
      if (id === activeId) setActiveId(rest[0].id);
      return rest;
    });
  };

  const send = async (text: string) => {
    if (!activeChat || !text.trim() || loading) return;
    const chatId = activeChat.id;
    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: text };

    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? {
              ...c,
              title: c.messages.length === 0 ? text.slice(0, 40) : c.title,
              messages: [...c.messages, userMsg],
            }
          : c
      )
    );
    setLoading(true);
    setError(null);

    try {
      const reply = await sendMessage(text, activeChat.messages);
      setChats((prev) =>
        prev.map((c) =>
          c.id === chatId ? { ...c, messages: [...c.messages, reply] } : c
        )
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Terjadi kesalahan.");
    } finally {
      setLoading(false);
    }
  };

  return { chats, activeChat, activeId, loading, error, ready, createChat, selectChat, deleteChat, send };
}
