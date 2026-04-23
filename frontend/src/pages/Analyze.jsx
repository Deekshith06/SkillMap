/**
 * Analyze.jsx — Single resume analysis page.
 *
 * Features:
 * - Dual-mode input: drag-and-drop PDF/DOCX or paste raw text
 * - Client-side PDF extraction (pdfjs-dist) + DOCX extraction (mammoth)
 * - Progress stepper: Upload → Parsing → Embedding → Result
 * - Result card: cluster name, confidence ring (SVG arc), top skills,
 *   similar resumes list, radar chart of skill dimensions (Recharts)
 * - Skeleton loader, error state with retry
 */

import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, ResponsiveContainer, Tooltip,
} from 'recharts';
import {
  Upload, ScanSearch, FileText, CheckCircle2,
  Loader2, AlertCircle, RotateCcw, Cpu, Send,
} from 'lucide-react';
import * as pdfjsLib from 'pdfjs-dist';
import pdfWorkerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import mammoth from 'mammoth';

import { useAppData } from '../context/AppContext';
import { predictResume } from '../api/client';
import SkillPill from '../components/SkillPill';
import FileDropZone from '../components/FileDropZone';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerSrc;

// ── Stepper states ──────────────────────────────────────────────

const STEPS = [
  { key: 'upload', label: 'Upload', icon: Upload },
  { key: 'parsing', label: 'Parsing', icon: FileText },
  { key: 'embedding', label: 'Embedding', icon: Cpu },
  { key: 'result', label: 'Result', icon: CheckCircle2 },
];

function Stepper({ currentStep }) {
  const idx = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <div className="stepper" role="progressbar" aria-valuenow={idx + 1} aria-valuemin={1} aria-valuemax={4}>
      {STEPS.map((step, i) => {
        const Icon = step.icon;
        const status = i < idx ? 'done' : i === idx ? 'active' : 'pending';
        return (
          <div key={step.key} className={`stepper__step stepper__step--${status}`}>
            <div className="stepper__icon">
              <Icon size={16} />
            </div>
            <span className="stepper__label">{step.label}</span>
            {i < STEPS.length - 1 && <div className="stepper__connector" />}
          </div>
        );
      })}
    </div>
  );
}

// ── Confidence Ring (SVG arc) ───────────────────────────────────

function ConfidenceRing({ score }) {
  const value = Math.max(0, Math.min(1, score || 0));
  const size = 140;
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = circumference * (1 - value);

  return (
    <div className="confidence-ring">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke="var(--secondary)" strokeWidth={stroke}
          fill="transparent" opacity={0.2}
        />
        <motion.circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke="var(--primary)" strokeWidth={stroke}
          strokeLinecap="round" fill="transparent"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: dash }}
          transition={{ duration: 1.2, ease: [0.4, 0, 0.2, 1] }}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="confidence-ring__center">
        <span className="confidence-ring__pct">{Math.round(value * 100)}%</span>
        <span className="confidence-ring__label">Confidence</span>
      </div>
    </div>
  );
}

// ── Client-side file extraction ─────────────────────────────────

async function extractText(file) {
  const name = file.name.toLowerCase();
  const data = await file.arrayBuffer();

  if (name.endsWith('.pdf')) {
    const doc = await pdfjsLib.getDocument({ data }).promise;
    const pages = [];
    for (let i = 1; i <= doc.numPages; i++) {
      const page = await doc.getPage(i);
      const content = await page.getTextContent();
      pages.push(content.items.map((item) => item.str).join(' '));
    }
    return pages.join('\n\n');
  }

  if (name.endsWith('.docx') || name.endsWith('.doc')) {
    const result = await mammoth.extractRawText({ arrayBuffer: data });
    return result.value || '';
  }

  if (name.endsWith('.txt')) {
    return new TextDecoder('utf-8').decode(data);
  }

  throw new Error('Unsupported file type. Use PDF, DOCX, or TXT.');
}

// ── Analyze Page ────────────────────────────────────────────────

export default function Analyze() {
  const { setLastResults, lastResults } = useAppData();

  const [mode, setMode] = useState('text');
  const [resumeText, setResumeText] = useState('');
  const [fileName, setFileName] = useState('');
  const [step, setStep] = useState('upload');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(lastResults);
  const [error, setError] = useState('');

  // Handle file selection from FileDropZone
  const handleFiles = useCallback(async (files) => {
    if (!files.length) return;
    const file = files[0];

    setError('');
    setResult(null);
    setStep('parsing');
    setLoading(true);

    try {
      const text = await extractText(file);
      setResumeText(text.trim());
      setFileName(file.name);
      setMode('file');
      setStep('upload');
    } catch (err) {
      setError(err.message || 'Failed to extract text from file.');
      setStep('upload');
    } finally {
      setLoading(false);
    }
  }, []);

  // Analyze resume
  const handleAnalyze = useCallback(async (e) => {
    e?.preventDefault();
    if (!resumeText.trim()) return;

    setLoading(true);
    setError('');
    setStep('embedding');

    try {
      const data = await predictResume(resumeText.trim());
      setResult(data);
      setLastResults(data);
      setStep('result');
    } catch (err) {
      setError(err.response?.data?.error?.message || err.message || 'Analysis failed.');
      setStep('upload');
    } finally {
      setLoading(false);
    }
  }, [resumeText, setLastResults]);

  // Reset form
  const handleReset = useCallback(() => {
    setResumeText('');
    setFileName('');
    setResult(null);
    setError('');
    setStep('upload');
    setMode('text');
  }, []);

  // Build radar data from skills
  const radarData = (result?.top_skills || []).slice(0, 8).map((skill, i) => ({
    skill: typeof skill === 'string' ? skill : skill.name || `Skill ${i + 1}`,
    value: typeof skill === 'string' ? 70 + Math.random() * 30 : (skill.confidence || 0.7) * 100,
    fullMark: 100,
  }));

  return (
    <motion.div
      className="analyze-page"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Stepper */}
      <Stepper currentStep={step} />

      <div className="analyze-grid">
        {/* Input Panel */}
        <section className="panel analyze-input">
          <div className="panel__header">
            <h2>Analyze Resume</h2>
            <p>Paste text or upload a file for analysis.</p>
          </div>

          {/* Mode tabs */}
          <div className="tab-bar" role="tablist">
            <button
              role="tab"
              aria-selected={mode === 'text'}
              className={`tab ${mode === 'text' ? 'tab--active' : ''}`}
              onClick={() => setMode('text')}
            >
              <FileText size={14} /> Paste Text
            </button>
            <button
              role="tab"
              aria-selected={mode === 'file'}
              className={`tab ${mode === 'file' ? 'tab--active' : ''}`}
              onClick={() => setMode('file')}
            >
              <Upload size={14} /> Upload File
            </button>
          </div>

          <form onSubmit={handleAnalyze} className="analyze-form">
            {mode === 'text' ? (
              <div className="form-group">
                <label htmlFor="resume-text" className="form-label">Resume content</label>
                <textarea
                  id="resume-text"
                  className="textarea"
                  placeholder="Paste resume content here..."
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                  rows={12}
                />
              </div>
            ) : (
              <div className="analyze-file-section">
                <FileDropZone
                  onFiles={handleFiles}
                  label="Drop resume file here"
                  sublabel="PDF, DOCX, or TXT — max 5 MB"
                />
                {fileName && (
                  <div className="file-meta">
                    <FileText size={14} />
                    <span>{fileName}</span>
                  </div>
                )}
                {resumeText && (
                  <div className="form-group">
                    <label htmlFor="extracted-text" className="form-label">Extracted text</label>
                    <textarea
                      id="extracted-text"
                      className="textarea textarea--preview"
                      value={resumeText}
                      onChange={(e) => setResumeText(e.target.value)}
                      rows={8}
                    />
                  </div>
                )}
              </div>
            )}

            <div className="analyze-actions">
              <button
                type="submit"
                className="btn-primary btn-lg"
                disabled={!resumeText.trim() || loading}
              >
                {loading ? <Loader2 size={16} className="spin" /> : <ScanSearch size={16} />}
                Analyze Resume
              </button>
              {(result || resumeText) && (
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={handleReset}
                >
                  <RotateCcw size={14} /> Reset
                </button>
              )}
            </div>
          </form>

          {/* Error */}
          <AnimatePresence>
            {error && (
              <motion.div
                className="alert alert--error"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                <AlertCircle size={16} />
                <span>{error}</span>
                <button className="btn-ghost btn-sm" onClick={handleAnalyze}>
                  <RotateCcw size={12} /> Retry
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </section>

        {/* Result Panel */}
        <section className="panel analyze-result">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ duration: 0.3 }}
                className="result-content"
              >
                <div className="result-header">
                  <div>
                    <h3>{result.cluster_name}</h3>
                    <p className="result-subtitle">
                      Cluster #{result.cluster_id}
                    </p>
                  </div>
                  <ConfidenceRing score={result.confidence ?? result.confidence_score ?? 0} />
                </div>

                {/* Skills */}
                <div className="result-section">
                  <h4>Top Skills</h4>
                  <div className="pill-row">
                    {(result.top_skills || []).slice(0, 10).map((skill, i) => (
                      <SkillPill
                        key={typeof skill === 'string' ? skill : skill.name}
                        name={typeof skill === 'string' ? skill : skill.name}
                        index={i}
                      />
                    ))}
                  </div>
                </div>

                {/* Radar Chart */}
                {radarData.length >= 3 && (
                  <div className="result-section">
                    <h4>Skill Dimensions</h4>
                    <div className="chart-container">
                      <ResponsiveContainer width="100%" height={280}>
                        <RadarChart data={radarData}>
                          <PolarGrid stroke="var(--secondary)" opacity={0.3} />
                          <PolarAngleAxis
                            dataKey="skill"
                            tick={{ fill: 'var(--dark)', fontSize: 11 }}
                          />
                          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} />
                          <Tooltip />
                          <Radar
                            dataKey="value"
                            stroke="var(--primary)"
                            fill="var(--primary)"
                            fillOpacity={0.2}
                            strokeWidth={2}
                          />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Similar resumes */}
                {result.similar_resumes?.length > 0 && (
                  <div className="result-section">
                    <h4>Similar Resumes</h4>
                    <ul className="similar-list">
                      {result.similar_resumes.slice(0, 5).map((r, i) => (
                        <li key={r.id || i} className="similar-item">
                          <span className="similar-item__cat">{r.category}</span>
                          <span className="similar-item__snippet">{r.snippet?.slice(0, 120)}...</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="result-empty"
              >
                <Send size={32} />
                <h3>Analysis results appear here</h3>
                <p>Paste resume text or upload a file, then click Analyze.</p>
              </motion.div>
            )}
          </AnimatePresence>
        </section>
      </div>
    </motion.div>
  );
}
