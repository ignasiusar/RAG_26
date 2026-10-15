const prompts = [
  "Cari frontend di Malang. Saya fresh graduate dan menguasai React.",
  "Lowongan remote untuk backend Laravel",
  "Magang UI/UX di Yogyakarta",
];

export default function SuggestedPrompt({ onPick }: { onPick: (t: string) => void }) {
  return (
    <div className="flex flex-col gap-2">
      {prompts.map((p) => (
        <button
          key={p}
          onClick={() => onPick(p)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-sm text-slate-700 hover:border-emerald-700"
        >
          {p}
        </button>
      ))}
    </div>
  );
}
