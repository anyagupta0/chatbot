import { FileText, CheckCircle, Loader2, AlertCircle } from 'lucide-react'

export default function DocumentStatus({ document }) {
  if (!document) return null

  const { filename, file_size, page_count, status } = document
  const sizeMB = (file_size / 1024 / 1024).toFixed(1)

  return (
    <div className="flex items-start gap-3 p-4 border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800/50 animate-slide-up">
      <div className="p-2.5 rounded-lg bg-violet-50 dark:bg-violet-900/20">
        <FileText size={20} className="text-violet-600 dark:text-violet-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-surface-800 dark:text-surface-200 truncate">
          📄 {filename}
        </p>
        <div className="flex items-center gap-3 mt-1 text-xs text-surface-500">
          <span>{sizeMB} MB</span>
          {page_count > 0 && <span>{page_count} pages</span>}
        </div>
        <div className="flex flex-col gap-1 mt-2">
          <StatusLine done={true} label="Uploaded" />
          <StatusLine done={status === 'ready'} loading={status === 'processing'} label="Text extracted" />
          <StatusLine done={status === 'ready'} loading={status === 'processing'} label="Ready for analysis" />
        </div>
      </div>
    </div>
  )
}

function StatusLine({ done, loading, label }) {
  return (
    <div className="flex items-center gap-1.5 text-xs">
      {done ? (
        <CheckCircle size={12} className="text-emerald-500" />
      ) : loading ? (
        <Loader2 size={12} className="text-amber-500 animate-spin" />
      ) : (
        <div className="w-3 h-3 rounded-full border border-surface-300" />
      )}
      <span className={done ? 'text-emerald-600 dark:text-emerald-400' : 'text-surface-400'}>
        {done ? '✓' : loading ? '⟳' : '○'} {label}
      </span>
    </div>
  )
}
