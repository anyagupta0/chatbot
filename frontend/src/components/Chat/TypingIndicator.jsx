export default function TypingIndicator() {
  return (
    <div className="py-4 animate-fade-in">
      <div className="max-w-3xl mx-auto px-4">
        <div className="flex gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary-100 dark:bg-primary-900/40 flex items-center justify-center shrink-0">
            <div className="w-4 h-4 rounded-full bg-primary-500 animate-pulse" />
          </div>
          <div className="flex items-center gap-3 px-4 py-3 bg-surface-50 dark:bg-surface-800 rounded-2xl rounded-tl-md">
            <div className="flex gap-1.5">
              <div className="w-2 h-2 rounded-full bg-primary-400 typing-dot" />
              <div className="w-2 h-2 rounded-full bg-primary-400 typing-dot" />
              <div className="w-2 h-2 rounded-full bg-primary-400 typing-dot" />
            </div>
            <span className="text-sm text-surface-500 dark:text-surface-400">
              ResearchAI is thinking...
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
