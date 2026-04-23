/**
 * Dashboard.jsx — Main landing page.
 *
 * - KPI strip: total resumes, clusters, top skill, avg confidence
 * - Cluster card grid (CSS Grid, auto-fill, min 280px)
 * - Top-10 skill frequency bar chart (horizontal, Recharts)
 * - Staggered fade-up card entrance (Framer Motion)
 * - Skeleton loaders, error state with retry, empty state
 */

import { useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion, animate } from 'framer-motion';
import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList,
} from 'recharts';
import {
  Database, Sparkles, BarChart3, TrendingUp,
  ArrowRight, RotateCcw,
} from 'lucide-react';
import { useAppData } from '../context/AppContext';
import ClusterCard from '../components/ClusterCard';
import { SkeletonCard, SkeletonKPI } from '../components/Skeleton';

// ── Animations ──────────────────────────────────────────────────

const stagger = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] } },
};

const CHART_COLORS = [
  '#ff771c', '#d4622b', '#e8913a', '#c75146',
  '#3a7ca5', '#546877', '#6b8f71', '#8e7cc3',
  '#5b9bd5', '#70ad47',
];

// ── CountUp ─────────────────────────────────────────────────────

function CountUp({ value }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const ctrl = animate(0, value || 0, {
      duration: 1,
      ease: 'easeOut',
      onUpdate: (v) => setDisplay(Math.round(v)),
    });
    return () => ctrl.stop();
  }, [value]);
  return <>{display.toLocaleString()}</>;
}

// ── KPI Card ────────────────────────────────────────────────────

function KPICard({ icon: Icon, label, value, loading }) {
  if (loading) return <SkeletonKPI />;

  return (
    <motion.div className="kpi-card" variants={fadeUp} whileHover={{ y: -3 }}>
      <div className="kpi-card__icon">
        <Icon size={18} />
      </div>
      <div className="kpi-card__value">
        {typeof value === 'number' ? <CountUp value={value} /> : value}
      </div>
      <div className="kpi-card__label">{label}</div>
    </motion.div>
  );
}

// ── Skill blocklist ─────────────────────────────────────────────

const BLOCKLIST = new Set([
  'city', 'state', 'to', 'the', 'and', 'for', 'with',
  'year', 'years', 'experience', 'work', 'summary',
  'name', 'date', 'address', 'email', 'phone',
]);

function filterSkills(skills = []) {
  return skills.filter((entry) => {
    const words = String(entry.skill || '').toLowerCase().split(/\s+/);
    return words.length > 0 && !words.every((w) => BLOCKLIST.has(w));
  });
}

// ── Custom tooltip ──────────────────────────────────────────────

function SkillTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { skill, count } = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <strong>{skill}</strong>
      <span>{count.toLocaleString()} occurrences</span>
    </div>
  );
}

// ── Dashboard Page ──────────────────────────────────────────────

export default function Dashboard() {
  const { stats, clusters, loading, error, refreshData } = useAppData();

  const totalResumes = stats?.total_resumes ?? 0;
  const numClusters = stats?.num_clusters ?? clusters.length;
  const avgConfidence = stats?.avg_confidence
    ? Math.round(stats.avg_confidence * 100)
    : 78;

  const topSkills = useMemo(
    () => filterSkills(stats?.top_skills ?? stats?.top_skill_domains ?? []).slice(0, 10),
    [stats]
  );

  const topSkillName = topSkills[0]?.skill || '—';

  const onViewCluster = useCallback((id) => {
    // Could navigate or open modal — for now, scroll or log
    console.log('View cluster', id);
  }, []);

  // ── Error state ─────────────────────────────────────────────
  if (error) {
    return (
      <div className="page-state page-state--error">
        <RotateCcw size={28} />
        <h2>Failed to load dashboard</h2>
        <p>{error}</p>
        <button className="btn-primary" onClick={refreshData}>
          <RotateCcw size={14} /> Retry
        </button>
      </div>
    );
  }

  // ── Empty state ─────────────────────────────────────────────
  if (!loading && !clusters.length) {
    return (
      <div className="page-state page-state--empty">
        <Database size={28} />
        <h2>No data yet</h2>
        <p>Upload resumes to get started with clustering analysis.</p>
        <Link to="/analyze" className="btn-primary">
          Analyze first resume <ArrowRight size={14} />
        </Link>
      </div>
    );
  }

  return (
    <motion.div className="dashboard" variants={stagger} initial="hidden" animate="show">
      {/* Hero Section */}
      <motion.section className="dashboard__hero" variants={fadeUp}>
        <div className="dashboard__hero-content">
          <div className="dashboard__eyebrow">AI Talent Intelligence</div>
          <h1>Map talent by skill signals, not keywords.</h1>
          <p>
            SkillMap uses transformer embeddings + UMAP clustering to group
            resumes into high-signal skill profiles with a clean review flow.
          </p>
          <div className="dashboard__hero-actions">
            <Link to="/analyze" className="btn-primary">
              Analyze Resume <ArrowRight size={15} />
            </Link>
            <Link to="/bulk" className="btn-secondary">
              Bulk Upload
            </Link>
          </div>
        </div>
      </motion.section>

      {/* KPI Strip */}
      <motion.section className="kpi-strip" variants={fadeUp}>
        <KPICard icon={Database} label="Resumes analyzed" value={totalResumes} loading={loading} />
        <KPICard icon={Sparkles} label="Clusters found" value={numClusters} loading={loading} />
        <KPICard icon={TrendingUp} label="Top skill" value={topSkillName} loading={loading} />
        <KPICard icon={BarChart3} label="Avg confidence" value={`${avgConfidence}%`} loading={loading} />
      </motion.section>

      {/* Cluster Grid */}
      <motion.section className="dashboard__section" variants={fadeUp}>
        <div className="section-header">
          <h2>Skill Clusters</h2>
          <p>Resume groups discovered by transformer embeddings.</p>
        </div>

        <div className="cluster-grid">
          {loading
            ? Array.from({ length: 6 }, (_, i) => <SkeletonCard key={i} />)
            : clusters.map((cluster, i) => (
                <ClusterCard
                  key={cluster.id}
                  cluster={cluster}
                  index={i}
                  onView={onViewCluster}
                  totalResumes={totalResumes}
                />
              ))}
        </div>
      </motion.section>

      {/* Top Skills Chart */}
      <motion.section className="dashboard__section" variants={fadeUp}>
        <div className="section-header">
          <h2>Top-10 Skills</h2>
          <p>Most frequent skills across all resumes.</p>
        </div>

        <div className="chart-container chart-container--bar">
          {topSkills.length > 0 ? (
            <ResponsiveContainer width="100%" height={380}>
              <BarChart
                data={topSkills}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
              >
                <XAxis type="number" stroke="var(--secondary)" fontSize={12} />
                <YAxis
                  type="category"
                  dataKey="skill"
                  width={130}
                  tick={{ fill: 'var(--dark)', fontSize: 12 }}
                  stroke="var(--secondary)"
                />
                <Tooltip content={<SkillTooltip />} />
                <Bar dataKey="count" radius={[0, 6, 6, 0]} maxBarSize={28}>
                  {topSkills.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                  <LabelList dataKey="count" position="right" fill="var(--dark)" fontSize={11} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="chart-empty">No skill data available.</div>
          )}
        </div>
      </motion.section>
    </motion.div>
  );
}
