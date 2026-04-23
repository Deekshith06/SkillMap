/**
 * api/client.js — Centralised API client for SkillMap.
 *
 * Features:
 *  - Base URL from import.meta.env.VITE_API_URL
 *  - Exponential back-off retry (max 3 attempts)
 *  - Automatic JSON Content-Type
 *  - Unwraps { data, meta } response envelope
 */

import axios from 'axios';

const BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:5001').replace(/\/$/, '');

const client = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120_000, // 2 min for heavy ML inference
});

/**
 * Exponential back-off retry wrapper.
 * Retries on 5xx or network errors, up to maxRetries attempts.
 */
async function withRetry(requestFn, maxRetries = 3) {
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await requestFn();
      return response;
    } catch (err) {
      lastError = err;
      const status = err.response?.status;

      // Only retry on server errors or network failures
      const isRetryable = !status || status >= 500;
      if (!isRetryable || attempt === maxRetries - 1) {
        throw err;
      }

      // Exponential back-off: 500ms, 1000ms, 2000ms
      const delay = Math.pow(2, attempt) * 500;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

/**
 * Unwrap the standardised response envelope.
 * Server returns { data: ..., meta: { duration_ms } }
 * or { error: { code, message } }
 */
function unwrap(response) {
  const body = response.data;

  // New-format envelope
  if (body && typeof body === 'object' && 'data' in body) {
    return body.data;
  }

  // Legacy format (no envelope) — return as-is
  return body;
}

// ── Public API methods ──────────────────────────────────────────

export async function getHealth() {
  const res = await withRetry(() => client.get('/health'));
  return unwrap(res);
}

export async function getStats() {
  const res = await withRetry(() => client.get('/stats'));
  return unwrap(res);
}

export async function getClusters() {
  const res = await withRetry(() => client.get('/clusters'));
  return unwrap(res);
}

export async function getClusterResumes(clusterId, page = 1, perPage = 25) {
  const res = await withRetry(() =>
    client.get(`/clusters/${clusterId}/resumes`, {
      params: { page, per_page: perPage },
    })
  );
  return unwrap(res);
}

export async function predictResume(text) {
  const res = await withRetry(() =>
    client.post('/predict', { resume_text: text })
  );
  return unwrap(res);
}

export async function predictResumeFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await withRetry(() =>
    client.post('/predict', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  );
  return unwrap(res);
}

export async function bulkPredictTexts(resumes) {
  const res = await withRetry(() =>
    client.post('/bulk-predict', { resumes })
  );
  return unwrap(res);
}

export async function bulkPredictFiles(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const res = await withRetry(() =>
    client.post('/bulk-predict', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300_000, // 5 min for bulk
    })
  );
  return unwrap(res);
}

export default client;
