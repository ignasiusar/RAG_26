import { useState } from "react";
import { BriefcaseBusiness, MoreHorizontal } from "lucide-react";
import ChatInput from "./ChatInput";
import ChatMessage, { type MessageRole } from "./ChatMessage";
import "../../styles/chat.css";

interface Message {
    id: string;
    role: MessageRole;
    content: string;
    time: string;
}

const initialMessages: Message[] = [
    {
        id: "message-1",
        role: "assistant",
        content:
            "Halo! Saya bisa membantu kamu mencari pekerjaan berdasarkan posisi, lokasi, dan kemampuan yang kamu miliki.",
        time: "15.38",
    },
    {
        id: "message-2",
        role: "user",
        content:
            "Saya mencari posisi Frontend Developer di Malang yang menerima fresh graduate.",
        time: "15.39",
    },
    {
        id: "message-3",
        role: "assistant",
        content:
            "Baik, saya akan membantu mencari lowongan yang sesuai dengan kriteria tersebut.",
        time: "15.39",
    },
];

function ChatPanel() {
    const [messages, setMessages] = useState<Message[]>(initialMessages);

    const handleSendMessage = (content: string) => {
        const currentTime = new Intl.DateTimeFormat("id-ID", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
        })
            .format(new Date())
            .replace(".", ":");

        const newMessage: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content,
            time: currentTime,
        };

        setMessages((currentMessages) => [
            ...currentMessages,
            newMessage,
        ]);
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
                            <span>Siap membantu</span>
                        </div>
                    </div>
                </div>

                <button
                    className="chat-panel__menu"
                    type="button"
                    aria-label="Buka menu percakapan"
                >
                    <MoreHorizontal size={22} />
                </button>
            </header>

            <div className="chat-panel__content">
                <div className="chat-message-list">
                    {messages.map((message) => (
                        <ChatMessage
                            key={message.id}
                            role={message.role}
                            content={message.content}
                            time={message.time}
                        />
                    ))}
                </div>
            </div>

            <footer className="chat-panel__footer">
                <ChatInput onSend={handleSendMessage} />
            </footer>
        </section>
    );
}

export default ChatPanel;