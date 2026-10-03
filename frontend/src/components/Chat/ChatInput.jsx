import { useState, useRef } from 'react'
import { Send, Paperclip, Search, BarChart3, Loader2, X, FileText, Table } from 'lucide-react'

export default function ChatInput({ 
  onSend, onFileUpload, isLoading, onCancel, disabled 
}) {
  const [input, setInput] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [mode, setMode] = useState('chat')
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)

  function handleSubmit(e) {
    e?.preventDefault()
    if ((!input.trim() && !selectedFile) || isLoading) return

    if (selectedFile) {
      onFileUpload(selectedFile)
      setSelectedFile(null)
    }

    if (input.trim()) {
      onSend(input.trim(), mode)
      setInput('')
      setMode('chat')
    }

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  function handleInput(e) {
    setInput(e.target.value)
    // Auto-resize textarea
    const ta = textareaRef.current
    if (ta) {
      ta.style.height = 'auto'
      ta.style.height = Math.min(ta.scrollHeight, 200) + 'px'
    }
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (file) {
      const ext = file.name.split('.').pop().toLowerCase()
      if (['pdf', 'csv', 'xlsx', 'xls'].includes(ext)) {
        setSelectedFile(file)
      } else {
        alert('Please upload PDF, CSV, or XLSX files only.')
      }
    }
    e.target.value = ''
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      const ext = file.name.split('.').pop().toLowerCase()
      if (['pdf', 'csv', 'xlsx', 'xls'].includes(ext)) {
        setSelectedFile(file)
      }
    }
  }

  const modeButtons = [
    { id: 'research', icon: Search, label: 'Research', color: 'text-blue-500' },
    { id: 'analyze', icon: BarChart3, label: 'Analyze', color: 'text-emerald-500' },
  ]

  function getFileIcon(file) {
    if (!file) return FileText
    const ext = file.name.split('.').pop().toLowerCase()
    if (ext === 'pdf') return FileText
    return Table
  }

  const FileIcon = getFileIcon(selectedFile)

  return (
    <div
      className={`
        w-full max-w-3xl mx-auto px-4 pb-4 pt-2
        ${dragOver ? 'ring-2 ring-primary-400 rounded-2xl' : ''}
      `}
      onDragOver={e => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      {/* Selected file preview */}
      {selectedFile && (
        <div className="mb-2 flex items-center gap-2 px-3 py-2 bg-surface-50 dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700 animate-fade-in">
          <FileIcon size={16} className="text-primary-500" />
          <span className="text-sm text-surface-700 dark:text-surface-300 truncate flex-1">
            {selectedFile.name}
          </span>
          <span className="text-xs text-surface-400">
            {(selectedFile.size / 1024 / 1024).toFixed(1)} MB
          </span>
          <button
            onClick={() => setSelectedFile(null)}
            className="p-0.5 hover:bg-surface-200 dark:hover:bg-surface-700 rounded"
          >
            <X size={14} className="text-surface-400" />
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-end bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 
                        rounded-2xl shadow-sm hover:shadow-md transition-shadow focus-within:shadow-md focus-within:border-primary-300 dark:focus-within:border-primary-600">
          {/* Attach button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-3 pb-3.5 text-surface-400 hover:text-primary-500 transition-colors"
            title="Attach file (PDF, CSV, XLSX)"
          >
            <Paperclip size={20} />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.csv,.xlsx,.xls"
            onChange={handleFileChange}
          />

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Ask ResearchAI anything..."
            rows={1}
            disabled={disabled}
            className="flex-1 resize-none py-3 px-1 text-surface-900 dark:text-surface-100 
                       bg-transparent placeholder:text-surface-400 focus:outline-none
                       text-[15px] leading-relaxed max-h-[200px]"
          />

          {/* Right side buttons */}
          <div className="flex items-center gap-1 pr-2 pb-2">
            {/* Mode buttons */}
            {modeButtons.map(({ id, icon: Icon, label, color }) => (
              <button
                key={id}
                type="button"
                onClick={() => setMode(mode === id ? 'chat' : id)}
                className={`
                  p-2 rounded-lg text-sm transition-all duration-200
                  ${mode === id 
                    ? `bg-primary-50 dark:bg-primary-900/30 ${color}` 
                    : 'text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-700'}
                `}
                title={label}
              >
                <Icon size={18} />
              </button>
            ))}

            {/* Send / Loading / Cancel */}
            {isLoading ? (
              <button
                type="button"
                onClick={onCancel}
                className="p-2 rounded-xl bg-red-500 text-white hover:bg-red-600 transition-colors"
                title="Cancel"
              >
                <X size={18} />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim() && !selectedFile}
                className="p-2 rounded-xl bg-primary-600 text-white hover:bg-primary-700 
                           disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200
                           disabled:hover:bg-primary-600"
                title="Send message"
              >
                <Send size={18} />
              </button>
            )}
          </div>
        </div>

        {/* Mode indicator */}
        {mode !== 'chat' && (
          <div className="absolute -top-7 left-4 flex items-center gap-1.5 animate-fade-in">
            <span className="text-xs font-medium text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30 px-2 py-0.5 rounded-full">
              {mode === 'research' ? '🔎 Research Mode' : '📊 Analyze Mode'}
            </span>
            <button onClick={() => setMode('chat')} className="text-surface-400 hover:text-surface-600">
              <X size={12} />
            </button>
          </div>
        )}
      </form>

      {dragOver && (
        <div className="absolute inset-0 flex items-center justify-center bg-primary-50/80 dark:bg-primary-900/30 rounded-2xl border-2 border-dashed border-primary-400 z-10">
          <p className="text-primary-600 dark:text-primary-400 font-medium">Drop your file here</p>
        </div>
      )}
    </div>
  )
}
