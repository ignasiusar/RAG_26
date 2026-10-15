import { Job } from "@/types";
import JobCard from "./JobCard";
import JobFilter from "./JobFilter";
import EmptyJobs from "./EmptyJobs";

export default function JobResults({ jobs }: { jobs: Job[] }) {
  const tags = Array.from(new Set(jobs.flatMap((j) => [j.location, j.mode])));
  return (
    <section className="h-full min-h-0 overflow-y-auto p-6">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-2xl font-semibold">Peluang untukmu</h2>
        <span className="text-sm text-slate-500">{jobs.length} lowongan</span>
      </div>
      <JobFilter tags={tags} />
      <div className="space-y-3">
        {jobs.length ? jobs.map((j) => <JobCard key={j.id} job={j} />) : <EmptyJobs />}
      </div>
    </section>
  );
}
