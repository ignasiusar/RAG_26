export default function JobFilter({ tags }: { tags: string[] }) {
  if (!tags.length) return null;
  return (
    <div className="mb-4 flex flex-wrap gap-2">
      {tags.map((t) => (
        <span key={t} className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">{t}</span>
      ))}
    </div>
  );
}
