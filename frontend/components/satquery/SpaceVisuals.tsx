type VisualProps = {
  className?: string;
};

/** Decorative SVGs kept separate from the imagery viewport so uploaded imagery is never altered. */
export function OrbitSatellite({ className }: VisualProps) {
  return (
    <svg
      viewBox="0 0 260 150"
      aria-hidden="true"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="sat-panel" x1="0" y1="0" x2="1" y2="1">
          <stop stopColor="#2d84d8" />
          <stop offset="1" stopColor="#102d6a" />
        </linearGradient>
        <linearGradient id="sat-body" x1="0" y1="0" x2="1" y2="1">
          <stop stopColor="#ffd36f" />
          <stop offset="1" stopColor="#a66a19" />
        </linearGradient>
        <filter id="sat-glow" x="-30%" y="-50%" width="160%" height="200%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <g filter="url(#sat-glow)" transform="rotate(-17 130 74)">
        <path d="M125 58L100 42L98 50L119 68L125 58Z" fill="#7f571f" />
        <rect
          x="112"
          y="47"
          width="45"
          height="45"
          rx="6"
          fill="url(#sat-body)"
          stroke="#ffe2a0"
          strokeWidth="2"
        />
        <path d="M120 50H150V67H120V50Z" fill="#d39027" opacity=".72" />
        <circle cx="136" cy="74" r="7" fill="#18386d" stroke="#f7cc6e" strokeWidth="2" />
        <path d="M157 64L169 61L172 71L158 76" fill="#a7741c" stroke="#e7bd60" strokeWidth="1.4" />
        <path
          d="M103 72L53 72L45 94L108 92L103 72Z"
          fill="url(#sat-panel)"
          stroke="#78c8ff"
          strokeWidth="2"
        />
        <path
          d="M170 65L222 54L229 76L177 86L170 65Z"
          fill="url(#sat-panel)"
          stroke="#78c8ff"
          strokeWidth="2"
        />
        {[70, 87, 190, 207].map((x) => (
          <path key={x} d={`M${x} 70L${x - 7} 94`} stroke="#8ed5ff" strokeWidth="1" opacity=".72" />
        ))}
        <path d="M124 92L121 110L138 112L143 92" fill="#ce8b20" />
        <path d="M130 111L126 121" stroke="#e9d2a1" strokeWidth="2" />
      </g>
    </svg>
  );
}

export function IndiaMapVisual({ className }: VisualProps) {
  return (
    <svg
      viewBox="0 0 840 430"
      role="img"
      aria-label="Illustrated map of the Indian subcontinent"
      className={className}
      preserveAspectRatio="xMidYMid slice"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="ocean" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#071f3a" />
          <stop offset="1" stopColor="#041326" />
        </linearGradient>
        <radialGradient id="land" cx="48%" cy="44%" r="70%">
          <stop stopColor="#6a8657" />
          <stop offset=".5" stopColor="#526c40" />
          <stop offset="1" stopColor="#263d2e" />
        </radialGradient>
        <filter id="map-soft" x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation="1.1" />
        </filter>
        <pattern id="map-grid" width="58" height="46" patternUnits="userSpaceOnUse">
          <path d="M58 0H0V46" fill="none" stroke="#66a9d8" strokeOpacity=".13" strokeWidth="1" />
        </pattern>
      </defs>
      <rect width="840" height="430" fill="url(#ocean)" />
      <rect width="840" height="430" fill="url(#map-grid)" />
      <g opacity=".28" filter="url(#map-soft)">
        <path
          d="M0 72C120 40 153 96 214 116C250 128 287 103 316 96L338 126L309 150L273 167L245 191L202 190L157 164L74 155L0 169V72Z"
          fill="#96bca4"
        />
        <path
          d="M462 36C531 23 609 39 669 82L715 106L698 140L640 159L590 139L548 105L489 91L462 36Z"
          fill="#9cbe8b"
        />
      </g>
      <g>
        <path
          d="M395 76L432 82L451 104L480 111L492 139L521 155L518 184L544 203L537 230L556 258L543 283L555 310L532 339L516 370L490 361L477 334L453 315L438 278L416 262L401 229L384 203L390 174L371 156L378 128L365 108L395 76Z"
          fill="url(#land)"
          stroke="#a0c586"
          strokeOpacity=".66"
          strokeWidth="2"
        />
        <path
          d="M404 85L423 100L410 132L429 153L419 185L438 203L421 230L442 269L458 290"
          fill="none"
          stroke="#c1ab6c"
          strokeOpacity=".65"
          strokeWidth="3"
        />
        <path
          d="M458 112L466 149L492 173L484 203L518 226"
          fill="none"
          stroke="#c1ab6c"
          strokeOpacity=".55"
          strokeWidth="2"
        />
        <path
          d="M372 157L342 145L330 130L353 114L369 118"
          fill="#566a3e"
          stroke="#a0c586"
          strokeOpacity=".45"
          strokeWidth="1.5"
        />
        <path
          d="M536 211L568 208L591 230L579 246L553 239Z"
          fill="#4d6540"
          stroke="#a0c586"
          strokeOpacity=".42"
          strokeWidth="1.5"
        />
        <path
          d="M542 332L556 358L548 388L538 371L531 347Z"
          fill="#435b39"
          stroke="#a0c586"
          strokeOpacity=".36"
          strokeWidth="1"
        />
        <path
          d="M592 280L606 299L598 320L588 304Z"
          fill="#487042"
          stroke="#a0c586"
          strokeOpacity=".35"
          strokeWidth="1"
        />
      </g>
      <g opacity=".6">
        {[
          { x: 440, y: 167 },
          { x: 482, y: 183 },
          { x: 461, y: 218 },
          { x: 505, y: 253 },
          { x: 424, y: 247 },
          { x: 502, y: 285 },
        ].map((city, index) => (
          <circle key={index} cx={city.x} cy={city.y} r={index === 3 ? 4 : 2.4} fill="#ffb149" />
        ))}
      </g>
      <path
        d="M246 225C327 188 333 228 382 202"
        fill="none"
        stroke="#5797d8"
        strokeOpacity=".34"
        strokeWidth="8"
      />
      <path
        d="M480 104C463 152 487 203 486 254C485 301 513 339 523 370"
        fill="none"
        stroke="#c5d7ba"
        strokeOpacity=".38"
        strokeWidth="1.5"
      />
      <path
        d="M297 106L598 342"
        stroke="#1d7ab5"
        strokeOpacity=".26"
        strokeWidth="1.5"
        strokeDasharray="8 7"
      />
      <g transform="translate(492 172)">
        <rect
          x="-17"
          y="-17"
          width="34"
          height="34"
          rx="2"
          fill="#ff841f"
          fillOpacity=".18"
          stroke="#ff9a42"
          strokeWidth="2"
          strokeDasharray="5 4"
        />
        <path d="M0-26V-13M0 13V26M-26 0H-13M13 0H26" stroke="#ffae69" strokeWidth="1.6" />
        <circle r="4.5" fill="#ff941f" stroke="#ffe0ad" strokeWidth="1.5" />
      </g>
      <text
        x="690"
        y="394"
        fill="#a7c8df"
        fontSize="12"
        fontFamily="ui-monospace, monospace"
        opacity=".8"
      >
        N
      </text>
      <path d="M697 407L704 391L711 407H706V420H702V407H697Z" fill="#d6e8f6" opacity=".88" />
      <g
        transform="translate(644 390)"
        fill="#95b6cc"
        fontFamily="ui-monospace, monospace"
        fontSize="10"
        opacity=".72"
      >
        <path d="M0 10H80" stroke="#95b6cc" strokeWidth="2" />
        <path d="M0 6V14M40 6V14M80 6V14" stroke="#95b6cc" strokeWidth="2" />
        <text x="0" y="29">
          0
        </text>
        <text x="31" y="29">
          250
        </text>
        <text x="69" y="29">
          500 km
        </text>
      </g>
    </svg>
  );
}

type RocketProps = VisualProps & {
  isLaunching?: boolean;
};

export function RocketLaunch({ className, isLaunching }: RocketProps) {
  return (
    <svg
      viewBox="0 0 180 370"
      aria-hidden="true"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="rocket-body" x1="0" y1="0" x2="1" y2="0">
          <stop stopColor="#c5d2db" />
          <stop offset=".5" stopColor="#f7f2e6" />
          <stop offset="1" stopColor="#8d9da8" />
        </linearGradient>
        <linearGradient id="rocket-flame" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#fff5a6" />
          <stop offset=".36" stopColor="#ff9a1e" />
          <stop offset="1" stopColor="#eb4010" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="rocket-flame-boost" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#ffffff" />
          <stop offset=".2" stopColor="#ffea79" />
          <stop offset=".55" stopColor="#ff6200" />
          <stop offset="1" stopColor="#eb2200" stopOpacity="0" />
        </linearGradient>
        <filter id="rocket-glow" x="-70%" y="-30%" width="240%" height="180%">
          <feGaussianBlur stdDeviation="10" />
        </filter>
        <filter id="rocket-intense-glow" x="-90%" y="-50%" width="280%" height="220%">
          <feGaussianBlur stdDeviation="16" />
        </filter>
      </defs>

      {/* Thruster Plume Glow */}
      <ellipse
        cx="90"
        cy="295"
        rx={isLaunching ? "65" : "45"}
        ry={isLaunching ? "55" : "33"}
        fill="#fb721e"
        opacity={isLaunching ? ".8" : ".36"}
        filter={isLaunching ? "url(#rocket-intense-glow)" : "url(#rocket-glow)"}
      />

      {/* Primary Thrust Flame */}
      {isLaunching ? (
        <>
          <path d="M68 270L90 395L112 270Z" fill="url(#rocket-flame-boost)" />
          <path d="M74 260L83 345L90 275L97 345L106 260Z" fill="#ffb428" opacity=".95" />
          <path d="M82 260L90 320L98 260Z" fill="#ffffff" opacity=".95" />
        </>
      ) : (
        <>
          <path d="M73 272L90 352L106 272Z" fill="url(#rocket-flame)" />
          <path d="M76 260L83 321L91 267L99 321L105 260Z" fill="#ff8c1d" opacity=".75" />
        </>
      )}

      {/* Rocket Main Body */}
      <path
        d="M73 78C75 41 80 18 90 6C100 18 105 41 107 78V246H73V78Z"
        fill="url(#rocket-body)"
        stroke="#f6f6ee"
        strokeWidth="1.5"
      />
      <path d="M72 112H108V151H72Z" fill="#b6532d" />
      <path d="M72 151H108V166H72Z" fill="#f0e6d5" />
      <path d="M72 166H108V206H72Z" fill="#b6532d" />
      <path d="M73 206H107V246H73Z" fill="url(#rocket-body)" />
      
      {/* Fins */}
      <path d="M73 200L51 237L73 232V206Z" fill="#beccd4" stroke="#eff4f4" strokeWidth="1" />
      <path d="M107 200L129 237L107 232V206Z" fill="#beccd4" stroke="#eff4f4" strokeWidth="1" />
      
      {/* Nose Cone Tip */}
      <path d="M82 20L90 9L98 20Z" fill="#0d2740" />
      <circle cx="90" cy="8" r="2.5" fill="#f68428" />

      {/* Structural Seams */}
      <path d="M76 78H104" stroke="#50606d" strokeWidth="1" opacity=".7" />
      <path d="M73 151H107M73 166H107M73 206H107" stroke="#74452f" strokeWidth="1" />
      
      {/* Launch Smoke Base Clouds */}
      <g opacity={isLaunching ? ".65" : ".26"} fill="#d4e4ed">
        <circle cx="20" cy="322" r="17" />
        <circle cx="155" cy="331" r="24" />
        <circle cx="46" cy="347" r="25" />
        <circle cx="124" cy="352" r="29" />
        {isLaunching && (
          <>
            <circle cx="90" cy="340" r="32" fill="#ffe0a0" opacity=".4" />
            <circle cx="35" cy="320" r="22" opacity=".5" />
            <circle cx="140" cy="320" r="26" opacity=".5" />
          </>
        )}
      </g>
    </svg>
  );
}
