/**
 * ScoreDashboard.jsx — Screen 2: Score + Domains + Suggestions (read-only).
 */
import { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Edit3 } from 'lucide-react';
import ScoreRing from '../components/ScoreRing';
import SubScoreBar from '../components/SubScoreBar';
import SuggestionPanel from '../components/SuggestionPanel';
import DomainChart from '../components/DomainChart';
import ResumePreview from '../components/ResumePreview';
import { useResume } from '../context/ResumeContext';

const SUB_LABELS = [
  { key: 'keywords',     label: 'Keywords' },
  { key: 'formatting',   label: 'Formatting' },
  { key: 'contact',      label: 'Contact' },
  { key: 'structure',    label: 'Structure' },
  { key: 'achievements', label: 'Achievements' },
  { key: 'actionVerbs',  label: 'Action Verbs' },
  { key: 'length',       label: 'Length' },
];

export default function ScoreDashboard() {
  const { state, dispatch, runScore } = useResume();
  const navigate = useNavigate();
  const { scoreResult, parsedSections } = state;

  useEffect(() => {
    if (!state.rawText) navigate('/ats');
    if (state.rawText && !scoreResult) runScore(state.rawText);
  }, [state.rawText, scoreResult, runScore, navigate]);

  const flagged = useMemo(() => {
    if (!scoreResult) return [];
    return Object.entries(scoreResult.categories)
      .filter(([, v]) => v.score < v.max * 0.6)
      .map(([k]) => k);
  }, [scoreResult]);

  if (!scoreResult) {
    return (
      <div className="upload-screen">
        <div className="surface" style={{ padding: 'var(--sp-xl)', textAlign: 'center' }}>
          <div className="skeleton" style={{ width: 180, height: 180, borderRadius: '50%', margin: '0 auto var(--sp-lg)' }} />
          <p style={{ color: 'var(--clr-muted)' }}>Scoring your resume…</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div className="score-dashboard"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }}
      transition={{ duration: 0.25 }}>
      {/* LEFT — Score + Domains */}
      <div className="score-dashboard__left">
        <ScoreRing score={scoreResult.total} />
        <div className="sub-scores">
          {SUB_LABELS.map(({ key, label }, i) => (
            <SubScoreBar
              key={key}
              label={label}
              score={scoreResult.categories[key]?.score || 0}
              max={scoreResult.categories[key]?.max || 1}
              delay={i * 0.06}
            />
          ))}
        </div>

        {/* Domain Matching */}
        <DomainChart domains={scoreResult.domains || []} />

        <button className="btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: 'var(--sp-lg)' }}
          onClick={() => { dispatch({ type: 'SET_SCREEN', payload: 'editor' }); navigate('/ats/editor'); }}>
          <Edit3 size={16} /> Edit Resume
        </button>
      </div>

      {/* CENTER — Preview */}
      <div className="score-dashboard__center">
        <ResumePreview sections={parsedSections} flaggedSections={flagged} />
      </div>

      {/* RIGHT — Suggestions (read-only guidance) */}
      <div className="score-dashboard__right">
        <SuggestionPanel suggestions={scoreResult.suggestions} />
      </div>
    </motion.div>
  );
}
