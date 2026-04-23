/**
 * resumeParser.js — Parse raw text into structured resume sections.
 */
import sectionKeywords from '../data/sectionKeywords.json';

const SECTION_TEMPLATES = {
  summary: 'Results-driven professional with X years of experience in [field]. Proven track record of delivering impactful solutions that drive business growth.',
  experience: 'Company Name | Job Title\nMonth Year – Present\n• Led cross-functional initiative that achieved [result]\n• Developed and implemented [project] resulting in [metric]\n• Collaborated with stakeholders to [action] improving [outcome]',
  education: 'Degree — Major\nUniversity Name, City, State\nGraduation: Month Year\nGPA: X.X/4.0 (if 3.5+)',
  skills: 'Technical: [skill1], [skill2], [skill3]\nTools: [tool1], [tool2]\nSoft Skills: [skill1], [skill2]',
  projects: 'Project Name | Link\n• Built [technology] solution that [impact]\n• Resulted in [quantified outcome]',
  certifications: 'Certification Name — Issuing Organization, Month Year',
  languages: 'English (Native), Spanish (Professional Working)',
};

export function parseSections(text) {
  const lines = text.split('\n');
  const sections = [];
  let currentType = 'summary';
  let currentTitle = 'Summary';
  let currentLines = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) { currentLines.push(line); continue; }

    const lower = trimmed.toLowerCase().replace(/[^a-z\s]/g, '').trim();
    let matchedType = null;

    for (const [type, keywords] of Object.entries(sectionKeywords)) {
      if (keywords.some(kw => lower === kw || (lower.length < 40 && lower.includes(kw)))) {
        matchedType = type;
        break;
      }
    }

    if (matchedType) {
      if (currentLines.length > 0) {
        sections.push({
          id: `sec-${sections.length}`,
          type: currentType,
          title: currentTitle,
          content: currentLines.join('\n').trim(),
        });
      }
      currentType = matchedType;
      currentTitle = trimmed;
      currentLines = [];
    } else {
      currentLines.push(line);
    }
  }

  if (currentLines.length > 0) {
    sections.push({
      id: `sec-${sections.length}`,
      type: currentType,
      title: currentTitle,
      content: currentLines.join('\n').trim(),
    });
  }

  return sections.length > 0 ? sections : [{ id: 'sec-0', type: 'summary', title: 'Resume', content: text }];
}

export function getTemplate(sectionType) {
  return SECTION_TEMPLATES[sectionType] || '';
}

export { SECTION_TEMPLATES };
