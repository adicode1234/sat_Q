import { useState, useRef, useEffect } from "react";
import {
  IconRocket,
  IconPlayerPlay,
  IconSatellite,
  IconBrain,
  IconMapPin,
  IconLeaf,
  IconChevronRight,
  IconChevronDown,
  IconLogout,
  IconUserCircle,
  IconBrandLinkedin,
  IconBrandInstagram,
  IconMail,
  IconUser,
  IconMessageCircle,
  IconSend,
  IconX,
} from "@tabler/icons-react";
import type { Mode } from "@/routes";
import { AboutModal } from "./AboutModal";
import * as Dialog from "@radix-ui/react-dialog";

interface SatQueryLandingProps {
  onExplorePlatform: (selectedMode?: Mode, initialQuery?: string) => void;
  isLoggedIn?: boolean;
  authUser?: { id?: string; email?: string; name?: string } | null;
  userAvatarUrl?: string;
  onLogout?: () => void;
  onAuthClick?: (mode: 'signin' | 'signup') => void;
}

export function SatQueryLanding({
  onExplorePlatform,
  isLoggedIn = false,
  authUser,
  userAvatarUrl,
  onLogout,
  onAuthClick,
}: SatQueryLandingProps) {
  const [activeNav, setActiveNav] = useState("Home");
  const [showAboutModal, setShowAboutModal] = useState(false);
  const [showContact, setShowContact] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement | null>(null);
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactQuery, setContactQuery] = useState("");

  const resolvedAvatar = userAvatarUrl || (() => {
    try {
      return localStorage.getItem('satquery_user_avatar') || '';
    } catch {
      return '';
    }
  })();

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(e.target as Node)) {
        setShowProfileMenu(false);
      }
    };
    if (showProfileMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showProfileMenu]);

  const navItems = [
    { id: "Home", label: "Home", mode: undefined },
    { id: "About", label: "About", mode: undefined },
    { id: "Gallery", label: "Gallery", mode: "single" as Mode },
    { id: "Contact", label: "Contact", mode: undefined },
  ];

  const featureCards = [
    {
      id: "satellite-data",
      title: "Satellite Data",
      desc: "High resolution & multi-spectral",
      icon: IconSatellite,
      mode: "single" as Mode,
    },
    {
      id: "ai-analysis",
      title: "AI Analysis",
      desc: "Advanced machine learning & VQA",
      icon: IconBrain,
      mode: "single" as Mode,
    },
    {
      id: "real-world-insights",
      title: "Real-world Insights",
      desc: "For agriculture, disaster, urban & more",
      icon: IconMapPin,
      mode: "bitemporal" as Mode,
    },
    {
      id: "sustainable-future",
      title: "A Sustainable Future",
      desc: "Data for a better planet",
      icon: IconLeaf,
      mode: "fusion" as Mode,
    },
  ];

  const handleContactSubmit = () => {
    if (!contactName.trim() || !contactEmail.trim() || !contactQuery.trim()) return;
    const subject = encodeURIComponent(`SatQuery Contact from ${contactName}`);
    const body = encodeURIComponent(
      `Name: ${contactName}\nEmail: ${contactEmail}\n\nMessage:\n${contactQuery}`
    );
    window.location.href = `mailto:adi1234@gmail.com?subject=${subject}&body=${body}`;
  };

  return (
    <div className="sat-landing-root">
      <div className="sat-landing-stage">
        {/* Crisp 2.7K Background Artwork - Space, Earth & Satellites */}
        <img
          src="/satquery_hero_bg.png"
          alt="SatQuery AI - Earth Observation Intelligence"
          className="sat-landing-backdrop"
        />

        {/* ── ANIMATED LAYER 1: Earth Atmosphere Glow & Rotation ── */}
        <div className="sat-earth-anim-layer" aria-hidden="true">
          <div className="sat-earth-atmo-ring sat-earth-atmo-1" />
          <div className="sat-earth-atmo-ring sat-earth-atmo-2" />
          <div className="sat-earth-rotate-stripe" />
          <div className="sat-earth-city-glow sat-city-glow-1" />
          <div className="sat-earth-city-glow sat-city-glow-2" />
          <div className="sat-earth-city-glow sat-city-glow-3" />
        </div>

        {/* ── ANIMATED LAYER 2: Orbiting Satellite ── */}
        <div className="sat-orbit-layer" aria-hidden="true">
          <svg
            className="sat-orbit-svg"
            viewBox="0 0 800 450"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <ellipse
              cx="500" cy="340" rx="260" ry="120"
              stroke="rgba(56,189,248,0.15)" strokeWidth="1"
              strokeDasharray="6 8"
            />
            <ellipse
              cx="500" cy="340" rx="320" ry="90"
              stroke="rgba(139,92,246,0.10)" strokeWidth="1"
              strokeDasharray="4 10"
              transform="rotate(-15 500 340)"
            />
          </svg>
        </div>


        {/* ── ANIMATED LAYER 3: Twinkling Stars ── */}
        <div className="sat-stars-layer" aria-hidden="true">
          {Array.from({ length: 30 }).map((_, i) => (
            <div
              key={i}
              className="sat-star"
              style={{
                left: `${(i * 37 + 3) % 100}%`,
                top: `${(i * 23 + 7) % 60}%`,
                animationDelay: `${(i * 0.31) % 4}s`,
                animationDuration: `${2 + (i % 3)}s`,
                width: i % 5 === 0 ? '2.5px' : '1.5px',
                height: i % 5 === 0 ? '2.5px' : '1.5px',
              }}
            />
          ))}
        </div>

        {/* ── ANIMATED LAYER 4: Scanning beam ── */}
        <div className="sat-scan-beam" aria-hidden="true" />

        {/* ── 1. NATIVE RETINA HEADER ── */}
        <header className="sat-live-header">
          <div className="sat-live-brand" onClick={() => setActiveNav("Home")} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <img src="/satquery_logo.png" alt="SatQuery Logo" className="sat-brand-logo-img" />
            <span className="sat-brand-name">SATQUERY</span>
          </div>

          <nav className="sat-live-nav" aria-label="Main Navigation">
            {navItems.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`sat-nav-btn ${activeNav === item.id ? "sat-nav-active" : ""}`}
                onClick={() => {
                  setActiveNav(item.id);
                  if (item.id === "About") {
                    setShowAboutModal(true);
                  } else if (item.id === "Contact") {
                    setShowContact(true);
                  } else if (item.mode) {
                    onExplorePlatform(item.mode);
                  }
                }}
              >
                <span>{item.label}</span>
                {activeNav === item.id && <span className="sat-nav-pill-line" />}
              </button>
            ))}
          </nav>

          <div className="sat-live-header-right">
            {isLoggedIn ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <button
                  type="button"
                  className="sat-live-sys-btn"
                  onClick={() => onExplorePlatform('single')}
                  title="Open SatQuery Systems"
                >
                  <IconSatellite size={16} stroke={2} />
                  <span className="sat-sys-btn-text">SatQuery Systems</span>
                  <IconChevronRight size={14} stroke={2.5} />
                </button>

                {/* ── User Profile Pill & Dropdown ── */}
                <div className="sat-landing-profile-wrapper" ref={profileMenuRef}>
                  <button
                    type="button"
                    className="sat-landing-user-btn"
                    onClick={() => setShowProfileMenu((prev) => !prev)}
                    title={`Account Profile: ${authUser?.name || 'User'}`}
                    aria-label="User Profile and Settings"
                  >
                    <div className="sat-landing-avatar-wrap">
                      {resolvedAvatar ? (
                        <img
                          src={resolvedAvatar}
                          alt={authUser?.name || 'User'}
                          className="sat-landing-avatar-img"
                        />
                      ) : (
                        <div className="sat-landing-avatar-fallback">
                          {(authUser?.name || 'U').charAt(0).toUpperCase()}
                        </div>
                      )}
                      <span className="sat-landing-status-dot" />
                    </div>
                    <span className="sat-landing-user-name">{authUser?.name || 'Account'}</span>
                    <IconChevronDown
                      size={13}
                      stroke={2.5}
                      className={`sat-landing-chevron ${showProfileMenu ? 'sat-chevron-rotated' : ''}`}
                    />
                  </button>

                  {/* Dropdown Menu */}
                  {showProfileMenu && (
                    <div className="sat-landing-profile-menu" role="menu">
                      <div className="sat-landing-pm-header">
                        <div className="sat-landing-avatar-wrap" style={{ width: 40, height: 40, flexShrink: 0 }}>
                          {resolvedAvatar ? (
                            <img
                              src={resolvedAvatar}
                              alt={authUser?.name || 'User'}
                              className="sat-landing-avatar-img"
                              style={{ width: 40, height: 40 }}
                            />
                          ) : (
                            <div className="sat-landing-avatar-fallback" style={{ width: 40, height: 40, fontSize: 16 }}>
                              {(authUser?.name || 'U').charAt(0).toUpperCase()}
                            </div>
                          )}
                        </div>
                        <div className="sat-landing-pm-meta">
                          <div className="sat-landing-pm-name">{authUser?.name || 'SatQuery User'}</div>
                          <div className="sat-landing-pm-email">{authUser?.email || 'Logged in'}</div>
                          <div className="sat-landing-pm-badge">
                            <span className="sat-landing-dot-pulse" />
                            <span>ONLINE</span>
                          </div>
                        </div>
                      </div>

                      <div className="sat-landing-pm-divider" />

                      <button
                        type="button"
                        className="sat-landing-pm-action"
                        onClick={() => {
                          setShowProfileMenu(false);
                          onExplorePlatform('single');
                        }}
                      >
                        <IconSatellite size={16} stroke={2} style={{ color: '#38bdf8' }} />
                        <span>Launch Workspace</span>
                      </button>

                      {onLogout && (
                        <button
                          type="button"
                          className="sat-landing-pm-action sat-landing-pm-logout"
                          onClick={() => {
                            setShowProfileMenu(false);
                            onLogout();
                          }}
                        >
                          <IconLogout size={16} stroke={2} style={{ color: '#f87171' }} />
                          <span>Sign Out</span>
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  type="button"
                  className="sat-nav-btn"
                  onClick={() => onAuthClick ? onAuthClick('signin') : onExplorePlatform('single')}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '20px',
                    color: '#e2e8f0',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: 'transparent',
                    border: 'none',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.color = '#38bdf8'; }}
                  onMouseLeave={e => { e.currentTarget.style.color = '#e2e8f0'; }}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  className="sat-live-sys-btn"
                  onClick={() => onAuthClick ? onAuthClick('signup') : onExplorePlatform('single')}
                  title="Sign Up for SatQuery AI"
                  style={{
                    padding: '7px 16px',
                    borderRadius: '20px',
                    background: 'linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%)',
                    border: '1px solid rgba(56, 189, 248, 0.5)',
                    color: '#ffffff',
                    fontWeight: 700,
                    fontSize: '13px',
                    boxShadow: '0 0 16px rgba(2, 132, 199, 0.4)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <IconUser size={15} />
                  <span>Sign Up</span>
                  <IconChevronRight size={13} stroke={2.5} />
                </button>
              </div>
            )}
          </div>
        </header>

        {/* ── MOBILE NAV BAR (Quick navigation on phones) ── */}
        <nav className="sat-mobile-nav-bar" aria-label="Mobile Quick Navigation">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`sat-mobile-nav-pill ${activeNav === item.id ? "sat-mobile-nav-pill-active" : ""}`}
              onClick={() => {
                setActiveNav(item.id);
                if (item.id === "About") {
                  setShowAboutModal(true);
                } else if (item.id === "Contact") {
                  setShowContact(true);
                } else if (item.mode) {
                  onExplorePlatform(item.mode);
                }
              }}
            >
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* ── 2. HERO CONTENT (LEFT SIDE) ── */}
        <div className="sat-live-hero">
          <div className="sat-hero-eyebrow">
            <span className="sat-eyebrow-rule" />
            <span className="sat-eyebrow-text">INTELLIGENT SATELLITE & EARTH OBSERVATION</span>
            <span className="sat-eyebrow-rule" />
          </div>

          <h1 className="sat-hero-title">SATQUERY</h1>
          <h2 className="sat-hero-subtitle">Smarter Insights from Space</h2>

          <p className="sat-hero-desc">
            AI-powered satellite intelligence platform, turning Earth observation data into actionable insights for a better tomorrow.
          </p>

          <div className="sat-hero-actions">
            <button type="button" className="sat-btn-explore" onClick={() => onExplorePlatform('single')} title="Launch Neural Analysis Platform">
              <IconRocket size={17} stroke={2.2} />
              <span>Explore Platform</span>
              <IconChevronRight size={15} stroke={2.5} />
            </button>

            <Dialog.Root>
              <Dialog.Trigger asChild>
                <button type="button" className="sat-btn-learn" title="Watch the SatQuery AI walkthrough">
                  <IconPlayerPlay size={16} stroke={2} />
                  <span>Learn More</span>
                </button>
              </Dialog.Trigger>
              <Dialog.Portal>
                <Dialog.Overlay className="sat-video-overlay" />
                <Dialog.Content className="sat-video-dialog">
                  <Dialog.Title className="sat-video-title">See SatQuery AI in action</Dialog.Title>
                  <Dialog.Description className="sat-video-description">
                    Watch the platform walkthrough.
                  </Dialog.Description>
                  <video controls playsInline preload="metadata" className="sat-walkthrough-video" aria-label="SatQuery AI platform walkthrough">
                    <source src="/videos/satquery-walkthrough.mp4" type="video/mp4" />
                    Your browser does not support embedded video. <a href="/videos/satquery-walkthrough.mp4">Open the walkthrough</a>.
                  </video>
                  <Dialog.Close asChild>
                    <button type="button" className="sat-video-close" aria-label="Close walkthrough">
                      <IconX size={22} />
                    </button>
                  </Dialog.Close>
                </Dialog.Content>
              </Dialog.Portal>
            </Dialog.Root>
          </div>
        </div>

        <AboutModal
          isOpen={showAboutModal}
          onClose={() => setShowAboutModal(false)}
          onExplore={() => {
            setShowAboutModal(false);
            onExplorePlatform('single');
          }}
        />

        <button
          type="button"
          className="sat-emblem-click-target"
          onClick={() => onExplorePlatform('single')}
          title="Launch SatQuery Platform"
          aria-label="Launch SatQuery Platform"
        />

        {/* ── 3. BOTTOM 4 FEATURE CARDS ── */}
        <div className="sat-live-cards">
          {featureCards.map((card) => {
            const Icon = card.icon;
            return (
              <button
                key={card.id}
                type="button"
                className="sat-live-card"
                onClick={() => onExplorePlatform(card.mode)}
                title={card.title}
              >
                <div className="sat-card-icon-wrap">
                  <Icon size={20} stroke={2} />
                </div>
                <div className="sat-card-text">
                  <span className="sat-card-title">{card.title}</span>
                  <span className="sat-card-desc">{card.desc}</span>
                </div>
              </button>
            );
          })}
        </div>

      </div>

      {/* ── CONTACT MODAL ── */}
      {showContact && (
        <div
          onClick={() => setShowContact(false)}
          style={{
            position: 'fixed', inset: 0, zIndex: 9999,
            background: 'radial-gradient(ellipse at center, rgba(2,132,199,0.12) 0%, rgba(0,0,0,0.85) 70%)',
            backdropFilter: 'blur(12px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '20px',
            animation: 'contactOverlayIn 0.25s ease',
          }}
        >
          <style>{`
            @keyframes contactOverlayIn { from { opacity: 0 } to { opacity: 1 } }
            @keyframes contactModalIn { from { opacity: 0; transform: scale(0.92) translateY(20px) } to { opacity: 1; transform: scale(1) translateY(0) } }
            @keyframes orbitSpin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
            @keyframes orbitSpinReverse { from { transform: rotate(0deg) } to { transform: rotate(-360deg) } }
            @keyframes pulseGlow { 0%,100% { opacity: 0.4; transform: scale(1) } 50% { opacity: 0.8; transform: scale(1.05) } }
            @keyframes floatParticle { 0%,100% { transform: translateY(0px) } 50% { transform: translateY(-8px) } }
            @keyframes scanLine { from { transform: translateY(-100%) } to { transform: translateY(400%) } }
            @keyframes typewriterBlink { 0%,100% { opacity: 1 } 50% { opacity: 0 } }
            @keyframes btnShine { 0% { background-position: -200% center } 100% { background-position: 200% center } }
            .contact-input-wrap { transition: all 0.25s ease; }
            .contact-input-wrap:focus-within {
              border-color: rgba(56,189,248,0.7) !important;
              box-shadow: 0 0 0 3px rgba(56,189,248,0.12), 0 0 20px rgba(56,189,248,0.1) !important;
              background: rgba(56,189,248,0.06) !important;
            }
            .contact-input-wrap:focus-within .contact-icon { color: #38bdf8 !important; }
            .contact-send-btn:not(:disabled):hover {
              transform: translateY(-1px);
              box-shadow: 0 8px 32px rgba(2,132,199,0.5) !important;
              background-size: 200% auto !important;
              animation: btnShine 1.5s linear infinite !important;
            }
            .contact-send-btn:not(:disabled):active { transform: translateY(0); }
            .social-pill:hover { transform: translateY(-2px); filter: brightness(1.2); }
            @media (max-width: 600px) {
              .sat-contact-card {
                padding: 22px 16px 18px !important;
              }
            }
          `}</style>

          <div
            onClick={e => e.stopPropagation()}
            style={{
              position: 'relative',
              width: '100%',
              maxWidth: 'min(460px, calc(100vw - 24px))',
              animation: 'contactModalIn 0.3s cubic-bezier(0.34,1.56,0.64,1)',
            }}
          >
            {/* Orbital decoration rings */}
            <div style={{ position: 'absolute', inset: '-40px', zIndex: 0, pointerEvents: 'none' }}>
              <div style={{
                position: 'absolute', inset: 0,
                border: '1px solid rgba(56,189,248,0.12)',
                borderRadius: '50%',
                animation: 'orbitSpin 12s linear infinite',
              }}>
                <div style={{ position: 'absolute', top: '-4px', left: '50%', width: '8px', height: '8px', background: '#38bdf8', borderRadius: '50%', boxShadow: '0 0 8px #38bdf8', transform: 'translateX(-50%)' }} />
              </div>
              <div style={{
                position: 'absolute', inset: '14px',
                border: '1px solid rgba(139,92,246,0.1)',
                borderRadius: '50%',
                animation: 'orbitSpinReverse 18s linear infinite',
              }}>
                <div style={{ position: 'absolute', bottom: '-4px', left: '30%', width: '6px', height: '6px', background: '#a78bfa', borderRadius: '50%', boxShadow: '0 0 6px #a78bfa' }} />
              </div>
            </div>

            {/* Ambient glow blobs */}
            <div style={{ position: 'absolute', top: '-60px', left: '-40px', width: '200px', height: '200px', background: 'radial-gradient(circle, rgba(2,132,199,0.2) 0%, transparent 70%)', borderRadius: '50%', animation: 'pulseGlow 3s ease-in-out infinite', zIndex: 0, pointerEvents: 'none' }} />
            <div style={{ position: 'absolute', bottom: '-40px', right: '-30px', width: '160px', height: '160px', background: 'radial-gradient(circle, rgba(139,92,246,0.18) 0%, transparent 70%)', borderRadius: '50%', animation: 'pulseGlow 4s ease-in-out infinite 1s', zIndex: 0, pointerEvents: 'none' }} />

            {/* Main card */}
            <div
              className="sat-contact-card"
              style={{
                position: 'relative', zIndex: 1,
                background: 'linear-gradient(145deg, rgba(10,22,40,0.97) 0%, rgba(13,31,60,0.97) 50%, rgba(8,16,32,0.97) 100%)',
                border: '1px solid rgba(56,189,248,0.3)',
                borderRadius: '20px',
                padding: '36px 32px 28px',
                boxShadow: '0 32px 80px rgba(0,0,0,0.8), 0 0 0 1px rgba(56,189,248,0.08), inset 0 1px 0 rgba(255,255,255,0.05)',
                overflow: 'hidden',
              }}
            >
              {/* Top scanline shimmer */}
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
                background: 'linear-gradient(90deg, transparent, #38bdf8, #a78bfa, transparent)',
                opacity: 0.8,
              }} />
              {/* Moving scan line */}
              <div style={{
                position: 'absolute', left: 0, right: 0, height: '1px',
                background: 'linear-gradient(90deg, transparent, rgba(56,189,248,0.4), transparent)',
                animation: 'scanLine 4s linear infinite',
                pointerEvents: 'none',
              }} />

              {/* Corner brackets */}
              {[
                { top: 10, left: 10, borderTop: '2px solid #38bdf8', borderLeft: '2px solid #38bdf8', borderRadius: '4px 0 0 0' },
                { top: 10, right: 10, borderTop: '2px solid #38bdf8', borderRight: '2px solid #38bdf8', borderRadius: '0 4px 0 0' },
                { bottom: 10, left: 10, borderBottom: '2px solid rgba(139,92,246,0.6)', borderLeft: '2px solid rgba(139,92,246,0.6)', borderRadius: '0 0 0 4px' },
                { bottom: 10, right: 10, borderBottom: '2px solid rgba(139,92,246,0.6)', borderRight: '2px solid rgba(139,92,246,0.6)', borderRadius: '0 0 4px 0' },
              ].map((s, i) => (
                <div key={i} style={{ position: 'absolute', width: 16, height: 16, ...s, pointerEvents: 'none' }} />
              ))}

              {/* Close button */}
              <button
                type="button"
                onClick={() => setShowContact(false)}
                style={{
                  position: 'absolute', top: '16px', right: '16px',
                  background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px', color: '#64748b', cursor: 'pointer',
                  padding: '5px 7px', display: 'flex', transition: 'all 0.2s',
                }}
                onMouseEnter={e => { e.currentTarget.style.color = '#f1f5f9'; e.currentTarget.style.background = 'rgba(255,255,255,0.12)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; }}
              >
                <IconX size={15} />
              </button>

              {/* Header */}
              <div style={{ marginBottom: '28px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  {/* Animated icon badge */}
                  <div style={{
                    width: 40, height: 40, borderRadius: '10px',
                    background: 'linear-gradient(135deg, rgba(2,132,199,0.3), rgba(14,165,233,0.15))',
                    border: '1px solid rgba(56,189,248,0.4)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    boxShadow: '0 0 16px rgba(56,189,248,0.2)',
                    animation: 'pulseGlow 3s ease-in-out infinite',
                  }}>
                    <IconMail size={20} stroke={1.8} style={{ color: '#38bdf8' }} />
                  </div>
                  <div>
                    <div style={{ fontSize: '22px', fontWeight: 900, color: '#f1f5f9', letterSpacing: '0.2px', lineHeight: 1 }}>
                      Contact Us
                    </div>
                    <div style={{ fontSize: '10px', fontWeight: 700, color: '#38bdf8', letterSpacing: '2px', textTransform: 'uppercase', marginTop: '3px' }}>
                      🛰️ SATQUERY · DIRECT COMM LINK
                    </div>
                  </div>
                </div>
                <p style={{ fontSize: '12.5px', color: '#64748b', margin: 0, lineHeight: 1.6 }}>
                  Transmit your query — our team will respond within orbital cycle.
                </p>
              </div>

              {/* Name field */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ fontSize: '10px', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '1.2px', display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '7px' }}>
                  <span style={{ width: 4, height: 4, background: '#38bdf8', borderRadius: '50%', display: 'inline-block' }} />
                  Callsign / Name
                </label>
                <div className="contact-input-wrap" style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(56,189,248,0.18)', borderRadius: '10px', padding: '10px 14px', boxShadow: '0 2px 8px rgba(0,0,0,0.2)' }}>
                  <IconUser className="contact-icon" size={15} style={{ color: '#475569', flexShrink: 0, transition: 'color 0.2s' }} />
                  <input
                    type="text"
                    value={contactName}
                    onChange={e => setContactName(e.target.value)}
                    placeholder="Aditya Rajput"
                    style={{ background: 'transparent', border: 'none', outline: 'none', color: '#f1f5f9', fontSize: '13px', width: '100%', fontFamily: 'inherit' }}
                  />
                </div>
              </div>

              {/* Email field */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ fontSize: '10px', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '1.2px', display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '7px' }}>
                  <span style={{ width: 4, height: 4, background: '#38bdf8', borderRadius: '50%', display: 'inline-block' }} />
                  Frequency / Email
                </label>
                <div className="contact-input-wrap" style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(56,189,248,0.18)', borderRadius: '10px', padding: '10px 14px', boxShadow: '0 2px 8px rgba(0,0,0,0.2)' }}>
                  <IconMail className="contact-icon" size={15} style={{ color: '#475569', flexShrink: 0, transition: 'color 0.2s' }} />
                  <input
                    type="email"
                    value={contactEmail}
                    onChange={e => setContactEmail(e.target.value)}
                    placeholder="you@example.com"
                    style={{ background: 'transparent', border: 'none', outline: 'none', color: '#f1f5f9', fontSize: '13px', width: '100%', fontFamily: 'inherit' }}
                  />
                </div>
              </div>

              {/* Message field */}
              <div style={{ marginBottom: '22px' }}>
                <label style={{ fontSize: '10px', fontWeight: 800, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '1.2px', display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '7px' }}>
                  <span style={{ width: 4, height: 4, background: '#38bdf8', borderRadius: '50%', display: 'inline-block' }} />
                  Transmission / Message
                </label>
                <div className="contact-input-wrap" style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(56,189,248,0.18)', borderRadius: '10px', padding: '10px 14px', boxShadow: '0 2px 8px rgba(0,0,0,0.2)' }}>
                  <IconMessageCircle className="contact-icon" size={15} style={{ color: '#475569', flexShrink: 0, marginTop: '2px', transition: 'color 0.2s' }} />
                  <textarea
                    value={contactQuery}
                    onChange={e => setContactQuery(e.target.value)}
                    placeholder="Describe your mission objective..."
                    rows={4}
                    style={{ background: 'transparent', border: 'none', outline: 'none', color: '#f1f5f9', fontSize: '13px', width: '100%', resize: 'none', lineHeight: 1.6, fontFamily: 'inherit' }}
                  />
                </div>
                {/* Character count */}
                <div style={{ textAlign: 'right', fontSize: '10px', color: '#334155', marginTop: '4px' }}>
                  {contactQuery.length} chars
                </div>
              </div>

              {/* Send button */}
              <button
                type="button"
                className="contact-send-btn"
                onClick={handleContactSubmit}
                disabled={!contactName.trim() || !contactEmail.trim() || !contactQuery.trim()}
                style={{
                  width: '100%', padding: '13px', borderRadius: '12px',
                  background: (!contactName.trim() || !contactEmail.trim() || !contactQuery.trim())
                    ? 'rgba(30,41,59,0.8)'
                    : 'linear-gradient(135deg, #0284c7 0%, #0ea5e9 50%, #38bdf8 100%)',
                  backgroundSize: '200% auto',
                  border: (!contactName.trim() || !contactEmail.trim() || !contactQuery.trim())
                    ? '1px solid rgba(56,189,248,0.1)'
                    : '1px solid rgba(56,189,248,0.4)',
                  color: (!contactName.trim() || !contactEmail.trim() || !contactQuery.trim()) ? '#475569' : '#fff',
                  fontWeight: 800, fontSize: '14px', letterSpacing: '0.5px',
                  cursor: (!contactName.trim() || !contactEmail.trim() || !contactQuery.trim()) ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
                  transition: 'all 0.25s ease',
                  boxShadow: (!contactName.trim() || !contactEmail.trim() || !contactQuery.trim()) ? 'none' : '0 4px 24px rgba(2,132,199,0.35)',
                  textTransform: 'uppercase',
                  fontFamily: 'inherit',
                }}
              >
                <IconSend size={16} stroke={2.2} />
                <span>Transmit Message</span>
                {(contactName.trim() && contactEmail.trim() && contactQuery.trim()) && (
                  <span style={{ fontSize: '10px', background: 'rgba(255,255,255,0.2)', padding: '2px 7px', borderRadius: '20px' }}>→</span>
                )}
              </button>

              {/* Divider */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: '20px 0 16px' }}>
                <div style={{ flex: 1, height: '1px', background: 'linear-gradient(to right, transparent, rgba(56,189,248,0.2))' }} />
                <span style={{ fontSize: '10px', color: '#334155', letterSpacing: '1px', textTransform: 'uppercase' }}>Connect</span>
                <div style={{ flex: 1, height: '1px', background: 'linear-gradient(to left, transparent, rgba(56,189,248,0.2))' }} />
              </div>

              {/* Social pills */}
              <div style={{ display: 'flex', gap: '10px' }}>
                <a
                  href="https://www.linkedin.com/in/aditya-rajput-56835027b/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="social-pill"
                  style={{
                    flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '7px',
                    padding: '10px', borderRadius: '10px',
                    background: 'linear-gradient(135deg, rgba(14,118,168,0.25), rgba(2,132,199,0.1))',
                    border: '1px solid rgba(56,189,248,0.25)',
                    color: '#38bdf8', textDecoration: 'none', fontSize: '12px', fontWeight: 700,
                    transition: 'all 0.2s ease', letterSpacing: '0.3px',
                    boxShadow: '0 2px 12px rgba(2,132,199,0.15)',
                  }}
                >
                  <IconBrandLinkedin size={17} stroke={1.8} />
                  <span>LinkedIn</span>
                </a>
                <a
                  href="https://www.instagram.com/aditya_rajput_1122/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="social-pill"
                  style={{
                    flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '7px',
                    padding: '10px', borderRadius: '10px',
                    background: 'linear-gradient(135deg, rgba(168,85,247,0.2), rgba(236,72,153,0.1))',
                    border: '1px solid rgba(168,85,247,0.3)',
                    color: '#e879f9', textDecoration: 'none', fontSize: '12px', fontWeight: 700,
                    transition: 'all 0.2s ease', letterSpacing: '0.3px',
                    boxShadow: '0 2px 12px rgba(168,85,247,0.15)',
                  }}
                >
                  <IconBrandInstagram size={17} stroke={1.8} />
                  <span>Instagram</span>
                </a>
              </div>

              {/* Bottom status bar */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '16px', justifyContent: 'center' }}>
                <div style={{ width: 6, height: 6, background: '#22c55e', borderRadius: '50%', boxShadow: '0 0 6px #22c55e', animation: 'pulseGlow 2s ease-in-out infinite' }} />
                <span style={{ fontSize: '10px', color: '#334155', letterSpacing: '0.8px', textTransform: 'uppercase' }}>Secure Channel · AES-256 Encrypted</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SatQueryLanding;
