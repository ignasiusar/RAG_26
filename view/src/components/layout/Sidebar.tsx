import { Chat } from "@/types";

type Props = {
  chats: Chat[];
  activeId: string;
  onNew: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
};

export default function Sidebar({ chats, activeId, onNew, onSelect, onDelete }: Props) {
  return (
    <aside className="flex min-h-0 flex-col border-r border-slate-200 bg-slate-50 p-4">
      <button
        onClick={onNew}
        className="mb-4 w-full rounded-lg bg-emerald-800 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-900"
      >
        + Chat baru
      </button>
      <p className="mb-2 px-1 text-xs text-slate-500">Riwayat</p>
      <ul className="min-h-0 flex-1 space-y-1 overflow-y-auto">
        {chats.map((c) => (
          <li key={c.id} className="group flex items-center">
            <button
              onClick={() => onSelect(c.id)}
              className={`flex-1 truncate rounded-lg px-3 py-2 text-left text-sm ${
                c.id === activeId ? "bg-white font-medium shadow-sm" : "text-slate-600 hover:bg-white"
              }`}
            >
              {c.title}
            </button>
            <button
              onClick={() => onDelete(c.id)}
              aria-label="Hapus chat"
              className="ml-1 hidden px-2 text-slate-400 hover:text-red-600 group-hover:block"
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
