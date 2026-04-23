/**
 * App.jsx — Root application component.
 *
 * Sets up routing, navigation shell, context provider,
 * and wraps all pages in ErrorBoundary.
 */

import { useState } from 'react';
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  LayoutDashboard, ScanSearch, Upload as UploadIcon, BarChart3,
  Database, ArrowRight, Menu, X, FileSearch,
} from 'lucide-react';

import { AppProvider } from './context/AppContext';
import { ResumeProvider } from './context/ResumeContext';
import ErrorBoundary from './components/ErrorBoundary';

import Dashboard from './pages/Dashboard';
import Analyze from './pages/Analyze';
import BulkUpload from './pages/BulkUpload';
import Insights from './pages/Insights';
import ATSUpload from './pages/Upload';
import ScoreDashboard from './pages/ScoreDashboard';
import ATSEditor from './pages/Editor';

// ── Navigation items ────────────────────────────────────────────

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/analyze', label: 'Analyze', icon: ScanSearch },
  { to: '/bulk', label: 'Bulk Upload', icon: UploadIcon },
  { to: '/insights', label: 'Insights', icon: BarChart3 },
  { to: '/ats', label: 'ATS Editor', icon: FileSearch },
];

// ── Page transitions ────────────────────────────────────────────

const pageVariants = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -24 },
};

const pageTransition = {
  duration: 0.3,
  ease: [0.4, 0, 0.2, 1],
};

// ── Navbar ──────────────────────────────────────────────────────

function Navbar({ onMenuOpen }) {
  return (
    <header className="navbar">
      <div className="navbar__inner">
        <Link to="/" className="navbar__brand">
          <span className="navbar__logo">
            <Database size={16} />
          </span>
          <span className="navbar__name">SkillMap</span>
        </Link>

        <nav className="navbar__links" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `navbar__link ${isActive ? 'navbar__link--active' : ''}`
              }
            >
              {({ isActive }) => (
                <span className="navbar__link-inner">
                  {isActive && (
                    <motion.span
                      className="navbar__pill"
                      layoutId="nav-pill"
                      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
                    />
                  )}
                  <item.icon size={14} />
                  <span>{item.label}</span>
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="navbar__actions">
          <Link to="/analyze" className="btn-primary btn-sm navbar__cta">
            Get Started <ArrowRight size={14} />
          </Link>
          <button
            type="button"
            className="btn-icon navbar__menu-btn"
            onClick={onMenuOpen}
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>
        </div>
      </div>
    </header>
  );
}

// ── Mobile menu ─────────────────────────────────────────────────

function MobileMenu({ open, onClose }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="mobile-menu"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="mobile-menu__panel"
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -20, opacity: 0 }}
          >
            <div className="mobile-menu__header">
              <span>Navigation</span>
              <button className="btn-icon" onClick={onClose} aria-label="Close menu">
                <X size={18} />
              </button>
            </div>
            <nav className="mobile-menu__nav">
              {NAV_ITEMS.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `mobile-menu__link ${isActive ? 'mobile-menu__link--active' : ''}`
                  }
                >
                  <item.icon size={16} />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </nav>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ── App Shell ───────────────────────────────────────────────────

export default function App() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <AppProvider>
      <ResumeProvider>
        <div className="app">
          <Navbar onMenuOpen={() => setMobileMenuOpen(true)} />
          <MobileMenu
            open={mobileMenuOpen}
            onClose={() => setMobileMenuOpen(false)}
          />

          <main className="app__main">
            <ErrorBoundary>
              <AnimatePresence mode="wait">
                <Routes location={location} key={location.pathname}>
                  <Route
                    path="/"
                    element={
                      <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit" transition={pageTransition}>
                        <Dashboard />
                      </motion.div>
                    }
                  />
                  <Route
                    path="/analyze"
                    element={
                      <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit" transition={pageTransition}>
                        <Analyze />
                      </motion.div>
                    }
                  />
                  <Route
                    path="/bulk"
                    element={
                      <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit" transition={pageTransition}>
                        <BulkUpload />
                      </motion.div>
                    }
                  />
                  <Route
                    path="/insights"
                    element={
                      <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit" transition={pageTransition}>
                        <Insights />
                      </motion.div>
                    }
                  />
                  <Route
                    path="/ats"
                    element={
                      <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit" transition={pageTransition}>
                        <ATSUpload />
                      </motion.div>
                    }
                  />
                  <Route
                    path="/ats/score"
                    element={<ScoreDashboard />}
                  />
                  <Route
                    path="/ats/editor"
                    element={<ATSEditor />}
                  />
                </Routes>
              </AnimatePresence>
            </ErrorBoundary>
          </main>
        </div>
      </ResumeProvider>
    </AppProvider>
  );
}
