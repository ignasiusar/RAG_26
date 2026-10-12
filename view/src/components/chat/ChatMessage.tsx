import { BriefcaseBusiness, User } from "lucide-react";

export type MessageRole = "assistant" | "user";

interface ChatMessageProps {
    role: MessageRole;
    content: string;
    time: string;
}

function ChatMessage({ role, content, time }: ChatMessageProps) {
    const isUser = role === "user";

    return (
        <article
            className={`chat-message ${isUser ? "chat-message--user" : "chat-message--assistant"
                }`}
        >
            <div className="chat-message__avatar" aria-hidden="true">
                {isUser ? (
                    <User size={17} strokeWidth={2} />
                ) : (
                    <BriefcaseBusiness size={17} strokeWidth={2} />
                )}
            </div>

            <div className="chat-message__body">
                <div className="chat-message__bubble">
                    <p>{content}</p>
                </div>

                <time className="chat-message__time">{time}</time>
            </div>
        </article>
    );
}

export default ChatMessage;