import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { User, Bot, Copy, Check, RotateCcw } from 'lucide-react'
import { useState } from 'react'
import ResearchCards from '../Research/ResearchCards'
import ChartDisplay from '../Dataset/ChartDisplay'

export default function ChatMessage({ message, onRetry }) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'
  const metadata = message.metadata || {}

  function handleCopy() {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={`py-4 animate-fade-in ${isUser ? '' : ''}`}>
      <div className="max-w-3xl mx-auto px-4">
        <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
          {/* Avatar */}
          {!isUser && (
            <div className="w-8 h-8 rounded-lg bg-primary-100 dark:bg-primary-900/40 flex items-center justify-center shrink-0 mt-0.5">
              <Bot size={16} className="text-primary-600 dark:text-primary-400" />
            </div>
          )}

          {/* Message content */}
          <div className={`
            max-w-[85%] lg:max-w-[75%]
            ${isUser 
              ? 'bg-primary-600 text-white rounded-2xl rounded-br-md px-4 py-2.5' 
              : 'flex-1 min-w-0'}
          `}>
            {isUser ? (
              <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="space-y-3">
                {/* Markdown content */}
                <div className="markdown-body text-surface-800 dark:text-surface-200 text-[15px]">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>

                {/* Research papers */}
                {metadata.papers && metadata.papers.length > 0 && (
                  <ResearchCards papers={metadata.papers} />
                )}

                {/* Chart */}
                {metadata.chart && !metadata.chart.error && (
                  <ChartDisplay chartData={metadata.chart} />
                )}

                {/* Action buttons */}
                <div className="flex items-center gap-1 pt-1">
                  <button
                    onClick={handleCopy}
                    className="p-1.5 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 
                               hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
                    title="Copy"
                  >
                    {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                  </button>
                  {onRetry && (
                    <button
                      onClick={() => onRetry(message)}
                      className="p-1.5 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 
                                 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
                      title="Retry"
                    >
                      <RotateCcw size={14} />
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User avatar */}
          {isUser && (
            <div className="w-8 h-8 rounded-lg bg-surface-200 dark:bg-surface-700 flex items-center justify-center shrink-0 mt-0.5">
              <User size={16} className="text-surface-600 dark:text-surface-400" />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
