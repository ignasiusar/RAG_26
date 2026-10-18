const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface ApiSource {
    posisi: string;
    perusahaan: string;
    lokasi: string;
    url: string;
}

export interface ChatResponse {
    status: string;
    reply: string;
    sources: ApiSource[];
}

export async function sendChat(
    sessionId: string,
    message: string,
): Promise<ChatResponse> {
    const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_session_id: sessionId, message }),
    });

    if (!res.ok) {
        throw new Error(`Server error ${res.status}`);
    }
    return res.json();
}