/**
 * ScoreRing.jsx — Animated SVG score arc.
 */
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

function getColor(score) {
  if (score >= 90) return 'var(--clr-score-top)';
  if (score >= 75) return 'var(--clr-score-good)';
  if (score >= 50) return 'var(--clr-score-mid)';
  return 'var(--clr-score-low)';
}

export default function ScoreRing({ score = 0, size = 180, stroke = 10, label = 'ATS Score' }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (animatedScore / 100) * circumference;
  const color = getColor(score);

  useEffect(() => {
    let frame;
    const duration = 600;
    const start = performance.now();
    const from = animatedScore;
    const to = score;

    const animate = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(from + (to - from) * eased));
      if (progress < 1) frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  return (
    <div className="score-ring" aria-label={`ATS score: ${score} out of 100`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="var(--clr-border)" strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={color} strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </svg>
      <div className="score-ring__label">
        <span className="score-ring__value" style={{ color }}>{animatedScore}</span>
        <span className="score-ring__max">/100</span>
      </div>
      <p className="score-ring__text">{label}</p>
    </div>
  );
}
