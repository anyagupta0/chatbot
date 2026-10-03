import { useState, useEffect } from 'react'
import { X, Key, Check, AlertCircle, Eye, EyeOff, Save, Sparkles, Cpu } from 'lucide-react'
import { getSettings, updateSettings } from '../../services/api'

const PROVIDER_PRESETS = {
  openai: {
    label: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    defaultModel: 'gpt-4o',
    placeholder: 'sk-...',
  },
  gemini: {
    label: 'Google Gemini',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/',
    models: ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-pro'],
    defaultModel: 'gemini-2.5-flash',
    placeholder: 'AIzaSy...',
  },
  groq: {
    label: 'Groq (Fast / Free Tier)',
    baseUrl: 'https://api.groq.com/openai/v1',
    models: ['openai/gpt-oss-20b', 'qwen/qwen3.8-27b', 'openai/gpt-oss-120b'],
    defaultModel: 'openai/gpt-oss-20b',
    placeholder: 'gsk_...',
  },
  openrouter: {
    label: 'OpenRouter',
    baseUrl: 'https://openrouter.ai/api/v1',
    models: ['openai/gpt-4o-mini', 'anthropic/claude-3.5-sonnet', 'meta-llama/llama-3.3-70b-instruct'],
    defaultModel: 'openai/gpt-4o-mini',
    placeholder: 'sk-or-...',
  },
  local: {
    label: 'Local LLM (Ollama)',
    baseUrl: 'http://localhost:11434/v1',
    models: ['llama3.2', 'mistral', 'qwen2.5'],
    defaultModel: 'llama3.2',
    placeholder: 'ollama (no key required)',
  },
}

export default function SettingsModal({ isOpen, onClose, onSaved }) {
  const [provider, setProvider] = useState('openai')
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('gpt-4o')
  const [baseUrl, setBaseUrl] = useState('https://api.openai.com/v1')
  const [showKey, setShowKey] = useState(false)
  const [status, setStatus] = useState(null) // 'loading' | 'success' | 'error'
  const [statusMsg, setStatusMsg] = useState('')
  const [activeConfig, setActiveConfig] = useState(null)

  useEffect(() => {
    if (isOpen) {
      loadCurrentSettings()
    }
  }, [isOpen])

  async function loadCurrentSettings() {
    try {
      const data = await getSettings()
      setActiveConfig(data)
      const currentProvider = data.provider || 'openai'
      setProvider(currentProvider)
      setModel(data.model || 'gpt-4o')
      setBaseUrl(data.base_url || 'https://api.openai.com/v1')
      setApiKey('')
    } catch (err) {
      console.error('Failed to load settings:', err)
    }
  }

  function handleProviderChange(newProvider) {
    setProvider(newProvider)
    const preset = PROVIDER_PRESETS[newProvider]
    if (preset) {
      setBaseUrl(preset.baseUrl)
      setModel(preset.defaultModel)
    }
  }

  async function handleSave(e) {
    e?.preventDefault()
    setStatus('loading')
    setStatusMsg('')

    try {
      const payload = {
        provider,
        model,
        base_url: baseUrl,
      }
      if (apiKey.trim()) {
        payload.api_key = apiKey.trim()
      } else if (provider === 'local') {
        payload.api_key = 'local-ollama'
      }

      const res = await updateSettings(payload)
      setStatus('success')
      setStatusMsg('AI connection updated successfully!')
      setActiveConfig(res)
      setApiKey('')
      onSaved?.(res)
      setTimeout(() => {
        setStatus(null)
        onClose()
      }, 1200)
    } catch (err) {
      setStatus('error')
      setStatusMsg(err.message || 'Failed to update settings')
    }
  }

  if (!isOpen) return null

  const preset = PROVIDER_PRESETS[provider] || PROVIDER_PRESETS.openai

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fade-in">
      <div className="bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-surface-100 dark:border-surface-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-primary-100 dark:bg-primary-900/40 text-primary-600 dark:text-primary-400">
              <Cpu size={20} />
            </div>
            <div>
              <h2 className="font-semibold text-base text-surface-900 dark:text-surface-100">
                AI Provider Settings
              </h2>
              <p className="text-xs text-surface-400">
                Connect your OpenAI, Gemini, or Groq API key
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Current status pill */}
        <div className="px-6 pt-4">
          <div className="flex items-center justify-between p-3 rounded-xl bg-surface-50 dark:bg-surface-800/60 border border-surface-200 dark:border-surface-700">
            <div className="flex items-center gap-2">
              <div className={`w-2.5 h-2.5 rounded-full ${activeConfig?.has_key ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
              <span className="text-xs font-medium text-surface-700 dark:text-surface-300">
                {activeConfig?.has_key
                  ? `Connected: ${activeConfig.provider.toUpperCase()} (${activeConfig.model})`
                  : 'Running in Demo Mode (Mock AI)'}
              </span>
            </div>
            {activeConfig?.has_key && (
              <span className="text-[11px] text-surface-400 font-mono">
                {activeConfig.masked_key}
              </span>
            )}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSave} className="p-6 space-y-4">
          {/* Provider Select */}
          <div>
            <label className="block text-xs font-semibold text-surface-600 dark:text-surface-400 uppercase tracking-wider mb-1.5">
              Provider
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {Object.entries(PROVIDER_PRESETS).map(([key, item]) => (
                <button
                  type="button"
                  key={key}
                  onClick={() => handleProviderChange(key)}
                  className={`
                    p-2.5 text-xs font-medium rounded-xl border text-left transition-all
                    ${provider === key
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-300'
                      : 'border-surface-200 dark:border-surface-700 hover:bg-surface-50 dark:hover:bg-surface-800 text-surface-700 dark:text-surface-300'}
                  `}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {/* API Key */}
          {provider !== 'local' && (
            <div>
              <label className="block text-xs font-semibold text-surface-600 dark:text-surface-400 uppercase tracking-wider mb-1.5">
                API Key
              </label>
              <div className="relative">
                <input
                  type={showKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={e => setApiKey(e.target.value)}
                  placeholder={activeConfig?.has_key ? '•••••••••••••••••••• (Leave blank to keep current)' : preset.placeholder}
                  className="w-full pl-3 pr-10 py-2.5 text-sm rounded-xl bg-surface-50 dark:bg-surface-800 
                             border border-surface-200 dark:border-surface-700
                             text-surface-900 dark:text-surface-100 placeholder:text-surface-400
                             focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600 dark:hover:text-surface-300"
                >
                  {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          )}

          {/* Model selection */}
          <div>
            <label className="block text-xs font-semibold text-surface-600 dark:text-surface-400 uppercase tracking-wider mb-1.5">
              Model
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={model}
                onChange={e => setModel(e.target.value)}
                placeholder="gpt-4o"
                className="flex-1 px-3 py-2 text-sm rounded-xl bg-surface-50 dark:bg-surface-800 
                           border border-surface-200 dark:border-surface-700
                           text-surface-900 dark:text-surface-100 placeholder:text-surface-400
                           focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500 font-mono text-xs"
              />
            </div>
            {preset.models && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {preset.models.map(m => (
                  <button
                    type="button"
                    key={m}
                    onClick={() => setModel(m)}
                    className={`
                      text-[11px] px-2 py-0.5 rounded-lg border transition-colors
                      ${model === m
                        ? 'bg-primary-50 dark:bg-primary-900/40 border-primary-400 text-primary-600 dark:text-primary-300 font-medium'
                        : 'border-surface-200 dark:border-surface-700 text-surface-500 hover:bg-surface-50 dark:hover:bg-surface-800'}
                    `}
                  >
                    {m}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Status feedback */}
          {statusMsg && (
            <div className={`p-3 rounded-xl text-xs flex items-center gap-2 ${status === 'error' ? 'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-300 border border-red-200 dark:border-red-800' : 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'}`}>
              {status === 'error' ? <AlertCircle size={15} /> : <Check size={15} />}
              <span>{statusMsg}</span>
            </div>
          )}

          {/* Footer buttons */}
          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium rounded-xl text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={status === 'loading'}
              className="flex items-center gap-2 px-5 py-2 text-xs font-medium rounded-xl bg-primary-600 hover:bg-primary-700 text-white shadow-sm hover:shadow transition-all disabled:opacity-50"
            >
              <Save size={14} />
              <span>{status === 'loading' ? 'Saving...' : 'Save & Connect'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
