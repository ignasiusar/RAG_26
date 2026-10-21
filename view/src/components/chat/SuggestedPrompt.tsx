import { ArrowUpRight } from "lucide-react";

interface SuggestedPromptProps {
    onSelect: (prompt: string) => void;
}

const prompts = [
    "Cari lowongan frontend di Malang",
    "Pekerjaan untuk fresh graduate",
    "Cari pekerjaan dengan sistem remote",
    "Apa skill yang dibutuhkan perusahaan?",
];

function SuggestedPrompt({ onSelect }: SuggestedPromptProps) {
    return (
        <div className="suggested-prompts">
            <p className="suggested-prompts__label">
                Kamu bisa mencoba pertanyaan berikut:
            </p>

            <div className="suggested-prompts__grid">
                {prompts.map((prompt) => (
                    <button
                        key={prompt}
                        className="suggested-prompts__button"
                        type="button"
                        onClick={() => onSelect(prompt)}
                    >
                        <span>{prompt}</span>
                        <ArrowUpRight size={16} />
                    </button>
                ))}
            </div>
        </div>
    );
}

export default SuggestedPrompt;