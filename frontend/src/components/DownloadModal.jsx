/** DownloadModal.jsx — Export options with before/after comparison. */
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, FileDown, FileType, X } from 'lucide-react';
import ScoreRing from './ScoreRing';
import { exportToPDF } from '../lib/exportPDF';
import { exportToDOCX, exportToTXT } from '../lib/exportDOCX';

export default function DownloadModal({ isOpen, onClose, sections, originalScore, currentScore, appliedCount }) {
  if (!isOpen) return null;

  const handlePDF = () => {
    const el = document.getElementById('a4-preview-content');
    if (el) exportToPDF(el);
  };
  const handleDOCX = () => exportToDOCX(sections);
  const handleTXT = () => exportToTXT(sections);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div className="modal-overlay"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          onClick={onClose}>
          <motion.div className="modal-content"
            initial={{ y: 80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 80, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-lg)' }}>
              <h2>Download Resume</h2>
              <button onClick={onClose} aria-label="Close modal"><X size={20} /></button>
            </div>

            {currentScore >= 90 && (
              <div className="download-modal__badge">
                🎉 Your resume is ATS-ready!
              </div>
            )}

            <div className="download-modal__comparison">
              <div className="download-modal__stat">
                <ScoreRing score={originalScore || 0} size={100} stroke={7} label="" />
                <p className="download-modal__stat-label">Before</p>
              </div>
              <div className="download-modal__stat">
                <ScoreRing score={currentScore || 0} size={100} stroke={7} label="" />
                <p className="download-modal__stat-label">After</p>
              </div>
            </div>

            <p style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--clr-muted)', marginBottom: 'var(--sp-lg)' }}>
              {appliedCount} suggestion{appliedCount !== 1 ? 's' : ''} applied · Score delta: +{Math.max(0, (currentScore || 0) - (originalScore || 0))}
            </p>

            <div className="download-modal__buttons">
              <button className="btn-primary" onClick={handlePDF}><FileText size={16} /> PDF</button>
              <button className="btn-ghost" onClick={handleDOCX}><FileDown size={16} /> DOCX</button>
              <button className="btn-ghost" onClick={handleTXT}><FileType size={16} /> TXT</button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
