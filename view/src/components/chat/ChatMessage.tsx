import { BriefcaseBusiness, User } from "lucide-react";
import SourceList, { type SourceItem } from "./SourceList";

export type MessageRole = "assistant" | "user";

interface ChatMessageProps {
    role: MessageRole;
    content: string;
    time: string;
    sources?: SourceItem[];
}

function ChatMessage({
    role,
    content,
    time,
    sources = [],
}: ChatMessageProps) {
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

                {!isUser && <SourceList sources={sources} />}

                <time className="chat-message__time">{time}</time>
            </div>
        </article>
    );
}

export default ChatMessage;