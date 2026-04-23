/**
 * ConfidenceBar — Animated horizontal progress bar showing confidence.
 */

import { motion } from 'framer-motion';

export default function ConfidenceBar({ value = 0, label = 'Confidence' }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);

  return (
    <div className="confidence-bar" role="meter" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
      <div className="confidence-bar__header">
        <span className="confidence-bar__label">{label}</span>
        <span className="confidence-bar__value">{pct}%</span>
      </div>
      <div className="confidence-bar__track">
        <motion.div
          className="confidence-bar__fill"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
        />
      </div>
    </div>
  );
}
