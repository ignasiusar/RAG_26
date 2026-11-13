const API_URL = (
    import.meta.env.VITE_API_URL ?? "/api"
).replace(/\/$/, "");

const KEY = "temukerja.session";

function storedToken(): string | null {
    try {
        return sessionStorage.getItem(KEY);
    } catch {
        return null;
    }
}

let token = storedToken();

export function setToken(value: string | null) {
    token = value;

    try {
        if (value) {
            sessionStorage.setItem(KEY, value);
        } else {
            sessionStorage.removeItem(KEY);
        }
    } catch {
        // Login tetap dapat berjalan menggunakan memori.
    }
}

export const hasToken = () => Boolean(token);

export interface User {
    id: string;
    name: string;
    email: string;
}

export interface ApiSource {
    posisi: string;
    perusahaan: string;
    lokasi: string;
    url: string;
}

export interface Quota {
    limit: number;
    used: number;
    remaining: number;
    remaining_percent: number;
    blocked: boolean;
    reset_at: number | null;
    retry_after: number;
    server_time: number;
}

export interface Conversation {
    id: string;
    title: string;
    created_at: number;
    updated_at: number;
}

export interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    sources: ApiSource[];
    created_at: number;
}

export class ApiError extends Error {
    constructor(
        message: string,
        public status: number,
        public quota?: Quota,
    ) {
        super(message);
    }
}

async function request<T>(
    path: string,
    method = "GET",
    body?: unknown,
): Promise<T> {
    let response: Response;

    const requestToken = token;
    const controller = new AbortController();

    const timeout = setTimeout(
        () => controller.abort(),
        path === "/chat" ? 650000 : 30000,
    );

    try {
        response = await fetch(`${API_URL}${path}`, {
            method,
            headers: {
                ...(body !== undefined
                    ? { "Content-Type": "application/json" }
                    : {}),
                ...(requestToken
                    ? { Authorization: `Bearer ${requestToken}` }
                    : {}),
            },
            body:
                body === undefined
                    ? undefined
                    : JSON.stringify(body),
            cache: "no-store",
            signal: controller.signal,
        });
    } catch {
        throw new ApiError(
            controller.signal.aborted
                ? "Waktu tunggu habis. Periksa riwayat sebelum mengirim ulang."
                : "Belum bisa terhubung ke server. Pastikan backend Docker sudah berjalan.",
            0,
        );
    } finally {
        clearTimeout(timeout);
    }

    const data =
        response.status === 204
            ? null
            : await response.json().catch(() => null);

    if (!response.ok) {
        if (
            response.status === 401 &&
            requestToken &&
            requestToken === token &&
            path !== "/auth/login"
        ) {
            setToken(null);
            window.dispatchEvent(
                new Event("temukerja:expired"),
            );
        }

        const detail = data?.detail;

        const message =
            typeof detail === "string"
                ? detail
                : Array.isArray(detail)
                  ? "Periksa kembali isianmu. Password minimal 8 karakter."
                  : detail?.message ??
                    `Permintaan gagal (${response.status}).`;

        throw new ApiError(
            message,
            response.status,
            detail?.quota,
        );
    }

    return data as T;
}

export const api = {
    me: () => request<User>("/auth/me"),

    register: (
        name: string,
        email: string,
        password: string,
    ) =>
        request<User>("/auth/register", "POST", {
            name,
            email,
            password,
        }),

    async login(email: string, password: string) {
        const data = await request<{
            access_token: string;
            user: User;
        }>("/auth/login", "POST", {
            email,
            password,
        });

        setToken(data.access_token);
        return data.user;
    },

    async logout() {
        const currentToken = token;

        await request("/auth/logout", "POST");

        if (token === currentToken) {
            setToken(null);
        }
    },

    quota: () => request<Quota>("/quota"),

    conversations: (offset = 0, q = "") =>
        request<{
            items: Conversation[];
            has_more: boolean;
        }>(
            `/conversations?offset=${offset}&q=${encodeURIComponent(q)}`,
        ),

    create: (title: string) =>
        request<Conversation>(
            "/conversations",
            "POST",
            { title },
        ),

    conversation: (id: string) =>
        request<{
            conversation: Conversation;
            messages: Message[];
        }>(`/conversations/${id}`),

    rename: (id: string, title: string) =>
        request<Conversation>(
            `/conversations/${id}`,
            "PATCH",
            { title },
        ),

    remove: (id: string) =>
        request<void>(
            `/conversations/${id}`,
            "DELETE",
        ),

    chat: (
        conversation_id: string,
        message: string,
    ) =>
        request<{
            messages: Message[];
            quota: Quota;
        }>("/chat", "POST", {
            conversation_id,
            message,
        }),
};

// Dipertahankan agar komponen ChatPanel lama tetap terkompilasi.
// App baru menggunakan api.chat().
export async function sendChat(
    sessionId: string,
    message: string,
) {
    const data = await api.chat(sessionId, message);

    const reply = data.messages.find(
        item => item.role === "assistant",
    );

    return {
        status: "success",
        reply: reply?.content ?? "",
        sources: reply?.sources ?? [],
    };
}