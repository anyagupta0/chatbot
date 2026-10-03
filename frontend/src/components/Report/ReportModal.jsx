import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { X, Download, Copy, Check, FileText, Loader2 } from 'lucide-react'

export default function ReportModal({ isOpen, onClose, report, isGenerating }) {
  const [copied, setCopied] = useState(false)

  if (!isOpen) return null

  function handleCopy() {
    if (!report?.content) return
    navigator.clipboard.writeText(report.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function handleDownload() {
    if (!report?.content) return
    const blob = new Blob([report.content], { type: 'text/markdown;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${(report.title || 'research-report').replace(/\s+/g, '_')}.md`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fade-in">
      <div className="bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-100 dark:border-surface-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-primary-100 dark:bg-primary-900/40 text-primary-600 dark:text-primary-400">
              <FileText size={20} />
            </div>
            <div>
              <h2 className="font-semibold text-lg text-surface-900 dark:text-surface-100">
                {report?.title || 'Research Report'}
              </h2>
              <p className="text-xs text-surface-400">
                {isGenerating ? 'Synthesizing literature, findings, and analysis...' : 'Structured academic research document'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {!isGenerating && report?.content && (
              <>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-surface-100 hover:bg-surface-200 dark:bg-surface-800 dark:hover:bg-surface-700 text-surface-700 dark:text-surface-300 transition-colors"
                  title="Copy Report Markdown"
                >
                  {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-primary-600 hover:bg-primary-700 text-white transition-colors"
                  title="Download Markdown"
                >
                  <Download size={14} />
                  <span>Download .md</span>
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {isGenerating ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <Loader2 size={36} className="text-primary-600 animate-spin mb-4" />
              <h3 className="text-base font-semibold text-surface-800 dark:text-surface-200">
                Compiling Academic Report
              </h3>
              <p className="text-sm text-surface-400 mt-1 max-w-sm">
                Analyzing discussion history, evidence synthesis, citations, and formulating research gaps...
              </p>
            </div>
          ) : report?.content ? (
            <div className="markdown-body text-surface-800 dark:text-surface-200 text-sm leading-relaxed max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {report.content}
              </ReactMarkdown>
            </div>
          ) : (
            <div className="text-center py-16 text-surface-400 text-sm">
              No report generated yet. Chat or add research to generate a comprehensive report.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
