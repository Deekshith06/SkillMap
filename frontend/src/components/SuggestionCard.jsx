/** SuggestionCard.jsx — Single suggestion as guidance (no apply button). */
import { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertTriangle, Info, ChevronDown, ChevronUp } from 'lucide-react';

const PRIORITY_ICON = {
  critical: <AlertTriangle size={14} color="var(--clr-score-low)" />,
  important: <Info size={14} color="var(--clr-score-mid)" />,
  nice: <CheckCircle size={14} color="var(--clr-score-good)" />,
};

const PRIORITY_LABEL = {
  critical: 'Critical',
  important: 'Important',
  nice: 'Nice to have',
};

export default function SuggestionCard({ suggestion, index = 0 }) {
  const [expanded, setExpanded] = useState(false);
  const { priority, title, detail, diff, category } = suggestion;

  return (
    <motion.div className="suggestion-card"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: index * 0.04 }}>
      <div
        className="suggestion-card__header"
        style={{ cursor: diff ? 'pointer' : 'default' }}
        onClick={() => diff && setExpanded(v => !v)}>
        <span className={`suggestion-card__dot suggestion-card__dot--${priority}`} />
        <span className="suggestion-card__title">{title}</span>
        <span className="suggestion-card__priority-badge" style={{
          fontSize: '0.65rem', fontWeight: 600,
          color: priority === 'critical' ? 'var(--clr-score-low)' : priority === 'important' ? 'var(--clr-score-mid)' : 'var(--clr-score-good)',
          textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap',
        }}>
          {PRIORITY_LABEL[priority]}
        </span>
        {diff && (expanded ? <ChevronUp size={14} color="var(--clr-muted)" /> : <ChevronDown size={14} color="var(--clr-muted)" />)}
      </div>
      <p className="suggestion-card__detail">{detail}</p>
      {expanded && diff && (
        <motion.div
          className="diff-box"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.2 }}>
          <div className="diff-box__before"><strong>Before:</strong> {diff.before}</div>
          <div className="diff-box__after"><strong>After:</strong> {diff.after}</div>
        </motion.div>
      )}
    </motion.div>
  );
}
