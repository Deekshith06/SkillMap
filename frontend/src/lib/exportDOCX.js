/** exportDOCX.js — docx.js wrapper for DOCX download. */
import { Document, Packer, Paragraph, HeadingLevel, TextRun } from 'docx';
import { saveAs } from 'file-saver';

export async function exportToDOCX(sections, filename = 'resume-optimised.docx') {
  const children = [];

  for (const sec of sections) {
    children.push(new Paragraph({
      text: sec.title,
      heading: HeadingLevel.HEADING_2,
      spacing: { before: 240, after: 120 },
    }));

    const lines = sec.content.split('\n').filter(l => l.trim());
    for (const line of lines) {
      const trimmed = line.trim();
      const isBullet = /^[-•–—*]/.test(trimmed);
      children.push(new Paragraph({
        children: [new TextRun({ text: trimmed.replace(/^[-•–—*]\s*/, ''), size: 22 })],
        bullet: isBullet ? { level: 0 } : undefined,
        spacing: { after: 80 },
      }));
    }
  }

  const doc = new Document({ sections: [{ children }] });
  const blob = await Packer.toBlob(doc);
  saveAs(blob, filename);
}

export function exportToTXT(sections, filename = 'resume-optimised.txt') {
  const text = sections.map(s => `${s.title}\n${'─'.repeat(40)}\n${s.content}`).join('\n\n');
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  saveAs(blob, filename);
}
