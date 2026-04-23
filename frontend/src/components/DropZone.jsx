/** DropZone.jsx — File upload drag-and-drop area. */
import { useRef, useState, useCallback } from 'react';
import { Upload } from 'lucide-react';
import { validateFile } from '../lib/extractors';

export default function DropZone({ onFileSelect, disabled = false }) {
  const inputRef = useRef(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState(null);

  const handleFile = useCallback((file) => {
    const err = validateFile(file);
    if (err) { setError(err); return; }
    setError(null);
    onFileSelect?.(file);
  }, [onFileSelect]);

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const onDragOver = (e) => { e.preventDefault(); setIsDragOver(true); };
  const onDragLeave = () => setIsDragOver(false);
  const onChange = (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); };

  return (
    <div>
      <div
        className={`dropzone ${isDragOver ? 'dropzone--active' : ''}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-dropeffect="copy"
        aria-label="Upload resume file"
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click(); }}
      >
        <div className="dropzone__icon"><Upload size={32} /></div>
        <p className="dropzone__label">
          Drag and drop your file here, or <span>browse</span>
        </p>
        <p style={{ fontSize: '0.75rem', color: 'var(--clr-muted)', marginTop: 8 }}>
          PDF, DOCX, or TXT — max 5 MB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={onChange}
          style={{ display: 'none' }}
          disabled={disabled}
          id="resume-file-input"
          aria-label="Choose resume file"
        />
      </div>
      {error && <p className="upload-error">{error}</p>}
    </div>
  );
}
