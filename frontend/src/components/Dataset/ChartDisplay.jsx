import { useMemo } from 'react'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e', '#8b5cf6', '#ec4899', '#14b8a6']

export default function ChartDisplay({ chartData }) {
  if (!chartData || chartData.error) {
    return null
  }

  const { type, data, xKey, yKey, columns } = chartData

  const tooltipStyle = {
    contentStyle: {
      backgroundColor: '#1f2937',
      border: 'none',
      borderRadius: '8px',
      color: '#f3f4f6',
      fontSize: '12px',
    },
  }

  if (!data || data.length === 0) {
    return (
      <div className="p-4 text-center text-surface-400 text-sm border border-surface-200 dark:border-surface-700 rounded-xl">
        No data available for chart
      </div>
    )
  }

  function renderChart() {
    switch (type) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
              <XAxis 
                dataKey={xKey} 
                tick={{ fontSize: 11, fill: '#6b7280' }} 
                angle={data.length > 8 ? -45 : 0}
                textAnchor={data.length > 8 ? 'end' : 'middle'}
                height={data.length > 8 ? 70 : 30}
              />
              <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey={yKey} fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={50} />
            </BarChart>
          </ResponsiveContainer>
        )

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
              <XAxis dataKey={xKey} tick={{ fontSize: 11, fill: '#6b7280' }} />
              <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} />
              <Tooltip {...tooltipStyle} />
              <Line 
                type="monotone" dataKey={yKey} stroke="#6366f1" 
                strokeWidth={2} dot={{ r: 4, fill: '#6366f1' }} 
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%" cy="50%"
                innerRadius={60} outerRadius={100}
                dataKey="value"
                nameKey="name"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={{ stroke: '#9ca3af', strokeWidth: 1 }}
              >
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip {...tooltipStyle} />
              <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
        )

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
              <XAxis dataKey={xKey} tick={{ fontSize: 11, fill: '#6b7280' }} name={xKey} />
              <YAxis dataKey={yKey} tick={{ fontSize: 11, fill: '#6b7280' }} name={yKey} />
              <Tooltip {...tooltipStyle} />
              <Scatter data={data} fill="#6366f1" />
            </ScatterChart>
          </ResponsiveContainer>
        )

      case 'correlation':
        // Render as a simple table for correlation matrix
        return (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  <th className="px-2 py-1 text-left font-medium text-surface-500"></th>
                  {columns?.map(col => (
                    <th key={col} className="px-2 py-1 text-center font-medium text-surface-500 max-w-[80px] truncate">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map(row => (
                  <tr key={row.name}>
                    <td className="px-2 py-1 font-medium text-surface-700 dark:text-surface-300 max-w-[80px] truncate">
                      {row.name}
                    </td>
                    {columns?.map(col => {
                      const val = row[col]
                      const absVal = Math.abs(val || 0)
                      const bg = val > 0
                        ? `rgba(99, 102, 241, ${absVal * 0.5})`
                        : `rgba(244, 63, 94, ${absVal * 0.5})`
                      return (
                        <td
                          key={col}
                          className="px-2 py-1 text-center font-mono"
                          style={{ backgroundColor: bg }}
                        >
                          {val?.toFixed?.(2) ?? '-'}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )

      default:
        return <p className="text-sm text-surface-400">Unsupported chart type: {type}</p>
    }
  }

  return (
    <div className="mt-3 p-4 border border-surface-200 dark:border-surface-700 rounded-xl bg-white dark:bg-surface-800/50 animate-scale-in">
      {renderChart()}
    </div>
  )
}
