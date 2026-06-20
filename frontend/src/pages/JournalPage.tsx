import { EmptyState } from "../components/ui/State";

export function JournalPage() {
  return (
    <div className="max-w-3xl rounded-md border border-line bg-slate-900 p-4">
      <h2 className="mb-3 text-sm font-semibold text-slate-100">Trade Journal</h2>
      <EmptyState message="Journal UI is ready for trade review workflows. No journal entries are loaded yet." />
    </div>
  );
}
