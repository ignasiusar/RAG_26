import {
    useState,
    type FormEvent,
    type KeyboardEvent,
} from "react";
import { Paperclip, Send } from "lucide-react";

interface ChatInputProps {
    onSend: (message: string) => void;
}

function ChatInput({ onSend }: ChatInputProps) {
    const [message, setMessage] = useState("");

    const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        const cleanMessage = message.trim();

        if (!cleanMessage) {
            return;
        }

        onSend(cleanMessage);
        setMessage("");
    };

    const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            event.currentTarget.form?.requestSubmit();
        }
    };

    return (
        <div className="chat-input">
            <form className="chat-input__form" onSubmit={handleSubmit}>
                <button
                    className="chat-input__attachment"
                    type="button"
                    aria-label="Tambahkan lampiran"
                >
                    <Paperclip size={19} />
                </button>

                <textarea
                    aria-label="Tulis pesan"
                    placeholder="Tanyakan lowongan pekerjaan..."
                    rows={1}
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                    onKeyDown={handleKeyDown}
                />

                <button
                    className="chat-input__send"
                    type="submit"
                    aria-label="Kirim pesan"
                    disabled={!message.trim()}
                >
                    <Send size={18} />
                </button>
            </form>

            <p className="chat-input__note">
                Tekan Enter untuk mengirim · Shift + Enter untuk baris baru
            </p>
        </div>
    );
}

export default ChatInput;