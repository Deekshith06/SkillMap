/**
 * Upload.jsx — Screen 1: Full-viewport upload zone.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileText, X } from 'lucide-react';
import DropZone from '../components/DropZone';
import { useResume } from '../context/ResumeContext';
import { extractText } from '../lib/extractors';

export default function Upload() {
  const { state, dispatch, runScore } = useResume();
  const [selectedFile, setSelectedFile] = useState(null);
  const navigate = useNavigate();

  const onFileSelect = (file) => {
    setSelectedFile(file);
    dispatch({ type: 'SET_FILE', payload: file });
  };

  const clearFile = () => {
    setSelectedFile(null);
    dispatch({ type: 'SET_FILE', payload: null });
  };

  const analyse = async () => {
    if (!selectedFile) return;
    dispatch({ type: 'SET_PARSING', payload: true });
    try {
      const text = await extractText(selectedFile);
      dispatch({ type: 'SET_RAW_TEXT', payload: text });
      runScore(text);
      dispatch({ type: 'SET_SCREEN', payload: 'score' });
      navigate('/ats/score');
    } catch (err) {
      dispatch({ type: 'SET_PARSE_ERROR', payload: err.message });
    }
  };

  return (
    <motion.div className="upload-screen"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}>
      <div className="upload-card surface">
        <h1>Optimise your resume</h1>
        <p className="subtitle">Upload PDF or DOCX to get your ATS score instantly</p>

        {!selectedFile && <DropZone onFileSelect={onFileSelect} disabled={state.isParsing} />}

        {selectedFile && (
          <>
            <div className="file-badge">
              <FileText size={16} />
              {selectedFile.name}
              <button onClick={clearFile} aria-label="Remove file"><X size={14} /></button>
            </div>

            <button
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={analyse}
              disabled={state.isParsing}>
              {state.isParsing ? 'Parsing…' : 'Analyse resume'}
            </button>

            {state.isParsing && (
              <div className="parse-progress"><div className="parse-progress__bar" /></div>
            )}
          </>
        )}

        {state.parseError && <p className="upload-error">{state.parseError}</p>}
      </div>
    </motion.div>
  );
}
