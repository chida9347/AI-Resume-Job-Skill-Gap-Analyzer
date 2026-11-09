import React from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const GREEN = '#244b3e'
const LEAF = '#89a744'
const CORAL = '#c16f5b'
const MUTED = '#b9c6b2'

function TooltipBox({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <b>{label}</b>
      {payload.map((item) => (
        <span key={item.dataKey}>{item.name}: {Math.round(item.value)}</span>
      ))}
    </div>
  )
}

export function CoverageChart({ comparison, ats }) {
  const data = [
    {
      name: 'Required coverage',
      value: comparison?.required_coverage ?? comparison?.similarity_score ?? 0,
    },
    {
      name: 'Preferred coverage',
      value: comparison?.preferred_coverage ?? 0,
    },
    {
      name: 'Job keywords',
      value: ats?.keyword_match ?? 0,
    },
    {
      name: 'ATS estimate',
      value: ats?.ats_score ?? 0,
    },
  ]

  return (
    <div className="chart-wrap" aria-label="Coverage and estimate chart">
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e3e6dc" />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#6e766e' }} interval={0} tickLine={false} axisLine={false} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#8a9188' }} tickLine={false} axisLine={false} />
          <Tooltip content={<TooltipBox />} cursor={{ fill: 'rgba(137, 167, 68, 0.08)' }} />
          <Bar dataKey="value" name="Score" radius={[3, 3, 0, 0]} maxBarSize={46}>
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={index === 3 ? CORAL : index === 2 ? LEAF : GREEN} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="chart-footnote">Scores are estimates from the supplied text, not an employer ATS result.</p>
    </div>
  )
}

export function AtsBreakdownChart({ ats }) {
  const breakdown = Array.isArray(ats?.breakdown) ? ats.breakdown : []
  const data = breakdown.length
    ? breakdown.map((item) => ({
        name: item.label || item.component,
        value: item.score,
        points: item.points,
      }))
    : Object.entries(ats?.score_breakdown || {}).map(([name, value]) => ({
        name: name.replaceAll('_', ' '),
        value,
        points: value,
      }))

  if (!data.length) return <p className="empty-note">No ATS component detail is available for this saved analysis.</p>

  return (
    <div className="chart-wrap" aria-label="ATS component scores chart">
      <ResponsiveContainer width="100%" height={Math.max(220, data.length * 34)}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 18, left: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e3e6dc" />
          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: '#8a9188' }} tickLine={false} axisLine={false} />
          <YAxis
            type="category"
            dataKey="name"
            width={132}
            tick={{ fontSize: 10, fill: '#5f685f' }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<TooltipBox />} cursor={{ fill: 'rgba(137, 167, 68, 0.08)' }} />
          <Bar dataKey="value" name="Component score" fill={MUTED} radius={[0, 3, 3, 0]} maxBarSize={18}>
            {data.map((entry, index) => (
              <Cell key={`${entry.name}-${index}`} fill={index % 2 === 0 ? LEAF : GREEN} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function JobComponentsChart({ components, labels = {} }) {
  const data = Object.entries(components || {}).map(([key, value]) => ({
    name: labels[key] || key.replaceAll('_', ' '),
    value,
  }))
  if (!data.length) return null

  return (
    <div className="chart-wrap job-chart" aria-label="Job compatibility components chart">
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e3e6dc" />
          <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#6e766e' }} interval={0} tickLine={false} axisLine={false} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#8a9188' }} tickLine={false} axisLine={false} />
          <Tooltip content={<TooltipBox />} cursor={{ fill: 'rgba(137, 167, 68, 0.08)' }} />
          <Bar dataKey="value" name="Score" fill={GREEN} radius={[3, 3, 0, 0]} maxBarSize={40} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
