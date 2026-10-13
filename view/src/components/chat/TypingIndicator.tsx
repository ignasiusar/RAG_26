import { BriefcaseBusiness } from "lucide-react";

function TypingIndicator() {
    return (
        <article className="chat-message chat-message--assistant">
            <div className="chat-message__avatar" aria-hidden="true">
                <BriefcaseBusiness size={17} strokeWidth={2} />
            </div>

            <div
                className="typing-indicator"
                role="status"
                aria-label="Asisten sedang mengetik"
            >
                <span />
                <span />
                <span />
            </div>
        </article>
    );
}

export default TypingIndicator;