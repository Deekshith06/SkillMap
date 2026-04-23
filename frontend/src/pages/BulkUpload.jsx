/**
 * BulkUpload.jsx — Multi-file batch analysis page.
 *
 * Features:
 * - Multi-file drag zone (up to 50 files, per-file progress)
 * - Results table: name, cluster, confidence, top skills, actions
 * - Sort & filter by cluster or confidence threshold
 * - CSV export (client-side Blob)
 * - Pagination (25 per page)
 * - Skeleton/loading/error/empty states
 */

import { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Download, Loader2, ScanSearch, Trash2,
  ChevronLeft, ChevronRight, Filter,
  AlertCircle, RotateCcw, FileSpreadsheet,
} from 'lucide-react';
import * as pdfjsLib from 'pdfjs-dist';
import pdfWorkerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import mammoth from 'mammoth';

import { useAppData } from '../context/AppContext';
import { predictResume } from '../api/client';
import FileDropZone from '../components/FileDropZone';
import SkillPill from '../components/SkillPill';
import ConfidenceBar from '../components/ConfidenceBar';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerSrc;

const PER_PAGE = 25;

// ── File extraction ─────────────────────────────────────────────

async function extractText(file) {
  const name = file.name.toLowerCase();
  const buf = await file.arrayBuffer();

  if (name.endsWith('.pdf')) {
    const doc = await pdfjsLib.getDocument({ data: buf }).promise;
    const pages = [];
    for (let i = 1; i <= doc.numPages; i++) {
      const page = await doc.getPage(i);
      const content = await page.getTextContent();
      pages.push(content.items.map((it) => it.str).join(' '));
    }
    return pages.join('\n\n');
  }

  if (name.endsWith('.docx') || name.endsWith('.doc')) {
    const r = await mammoth.extractRawText({ arrayBuffer: buf });
    return r.value || '';
  }

  if (name.endsWith('.txt')) {
    return new TextDecoder('utf-8').decode(buf);
  }

  throw new Error('Unsupported type');
}

// ── BulkUpload Page ─────────────────────────────────────────────

export default function BulkUpload() {
  const { setBulkResults } = useAppData();

  const [files, setFiles] = useState([]);         // { id, file, name, status, text, result?, error? }
  const [processing, setProcessing] = useState(false);
  const [processedCount, setProcessedCount] = useState(0);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');

  // Filters
  const [filterCluster, setFilterCluster] = useState('');
  const [filterMinConf, setFilterMinConf] = useState(0);
  const [sortField, setSortField] = useState('index');
  const [sortDir, setSortDir] = useState('asc');
  const [page, setPage] = useState(1);

  // ── File handling ───────────────────────────────────────────

  const handleFiles = useCallback((newFiles) => {
    setFiles((prev) => {
      const existing = prev.length;
      const additions = newFiles.slice(0, 50 - existing).map((f, i) => ({
        id: Date.now() + i,
        file: f,
        name: f.name,
        status: 'pending', // pending | extracting | analyzing | done | error
        text: '',
        result: null,
        error: null,
      }));
      return [...prev, ...additions];
    });
  }, []);

  const removeFile = useCallback((id) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setFiles([]);
    setResults([]);
    setProcessedCount(0);
    setError('');
    setPage(1);
  }, []);

  // ── Process all files ───────────────────────────────────────

  const processAll = useCallback(async () => {
    if (!files.length) return;

    setProcessing(true);
    setError('');
    setProcessedCount(0);
    const allResults = [];

    for (let i = 0; i < files.length; i++) {
      const f = files[i];

      // Update status: extracting
      setFiles((prev) =>
        prev.map((x) => (x.id === f.id ? { ...x, status: 'extracting' } : x))
      );

      try {
        // Extract text
        const text = await extractText(f.file);

        // Update status: analyzing
        setFiles((prev) =>
          prev.map((x) => (x.id === f.id ? { ...x, status: 'analyzing', text } : x))
        );

        // Predict
        const result = await predictResume(text.trim());

        // Update status: done
        setFiles((prev) =>
          prev.map((x) => (x.id === f.id ? { ...x, status: 'done', result } : x))
        );

        allResults.push({
          index: i,
          filename: f.name,
          cluster_id: result.cluster_id,
          cluster_name: result.cluster_name,
          confidence: result.confidence ?? result.confidence_score ?? 0,
          top_skills: result.top_skills || [],
        });
      } catch (err) {
        setFiles((prev) =>
          prev.map((x) =>
            x.id === f.id ? { ...x, status: 'error', error: err.message } : x
          )
        );

        allResults.push({
          index: i,
          filename: f.name,
          error: err.message,
        });
      }

      setProcessedCount(i + 1);
    }

    setResults(allResults);
    setBulkResults(allResults);
    setProcessing(false);
  }, [files, setBulkResults]);

  // ── Filtering & sorting ─────────────────────────────────────

  const successResults = useMemo(
    () => results.filter((r) => !r.error),
    [results]
  );

  const clusterNames = useMemo(
    () => [...new Set(successResults.map((r) => r.cluster_name))].sort(),
    [successResults]
  );

  const filtered = useMemo(() => {
    let data = [...successResults];

    if (filterCluster) {
      data = data.filter((r) => r.cluster_name === filterCluster);
    }
    if (filterMinConf > 0) {
      data = data.filter((r) => (r.confidence || 0) >= filterMinConf / 100);
    }

    data.sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      if (sortField === 'confidence') {
        return ((a.confidence || 0) - (b.confidence || 0)) * dir;
      }
      if (sortField === 'cluster') {
        return (a.cluster_name || '').localeCompare(b.cluster_name || '') * dir;
      }
      return (a.index - b.index) * dir;
    });

    return data;
  }, [successResults, filterCluster, filterMinConf, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const pageResults = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  // ── CSV Export ──────────────────────────────────────────────

  const exportCsv = useCallback(() => {
    const headers = ['Index', 'Filename', 'Cluster ID', 'Cluster Name', 'Confidence', 'Top Skills'];
    const rows = filtered.map((r) => [
      r.index,
      r.filename || '',
      r.cluster_id ?? '',
      r.cluster_name || '',
      r.confidence != null ? (r.confidence * 100).toFixed(1) + '%' : '',
      (r.top_skills || []).join(' | '),
    ]);

    const csv = [headers, ...rows]
      .map((row) =>
        row.map((c) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')
      )
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `skillmap-bulk-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [filtered]);

  const toggleSort = useCallback((field) => {
    setSortField(field);
    setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
  }, []);

  const progress = files.length > 0
    ? Math.round((processedCount / files.length) * 100)
    : 0;

  return (
    <motion.div
      className="bulk-page"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Upload Section */}
      <section className="panel">
        <div className="panel__header">
          <h2>Bulk Upload</h2>
          <p>Upload up to 50 resumes for batch analysis.</p>
        </div>

        <FileDropZone
          onFiles={handleFiles}
          multiple
          maxFiles={50}
          label="Drop multiple resume files"
          sublabel={`PDF, DOCX, or TXT — ${files.length}/50 files queued`}
        />

        {/* File queue */}
        {files.length > 0 && (
          <div className="file-queue">
            <div className="file-queue__header">
              <span>{files.length} file(s) queued</span>
              <button className="btn-ghost btn-sm" onClick={clearAll}>
                <Trash2 size={12} /> Clear all
              </button>
            </div>

            <div className="file-queue__list">
              {files.map((f) => (
                <div key={f.id} className={`file-queue__item file-queue__item--${f.status}`}>
                  <span className="file-queue__name">{f.name}</span>
                  <span className="file-queue__status">
                    {f.status === 'pending' && 'Queued'}
                    {f.status === 'extracting' && 'Extracting...'}
                    {f.status === 'analyzing' && 'Analyzing...'}
                    {f.status === 'done' && '✓ Done'}
                    {f.status === 'error' && `✗ ${f.error}`}
                  </span>
                  <button
                    className="btn-icon"
                    onClick={() => removeFile(f.id)}
                    aria-label={`Remove ${f.name}`}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="bulk-actions">
          <button
            className="btn-primary btn-lg"
            onClick={processAll}
            disabled={processing || !files.length}
          >
            {processing ? <Loader2 size={16} className="spin" /> : <ScanSearch size={16} />}
            Analyze All ({files.length})
          </button>
        </div>

        {/* Progress bar */}
        {processing && (
          <div className="progress-bar-wrapper">
            <div className="progress-bar__label">Processing {processedCount}/{files.length} ({progress}%)</div>
            <div className="progress-bar__track">
              <motion.div
                className="progress-bar__fill"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.2 }}
              />
            </div>
          </div>
        )}

        <AnimatePresence>
          {error && (
            <motion.div
              className="alert alert--error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <AlertCircle size={16} />
              <span>{error}</span>
            </motion.div>
          )}
        </AnimatePresence>
      </section>

      {/* Results Section */}
      <section className="panel">
        <div className="panel__header panel__header--row">
          <div>
            <h2>Results</h2>
            <p>{filtered.length} of {successResults.length} results shown</p>
          </div>
          <div className="panel__actions">
            <button
              className="btn-accent"
              onClick={exportCsv}
              disabled={!filtered.length}
            >
              <Download size={14} /> Export CSV
            </button>
          </div>
        </div>

        {/* Filters */}
        {successResults.length > 0 && (
          <div className="bulk-filters">
            <div className="form-group form-group--inline">
              <label htmlFor="filter-cluster"><Filter size={12} /> Cluster</label>
              <select
                id="filter-cluster"
                value={filterCluster}
                onChange={(e) => { setFilterCluster(e.target.value); setPage(1); }}
              >
                <option value="">All clusters</option>
                {clusterNames.map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>

            <div className="form-group form-group--inline">
              <label htmlFor="filter-confidence">Min confidence</label>
              <input
                id="filter-confidence"
                type="number"
                min={0}
                max={100}
                step={5}
                value={filterMinConf}
                onChange={(e) => { setFilterMinConf(Number(e.target.value)); setPage(1); }}
                style={{ width: '70px' }}
              />
              <span>%</span>
            </div>
          </div>
        )}

        {/* Results table */}
        {pageResults.length > 0 ? (
          <>
            <div className="results-table-wrap">
              <table className="results-table">
                <thead>
                  <tr>
                    <th onClick={() => toggleSort('index')} style={{ cursor: 'pointer' }}>
                      # {sortField === 'index' ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                    </th>
                    <th>Filename</th>
                    <th onClick={() => toggleSort('cluster')} style={{ cursor: 'pointer' }}>
                      Cluster {sortField === 'cluster' ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                    </th>
                    <th onClick={() => toggleSort('confidence')} style={{ cursor: 'pointer' }}>
                      Confidence {sortField === 'confidence' ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                    </th>
                    <th>Top Skills</th>
                  </tr>
                </thead>
                <tbody>
                  {pageResults.map((r) => (
                    <tr key={r.index}>
                      <td>{r.index + 1}</td>
                      <td className="td-filename">{r.filename || `Resume ${r.index + 1}`}</td>
                      <td>
                        <span className="cluster-badge">{r.cluster_name}</span>
                      </td>
                      <td>
                        <ConfidenceBar value={r.confidence} label="" />
                      </td>
                      <td>
                        <div className="pill-row pill-row--compact">
                          {(r.top_skills || []).slice(0, 3).map((s, i) => (
                            <SkillPill key={s} name={s} index={i} />
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="pagination">
              <button
                className="btn-icon"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                aria-label="Previous page"
              >
                <ChevronLeft size={16} />
              </button>
              <span>
                Page {page} of {totalPages}
              </span>
              <button
                className="btn-icon"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                aria-label="Next page"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </>
        ) : (
          <div className="page-state page-state--empty" style={{ padding: '3rem 1rem' }}>
            <FileSpreadsheet size={28} />
            <h3>{results.length ? 'No matching results' : 'No results yet'}</h3>
            <p>
              {results.length
                ? 'Try adjusting your filters.'
                : 'Upload and analyze files to see results here.'}
            </p>
          </div>
        )}
      </section>
    </motion.div>
  );
}
