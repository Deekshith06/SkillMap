/** SuggestionPanel.jsx — Grouped suggestion list (read-only guidance). */
import SuggestionCard from './SuggestionCard';

export default function SuggestionPanel({ suggestions = [] }) {
  const groups = {
    critical: suggestions.filter(s => s.priority === 'critical'),
    important: suggestions.filter(s => s.priority === 'important'),
    nice: suggestions.filter(s => s.priority === 'nice'),
  };
  const total = suggestions.length;
  const labels = { critical: 'Critical', important: 'Important', nice: 'Nice to have' };
  let globalIdx = 0;

  return (
    <div>
      <h3 className="suggestion-panel__heading">
        Suggestions <span className="suggestion-panel__count">{total}</span>
      </h3>
      {Object.entries(groups).map(([key, items]) => {
        if (items.length === 0) return null;
        return (
          <div key={key}>
            <p className="suggestion-group__title">{labels[key]} ({items.length})</p>
            {items.map(s => {
              const idx = globalIdx++;
              return <SuggestionCard key={s.id} suggestion={s} index={idx} />;
            })}
          </div>
        );
      })}
      {total === 0 && (
        <p style={{ color: 'var(--clr-muted)', fontSize: '0.85rem', textAlign: 'center', marginTop: 'var(--sp-xl)' }}>
          No suggestions — your resume looks great! 🎉
        </p>
      )}
    </div>
  );
}
