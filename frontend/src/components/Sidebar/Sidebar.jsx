import { useState, useEffect } from 'react'
import {
  Plus, Search, MessageSquare, Settings, HelpCircle, User,
  Trash2, Edit3, Check, X, ChevronLeft, Menu
} from 'lucide-react'
import { getChats, deleteChat, renameChat, searchChats, clearAllChats } from '../../services/api'

export default function Sidebar({ 
  isOpen, onToggle, activeChat, onSelectChat, onNewChat, onOpenSettings
}) {
  const [chats, setChats] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editTitle, setEditTitle] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleClearAll() {
    if (window.confirm('Are you sure you want to delete all chat history and uploaded data?')) {
      try {
        await clearAllChats()
        setChats([])
        onNewChat()
      } catch (err) {
        console.error('Failed to clear all history:', err)
      }
    }
  }

  useEffect(() => {
    loadChats()
  }, [])

  async function loadChats() {
    try {
      setLoading(true)
      const data = await getChats()
      setChats(data.conversations || [])
    } catch (err) {
      console.error('Failed to load chats:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleSearch(query) {
    setSearchQuery(query)
    if (!query.trim()) {
      loadChats()
      return
    }
    try {
      const data = await searchChats(query)
      setChats(data.conversations || [])
    } catch (err) {
      console.error('Search failed:', err)
    }
  }

  async function handleDelete(e, chatId) {
    e.stopPropagation()
    try {
      await deleteChat(chatId)
      setChats(prev => prev.filter(c => c.id !== chatId))
      if (activeChat === chatId) onNewChat()
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  async function handleRename(chatId) {
    if (!editTitle.trim()) {
      setEditingId(null)
      return
    }
    try {
      await renameChat(chatId, editTitle)
      setChats(prev => prev.map(c => c.id === chatId ? { ...c, title: editTitle } : c))
      setEditingId(null)
    } catch (err) {
      console.error('Rename failed:', err)
    }
  }

  function startEdit(e, chat) {
    e.stopPropagation()
    setEditingId(chat.id)
    setEditTitle(chat.title)
  }

  // Group chats by date
  function groupByDate(chatList) {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    const weekAgo = new Date(today)
    weekAgo.setDate(weekAgo.getDate() - 7)

    const groups = { Today: [], Yesterday: [], 'This Week': [], Older: [] }

    chatList.forEach(chat => {
      const date = new Date(chat.updated_at || chat.created_at)
      if (date >= today) groups.Today.push(chat)
      else if (date >= yesterday) groups.Yesterday.push(chat)
      else if (date >= weekAgo) groups['This Week'].push(chat)
      else groups.Older.push(chat)
    })

    return groups
  }

  const grouped = groupByDate(chats)

  // Expose loadChats for parent
  useEffect(() => {
    window.__refreshSidebar = loadChats
  }, [])

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      <aside
        className={`
          fixed lg:relative z-50 h-full flex flex-col
          bg-white dark:bg-surface-900 border-r border-surface-200 dark:border-surface-800
          transition-all duration-300 ease-in-out
          ${isOpen ? 'w-72 translate-x-0' : 'w-0 -translate-x-full lg:w-0 lg:-translate-x-full'}
        `}
      >
        <div className="flex flex-col h-full w-72 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-surface-100 dark:border-surface-800">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
                <span className="text-white font-bold text-sm">R</span>
              </div>
              <span className="font-semibold text-surface-900 dark:text-white text-lg">ResearchAI</span>
            </div>
            <button
              onClick={onToggle}
              className="p-1.5 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800 text-surface-500 transition-colors"
            >
              <ChevronLeft size={18} />
            </button>
          </div>

          {/* New Chat Button */}
          <div className="p-3">
            <button
              onClick={() => { onNewChat(); if (window.innerWidth < 1024) onToggle() }}
              className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl border border-surface-200 dark:border-surface-700
                         hover:bg-surface-50 dark:hover:bg-surface-800 text-surface-700 dark:text-surface-300
                         transition-all duration-200 group"
            >
              <Plus size={18} className="text-primary-600 group-hover:rotate-90 transition-transform duration-200" />
              <span className="text-sm font-medium">New Chat</span>
            </button>
          </div>

          {/* Search */}
          <div className="px-3 pb-2">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-surface-400" />
              <input
                type="text"
                placeholder="Search chats..."
                value={searchQuery}
                onChange={e => handleSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm rounded-lg bg-surface-50 dark:bg-surface-800 
                           border border-surface-200 dark:border-surface-700
                           text-surface-900 dark:text-surface-100
                           placeholder:text-surface-400 focus:outline-none focus:ring-2 focus:ring-primary-500/30
                           focus:border-primary-500 transition-all"
              />
            </div>
          </div>

          {/* Chat List */}
          <div className="flex-1 overflow-y-auto px-2 pb-2">
            {Object.entries(grouped).map(([label, items]) =>
              items.length > 0 && (
                <div key={label} className="mb-3">
                  <p className="px-3 py-1.5 text-xs font-medium text-surface-400 dark:text-surface-500 uppercase tracking-wider">
                    {label}
                  </p>
                  {items.map(chat => (
                    <div
                      key={chat.id}
                      onClick={() => { onSelectChat(chat.id); if (window.innerWidth < 1024) onToggle() }}
                      className={`
                        group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer mb-0.5
                        transition-all duration-150
                        ${activeChat === chat.id
                          ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                          : 'hover:bg-surface-50 dark:hover:bg-surface-800 text-surface-700 dark:text-surface-300'}
                      `}
                    >
                      <MessageSquare size={15} className="shrink-0 opacity-50" />
                      {editingId === chat.id ? (
                        <div className="flex-1 flex items-center gap-1">
                          <input
                            value={editTitle}
                            onChange={e => setEditTitle(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleRename(chat.id)}
                            className="flex-1 text-sm bg-white dark:bg-surface-700 border border-primary-300 rounded px-2 py-0.5 focus:outline-none"
                            autoFocus
                            onClick={e => e.stopPropagation()}
                          />
                          <button onClick={() => handleRename(chat.id)} className="p-0.5 text-emerald-500">
                            <Check size={14} />
                          </button>
                          <button onClick={() => setEditingId(null)} className="p-0.5 text-surface-400">
                            <X size={14} />
                          </button>
                        </div>
                      ) : (
                        <>
                          <span className="flex-1 text-sm truncate">{chat.title}</span>
                          <div className="hidden group-hover:flex items-center gap-0.5">
                            <button
                              onClick={e => startEdit(e, chat)}
                              className="p-1 rounded hover:bg-surface-200 dark:hover:bg-surface-600"
                            >
                              <Edit3 size={12} />
                            </button>
                            <button
                              onClick={e => handleDelete(e, chat.id)}
                              className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500"
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )
            )}

            {chats.length === 0 && !loading && (
              <div className="text-center py-8 text-surface-400 text-sm">
                No conversations yet
              </div>
            )}
          </div>

          {/* Bottom Links */}
          <div className="border-t border-surface-100 dark:border-surface-800 p-2 space-y-0.5">
            {chats.length > 0 && (
              <button
                onClick={handleClearAll}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 text-xs font-medium transition-colors"
                title="Clear all conversations"
              >
                <Trash2 size={15} />
                <span>Clear All History</span>
              </button>
            )}
            {[
              { icon: Settings, label: 'Settings', onClick: onOpenSettings },
              { icon: HelpCircle, label: 'Help' },
              { icon: User, label: 'Profile' },
            ].map(({ icon: Icon, label, onClick }) => (
              <button
                key={label}
                onClick={onClick}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg
                           hover:bg-surface-50 dark:hover:bg-surface-800
                           text-surface-500 dark:text-surface-400 text-sm transition-colors"
              >
                <Icon size={16} />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>
      </aside>
    </>
  )
}
