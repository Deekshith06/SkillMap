/**
 * extractors.js — Client-side PDF and DOCX text extraction.
 */

export async function extractFromPDF(file) {
  const pdfjsLib = await import('pdfjs-dist');
  pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;

  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
  const pages = [];

  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const text = content.items.map(item => item.str).join(' ');
    pages.push(text);
  }

  return pages.join('\n\n');
}

export async function extractFromDOCX(file) {
  const mammoth = await import('mammoth');
  const arrayBuffer = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer });
  return result.value;
}

export async function extractText(file) {
  const name = file.name.toLowerCase();
  if (name.endsWith('.pdf')) return extractFromPDF(file);
  if (name.endsWith('.docx')) return extractFromDOCX(file);
  if (name.endsWith('.txt')) return file.text();
  throw new Error('Unsupported file type. Please upload a PDF or DOCX.');
}

export function validateFile(file) {
  const MAX_SIZE = 5 * 1024 * 1024;
  const ALLOWED = ['.pdf', '.docx', '.txt'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();

  if (!ALLOWED.includes(ext)) return 'Only PDF, DOCX, and TXT files are accepted.';
  if (file.size > MAX_SIZE) return 'File size exceeds 5 MB limit.';
  return null;
}
