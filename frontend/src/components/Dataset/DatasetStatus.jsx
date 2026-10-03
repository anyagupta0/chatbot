import { Table, CheckCircle, Loader2 } from 'lucide-react'

export default function DatasetStatus({ dataset }) {
  if (!dataset) return null

  const { filename, file_size, row_count, column_count, summary, status } = dataset
  const sizeMB = (file_size / 1024 / 1024).toFixed(1)

  return (
    <div className="border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800/50 overflow-hidden animate-slide-up">
      {/* Header */}
      <div className="flex items-start gap-3 p-4">
        <div className="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-900/20">
          <Table size={20} className="text-amber-600 dark:text-amber-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-surface-800 dark:text-surface-200 truncate">
            📊 {filename}
          </p>
          <div className="flex items-center gap-3 mt-1 text-xs text-surface-500">
            <span>{sizeMB} MB</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      {status === 'ready' && (
        <div className="px-4 pb-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <StatCard label="Rows" value={row_count?.toLocaleString()} />
            <StatCard label="Columns" value={column_count} />
            <StatCard label="Missing" value={summary?.total_missing ?? 0} />
            <StatCard label="Duplicates" value={summary?.duplicates ?? 0} />
          </div>

          {/* Column preview */}
          {dataset.columns?.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-surface-500 mb-1.5">Columns</p>
              <div className="flex flex-wrap gap-1.5">
                {dataset.columns.slice(0, 10).map((col, i) => (
                  <span
                    key={i}
                    className="text-[10px] px-2 py-0.5 rounded-full bg-surface-100 dark:bg-surface-700 
                               text-surface-600 dark:text-surface-300 font-medium"
                  >
                    {col}
                  </span>
                ))}
                {dataset.columns.length > 10 && (
                  <span className="text-[10px] px-2 py-0.5 text-surface-400">
                    +{dataset.columns.length - 10} more
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Data preview */}
          {summary?.preview && summary.preview.length > 0 && (
            <div className="mt-3 overflow-x-auto">
              <p className="text-xs font-medium text-surface-500 mb-1.5">Preview</p>
              <table className="w-full text-[11px]">
                <thead>
                  <tr>
                    {Object.keys(summary.preview[0]).map(key => (
                      <th key={key} className="px-2 py-1 text-left font-medium text-surface-500 bg-surface-50 dark:bg-surface-700 whitespace-nowrap">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {summary.preview.slice(0, 3).map((row, i) => (
                    <tr key={i} className="border-t border-surface-100 dark:border-surface-700">
                      {Object.values(row).map((val, j) => (
                        <td key={j} className="px-2 py-1 text-surface-600 dark:text-surface-400 whitespace-nowrap max-w-[120px] truncate">
                          {String(val ?? '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex items-center gap-1.5 mt-3 text-xs text-emerald-600 dark:text-emerald-400">
            <CheckCircle size={12} />
            <span>Ready for analysis — ask me anything about this data</span>
          </div>
        </div>
      )}

      {status === 'processing' && (
        <div className="px-4 pb-4 flex items-center gap-2 text-xs text-amber-600">
          <Loader2 size={12} className="animate-spin" />
          <span>Processing dataset...</span>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="px-3 py-2 rounded-lg bg-surface-50 dark:bg-surface-700/50">
      <p className="text-[10px] text-surface-400 uppercase tracking-wide font-medium">{label}</p>
      <p className="text-lg font-bold text-surface-800 dark:text-surface-200">{value}</p>
    </div>
  )
}
