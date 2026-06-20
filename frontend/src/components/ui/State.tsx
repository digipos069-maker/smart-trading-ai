export function LoadingBlock({ label = "Loading" }: { label?: string }) {
  return (
    <div className="animate-pulse rounded-md border border-line bg-slate-900 p-4 text-sm text-slate-500">
      {label}...
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-dashed border-slate-700 bg-slate-900/60 p-6 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">
      {message}
    </div>
  );
}
