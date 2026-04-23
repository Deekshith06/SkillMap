/**
 * Skeleton — Animated loading placeholder.
 */

export default function Skeleton({ width, height = '1rem', borderRadius = '6px', style = {} }) {
  return (
    <div
      className="skeleton"
      style={{
        width: width || '100%',
        height,
        borderRadius,
        ...style,
      }}
      aria-hidden="true"
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <Skeleton height="8px" width="60px" />
      <Skeleton height="1.4rem" width="70%" style={{ marginTop: '12px' }} />
      <Skeleton height="0.9rem" width="40%" style={{ marginTop: '8px' }} />
      <div style={{ display: 'flex', gap: '6px', marginTop: '12px' }}>
        <Skeleton height="24px" width="60px" borderRadius="12px" />
        <Skeleton height="24px" width="72px" borderRadius="12px" />
        <Skeleton height="24px" width="52px" borderRadius="12px" />
      </div>
      <Skeleton height="6px" width="100%" style={{ marginTop: '16px' }} />
      <Skeleton height="36px" width="120px" borderRadius="8px" style={{ marginTop: '16px' }} />
    </div>
  );
}

export function SkeletonKPI() {
  return (
    <div className="skeleton-kpi">
      <Skeleton height="32px" width="32px" borderRadius="8px" />
      <Skeleton height="2rem" width="60%" style={{ marginTop: '8px' }} />
      <Skeleton height="0.85rem" width="40%" style={{ marginTop: '4px' }} />
    </div>
  );
}
