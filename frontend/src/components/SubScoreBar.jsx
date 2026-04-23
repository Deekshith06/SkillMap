/** SubScoreBar.jsx — Mini progress bar for score categories. */
import { motion } from 'framer-motion';

export default function SubScoreBar({ label, score, max, delay = 0 }) {
  const pct = max > 0 ? (score / max) * 100 : 0;
  return (
    <div className="sub-score-row">
      <span className="sub-score-row__label">{label}</span>
      <div className="sub-score-row__track">
        <motion.div
          className="sub-score-row__fill"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.4, delay, ease: [0.4, 0, 0.2, 1] }}
        />
      </div>
      <span className="sub-score-row__pts">{score}/{max}</span>
    </div>
  );
}
