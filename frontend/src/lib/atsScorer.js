/**
 * atsScorer.js — Client-side ATS scoring engine.
 *
 * scoreResume(text, jobDescription?) → ScoreResult
 * No API calls. All logic runs in the browser.
 */

import powerSkillsData from '../data/powerSkills.json';
import actionVerbsList from '../data/actionVerbs.json';
import sectionKeywords from '../data/sectionKeywords.json';

// ── Flatten skills for matching ──────────────────────────────────

function deepFlattenSkills(obj) {
  const result = [];
  for (const val of Object.values(obj)) {
    if (Array.isArray(val)) result.push(...val);
    else if (typeof val === 'object' && val !== null) result.push(...deepFlattenSkills(val));
  }
  return result;
}

const ALL_SKILLS = deepFlattenSkills(powerSkillsData).map(s => s.toLowerCase());
const SKILL_SET = new Set(ALL_SKILLS);
const ACTION_VERBS = new Set(actionVerbsList.map(v => v.toLowerCase()));
const WEAK_VERBS = new Set(['helped','worked','did','made','was','had','got','went','used','tried','handled','assisted','participated','responsible','involved']);

// ── Section detection ────────────────────────────────────────────

function detectSections(text) {
  const lines = text.split('\n');
  const sections = [];
  let current = { type: 'unknown', title: '', lines: [] };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) { current.lines.push(line); continue; }

    const lower = trimmed.toLowerCase().replace(/[^a-z\s]/g, '').trim();
    let matched = null;
    for (const [type, keywords] of Object.entries(sectionKeywords)) {
      if (keywords.some(kw => lower === kw || lower.startsWith(kw + ' ') || lower.endsWith(' ' + kw))) {
        matched = type;
        break;
      }
    }

    if (matched) {
      if (current.lines.length > 0 || current.type !== 'unknown') {
        sections.push({ ...current, content: current.lines.join('\n') });
      }
      current = { type: matched, title: trimmed, lines: [] };
    } else {
      current.lines.push(line);
    }
  }
  if (current.lines.length > 0 || current.type !== 'unknown') {
    sections.push({ ...current, content: current.lines.join('\n') });
  }
  return sections;
}

// ── 1. Keywords & Skills (30 pts) ────────────────────────────────

function matchSkill(skill, text, wordTokens) {
  if (skill.includes(' ')) {
    // Multi-word phrase: word boundary regex
    return getWordBoundaryRegex(skill).test(text);
  } else if (skill.length <= 2) {
    // Very short (R, C, AI, UX): exact token match only
    return wordTokens.has(skill);
  } else {
    // Normal: word boundary regex
    return getWordBoundaryRegex(skill).test(text);
  }
}

function scoreKeywords(text, jobDescription) {
  const lower = text.toLowerCase();
  const wordTokens = new Set(lower.split(/[\s,;|/()[\]{}<>:]+/).filter(Boolean));

  const matched = ALL_SKILLS.filter(s => matchSkill(s, lower, wordTokens));
  const matchedSet = [...new Set(matched)];

  let jdTerms = [];
  if (jobDescription) {
    const jdLower = jobDescription.toLowerCase();
    const jdTokens = new Set(jdLower.split(/[\s,;|/()[\]{}<>:]+/).filter(Boolean));
    jdTerms = ALL_SKILLS.filter(s => matchSkill(s, jdLower, jdTokens));
    jdTerms = [...new Set(jdTerms)];
  }

  const expected = Math.max(jdTerms.length || 12, 12);
  const missing = (jdTerms.length > 0 ? jdTerms : ALL_SKILLS.slice(0, 30))
    .filter(s => !matchedSet.includes(s)).slice(0, 15);

  const pts = Math.min(30, Math.round((matchedSet.length / expected) * 30));
  return {
    score: pts, max: 30,
    matched: matchedSet, missing,
    matchPct: Math.round((matchedSet.length / expected) * 100)
  };
}

// ── 2. Formatting & Parseability (20 pts) ────────────────────────

function scoreFormatting(text) {
  let pts = 20;
  const issues = [];

  if (/[│┃┆┇┊┋|]{2,}/m.test(text) || /\t.*\t.*\t/m.test(text)) {
    pts -= 5; issues.push('Table-like layout detected — ATS often misreads tables');
  }
  if (/\[image\]|\[graphic\]|\.png|\.jpg|\.svg/i.test(text)) {
    pts -= 5; issues.push('Image/graphic references detected — ATS cannot parse images');
  }
  const lines = text.split('\n');
  const wideLines = lines.filter(l => l.length > 120);
  if (wideLines.length > 3) {
    pts -= Math.min(4, wideLines.length); issues.push('Lines exceed 120 characters — may cause parsing issues');
  }
  const fancyBullets = (text.match(/[◆▶►★✦✧●○◉⬤⚫⬥◈▪▫]/g) || []).length;
  if (fancyBullets > 0) {
    pts -= Math.min(3, fancyBullets); issues.push('Fancy bullets detected — use standard dashes or dots');
  }

  const foundHeaders = Object.entries(sectionKeywords).filter(([, kws]) =>
    kws.some(kw => text.toLowerCase().includes(kw))
  );
  if (foundHeaders.length < 3) {
    pts -= 5; issues.push('Missing standard section headers');
  }

  return { score: Math.max(0, pts), max: 20, issues };
}

// ── 3. Contact Completeness (10 pts) ─────────────────────────────

function scoreContact(text) {
  let pts = 0;
  const details = {};

  if (/[\w.-]+@[\w.-]+\.\w{2,}/i.test(text)) { pts += 3; details.email = true; }
  if (/(\+?\d[\d\s\-().]{7,}\d)/.test(text)) { pts += 3; details.phone = true; }
  if (/linkedin\.com\/in\/[\w-]+/i.test(text)) { pts += 2; details.linkedin = true; }
  if (/\b[A-Z][a-z]+,?\s*[A-Z]{2}\b/.test(text) || /\b\d{5,6}\b/.test(text)) {
    pts += 2; details.location = true;
  }
  if (/github\.com\/[\w-]+/i.test(text)) { pts += 1; }

  return { score: Math.min(10, pts), max: 10, details };
}

// ── 4. Section Structure (15 pts) ────────────────────────────────

function scoreStructure(text) {
  const lower = text.toLowerCase();
  const required = ['summary', 'experience', 'education', 'skills'];
  const found = [];
  const missing = [];

  for (const sec of required) {
    const kws = sectionKeywords[sec] || [];
    if (kws.some(kw => lower.includes(kw))) found.push(sec);
    else missing.push(sec);
  }

  const pts = Math.round(found.length * 3.75);
  return { score: pts, max: 15, found, missing };
}

// ── 5. Quantified Achievements (15 pts) ──────────────────────────

function scoreAchievements(text) {
  const quantRegex = /\d+[%x×kmb$]|\$[\d,.]+|\d+\s*(?:users|clients|projects|customers|employees|members|teams|revenue|sales|leads)/gi;
  const matches = text.match(quantRegex) || [];
  const count = matches.length;

  let pts;
  if (count === 0) pts = 0;
  else if (count <= 2) pts = 6;
  else if (count <= 5) pts = 10;
  else if (count <= 9) pts = 13;
  else pts = 15;

  const lines = text.split('\n').filter(l => quantRegex.test(l)).slice(0, 5);
  return { score: pts, max: 15, count, examples: lines };
}

// ── 6. Action Verbs (5 pts) ──────────────────────────────────────

function scoreActionVerbs(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(l =>
    /^[-•–—*]/.test(l) || /^\d+[.)]/.test(l) || (l.length > 20 && l.length < 200)
  );
  if (lines.length === 0) return { score: 0, max: 5, coverage: 0, weak: [] };

  let strong = 0, weakFound = [];
  for (const line of lines) {
    const first = line.replace(/^[-•–—*\d.)]+\s*/, '').split(/\s+/)[0]?.toLowerCase();
    if (!first) continue;
    if (ACTION_VERBS.has(first)) strong++;
    else if (WEAK_VERBS.has(first)) weakFound.push(first);
  }

  const coverage = lines.length > 0 ? (strong / lines.length) * 100 : 0;
  let pts;
  if (coverage >= 80) pts = 5;
  else if (coverage >= 60) pts = 3;
  else if (coverage >= 40) pts = 2;
  else pts = 0;

  return { score: pts, max: 5, coverage: Math.round(coverage), weak: [...new Set(weakFound)] };
}

// ── 7. Length & Density (5 pts) ──────────────────────────────────

function scoreLength(text) {
  const wordCount = text.split(/\s+/).filter(Boolean).length;
  let pts, message;

  if (wordCount >= 400 && wordCount <= 700) { pts = 5; message = 'Optimal length for a 1-page resume'; }
  else if (wordCount >= 701 && wordCount <= 900) { pts = 3; message = 'Slightly dense — consider trimming'; }
  else if (wordCount >= 901 && wordCount <= 1200) { pts = 5; message = 'Good length for a 2-page resume'; }
  else if (wordCount > 1200) { pts = 2; message = 'Too long — most ATS prefer 1–2 pages'; }
  else if (wordCount < 250) { pts = 2; message = 'Too short — add more detail'; }
  else { pts = 3; message = 'Acceptable length'; }

  return { score: pts, max: 5, wordCount, message };
}

// ── Suggestion generator ─────────────────────────────────────────

function generateSuggestions(categories) {
  const suggestions = [];
  let id = 0;

  const add = (priority, category, title, detail, sectionTarget = null, diff = null) => {
    suggestions.push({ id: `s${id++}`, priority, category, title, detail, sectionTarget, diff });
  };

  const { keywords, formatting, contact, structure, achievements, actionVerbs, length } = categories;

  // Keywords
  if (keywords.score < 15) {
    add('critical', 'keywords', 'Add more relevant skills', `Only ${keywords.matched.length} skills detected. Add skills like: ${keywords.missing.slice(0,5).join(', ')}.`, 'skills');
  } else if (keywords.score < 24) {
    add('important', 'keywords', 'Expand your skillset', `You're missing key terms: ${keywords.missing.slice(0,4).join(', ')}. Weave them into your experience bullets.`, 'skills');
  }
  if (keywords.missing.length > 0 && keywords.score >= 24) {
    add('nice', 'keywords', 'Consider adding niche skills', `Skills like ${keywords.missing.slice(0,3).join(', ')} could strengthen your profile.`, 'skills');
  }

  // Formatting
  if (formatting.issues.length > 0) {
    for (const issue of formatting.issues.slice(0, 3)) {
      const p = formatting.score < 10 ? 'critical' : 'important';
      add(p, 'formatting', 'Fix formatting issue', issue);
    }
  }

  // Contact
  if (!contact.details.email) add('critical', 'contact', 'Add email address', 'ATS requires a valid email to contact you.', null);
  if (!contact.details.phone) add('critical', 'contact', 'Add phone number', 'Include a phone number for recruiter outreach.', null);
  if (!contact.details.linkedin) add('important', 'contact', 'Add LinkedIn profile', 'Recruiters often verify candidates via LinkedIn.', null);
  if (!contact.details.location) add('nice', 'contact', 'Add your location', 'City and state help with location-based job matching.', null);

  // Structure
  for (const missing of structure.missing) {
    add('critical', 'structure', `Add ${missing} section`, `A "${missing}" section is expected by ATS parsers and recruiters.`, null);
  }

  // Achievements
  if (achievements.count === 0) {
    add('critical', 'achievements', 'Quantify your impact', 'Add numbers to your experience bullets (e.g., "Increased revenue by 35%").', 'experience',
      { before: 'Managed the sales team', after: 'Managed a 12-person sales team, driving $2.4M in quarterly revenue (+35% YoY)' });
  } else if (achievements.count < 3) {
    add('important', 'achievements', 'Add more metrics', `Only ${achievements.count} quantified achievement(s) found. Aim for 5+.`, 'experience');
  }

  // Action Verbs
  if (actionVerbs.weak.length > 0) {
    add('important', 'actionVerbs', 'Replace weak verbs', `Avoid: "${actionVerbs.weak.slice(0,3).join('", "')}". Use strong verbs like "Spearheaded", "Optimized", "Delivered".`, 'experience',
      { before: `Helped with the project`, after: `Spearheaded the project delivery` });
  }
  if (actionVerbs.coverage < 60) {
    add('important', 'actionVerbs', 'Start bullets with verbs', `Only ${actionVerbs.coverage}% of bullets start with action verbs. Aim for 80%+.`, 'experience');
  }

  // Length
  if (length.wordCount < 250) {
    add('critical', 'length', 'Resume is too short', 'Your resume has fewer than 250 words. Expand your experience and skills sections.', null);
  } else if (length.wordCount > 1200) {
    add('important', 'length', 'Consider shortening', 'Your resume exceeds 1,200 words. Trim older roles and focus on relevant experience.', null);
  }

  // Sort by priority
  const order = { critical: 0, important: 1, nice: 2 };
  suggestions.sort((a, b) => order[a.priority] - order[b.priority]);

  return suggestions.slice(0, 12);
}

// ── Domain Detection ─────────────────────────────────────────────

const DOMAIN_LABELS = {
  Software_Engineering: 'Software Engineering',
  Data_Science: 'Data Science & Analytics',
  Healthcare: 'Healthcare & Clinical',
  Finance: 'Finance & Accounting',
  Marketing: 'Marketing & Digital',
  Project_Management: 'Project Management',
  Human_Resources: 'Human Resources',
  Design_UX: 'Design & UX',
};

// Cache compiled regexes for word-boundary matching
const _regexCache = new Map();
function getWordBoundaryRegex(term) {
  if (_regexCache.has(term)) return _regexCache.get(term);
  // Escape regex special chars, then wrap with word boundaries
  const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`\\b${escaped}\\b`, 'i');
  _regexCache.set(term, regex);
  return regex;
}

function detectDomains(text) {
  const lower = text.toLowerCase();
  // Pre-tokenize text into a word set for fast exact matching of short terms
  const wordTokens = new Set(lower.split(/[\s,;|/()[\]{}<>:]+/).filter(w => w.length > 0));
  const results = [];

  for (const [domainKey, subcategories] of Object.entries(powerSkillsData)) {
    if (domainKey === 'Soft_Skills') continue;

    const domainSkills = deepFlattenSkills(subcategories).map(s => s.toLowerCase());
    const totalKeywords = domainSkills.length;
    if (totalKeywords === 0) continue;

    let matchCount = 0;
    const matchedTerms = [];

    for (const skill of domainSkills) {
      const hasSpace = skill.includes(' ');
      let isMatch = false;

      if (hasSpace) {
        // Multi-word phrase: use word-boundary regex to avoid partial overlap
        isMatch = getWordBoundaryRegex(skill).test(text);
      } else if (skill.length <= 2) {
        // Very short terms (R, C, AI, QI, HR, UX): require exact token match
        // This prevents "ai" matching inside "training", "r" inside "your", etc.
        isMatch = wordTokens.has(skill);
      } else if (skill.length <= 4) {
        // Short terms (SQL, CSS, HTML, Java, etc.): word boundary match
        isMatch = getWordBoundaryRegex(skill).test(text);
      } else {
        // Normal length terms: word boundary match
        isMatch = getWordBoundaryRegex(skill).test(text);
      }

      if (isMatch) {
        matchCount++;
        matchedTerms.push(skill);
      }
    }

    // Require minimum 3 keyword matches to register a domain
    if (matchCount < 3) continue;

    // Weighted confidence: raw match ratio boosted by absolute match count
    const rawRatio = matchCount / totalKeywords;
    const densityBonus = Math.min(0.20, matchCount * 0.006);
    const confidence = Math.min(99, Math.round((rawRatio + densityBonus) * 100));

    // Suppress noise: minimum 3% confidence
    if (confidence < 3) continue;

    results.push({
      domain: DOMAIN_LABELS[domainKey] || domainKey,
      key: domainKey,
      confidence,
      matchedCount: matchCount,
      totalKeywords,
      topMatches: [...new Set(matchedTerms)].slice(0, 8),
    });
  }

  results.sort((a, b) => b.confidence - a.confidence);
  return results.slice(0, 5);
}

// ── Main export ──────────────────────────────────────────────────

export function scoreResume(text, jobDescription = '') {
  if (!text || text.trim().length < 10) {
    return { total: 0, categories: {}, suggestions: [], keywords: { matched: [], missing: [] }, sections: [], domains: [] };
  }

  const keywords = scoreKeywords(text, jobDescription);
  const formatting = scoreFormatting(text);
  const contact = scoreContact(text);
  const structure = scoreStructure(text);
  const achievements = scoreAchievements(text);
  const actionVerbs = scoreActionVerbs(text);
  const length = scoreLength(text);

  const categories = { keywords, formatting, contact, structure, achievements, actionVerbs, length };
  const total = Math.min(100, Object.values(categories).reduce((s, c) => s + c.score, 0));
  const suggestions = generateSuggestions(categories);
  const sections = detectSections(text);
  const domains = detectDomains(text);

  return { total, categories, suggestions, keywords: { matched: keywords.matched, missing: keywords.missing }, sections, domains };
}

export { detectSections, detectDomains };
