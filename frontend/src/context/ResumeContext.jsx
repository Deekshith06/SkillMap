/**
 * ResumeContext.jsx — Global state for ATS resume editor.
 */
import { createContext, useContext, useReducer, useCallback } from 'react';
import { scoreResume } from '../lib/atsScorer';
import { parseSections } from '../lib/resumeParser';

const ResumeContext = createContext(null);

const initialState = {
  file: null,
  rawText: '',
  parsedSections: [],
  scoreResult: null,
  originalScore: null,
  appliedSuggestions: [],
  isScoring: false,
  isParsing: false,
  parseError: null,
  currentScreen: 'upload',
};

function reducer(state, action) {
  switch (action.type) {
    case 'SET_FILE':
      return { ...state, file: action.payload, parseError: null };
    case 'SET_PARSING':
      return { ...state, isParsing: action.payload };
    case 'SET_PARSE_ERROR':
      return { ...state, parseError: action.payload, isParsing: false };
    case 'SET_RAW_TEXT': {
      const sections = parseSections(action.payload);
      return { ...state, rawText: action.payload, parsedSections: sections, isParsing: false };
    }
    case 'UPDATE_SCORE': {
      const isFirst = state.originalScore === null;
      return {
        ...state,
        scoreResult: action.payload,
        originalScore: isFirst ? action.payload.total : state.originalScore,
        isScoring: false,
      };
    }
    case 'SET_SCORING':
      return { ...state, isScoring: action.payload };
    case 'SET_SCREEN':
      return { ...state, currentScreen: action.payload };
    case 'UPDATE_SECTIONS':
      return { ...state, parsedSections: action.payload };
    case 'UPDATE_SECTION_CONTENT': {
      const sections = state.parsedSections.map(s =>
        s.id === action.payload.id ? { ...s, content: action.payload.content } : s
      );
      return { ...state, parsedSections: sections };
    }
    case 'ADD_SECTION': {
      const newSec = {
        id: `sec-${Date.now()}`,
        type: action.payload.type,
        title: action.payload.title,
        content: action.payload.content || '',
      };
      return { ...state, parsedSections: [...state.parsedSections, newSec] };
    }
    case 'DELETE_SECTION':
      return { ...state, parsedSections: state.parsedSections.filter(s => s.id !== action.payload) };
    case 'APPLY_SUGGESTION':
      return { ...state, appliedSuggestions: [...state.appliedSuggestions, action.payload] };
    case 'RESET':
      return { ...initialState };
    default:
      return state;
  }
}

export function ResumeProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  const runScore = useCallback(async (text) => {
    dispatch({ type: 'SET_SCORING', payload: true });
    const resumeText = text || state.rawText;

    try {
      // Try backend-powered scoring (NLP + BERT)
      const res = await fetch('http://localhost:5001/ats/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resumeText }),
        signal: AbortSignal.timeout(5000),
      });
      if (res.ok) {
        const json = await res.json();
        dispatch({ type: 'UPDATE_SCORE', payload: json.data });
        return;
      }
    } catch {
      // Backend unavailable — fall through to client-side
    }

    // Fallback: client-side scoring
    setTimeout(() => {
      const result = scoreResume(resumeText);
      dispatch({ type: 'UPDATE_SCORE', payload: result });
    }, 50);
  }, [state.rawText]);

  const getFullText = useCallback(() => {
    return state.parsedSections.map(s => `${s.title}\n${s.content}`).join('\n\n');
  }, [state.parsedSections]);

  return (
    <ResumeContext.Provider value={{ state, dispatch, runScore, getFullText }}>
      {children}
    </ResumeContext.Provider>
  );
}

export function useResume() {
  const ctx = useContext(ResumeContext);
  if (!ctx) throw new Error('useResume must be used within ResumeProvider');
  return ctx;
}
