/**
 * FileDropZone — Drag-and-drop file upload zone with validation.
 *
 * Validates file type (PDF/DOCX/TXT) and size (≤5MB per file)
 * client-side before passing files up.
 */

import { useState, useRef, useCallback } from 'react';
import { Upload, FileText, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ACCEPTED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
];

const ACCEPTED_EXTENSIONS = ['.pdf', '.docx', '.txt'];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

function validateFile(file) {
  const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
  if (!ACCEPTED_EXTENSIONS.includes(ext)) {
    return `"${file.name}" — unsupported type. Use PDF, DOCX, or TXT.`;
  }
  if (file.size > MAX_FILE_SIZE) {
    return `"${file.name}" — file too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Max 5 MB.`;
  }
  return null;
}

export default function FileDropZone({
  onFiles,
  maxFiles = 50,
  multiple = false,
  label = 'Drop files here or click to browse',
  sublabel = 'PDF, DOCX, or TXT — max 5 MB each',
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  const handleFiles = useCallback(
    (fileList) => {
      const files = Array.from(fileList);
      const errors = [];
      const valid = [];

      for (const file of files.slice(0, maxFiles)) {
        const err = validateFile(file);
        if (err) {
          errors.push(err);
        } else {
          valid.push(file);
        }
      }

      if (files.length > maxFiles) {
        errors.push(`Maximum ${maxFiles} files allowed.`);
      }

      setError(errors.join(' '));

      if (valid.length > 0) {
        onFiles?.(valid);
      }
    },
    [onFiles, maxFiles]
  );

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragOver(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const onDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const onDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const onInputChange = useCallback(
    (e) => {
      handleFiles(e.target.files);
      // Reset input so same file can be re-selected
      e.target.value = '';
    },
    [handleFiles]
  );

  return (
    <div className="file-drop-zone-wrapper">
      <motion.label
        className={`file-drop-zone ${isDragOver ? 'file-drop-zone--active' : ''}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        htmlFor="file-drop-input"
      >
        <Upload size={24} className="file-drop-zone__icon" />
        <div className="file-drop-zone__text">
          <strong>{label}</strong>
          <small>{sublabel}</small>
        </div>
        <input
          ref={inputRef}
          id="file-drop-input"
          type="file"
          accept=".pdf,.docx,.txt"
          multiple={multiple}
          onChange={onInputChange}
          hidden
        />
      </motion.label>

      <AnimatePresence>
        {error && (
          <motion.div
            className="file-drop-zone__error"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <AlertCircle size={14} />
            <span>{error}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
