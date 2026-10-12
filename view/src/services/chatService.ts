import { Message } from "@/types";

export async function sendMessage(
  text: string,
  history: Message[]
): Promise<Message> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text, history }),
  });
  if (!res.ok) throw new Error("Gagal menghubungi server. Coba lagi.");
  const data = await res.json();
  return data.message as Message;
}
