import { Job } from "@/types";

const chip = "rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600";

export default function JobCard({ job }: { job: Job }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold">{job.title}</h3>
          <p className="mt-1 text-sm text-slate-500">{job.company} · {job.location}</p>
        </div>
        <button aria-label="Simpan" className="rounded-lg border border-slate-200 px-2 py-1 text-slate-500 hover:text-emerald-800">
          ☐
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <span className={chip}>{job.mode}</span>
        {job.type && <span className={chip}>{job.type}</span>}
        {job.experience && <span className={chip}>{job.experience}</span>}
        {job.salary && <span className={chip}>{job.salary}</span>}
      </div>
      {job.match && (
        <p className="mt-3 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-900">{job.match}</p>
      )}
      {!job.salary && <p className="mt-3 text-sm text-slate-500">Gaji tidak dicantumkan di sumber.</p>}
      <div className="mt-4 flex justify-between border-t border-slate-100 pt-3 text-xs text-slate-500">
        <span>Diperiksa {job.checkedAt}</span>
        <a href="#" className="text-slate-700">Sumber {job.sourceId} ↗</a>
      </div>
    </article>
  );
}
