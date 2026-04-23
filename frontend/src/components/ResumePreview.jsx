/** ResumePreview.jsx — A4 styled resume preview. */
import { useRef, useEffect, useState } from 'react';

export default function ResumePreview({ sections = [], flaggedSections = [] }) {
  const wrapperRef = useRef(null);
  const containerRef = useRef(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const updateScale = () => {
      if (!containerRef.current) return;
      const parentWidth = containerRef.current.parentElement?.clientWidth || 800;
      const newScale = Math.min(1, (parentWidth - 48) / 794);
      setScale(newScale);
    };
    updateScale();
    window.addEventListener('resize', updateScale);
    return () => window.removeEventListener('resize', updateScale);
  }, []);

  return (
    <div ref={containerRef} style={{ width: '100%' }}>
      <div
        ref={wrapperRef}
        className="a4-wrapper"
        style={{ transform: `scale(${scale})`, marginBottom: `${(1 - scale) * -1123}px` }}
      >
        <div className="a4-preview" id="a4-preview-content">
          {sections.map(sec => (
            <div
              key={sec.id}
              className={flaggedSections.includes(sec.type) ? 'section--flagged' : ''}
              style={{ marginBottom: 16 }}
            >
              <h2>{sec.title}</h2>
              {sec.content.split('\n').map((line, i) => {
                const trimmed = line.trim();
                if (!trimmed) return <br key={i} />;
                if (/^[-•–—*]/.test(trimmed)) {
                  return <li key={i} style={{ marginLeft: 18 }}>{trimmed.replace(/^[-•–—*]\s*/, '')}</li>;
                }
                return <p key={i}>{trimmed}</p>;
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
