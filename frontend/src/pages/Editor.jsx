/**
 * Editor.jsx — Screen 3: Split editor + A4 preview.
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useDebouncedCallback } from 'use-debounce';
import { Bold, Italic, Underline, List, Plus, Download, GripVertical, Trash2 } from 'lucide-react';
import ScoreRing from '../components/ScoreRing';
import ResumePreview from '../components/ResumePreview';
import SuggestionPanel from '../components/SuggestionPanel';
import DownloadModal from '../components/DownloadModal';
import { useResume } from '../context/ResumeContext';
import { getTemplate } from '../lib/resumeParser';

function getScoreDotColor(score) {
  if (score >= 90) return 'var(--clr-score-top)';
  if (score >= 75) return 'var(--clr-score-good)';
  if (score >= 50) return 'var(--clr-score-mid)';
  return 'var(--clr-score-low)';
}

export default function Editor() {
  const { state, dispatch, runScore, getFullText } = useResume();
  const navigate = useNavigate();
  const [editorWidth, setEditorWidth] = useState(45);
  const [showDownload, setShowDownload] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const isDragging = useRef(false);
  const score = state.scoreResult?.total || 0;

  useEffect(() => {
    if (!state.rawText) navigate('/ats');
  }, [state.rawText, navigate]);

  const debouncedRescore = useDebouncedCallback(() => {
    const text = getFullText();
    runScore(text);
  }, 800);

  const handleContentChange = useCallback((sectionId, newContent) => {
    dispatch({ type: 'UPDATE_SECTION_CONTENT', payload: { id: sectionId, content: newContent } });
    debouncedRescore();
  }, [dispatch, debouncedRescore]);

  const handleTitleChange = useCallback((sectionId, newTitle) => {
    const sections = state.parsedSections.map(s =>
      s.id === sectionId ? { ...s, title: newTitle } : s
    );
    dispatch({ type: 'UPDATE_SECTIONS', payload: sections });
  }, [dispatch, state.parsedSections]);

  const addSection = () => {
    dispatch({
      type: 'ADD_SECTION',
      payload: { type: 'skills', title: 'New Section', content: getTemplate('skills') },
    });
    debouncedRescore();
  };

  const deleteSection = (id) => {
    dispatch({ type: 'DELETE_SECTION', payload: id });
    debouncedRescore();
  };

  const execCmd = (cmd) => document.execCommand(cmd, false, null);

  const onMouseDown = () => { isDragging.current = true; };
  useEffect(() => {
    const onMove = (e) => {
      if (!isDragging.current) return;
      const pct = (e.clientX / window.innerWidth) * 100;
      setEditorWidth(Math.max(25, Math.min(70, pct)));
    };
    const onUp = () => { isDragging.current = false; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
  }, []);



  return (
    <div className="editor-screen">
      {/* Editor pane */}
      <div className="editor-pane" style={{ width: `${editorWidth}%` }}>
        {/* Toolbar */}
        <div className="editor-toolbar">
          <button className="editor-toolbar__btn" onClick={() => execCmd('bold')} title="Bold" aria-label="Bold">
            <Bold size={16} />
          </button>
          <button className="editor-toolbar__btn" onClick={() => execCmd('italic')} title="Italic" aria-label="Italic">
            <Italic size={16} />
          </button>
          <button className="editor-toolbar__btn" onClick={() => execCmd('underline')} title="Underline" aria-label="Underline">
            <Underline size={16} />
          </button>
          <div className="editor-toolbar__divider" />
          <button className="editor-toolbar__btn" onClick={() => execCmd('insertUnorderedList')} title="Bullet list" aria-label="Bullet list">
            <List size={16} />
          </button>
          <button className="editor-toolbar__btn" onClick={addSection} title="Add section" aria-label="Add section">
            <Plus size={16} />
          </button>
          <div className="editor-toolbar__divider" />

          <div className="editor-toolbar__score">
            <div className="editor-toolbar__score-dot" style={{ background: getScoreDotColor(score) }} />
            ATS: {score}
          </div>
          <div className="editor-toolbar__divider" />
          <button className="btn-ghost" onClick={() => setShowSuggestions(v => !v)} style={{ fontSize: '0.8rem' }}>
            Tips ({state.scoreResult?.suggestions?.length || 0})
          </button>
          <button className="btn-primary" style={{ padding: '8px 16px', fontSize: '0.8rem' }}
            onClick={() => setShowDownload(true)}>
            <Download size={14} /> Download
          </button>
        </div>

        {/* Section blocks */}
        <div style={{ padding: 'var(--sp-md)' }}>
          {state.parsedSections.map((sec) => (
            <div key={sec.id} className="section-block">
              <div className="section-block__header">
                <span className="section-block__grip"><GripVertical size={16} /></span>
                <input
                  className="section-block__title"
                  value={sec.title}
                  onChange={e => handleTitleChange(sec.id, e.target.value)}
                  aria-label={`Section title: ${sec.title}`}
                />
                <button
                  className="section-block__delete"
                  onClick={() => deleteSection(sec.id)}
                  aria-label={`Delete ${sec.title}`}>
                  <Trash2 size={14} />
                </button>
              </div>
              <div
                className="section-block__content"
                contentEditable
                suppressContentEditableWarning
                onBlur={e => handleContentChange(sec.id, e.currentTarget.innerText)}
                dangerouslySetInnerHTML={{ __html: sec.content.replace(/\n/g, '<br/>') }}
              />
            </div>
          ))}
        </div>

        {/* Inline suggestions panel */}
        {showSuggestions && state.scoreResult && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            style={{ padding: 'var(--sp-md)', borderTop: '0.5px solid var(--clr-border)' }}>
            <SuggestionPanel
              suggestions={state.scoreResult.suggestions}
            />
          </motion.div>
        )}
      </div>

      {/* Resize handle */}
      <div className="editor-handle" onMouseDown={onMouseDown} />

      {/* Preview pane */}
      <div className="preview-pane">
        <ResumePreview sections={state.parsedSections} />
      </div>

      <DownloadModal
        isOpen={showDownload}
        onClose={() => setShowDownload(false)}
        sections={state.parsedSections}
        originalScore={state.originalScore}
        currentScore={score}
        appliedCount={state.appliedSuggestions.length}
      />
    </div>
  );
}
