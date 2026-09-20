import { useState } from 'react';

export type BoxOverlay = {
  type: 'bbox' | 'mask';
  width: number;
  height: number;
  image_id?: string;
  label?: string;
  data: unknown;
};

export function AnnotatedScene({ src, alt, overlay, showBoxes }: {
  src: string;
  alt: string;
  overlay?: BoxOverlay | null;
  showBoxes: boolean;
}) {
  const [loaded, setLoaded] = useState({ src: '', width: 0, height: 0 });
  const height = loaded.width ? 1000 * loaded.height / loaded.width : 1000;
  const boxes = overlay?.type === 'bbox' && overlay.width > 0 && overlay.height > 0 && Array.isArray(overlay.data)
    ? overlay.data.flatMap((item) => {
        if (!item || !Array.isArray(item.box) || item.box.length !== 4 || typeof item.label !== 'string') return [];
        if (!item.box.every((v: unknown) => typeof v === 'number' && Number.isFinite(v))) return [];
        const [left, top, right, bottom] = item.box;
        if (left < 0 || top < 0 || right > overlay.width || bottom > overlay.height || right <= left || bottom <= top) return [];
        return [{ label: item.label, x: left / overlay.width * 1000, y: top / overlay.height * height,
          width: (right - left) / overlay.width * 1000, height: (bottom - top) / overlay.height * height }];
      }) : [];
  return <>
    <img src={src} alt={alt} className="satt-viewport-image" onLoad={(event) => {
      setLoaded({ src, width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight });
    }} />
    {showBoxes && loaded.src === src && boxes.length > 0 && (
      <svg className="satt-object-boxes" viewBox={`0 0 1000 ${height}`} preserveAspectRatio="xMidYMid slice"
        role="img" aria-label={`${boxes.length} candidate object locations`}>
        {boxes.map((box, index) => {
          const label = `${index + 1}. ${box.label}`;
          const labelY = Math.max(18, box.y - 5);
          return <g key={`${index}-${box.label}`}>
            <title>{label} — {overlay?.label || 'Candidate detection'}</title>
            <rect x={box.x} y={box.y} width={box.width} height={box.height}
              fill="none" stroke="#ff553e" strokeWidth={2} vectorEffect="non-scaling-stroke" />
            <text x={Math.min(box.x + 3, 970)} y={labelY} fill="#fff" stroke="#06111f"
              strokeWidth={4} paintOrder="stroke" fontSize={18} fontWeight={700}>{label}</text>
          </g>;
        })}
      </svg>
    )}
  </>;
}
