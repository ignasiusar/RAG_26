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
import "../../styles/chat.css";

interface Message {
    id: string;
    role: MessageRole;
    content: string;
    time: string;
    sources?: SourceItem[];
}

const initialMessages: Message[] = [
    {
        id: "message-1",
        role: "assistant",
        content:
            "Halo! Saya bisa membantu kamu mencari pekerjaan berdasarkan posisi, lokasi, dan kemampuan yang kamu miliki.",
        time: "15.38",
    },
];

const mockSources: SourceItem[] = [
    {
        id: "source-1",
        title: "LinkedIn Jobs",
        description: "Sumber pencarian lowongan pekerjaan",
        url: "https://www.linkedin.com/jobs/",
    },
    {
        id: "source-2",
        title: "JobStreet Indonesia",
        description: "Sumber informasi posisi dan perusahaan",
        url: "https://www.jobstreet.co.id/",
    },
];

function getCurrentTime() {
    return new Intl.DateTimeFormat("id-ID", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    })
        .format(new Date())
        .replace(".", ":");
}

function ChatPanel() {
    const [messages, setMessages] = useState<Message[]>(initialMessages);
    const [hasStarted, setHasStarted] = useState(false);
    const [isTyping, setIsTyping] = useState(false);
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const bottomMessageRef = useRef<HTMLDivElement>(null);
    const responseTimeoutRef = useRef<number | null>(null);

    useEffect(() => {
        bottomMessageRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "end",
        });
    }, [messages, isTyping]);

    useEffect(() => {
        return () => {
            if (responseTimeoutRef.current !== null) {
                window.clearTimeout(responseTimeoutRef.current);
            }
        };
    }, []);

    const handleSendMessage = (content: string) => {
        if (isTyping) {
            return;
        }

        const userMessage: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content,
            time: getCurrentTime(),
        };

        setMessages((currentMessages) => [
            ...currentMessages,
            userMessage,
        ]);

        setHasStarted(true);
        setIsTyping(true);

        responseTimeoutRef.current = window.setTimeout(() => {
            const assistantMessage: Message = {
                id: crypto.randomUUID(),
                role: "assistant",
                content:
                    "Berikut contoh tampilan sumber yang nantinya akan dihasilkan dari proses pencarian RAG.",
                time: getCurrentTime(),
                sources: mockSources,
            };

            setMessages((currentMessages) => [
                ...currentMessages,
                assistantMessage,
            ]);

            setIsTyping(false);
            responseTimeoutRef.current = null;
        }, 1200);
    };

    const handleResetChat = () => {
        if (responseTimeoutRef.current !== null) {
            window.clearTimeout(responseTimeoutRef.current);
            responseTimeoutRef.current = null;
        }

        setMessages(initialMessages);
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