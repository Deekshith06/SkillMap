/**
 * ClusterCard — Card component for displaying cluster info.
 * Shows: name, resume count, top-3 skills as pills, confidence bar, CTA.
 */

import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import SkillPill from './SkillPill';
import ConfidenceBar from './ConfidenceBar';

const ACCENT_COLORS = [
  '#ff771c', '#546877', '#d4622b', '#3a7ca5',
  '#e8913a', '#6b8f71', '#c75146', '#8e7cc3',
];

export default function ClusterCard({
  cluster,
  index = 0,
  onView,
  totalResumes = 1,
}) {
  const accent = ACCENT_COLORS[index % ACCENT_COLORS.length];
  const topSkills = (cluster.top_skills || []).slice(0, 3);
  const confidence = cluster.avg_confidence || 0.75;

  return (
    <motion.article
      className="cluster-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: index * 0.08,
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1],
      }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
    >
      <div
        className="cluster-card__accent"
        style={{ backgroundColor: accent }}
      />

      <div className="cluster-card__header">
        <span
          className="cluster-card__dot"
          style={{ backgroundColor: accent }}
        />
        <span className="cluster-card__id">
          {String(cluster.id + 1).padStart(2, '0')}
        </span>
      </div>

      <h3 className="cluster-card__name">{cluster.name}</h3>

      <div className="cluster-card__count">
        {(cluster.size ?? cluster.resume_count ?? 0).toLocaleString()} resumes
      </div>

      <div className="cluster-card__pills">
        {topSkills.map((skill, i) => (
          <SkillPill key={skill} name={skill} index={i} />
        ))}
      </div>

      <ConfidenceBar value={confidence} />

      <button
        type="button"
        className="cluster-card__cta"
        onClick={() => onView?.(cluster.id)}
        aria-label={`View ${cluster.name} cluster`}
      >
        View cluster <ArrowRight size={14} />
      </button>
    </motion.article>
  );
}
