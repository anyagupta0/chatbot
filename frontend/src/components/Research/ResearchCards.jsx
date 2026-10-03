import { ExternalLink, BookOpen, Quote, Tag } from 'lucide-react'

export default function ResearchCards({ papers }) {
  if (!papers || papers.length === 0) return null

  return (
    <div className="space-y-3 mt-4 animate-slide-up">
      <div className="flex items-center gap-2 text-sm font-medium text-surface-500 dark:text-surface-400">
        <BookOpen size={14} />
        <span>Sources ({papers.length} papers found)</span>
      </div>

      <div className="space-y-2">
        {papers.map((paper, index) => (
          <div
            key={paper.id || index}
            className="group border border-surface-200 dark:border-surface-700 rounded-xl p-4
                       bg-white dark:bg-surface-800/50 hover:border-primary-300 dark:hover:border-primary-600
                       hover:shadow-sm transition-all duration-200"
          >
            {/* Title */}
            <h4 className="text-sm font-semibold text-surface-800 dark:text-surface-200 leading-snug mb-1.5 line-clamp-2">
              [{index + 1}] {paper.title}
            </h4>

            {/* Authors & Year */}
            <div className="flex items-center gap-2 text-xs text-surface-500 dark:text-surface-400 mb-2">
              {paper.authors?.length > 0 && (
                <span className="truncate max-w-[200px]">
                  {paper.authors.slice(0, 3).join(', ')}
                  {paper.authors.length > 3 ? ' et al.' : ''}
                </span>
              )}
              {paper.year && (
                <>
                  <span>·</span>
                  <span className="font-medium">{paper.year}</span>
                </>
              )}
              {paper.citations > 0 && (
                <>
                  <span>·</span>
                  <span>{paper.citations} citations</span>
                </>
              )}
            </div>

            {/* Abstract */}
            {paper.abstract && (
              <p className="text-xs text-surface-500 dark:text-surface-400 leading-relaxed mb-3 line-clamp-2">
                {paper.abstract}
              </p>
            )}

            {/* Keywords */}
            {paper.keywords?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-3">
                {paper.keywords.slice(0, 4).map((kw, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 
                               rounded-full bg-primary-50 dark:bg-primary-900/30 
                               text-primary-700 dark:text-primary-300"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            )}

            {/* Footer */}
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-surface-400 font-medium">
                {paper.source}
              </span>
              <div className="flex items-center gap-2">
                {paper.url && (
                  <a
                    href={paper.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary-600 dark:text-primary-400 
                               hover:text-primary-700 dark:hover:text-primary-300 font-medium"
                  >
                    Open <ExternalLink size={11} />
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
