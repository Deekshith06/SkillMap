/**
 * AppContext.jsx — Global state management with React Context + useReducer.
 *
 * Manages: stats, clusters, loading/error states, last results.
 * Persists last analysis results in sessionStorage.
 */

import { createContext, useContext, useEffect, useReducer, useCallback } from 'react';
import { getStats, getClusters } from '../api/client';

// ── Initial state ───────────────────────────────────────────────

function loadSessionResults() {
  try {
    const raw = sessionStorage.getItem('skillmap_last_results');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

const initialState = {
  stats: null,
  clusters: [],
  loading: true,
  error: null,
  lastResults: loadSessionResults(),
  bulkResults: [],
};

// ── Action types ────────────────────────────────────────────────

const ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_DATA: 'SET_DATA',
  SET_ERROR: 'SET_ERROR',
  SET_LAST_RESULTS: 'SET_LAST_RESULTS',
  SET_BULK_RESULTS: 'SET_BULK_RESULTS',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// ── Reducer ─────────────────────────────────────────────────────

function reducer(state, action) {
  switch (action.type) {
    case ACTIONS.SET_LOADING:
      return { ...state, loading: action.payload };

    case ACTIONS.SET_DATA:
      return {
        ...state,
        stats: action.payload.stats,
        clusters: action.payload.clusters,
        loading: false,
        error: null,
      };

    case ACTIONS.SET_ERROR:
      return { ...state, error: action.payload, loading: false };

    case ACTIONS.SET_LAST_RESULTS: {
      // Persist to sessionStorage
      try {
        sessionStorage.setItem(
          'skillmap_last_results',
          JSON.stringify(action.payload)
        );
      } catch { /* quota exceeded — ignore */ }
      return { ...state, lastResults: action.payload };
    }

    case ACTIONS.SET_BULK_RESULTS:
      return { ...state, bulkResults: action.payload };

    case ACTIONS.CLEAR_ERROR:
      return { ...state, error: null };

    default:
      return state;
  }
}

// ── Context ─────────────────────────────────────────────────────

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // Fetch initial data on mount
  useEffect(() => {
    let alive = true;

    async function load() {
      dispatch({ type: ACTIONS.SET_LOADING, payload: true });

      try {
        const [statsData, clusterData] = await Promise.all([
          getStats(),
          getClusters(),
        ]);

        if (!alive) return;

        dispatch({
          type: ACTIONS.SET_DATA,
          payload: { stats: statsData, clusters: clusterData },
        });
      } catch (err) {
        if (!alive) return;
        dispatch({
          type: ACTIONS.SET_ERROR,
          payload: err.message || 'Failed to load data from server.',
        });
      }
    }

    load();
    return () => { alive = false; };
  }, []);

  const setLastResults = useCallback((results) => {
    dispatch({ type: ACTIONS.SET_LAST_RESULTS, payload: results });
  }, []);

  const setBulkResults = useCallback((results) => {
    dispatch({ type: ACTIONS.SET_BULK_RESULTS, payload: results });
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: ACTIONS.CLEAR_ERROR });
  }, []);

  const refreshData = useCallback(async () => {
    dispatch({ type: ACTIONS.SET_LOADING, payload: true });
    try {
      const [statsData, clusterData] = await Promise.all([
        getStats(),
        getClusters(),
      ]);
      dispatch({
        type: ACTIONS.SET_DATA,
        payload: { stats: statsData, clusters: clusterData },
      });
    } catch (err) {
      dispatch({
        type: ACTIONS.SET_ERROR,
        payload: err.message || 'Failed to refresh data.',
      });
    }
  }, []);

  const value = {
    ...state,
    setLastResults,
    setBulkResults,
    clearError,
    refreshData,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppData() {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error('useAppData must be used within an AppProvider');
  }
  return ctx;
}

export default AppContext;
