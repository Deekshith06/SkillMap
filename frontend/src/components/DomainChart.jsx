/** DomainChart.jsx — Related professional domains with percentage bars. */
import { motion } from 'framer-motion';

const DOMAIN_COLORS = {
  Software_Engineering: '#3a7ca5',
  Data_Science: '#6b8f71',
  Healthcare: '#c75146',
  Finance: '#8e7cc3',
  Marketing: '#e8913a',
  Project_Management: '#546877',
  Human_Resources: '#d4622b',
  Design_UX: '#ff771c',
};

export default function DomainChart({ domains = [] }) {
  if (domains.length === 0) return null;

  return (
    <div className="domain-chart">
      <h3 className="domain-chart__heading">Related Domains</h3>
      <p className="domain-chart__subtitle">
        Based on keywords, skills, and experience detected in your resume
      </p>
      <div className="domain-chart__list">
        {domains.map((d, i) => (
          <motion.div
            key={d.key}
            className="domain-row"
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08, duration: 0.3, ease: [0.4, 0, 0.2, 1] }}>
            <div className="domain-row__header">
              <span className="domain-row__name">{d.domain}</span>
              <span className="domain-row__pct" style={{ color: DOMAIN_COLORS[d.key] || 'var(--clr-primary)' }}>
                {d.confidence}%
              </span>
            </div>
            <div className="domain-row__track">
              <motion.div
                className="domain-row__fill"
                style={{ background: DOMAIN_COLORS[d.key] || 'var(--clr-primary)' }}
                initial={{ width: 0 }}
                animate={{ width: `${d.confidence}%` }}
                transition={{ delay: i * 0.08 + 0.15, duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
              />
            </div>
            <div className="domain-row__tags">
              {d.topMatches.slice(0, 5).map(tag => (
                <span key={tag} className="domain-row__tag">{tag}</span>
              ))}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
