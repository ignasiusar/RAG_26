import { Source } from "@/types";

export default function SourceList({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <p className="mt-2 text-sm text-emerald-800">
      Berdasarkan sumber lowongan {sources.map((s) => s.id).join(", ")}
    </p>
  );
}
