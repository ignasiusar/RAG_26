import { useEffect, useRef, useState } from "react";
import {
    BriefcaseBusiness,
    MoreHorizontal,
    RotateCcw,
} from "lucide-react";
import ChatInput from "./ChatInput";
import ChatMessage, { type MessageRole } from "./ChatMessage";
import SuggestedPrompt from "./SuggestedPrompt";
import TypingIndicator from "./TypingIndicator";
import { type SourceItem } from "./SourceList";
import { sendChat, type ApiSource } from "../../services/ragApi";
import "../../styles/chat.css";

interface Message {
    id: string;
    role: MessageRole;
    content: string;
    time: string;
    sources?: SourceItem[];
}

// crypto.randomUUID hanya ada di konteks aman (HTTPS / localhost).
// Fallback ini mencegah crash saat FE dibuka dari HP lewat http://IP-laptop.
function makeId(): string {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
        return crypto.randomUUID();
    }
    return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function getCurrentTime(): string {
    return new Intl.DateTimeFormat("id-ID", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    })
        .format(new Date())
        .replace(".", ":");
}

function createInitialMessages(): Message[] {
    return [
        {
            id: "message-1",
            role: "assistant",
            content:
                "Halo! Saya bisa membantu kamu mencari pekerjaan berdasarkan posisi, lokasi, dan kemampuan yang kamu miliki.",
            time: getCurrentTime(),
        },
    ];
}

function toSourceItems(sources: ApiSource[]): SourceItem[] {
    const seen = new Set<string>();
    const items: SourceItem[] = [];

    for (const s of sources) {
        if (!s.url || seen.has(s.url)) continue;
        seen.add(s.url);
        items.push({
            id: `source-${items.length}`,
            title: `${s.posisi} - ${s.perusahaan}`,
            description: s.lokasi,
            url: s.url,
        });
    }
    return items;
}

function ChatPanel() {
    const [messages, setMessages] = useState<Message[]>(createInitialMessages);
    const [hasStarted, setHasStarted] = useState(false);
    const [isTyping, setIsTyping] = useState(false);
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const bottomMessageRef = useRef<HTMLDivElement>(null);
    // Session id disimpan di ref: dipakai backend untuk memuat riwayat,
    // dan jadi penanda untuk mengabaikan respons "basi" setelah chat di-reset.
    const sessionIdRef = useRef<string>(makeId());

    useEffect(() => {
        bottomMessageRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "end",
        });
    }, [messages, isTyping]);

    const appendMessage = (message: Message) => {
        setMessages((current) => [...current, message]);
    };

    const handleSendMessage = async (content: string) => {
        if (isTyping) return;

        const sessionAtSend = sessionIdRef.current;

        appendMessage({
            id: makeId(),
            role: "user",
            content,
            time: getCurrentTime(),
        });
        setHasStarted(true);
        setIsTyping(true);

        try {
            const data = await sendChat(sessionAtSend, content);
            if (sessionAtSend !== sessionIdRef.current) return; // chat sudah di-reset

            const sources = toSourceItems(data.sources);
            appendMessage({
                id: makeId(),
                role: "assistant",
                content: data.reply,
                time: getCurrentTime(),
                sources: sources.length > 0 ? sources : undefined,
            });
        } catch (err) {
            if (sessionAtSend !== sessionIdRef.current) return;

            appendMessage({
                id: makeId(),
                role: "assistant",
                content:
                    err instanceof Error
                        ? `Maaf, ${err.message}`
                        : "Maaf, terjadi kesalahan. Coba lagi sebentar.",
                time: getCurrentTime(),
            });
        } finally {
            if (sessionAtSend === sessionIdRef.current) {
                setIsTyping(false);
            }
        }
    };

    const handleResetChat = () => {
        sessionIdRef.current = makeId(); // sesi baru = riwayat backend baru
        setMessages(createInitialMessages());
        setHasStarted(false);
        setIsTyping(false);
        setIsMenuOpen(false);
    };

    return (
        <section className="chat-panel">
            <header className="chat-panel__header">
                <div className="chat-panel__identity">
                    <div className="chat-panel__avatar">
                        <BriefcaseBusiness size={22} strokeWidth={2} />
                    </div>

                    <div>
                        <h1>TemuKerja Assistant</h1>

                        <div className="chat-panel__status">
                            <span className="status-dot" />
                            <span>
                                {isTyping ? "Sedang mencari..." : "Siap membantu"}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="chat-panel__menu-wrapper">
                    <button
                        className="chat-panel__menu"
                        type="button"
                        aria-label="Buka menu percakapan"
                        aria-expanded={isMenuOpen}
                        onClick={() => setIsMenuOpen((current) => !current)}
                    >
                        <MoreHorizontal size={22} />
                    </button>

                    {isMenuOpen && (
                        <div className="chat-panel__dropdown" role="menu">
                            <button
                                type="button"
                                role="menuitem"
                                onClick={handleResetChat}
                            >
                                <RotateCcw size={16} />
                                <span>Mulai chat baru</span>
                            </button>
                        </div>
                    )}
                </div>
            </header>

            <div className="chat-panel__content">
                <div className="chat-message-list">
                    {messages.map((message) => (
                        <ChatMessage
                            key={message.id}
                            role={message.role}
                            content={message.content}
                            time={message.time}
                            sources={message.sources}
                        />
                    ))}

                    {!hasStarted && (
                        <SuggestedPrompt onSelect={handleSendMessage} />
                    )}

                    {isTyping && <TypingIndicator />}

                    <div ref={bottomMessageRef} />
                </div>
            </div>

            <footer className="chat-panel__footer">
                <ChatInput
                    onSend={handleSendMessage}
                    disabled={isTyping}
                />
            </footer>
        </section>
    );
}

export default ChatPanel;