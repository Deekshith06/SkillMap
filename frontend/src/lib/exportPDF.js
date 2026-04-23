/** exportPDF.js — html2pdf wrapper for A4 PDF download. */
export async function exportToPDF(element, filename = 'resume-optimised.pdf') {
  const html2pdf = (await import('html2pdf.js')).default;
  return html2pdf().set({
    margin: [12, 12, 12, 12],
    filename,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
  }).from(element).save();
}
