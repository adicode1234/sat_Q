type SceneImageProps = {
  variant: "before" | "after" | "sar";
  className?: string;
};

/** Abstract synthetic satellite scene: green land, blue water, gray built-up. */
export function SceneImage({ variant, className }: SceneImageProps) {
  const built = variant === "before" ? 0 : 1;
  const sar = variant === "sar";

  return (
    <svg
      viewBox="0 0 400 300"
      role="img"
      aria-label={`Synthetic ${variant} satellite scene preview`}
      className={className}
      preserveAspectRatio="none"
    >
      <rect width="400" height="300" fill={sar ? "#12161c" : "#101a16"} />
      {/* vegetation parcels */}
      {[0, 1, 2, 3].map((i) => (
        <rect
          key={`v${i}`}
          x={10 + i * 34}
          y={30 + (i % 2) * 24}
          width={30}
          height={110 + (i % 3) * 30}
          fill={sar ? "#2a3138" : "#2f7d55"}
          opacity={sar ? 0.7 : 0.85}
        />
      ))}
      <rect
        x="8"
        y="196"
        width="140"
        height="42"
        fill={sar ? "#242a30" : "#3a8f5f"}
        opacity="0.8"
      />
      {/* water body */}
      <path
        d="M14 250 Q70 226 130 246 Q186 264 150 292 L20 292 Z"
        fill={sar ? "#0a0d12" : "#2b5fa8"}
        opacity={sar ? 0.95 : 0.9}
      />
      <path
        d="M148 258 Q210 244 268 220"
        stroke={sar ? "#0a0d12" : "#2b5fa8"}
        strokeWidth="9"
        fill="none"
        opacity="0.85"
      />
      {/* built-up blocks */}
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <rect
          key={`b${i}`}
          x={190 + (i % 3) * 42}
          y={70 + Math.floor(i / 3) * 46}
          width={34}
          height={36}
          fill={sar ? "#cdd6e2" : "#8e9aa8"}
          opacity={sar ? 0.85 : 0.9}
        />
      ))}
      {built === 1 &&
        [0, 1, 2].map((i) => (
          <rect
            key={`nb${i}`}
            x={300 + (i % 2) * 40}
            y={44 + i * 34}
            width={30}
            height={28}
            fill={sar ? "#e6ecf5" : "#a8b3c1"}
            opacity="0.95"
          />
        ))}
      {/* road corridor */}
      <rect x="170" y="0" width="8" height="300" fill={sar ? "#3a424b" : "#5c6672"} opacity="0.9" />
      <rect
        x="170"
        y="150"
        width="230"
        height="7"
        fill={sar ? "#3a424b" : "#5c6672"}
        opacity="0.9"
      />
      {/* bare soil */}
      <rect
        x="240"
        y="200"
        width="150"
        height="70"
        fill={sar ? "#1d2228" : "#7d6a4f"}
        opacity="0.7"
      />
      {sar && (
        <g opacity="0.18">
          {Array.from({ length: 90 }).map((_, i) => (
            <rect
              key={`n${i}`}
              x={(i * 53) % 400}
              y={(i * 91) % 300}
              width="3"
              height="3"
              fill="#ffffff"
            />
          ))}
        </g>
      )}
    </svg>
  );
}
