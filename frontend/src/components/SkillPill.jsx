/**
 * SkillPill — A styled tag/pill for displaying skill names.
 * Supports optional confidence level colouring.
 */

import { motion } from 'framer-motion';

export default function SkillPill({ name, confidence, index = 0 }) {
  const tier =
    confidence >= 0.8
      ? 'high'
      : confidence >= 0.5
        ? 'mid'
        : 'low';

  return (
    <motion.span
      className={`skill-pill skill-pill--${confidence !== undefined ? tier : 'default'}`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.04, duration: 0.2 }}
    >
      {name}
      {confidence !== undefined && (
        <span className="skill-pill__score">
          {Math.round(confidence * 100)}%
        </span>
      )}
    </motion.span>
  );
}
