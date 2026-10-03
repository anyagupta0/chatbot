import { Search, Globe, FileText, BarChart3, GitCompare, FileOutput } from 'lucide-react'

export default function WelcomeScreen({ onQuickAction }) {
  const actions = [
    {
      icon: Search,
      label: 'Search Research Papers',
      description: 'Find papers from Semantic Scholar, arXiv, and more',
      mode: 'research',
      prompt: 'Find recent research papers about ',
      color: 'from-blue-500 to-cyan-500',
      bg: 'bg-blue-50 dark:bg-blue-900/20',
    },
    {
      icon: Globe,
      label: 'Research a Topic',
      description: 'Deep dive into any research topic',
      mode: 'research',
      prompt: 'Research the topic: ',
      color: 'from-emerald-500 to-teal-500',
      bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    },
    {
      icon: FileText,
      label: 'Analyze a PDF',
      description: 'Upload and analyze research papers',
      mode: 'upload_pdf',
      prompt: '',
      color: 'from-violet-500 to-purple-500',
      bg: 'bg-violet-50 dark:bg-violet-900/20',
    },
    {
      icon: BarChart3,
      label: 'Analyze Dataset',
      description: 'Upload CSV/XLSX for data insights',
      mode: 'upload_dataset',
      prompt: '',
      color: 'from-amber-500 to-orange-500',
      bg: 'bg-amber-50 dark:bg-amber-900/20',
    },
    {
      icon: GitCompare,
      label: 'Compare Papers',
      description: 'Compare multiple research papers',
      mode: 'research',
      prompt: 'Compare these research papers: ',
      color: 'from-rose-500 to-pink-500',
      bg: 'bg-rose-50 dark:bg-rose-900/20',
    },
    {
      icon: FileOutput,
      label: 'Generate Report',
      description: 'Create structured research reports',
      mode: 'report',
      prompt: 'Generate a research report on ',
      color: 'from-indigo-500 to-blue-500',
      bg: 'bg-indigo-50 dark:bg-indigo-900/20',
    },
  ]

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-12 animate-fade-in">
      {/* Hero */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/20">
            <span className="text-white font-bold text-xl">R</span>
          </div>
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold text-surface-900 dark:text-white mb-3 tracking-tight">
          Research smarter.<br />
          <span className="text-primary-600 dark:text-primary-400">Understand deeper.</span>
        </h1>
        <p className="text-surface-500 dark:text-surface-400 text-lg max-w-md mx-auto leading-relaxed">
          Your AI assistant for research, documents, and data analysis.
        </p>
      </div>

      {/* Quick Actions Grid */}
      <div className="w-full max-w-2xl">
        <p className="text-sm font-medium text-surface-400 dark:text-surface-500 mb-4 text-center">
          What would you like to explore?
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {actions.map(action => (
            <button
              key={action.label}
              onClick={() => onQuickAction(action)}
              className={`
                group relative flex flex-col items-start gap-2 p-4 rounded-xl
                border border-surface-200 dark:border-surface-700
                bg-white dark:bg-surface-800
                hover:border-primary-300 dark:hover:border-primary-600
                hover:shadow-md hover:shadow-primary-500/5
                transition-all duration-200
                text-left
              `}
            >
              <div className={`p-2 rounded-lg ${action.bg}`}>
                <action.icon size={18} className="text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-surface-800 dark:text-surface-200 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                  {action.label}
                </p>
                <p className="text-xs text-surface-400 dark:text-surface-500 mt-0.5 leading-relaxed">
                  {action.description}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
