import { Message } from "@/types";
import SourceList from "./SourceList";

export default function ChatMessage({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="ml-6 self-end rounded-xl bg-white px-4 py-3 text-sm shadow-sm">
        {message.content}
      </div>
    );
  }
  return (
    <div className="text-sm">
      <p className="mb-1 text-xs text-slate-500">TemuKerja</p>
      <p className="text-slate-700">{message.content}</p>
      {message.points && (
        <ul className="ml-4 mt-2 list-disc space-y-1 text-slate-800">
          {message.points.map((p) => <li key={p}>{p}</li>)}
        </ul>
      )}
      {message.sources && <SourceList sources={message.sources} />}
    </div>
  );
}
