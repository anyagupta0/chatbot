import { useState, useEffect, useRef } from 'react'
import {
  Menu, Moon, Sun, FileText, Table, FileOutput,
  Sparkles, Plus, X, AlertCircle, RefreshCw, Settings, Cpu
} from 'lucide-react'
import { ThemeProvider, useTheme } from './context/ThemeContext'
import Sidebar from './components/Sidebar/Sidebar'
import WelcomeScreen from './components/Chat/WelcomeScreen'
import ChatMessage from './components/Chat/ChatMessage'
import ChatInput from './components/Chat/ChatInput'
import TypingIndicator from './components/Chat/TypingIndicator'
import DocumentStatus from './components/Documents/DocumentStatus'
import DatasetStatus from './components/Dataset/DatasetStatus'
import ReportModal from './components/Report/ReportModal'
import SettingsModal from './components/Settings/SettingsModal'
import {
  sendMessage, getChat, createChat, uploadDocument,
  uploadDataset, generateReport, getSettings
} from './services/api'

function ChatApp() {
  const { dark, toggle } = useTheme()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeChatId, setActiveChatId] = useState(null)
  const [chatTitle, setChatTitle] = useState('New Chat')
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [activeDocument, setActiveDocument] = useState(null)
  const [activeDataset, setActiveDataset] = useState(null)
  const [reportModalOpen, setReportModalOpen] = useState(false)
  const [currentReport, setCurrentReport] = useState(null)
  const [isGeneratingReport, setIsGeneratingReport] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [activeConfig, setActiveConfig] = useState(null)

  const messagesEndRef = useRef(null)
  const abortControllerRef = useRef(null)
  const quickFileInputRef = useRef(null)
  const [quickUploadType, setQuickUploadType] = useState(null)

  useEffect(() => {
    loadSettingsConfig()
  }, [])

  async function loadSettingsConfig() {
    try {
      const cfg = await getSettings()
      setActiveConfig(cfg)
    } catch (err) {
      console.error('Failed to load settings config:', err)
    }
  }

  // Scroll to bottom when messages or loading state changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading, activeDocument, activeDataset])

  // Responsive sidebar: collapse by default on mobile
  useEffect(() => {
    if (window.innerWidth < 1024) {
      setSidebarOpen(false)
    }
  }, [])

  // Load chat messages when activeChatId changes
  async function handleSelectChat(chatId) {
    if (!chatId || chatId === activeChatId) return
    try {
      setIsLoading(true)
      setActiveChatId(chatId)
      const data = await getChat(chatId)
      setChatTitle(data.conversation?.title || 'Chat')
      setMessages(data.messages || [])
      setActiveDocument(data.documents?.[0] || null)
      setActiveDataset(data.datasets?.[0] || null)
    } catch (err) {
      console.error('Failed to load conversation:', err)
    } finally {
      setIsLoading(false)
    }
  }

  // Start a new chat
  function handleNewChat() {
    setActiveChatId(null)
    setChatTitle('New Chat')
    setMessages([])
    setActiveDocument(null)
    setActiveDataset(null)
    setUploadError(null)
  }

  // Send message
  async function handleSendMessage(content, mode = 'chat') {
    if (!content.trim() || isLoading) return

    // Optimistic user message
    const tempUserMsg = {
      id: 'user-' + Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempUserMsg])
    setIsLoading(true)

    try {
      const response = await sendMessage(
        content,
        activeChatId,
        mode,
        activeDocument?.id,
        activeDataset?.id
      )

      if (!activeChatId && response.conversation_id) {
        setActiveChatId(response.conversation_id)
        setChatTitle(content.slice(0, 45) + (content.length > 45 ? '...' : ''))
        window.__refreshSidebar?.()
      }

      const assistantMsg = {
        id: response.message_id,
        role: 'assistant',
        content: response.content,
        metadata: response.metadata || {},
        created_at: new Date().toISOString(),
      }

      setMessages(prev => [...prev, assistantMsg])
      window.__refreshSidebar?.()
    } catch (err) {
      console.error('Chat error:', err)
      const errorMsg = {
        id: 'err-' + Date.now(),
        role: 'assistant',
        content: `⚠️ **Error encountered:** ${err.message || 'Unable to generate response. Please try again.'}`,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  // Handle file uploads (PDF / CSV / XLSX)
  async function handleFileUpload(file) {
    if (!file) return
    const ext = file.name.split('.').pop().toLowerCase()
    setIsLoading(true)
    setUploadError(null)

    try {
      if (ext === 'pdf') {
        const doc = await uploadDocument(file, activeChatId)
        setActiveDocument(doc)
        if (!activeChatId && doc.conversation_id) {
          setActiveChatId(doc.conversation_id)
        }
        window.__refreshSidebar?.()
        // Prompt assistant about the document
        await handleSendMessage(`I uploaded the paper "${file.name}". Please summarize the key objectives, methodology, and primary conclusions.`, 'chat')
      } else if (['csv', 'xlsx', 'xls'].includes(ext)) {
        const ds = await uploadDataset(file, activeChatId)
        setActiveDataset(ds)
        if (!activeChatId && ds.conversation_id) {
          setActiveChatId(ds.conversation_id)
        }
        window.__refreshSidebar?.()
        // Prompt assistant about dataset
        await handleSendMessage(`I uploaded the dataset "${file.name}" with ${ds.row_count} rows and ${ds.column_count} columns. Provide an overview and highlight key statistical observations.`, 'analyze')
      } else {
        setUploadError('Unsupported file type. Please upload PDF, CSV, or XLSX.')
      }
    } catch (err) {
      console.error('Upload error:', err)
      setUploadError(err.message || 'Failed to upload and process file')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle Quick Action clicks from WelcomeScreen
  function handleQuickAction(action) {
    if (action.mode === 'upload_pdf') {
      setQuickUploadType('pdf')
      quickFileInputRef.current?.click()
    } else if (action.mode === 'upload_dataset') {
      setQuickUploadType('dataset')
      quickFileInputRef.current?.click()
    } else if (action.prompt) {
      handleSendMessage(action.prompt, action.mode || 'research')
    }
  }

  function handleQuickFileSelect(e) {
    const file = e.target.files?.[0]
    if (file) {
      handleFileUpload(file)
    }
    e.target.value = ''
  }

  // Generate research report
  async function handleGenerateReport() {
    if (!activeChatId || messages.length === 0) {
      alert('Start a research conversation before generating a report.')
      return
    }

    setReportModalOpen(true)
    setIsGeneratingReport(true)
    try {
      const report = await generateReport(activeChatId, `${chatTitle} - Academic Report`)
      setCurrentReport(report)
    } catch (err) {
      console.error('Report error:', err)
      alert('Failed to generate report: ' + err.message)
    } finally {
      setIsGeneratingReport(false)
    }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface-50 dark:bg-surface-950 text-surface-900 dark:text-surface-100 font-sans transition-colors duration-200">
      {/* Hidden file input for quick actions */}
      <input
        ref={quickFileInputRef}
        type="file"
        className="hidden"
        accept={quickUploadType === 'pdf' ? '.pdf' : '.csv,.xlsx,.xls'}
        onChange={handleQuickFileSelect}
      />

      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(prev => !prev)}
        activeChat={activeChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full min-w-0 relative">
        {/* Top Navigation Bar */}
        <header className="h-14 border-b border-surface-200 dark:border-surface-800 bg-white/80 dark:bg-surface-900/80 backdrop-blur-md flex items-center justify-between px-4 z-20 shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 rounded-xl text-surface-500 hover:text-surface-900 dark:hover:text-surface-100 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
                title="Open Sidebar"
              >
                <Menu size={18} />
              </button>
            )}

            <div className="flex items-center gap-2 min-w-0">
              <span className="font-semibold text-sm sm:text-base text-surface-900 dark:text-surface-100 truncate">
                {chatTitle}
              </span>

              {/* Status pill: Provider or Demo Mode */}
              <button
                onClick={() => setSettingsOpen(true)}
                className={`
                  hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors cursor-pointer
                  ${activeConfig?.has_key
                    ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800 hover:bg-emerald-100'
                    : 'bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800 hover:bg-amber-100'}
                `}
                title="Click to configure AI Provider"
              >
                <span className={`w-2 h-2 rounded-full ${activeConfig?.has_key ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
                <span>
                  {activeConfig?.has_key
                    ? `${activeConfig.provider.toUpperCase()} (${activeConfig.model})`
                    : 'Demo Mode (Click to connect)'}
                </span>
              </button>

              {/* Badges for active context */}
              {activeDocument && (
                <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-violet-50 dark:bg-violet-900/30 text-violet-600 dark:text-violet-300 text-xs font-medium border border-violet-200 dark:border-violet-800">
                  <FileText size={12} />
                  <span className="truncate max-w-[130px]">{activeDocument.filename}</span>
                  <button
                    onClick={() => setActiveDocument(null)}
                    className="hover:text-violet-900 dark:hover:text-white"
                  >
                    <X size={11} />
                  </button>
                </div>
              )}

              {activeDataset && (
                <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-300 text-xs font-medium border border-amber-200 dark:border-amber-800">
                  <Table size={12} />
                  <span className="truncate max-w-[130px]">{activeDataset.filename}</span>
                  <button
                    onClick={() => setActiveDataset(null)}
                    className="hover:text-amber-900 dark:hover:text-white"
                  >
                    <X size={11} />
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1.5 sm:gap-2">
            {messages.length > 0 && (
              <button
                onClick={handleGenerateReport}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary-50 dark:bg-primary-900/30 hover:bg-primary-100 dark:hover:bg-primary-900/50 text-primary-600 dark:text-primary-300 text-xs sm:text-sm font-medium border border-primary-200 dark:border-primary-800 transition-colors"
                title="Generate Research Report"
              >
                <FileOutput size={15} />
                <span className="hidden sm:inline">Generate Report</span>
              </button>
            )}

            <button
              onClick={() => setSettingsOpen(true)}
              className="p-2 rounded-xl text-surface-500 hover:text-surface-900 dark:hover:text-surface-100 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
              title="AI Settings"
            >
              <Settings size={18} />
            </button>

            <button
              onClick={handleNewChat}
              className="p-2 rounded-xl text-surface-500 hover:text-surface-900 dark:hover:text-surface-100 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
              title="New Chat"
            >
              <Plus size={18} />
            </button>

            <button
              onClick={toggle}
              className="p-2 rounded-xl text-surface-500 hover:text-surface-900 dark:hover:text-surface-100 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
              title={dark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>

        {/* Upload Error Banner */}
        {uploadError && (
          <div className="bg-red-50 dark:bg-red-900/30 border-b border-red-200 dark:border-red-800 px-4 py-2 flex items-center justify-between text-xs sm:text-sm text-red-600 dark:text-red-300">
            <div className="flex items-center gap-2">
              <AlertCircle size={15} />
              <span>{uploadError}</span>
            </div>
            <button onClick={() => setUploadError(null)} className="p-0.5 hover:opacity-75">
              <X size={14} />
            </button>
          </div>
        )}

        {/* Chat / Welcome Area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <WelcomeScreen onQuickAction={handleQuickAction} />
          ) : (
            <div className="pb-6">
              {/* Display uploaded document status if present */}
              {activeDocument && (
                <div className="max-w-3xl mx-auto px-4 pt-4">
                  <DocumentStatus document={activeDocument} />
                </div>
              )}

              {/* Display uploaded dataset status if present */}
              {activeDataset && (
                <div className="max-w-3xl mx-auto px-4 pt-4">
                  <DatasetStatus dataset={activeDataset} />
                </div>
              )}

              {/* Message List */}
              {messages.map(msg => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onRetry={msg.role === 'assistant' ? () => handleSendMessage(messages[messages.length - 2]?.content || 'Explain again') : null}
                />
              ))}

              {/* Typing indicator */}
              {isLoading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="shrink-0 bg-gradient-to-t from-surface-50 dark:from-surface-950 via-surface-50/80 dark:via-surface-950/80 to-transparent pt-3">
          <ChatInput
            onSend={handleSendMessage}
            onFileUpload={handleFileUpload}
            isLoading={isLoading}
            onCancel={() => {
              abortControllerRef.current?.abort()
              setIsLoading(false)
            }}
          />
        </div>
      </div>

      {/* Report Modal */}
      <ReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        report={currentReport}
        isGenerating={isGeneratingReport}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={cfg => setActiveConfig(cfg)}
      />
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <ChatApp />
    </ThemeProvider>
  )
}
