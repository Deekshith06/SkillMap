/**
 * Insights.jsx — Data visualisation page.
 *
 * Charts:
 * - Cluster distribution pie / donut chart
 * - Skill co-occurrence heatmap (Recharts)
 * - All charts: tooltips, legends, accessible colours, pattern/label
 * - Loading skeletons, error/empty states
 */

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, LabelList,
  ScatterChart, Scatter, ZAxis,
} from 'recharts';
import { BarChart3, RotateCcw, PieChartIcon } from 'lucide-react';
import { useAppData } from '../context/AppContext';
import Skeleton from '../components/Skeleton';

// ── Chart palette (accessible, never rely on colour alone) ──────

const PIE_COLORS = [
  '#ff771c', '#546877', '#d4622b', '#3a7ca5',
  '#e8913a', '#6b8f71', '#c75146', '#8e7cc3',
  '#5b9bd5', '#70ad47', '#ffc000', '#4472c4',
];

const PIE_PATTERNS = [
  'none', 'url(#pattern-stripe)', 'none', 'url(#pattern-dot)',
  'none', 'url(#pattern-stripe)', 'none', 'url(#pattern-dot)',
];

// ── Animations ──────────────────────────────────────────────────

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] } },
};

const stagger = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

// ── Custom tooltip ──────────────────────────────────────────────

function PieTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { name, resume_count, share } = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <strong>{name}</strong>
      <span>{resume_count?.toLocaleString()} resumes ({share}%)</span>
    </div>
  );
}

function BarTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <strong>{d.skill || d.name}</strong>
      <span>{(d.count ?? d.value)?.toLocaleString()} occurrences</span>
    </div>
  );
}

// ── Custom pie label (non-colour encoding) ──────────────────────

function renderPieLabel({ cx, cy, midAngle, innerRadius, outerRadius, share, name }) {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 1.4;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  if (share < 5) return null; // Don't render tiny labels

  return (
    <text
      x={x} y={y}
      fill="var(--dark)"
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      fontSize={11}
    >
      {name} ({share}%)
    </text>
  );
}

// ── Insights Page ───────────────────────────────────────────────

export default function Insights() {
  const { stats, loading, error, refreshData } = useAppData();

  // ── Cluster distribution data ─────────────────────────────
  const clusterData = useMemo(() => {
    const dist = stats?.cluster_distribution || [];
    return dist.map((c) => ({
      name: c.name,
      resume_count: c.resume_count,
      share: c.share,
    }));
  }, [stats]);

  // ── Skill distribution data ───────────────────────────────
  const skillData = useMemo(() => {
    const skills = stats?.skill_distribution || stats?.top_skills || [];
    return skills.slice(0, 15).map((s) => ({
      skill: s.skill,
      count: s.count,
    }));
  }, [stats]);

  // ── Heatmap data (skill co-occurrence) ────────────────────
  const heatmapData = useMemo(() => {
    if (!stats?.cluster_distribution) return [];

    const allSkills = new Set();
    stats.cluster_distribution.forEach((c) => {
      (c.top_skills || []).forEach((s) => allSkills.add(s));
    });

    const skillArr = [...allSkills].slice(0, 10);
    const points = [];

    for (let i = 0; i < skillArr.length; i++) {
      for (let j = 0; j < skillArr.length; j++) {
        // Count how many clusters share both skills
        let coOccurrence = 0;
        stats.cluster_distribution.forEach((c) => {
          const cs = new Set(c.top_skills || []);
          if (cs.has(skillArr[i]) && cs.has(skillArr[j])) {
            coOccurrence++;
          }
        });
        points.push({
          x: i,
          y: j,
          xLabel: skillArr[i],
          yLabel: skillArr[j],
          value: coOccurrence,
        });
      }
    }

    return { points, labels: skillArr };
  }, [stats]);

  // ── Error state ─────────────────────────────────────────────
  if (error) {
    return (
      <div className="page-state page-state--error">
        <RotateCcw size={28} />
        <h2>Failed to load insights</h2>
        <p>{error}</p>
        <button className="btn-primary" onClick={refreshData}>
          <RotateCcw size={14} /> Retry
        </button>
      </div>
    );
  }

  return (
    <motion.div
      className="insights-page"
      variants={stagger}
      initial="hidden"
      animate="show"
    >
      <motion.div className="page-header" variants={fadeUp}>
        <h1>Insights</h1>
        <p>Cluster distribution, skill analytics, and co-occurrence patterns.</p>
      </motion.div>

      {/* Cluster Distribution — Donut */}
      <motion.section className="panel" variants={fadeUp}>
        <div className="panel__header">
          <h2>Cluster Distribution</h2>
          <p>Proportional breakdown of resume clusters.</p>
        </div>

        <div className="chart-container chart-container--pie">
          {loading ? (
            <Skeleton height="300px" borderRadius="12px" />
          ) : clusterData.length > 0 ? (
            <ResponsiveContainer width="100%" height={360}>
              <PieChart>
                <defs>
                  <pattern id="pattern-stripe" patternUnits="userSpaceOnUse" width="4" height="4">
                    <path d="M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2" stroke="rgba(255,255,255,0.4)" strokeWidth="1" />
                  </pattern>
                  <pattern id="pattern-dot" patternUnits="userSpaceOnUse" width="4" height="4">
                    <circle cx="2" cy="2" r="1" fill="rgba(255,255,255,0.3)" />
                  </pattern>
                </defs>
                <Pie
                  data={clusterData}
                  dataKey="resume_count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={130}
                  paddingAngle={2}
                  label={renderPieLabel}
                  labelLine={false}
                >
                  {clusterData.map((_, i) => (
                    <Cell
                      key={i}
                      fill={PIE_COLORS[i % PIE_COLORS.length]}
                      stroke="var(--bg)"
                      strokeWidth={2}
                    />
                  ))}
                </Pie>
                <Tooltip content={<PieTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  iconType="circle"
                  formatter={(value) => (
                    <span style={{ color: 'var(--dark)', fontSize: '12px' }}>{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="chart-empty">
              <PieChartIcon size={24} />
              <p>No cluster data available.</p>
            </div>
          )}
        </div>
      </motion.section>

      {/* Skill Distribution — Bar */}
      <motion.section className="panel" variants={fadeUp}>
        <div className="panel__header">
          <h2>Skill Distribution</h2>
          <p>Top-15 skills across all analysed resumes.</p>
        </div>

        <div className="chart-container chart-container--bar">
          {loading ? (
            <Skeleton height="350px" borderRadius="12px" />
          ) : skillData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                data={skillData}
                layout="vertical"
                margin={{ top: 5, right: 40, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--secondary)" opacity={0.15} />
                <XAxis type="number" stroke="var(--secondary)" fontSize={11} />
                <YAxis
                  type="category"
                  dataKey="skill"
                  width={120}
                  tick={{ fill: 'var(--dark)', fontSize: 11 }}
                  stroke="var(--secondary)"
                />
                <Tooltip content={<BarTooltip />} />
                <Bar dataKey="count" radius={[0, 6, 6, 0]} maxBarSize={24}>
                  {skillData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                  <LabelList dataKey="count" position="right" fill="var(--dark)" fontSize={10} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="chart-empty">
              <BarChart3 size={24} />
              <p>No skill data available.</p>
            </div>
          )}
        </div>
      </motion.section>

      {/* Skill Co-occurrence Heatmap */}
      <motion.section className="panel" variants={fadeUp}>
        <div className="panel__header">
          <h2>Skill Co-occurrence</h2>
          <p>How often skills appear together across clusters.</p>
        </div>

        <div className="chart-container">
          {loading ? (
            <Skeleton height="320px" borderRadius="12px" />
          ) : heatmapData.points?.length > 0 ? (
            <div className="heatmap-grid">
              <div className="heatmap-header">
                <div className="heatmap-corner" />
                {heatmapData.labels.map((label) => (
                  <div key={label} className="heatmap-col-label" title={label}>
                    {label.length > 8 ? label.slice(0, 8) + '…' : label}
                  </div>
                ))}
              </div>
              {heatmapData.labels.map((rowLabel, ri) => (
                <div key={rowLabel} className="heatmap-row">
                  <div className="heatmap-row-label" title={rowLabel}>
                    {rowLabel.length > 10 ? rowLabel.slice(0, 10) + '…' : rowLabel}
                  </div>
                  {heatmapData.labels.map((_, ci) => {
                    const point = heatmapData.points.find(
                      (p) => p.x === ci && p.y === ri
                    );
                    const val = point?.value ?? 0;
                    const maxVal = Math.max(
                      ...heatmapData.points.map((p) => p.value),
                      1
                    );
                    const intensity = val / maxVal;
                    return (
                      <div
                        key={ci}
                        className="heatmap-cell"
                        style={{
                          backgroundColor: `rgba(255, 119, 28, ${intensity * 0.8 + 0.05})`,
                        }}
                        title={`${rowLabel} × ${heatmapData.labels[ci]}: ${val}`}
                        role="img"
                        aria-label={`${rowLabel} and ${heatmapData.labels[ci]}: co-occurrence ${val}`}
                      >
                        {val > 0 && <span>{val}</span>}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          ) : (
            <div className="chart-empty">
              <BarChart3 size={24} />
              <p>No co-occurrence data available.</p>
            </div>
          )}
        </div>
      </motion.section>
    </motion.div>
  );
}
