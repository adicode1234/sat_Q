import type { ReactNode } from "react";
import BackgroundVideo from "./BackgroundVideo";
import SatQueryBrand from "./SatQueryBrand";
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="auth-shell">
      <BackgroundVideo />
      <header>
        <SatQueryBrand />
        <span className="header-note">EARTH OBSERVATION / INTELLIGENCE</span>
      </header>
      <div className="auth-content">
        <section className="mission" aria-label="Earth intelligence">
          <p className="eyebrow">
            <span /> INTELLIGENT SATELLITE & EARTH OBSERVATION
          </p>
          <h1>
            Smarter insights.
            <br />
            <span>From space.</span>
          </h1>
          <p className="mission-copy">
            Turn satellite imagery into real-world insights.
            <br />
            Explore our changing planet with the power of AI.
          </p>
          <div className="mission-rule" />
          <p className="mission-caption">OBSERVE. UNDERSTAND. DISCOVER.</p>
        </section>
        {children}
      </div>
      <footer>
        <span>
          SATQUERY.AI <span className="footer-divider">/</span> Multimodal Earth
          Intelligence
        </span>
        <span>SECURE WORKSPACE ACCESS</span>
      </footer>
    </main>
  );
}
