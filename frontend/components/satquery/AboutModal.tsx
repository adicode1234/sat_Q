import { useState } from "react";
import {
  IconX,
  IconBrain,
  IconSatellite,
  IconLayersIntersect,
  IconShieldCheck,
  IconSparkles,
  IconTargetArrow,
  IconSearch,
  IconRocket,
  IconEye,
  IconDatabase,
  IconChartDots,
  IconArrowsDiff,
  IconQuote,
} from "@tabler/icons-react";

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExplore: () => void;
}

export function AboutModal({ isOpen, onClose, onExplore }: AboutModalProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "capabilities" | "architecture" | "pipeline" | "vision">("overview");

  if (!isOpen) return null;

  return (
    <div className="sat-about-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="sat-about-modal" onClick={(e) => e.stopPropagation()}>
        {/* Glow Header Accent */}
        <div className="sat-about-glow-top" />

        {/* Modal Header */}
        <header className="sat-about-header">
          <div className="sat-about-title-group">
            <div className="sat-about-icon-badge">
              <IconSatellite size={26} stroke={1.8} />
            </div>
            <div>
              <div className="sat-about-tagline">AGENTIC VISION-LANGUAGE SATELLITE PLATFORM</div>
              <h2 className="sat-about-main-heading">About SatQuery AI</h2>
              <p className="sat-about-sub-heading">Intelligence for the Earth, Powered by AI</p>
            </div>
          </div>
          <button
            type="button"
            className="sat-about-close-btn"
            onClick={onClose}
            title="Close About Modal"
            aria-label="Close"
          >
            <IconX size={20} />
          </button>
        </header>

        {/* Navigation Tabs */}
        <div className="sat-about-nav-tabs">
          <button
            type="button"
            className={`sat-atab ${activeTab === "overview" ? "sat-atab-active" : ""}`}
            onClick={() => setActiveTab("overview")}
          >
            <IconTargetArrow size={15} />
            <span>Overview</span>
          </button>
          <button
            type="button"
            className={`sat-atab ${activeTab === "capabilities" ? "sat-atab-active" : ""}`}
            onClick={() => setActiveTab("capabilities")}
          >
            <IconBrain size={15} />
            <span>Capabilities</span>
          </button>
          <button
            type="button"
            className={`sat-atab ${activeTab === "architecture" ? "sat-atab-active" : ""}`}
            onClick={() => setActiveTab("architecture")}
          >
            <IconLayersIntersect size={15} />
            <span>Agentic Specialists</span>
          </button>
          <button
            type="button"
            className={`sat-atab ${activeTab === "pipeline" ? "sat-atab-active" : ""}`}
            onClick={() => setActiveTab("pipeline")}
          >
            <IconChartDots size={15} />
            <span>6-Stage Pipeline</span>
          </button>
          <button
            type="button"
            className={`sat-atab ${activeTab === "vision" ? "sat-atab-active" : ""}`}
            onClick={() => setActiveTab("vision")}
          >
            <IconSparkles size={15} />
            <span>Our Vision</span>
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="sat-about-body">
          {/* TAB 1: OVERVIEW */}
          {activeTab === "overview" && (
            <div className="sat-about-section">
              <div className="sat-about-lead-card">
                <p className="sat-about-lead-text">
                  <strong>SatQuery AI</strong> is an agentic Vision-Language Assistant designed to make remote-sensing
                  image analysis simpler, faster, and universally accessible.
                </p>
                <p className="sat-about-text">
                  Satellite imagery contains valuable information about our planet — from water bodies, vegetation,
                  and urban development to critical infrastructure and environmental shifts. However, extracting meaningful
                  insights traditionally requires specialised knowledge of satellite data, complex GIS workflows,
                  multi-spectral radiometry, and dozens of disparate deep-learning models.
                </p>
                <div className="sat-about-highlight-box">
                  <IconShieldCheck size={22} className="text-cyan-400 flex-shrink-0" />
                  <span>
                    <strong>SatQuery AI brings these capabilities together</strong> through a single intelligent,
                    query-driven remote sensing workspace.
                  </span>
                </div>
              </div>

              {/* 3 Core Pillars */}
              <div className="sat-about-pillars-grid">
                <div className="sat-pillar-card">
                  <div className="sat-pillar-icon" style={{ background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8" }}>
                    <IconSearch size={22} />
                  </div>
                  <h3>Natural Language Query</h3>
                  <p>
                    Simply ask questions in plain English. The platform interprets user intent without manual model tuning.
                  </p>
                </div>
                <div className="sat-pillar-card">
                  <div className="sat-pillar-icon" style={{ background: "rgba(34, 197, 94, 0.15)", color: "#4ade80" }}>
                    <IconBrain size={22} />
                  </div>
                  <h3>Autonomous Specialists</h3>
                  <p>
                    Routes tasks dynamically to specialised remote-sensing models (VQA, Siamese Change, SAR Fusion).
                  </p>
                </div>
                <div className="sat-pillar-card">
                  <div className="sat-pillar-icon" style={{ background: "rgba(168, 85, 247, 0.15)", color: "#c084fc" }}>
                    <IconShieldCheck size={22} />
                  </div>
                  <h3>Evidence-Grounded</h3>
                  <p>
                    Every finding is backed with bounding boxes, change masks, physical index deltas, and full audit logs.
                  </p>
                </div>
              </div>

              {/* Supported Modalities Banner */}
              <div className="sat-modalities-card">
                <div className="sat-mc-title">
                  <IconDatabase size={17} className="text-cyan-400" />
                  <span>Built for Multimodal Earth Observation</span>
                </div>
                <div className="sat-mc-grid">
                  <div className="sat-mc-item">
                    <span className="sat-mc-badge">SINGLE IMAGE</span>
                    <strong>Optical / Multispectral / SAR</strong>
                    <p>Image understanding, land cover mapping & visual question answering.</p>
                  </div>
                  <div className="sat-mc-item">
                    <span className="sat-mc-badge">CROSS-MODAL PAIR</span>
                    <strong>Optical + SAR Radar Fusion</strong>
                    <p>Co-registered complementary penetration through cloud cover and foliage.</p>
                  </div>
                  <div className="sat-mc-item">
                    <span className="sat-mc-badge">BI-TEMPORAL PAIR</span>
                    <strong>Before & After Dual-Acquisition</strong>
                    <p>Sub-pixel coregistered temporal change detection, expansion & damage analysis.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: CAPABILITIES */}
          {activeTab === "capabilities" && (
            <div className="sat-about-section">
              <div className="sat-capabilities-grid">
                <div className="sat-cap-card">
                  <div className="sat-cap-icon-wrap">
                    <IconEye size={20} stroke={2} className="text-cyan-400" />
                  </div>
                  <div className="sat-cap-content">
                    <h4>Single-Image Understanding</h4>
                    <p>
                      Analyse individual optical, multispectral, or SAR images through visual question answering, scene
                      description, and text-guided region understanding with high precision.
                    </p>
                  </div>
                </div>

                <div className="sat-cap-card">
                  <div className="sat-cap-icon-wrap">
                    <IconArrowsDiff size={20} stroke={2} className="text-emerald-400" />
                  </div>
                  <div className="sat-cap-content">
                    <h4>Change Detection & Analysis</h4>
                    <p>
                      Compare acquisitions captured at different times to quantify what has shifted, where the anomaly
                      occurred, and how the observed region has evolved physically.
                    </p>
                  </div>
                </div>

                <div className="sat-cap-card">
                  <div className="sat-cap-icon-wrap">
                    <IconSatellite size={20} stroke={2} className="text-purple-400" />
                  </div>
                  <div className="sat-cap-content">
                    <h4>Optical + SAR Intelligence</h4>
                    <p>
                      Combine optical reflectance with all-weather synthetic aperture radar backscatter, illuminating
                      submerged features, night operations, and dense structural settlements.
                    </p>
                  </div>
                </div>

                <div className="sat-cap-card">
                  <div className="sat-cap-icon-wrap">
                    <IconBrain size={20} stroke={2} className="text-amber-400" />
                  </div>
                  <div className="sat-cap-content">
                    <h4>AI-Powered Query Understanding</h4>
                    <p>
                      Instead of manual parameter configuration, natural-language queries are parsed through an NLP intent
                      classifier that extracts spatial context, targets, and analysis directives.
                    </p>
                  </div>
                </div>

                <div className="sat-cap-card">
                  <div className="sat-cap-icon-wrap">
                    <IconShieldCheck size={20} stroke={2} className="text-teal-400" />
                  </div>
                  <div className="sat-cap-content">
                    <h4>Evidence-Grounded Results</h4>
                    <p>
                      Combines concise natural language findings with spatial bounding boxes, segmented masks, and
                      radiometric confidence scores so analysts can verify conclusions.
                    </p>
                  </div>
                </div>

                <div className="sat-cap-card">
                  <div className="sat-cap-icon-wrap">
                    <IconChartDots size={20} stroke={2} className="text-blue-400" />
                  </div>
                  <div className="sat-cap-content">
                    <h4>Auditable AI Workflow</h4>
                    <p>
                      Live execution tracing provides transparent, real-time feedback detailing specialist invocation,
                      feature vectors, physical agreement, and full JSON/HTML exportable audit reports.
                    </p>
                  </div>
                </div>
              </div>

              {/* Real World Applications Bar */}
              <div className="sat-apps-box">
                <h4>Designed for Real-World Earth Observation:</h4>
                <div className="sat-apps-chips">
                  <span>🌊 Water Resource Assessment</span>
                  <span>🏠 Urban Footprint Monitoring</span>
                  <span>🌲 Forest Canopy Protection</span>
                  <span>🌾 Agricultural Vitality</span>
                  <span>🚨 Disaster & Damage Assessment</span>
                  <span>🛣️ Transport & Corridor Mapping</span>
                  <span>⏱️ Multitemporal Change Tracking</span>
                  <span>📡 SAR Cross-Validation</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: ARCHITECTURE */}
          {activeTab === "architecture" && (
            <div className="sat-about-section">
              <div className="sat-arch-banner">
                <h3>One Interface. Multiple Remote-Sensing Specialists.</h3>
                <p>
                  SatQuery AI follows an <strong>agentic orchestration architecture</strong> rather than relying on a
                  single generic AI model. A central router delegates observation tasks to modular specialist models.
                </p>
              </div>

              <div className="sat-specialist-cards-grid">
                <div className="sat-spec-card">
                  <div className="sat-spec-badge">SPECIALIST 01</div>
                  <h4>Remote-Sensing VQA</h4>
                  <p>Fine-tuned transformer addressing open-ended questions against geospatial terrain.</p>
                  <span className="sat-spec-model">ViLT-B / RSVQA</span>
                </div>

                <div className="sat-spec-card">
                  <div className="sat-spec-badge">SPECIALIST 02</div>
                  <h4>Image Captioning & Scene Context</h4>
                  <p>Synthesizes comprehensive geographic summaries across multi-spectral bands.</p>
                  <span className="sat-spec-model">VRSBench Vision</span>
                </div>

                <div className="sat-spec-card">
                  <div className="sat-spec-badge">SPECIALIST 03</div>
                  <h4>Text-Guided Region Grounding</h4>
                  <p>Localizes exact coordinates, bridges, rivers, and facilities using zero-shot spatial bounding.</p>
                  <span className="sat-spec-model">Grounding DINO-RS</span>
                </div>

                <div className="sat-spec-card">
                  <div className="sat-spec-badge">SPECIALIST 04</div>
                  <h4>Multitemporal Siamese Change</h4>
                  <p>Calculates pixel-level difference vectors and isolates seasonal vs anthropogenic shifts.</p>
                  <span className="sat-spec-model">Bi-Temporal SiamNet</span>
                </div>

                <div className="sat-spec-card">
                  <div className="sat-spec-badge">SPECIALIST 05</div>
                  <h4>Optical–SAR Information Fusion</h4>
                  <p>Co-registers optical reflectance and SAR backscatter for penetrative water and urban classification.</p>
                  <span className="sat-spec-model">Cross-Modal Fuser</span>
                </div>

                <div className="sat-spec-card">
                  <div className="sat-spec-badge">SPECIALIST 06</div>
                  <h4>Physical Agreement Engine</h4>
                  <p>Calculates NDWI, NDVI, and polarimetric radar variance to mathematically cross-verify neural answers.</p>
                  <span className="sat-spec-model">Symbolic Engine</span>
                </div>
              </div>

              {/* Benchmarks & Datasets */}
              <div className="sat-benchmark-callout">
                <IconDatabase size={20} className="text-cyan-400 flex-shrink-0" />
                <div>
                  <strong>Domain-Adapted Intelligence on Project Benchmarks:</strong>
                  <p>
                    Specialised using global Earth-observation datasets including <strong>BigEarthNet</strong>,{" "}
                    <strong>VRSBench</strong>, <strong>RSVQA</strong>, and <strong>CDVQA</strong>.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: PIPELINE */}
          {activeTab === "pipeline" && (
            <div className="sat-about-section">
              <div className="sat-pipeline-intro">
                <h3>From Question to Evidence</h3>
                <p>How SatQuery AI processes your natural language observation in 6 autonomous stages:</p>
              </div>

              <div className="sat-stages-list">
                <div className="sat-stage-row">
                  <div className="sat-stage-num">01</div>
                  <div className="sat-stage-content">
                    <strong>Understand</strong>
                    <p>The system interprets the user's natural-language query and extracts spatial & thematic targets.</p>
                  </div>
                </div>

                <div className="sat-stage-row">
                  <div className="sat-stage-num">02</div>
                  <div className="sat-stage-content">
                    <strong>Validate</strong>
                    <p>Uploaded images are checked for sensor modality, GeoTIFF projection, band order, and co-registration.</p>
                  </div>
                </div>

                <div className="sat-stage-row">
                  <div className="sat-stage-num">03</div>
                  <div className="sat-stage-content">
                    <strong>Route</strong>
                    <p>The agentic controller selects the optimal combination of remote sensing models and specialized tools.</p>
                  </div>
                </div>

                <div className="sat-stage-row">
                  <div className="sat-stage-num">04</div>
                  <div className="sat-stage-content">
                    <strong>Analyse</strong>
                    <p>The neural specialists process the imagery to detect features, segment areas, and identify temporal variance.</p>
                  </div>
                </div>

                <div className="sat-stage-row">
                  <div className="sat-stage-num">05</div>
                  <div className="sat-stage-content">
                    <strong>Validate & Integrate</strong>
                    <p>Outputs are cross-checked against symbolic physical indicators (NDWI, radar sigma) to generate trust scores.</p>
                  </div>
                </div>

                <div className="sat-stage-row">
                  <div className="sat-stage-num">06</div>
                  <div className="sat-stage-content">
                    <strong>Explain</strong>
                    <p>The executive answer is generated alongside interactive visual overlays, metrics, and auditable event trace.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: VISION */}
          {activeTab === "vision" && (
            <div className="sat-about-section">
              <div className="sat-vision-hero-card">
                <div className="sat-vision-badge">
                  <IconSparkles size={14} />
                  <span>OUR VISION</span>
                </div>
                <h3>Making Satellite Intelligence Conversational</h3>
                <p>
                  Our mission is to make advanced Earth-observation analysis accessible to every researcher, planner,
                  and organisation through a clean, conversational interface.
                </p>

                <div className="sat-quote-block">
                  <IconQuote size={24} className="sat-quote-icon" />
                  <p className="sat-quote-sub">
                    Instead of asking: <em>"Which model should I run? Which band parameters do I configure?"</em>
                  </p>
                  <p className="sat-quote-main">
                    Users can simply ask:
                  </p>
                  <ul className="sat-sample-questions">
                    <li>“What changed between these two satellite acquisitions?”</li>
                    <li>“Where did the built-up urban footprint expand?”</li>
                    <li>“Use optical and SAR together to identify water-covered regions.”</li>
                    <li>“Describe the major land-cover types and vegetation health.”</li>
                  </ul>
                </div>

                <div className="sat-vision-closing">
                  <strong>Ask. Analyse. Understand.</strong>
                  <p>
                    SatQuery AI brings together <strong>Satellite Imagery + Vision-Language AI + Agentic Orchestration + Multimodal Analysis</strong>.
                  </p>
                  <div className="sat-vision-motto">
                    From pixels to insights — through natural language.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <footer className="sat-about-footer">
          <div className="sat-about-foot-meta">
            <span className="sat-foot-dot" />
            <span>SatQuery Systems v2.4 · Earth Observation Intelligence</span>
          </div>
          <div className="sat-about-foot-actions">
            <button type="button" className="sat-about-btn-sec" onClick={onClose}>
              Close
            </button>
            <button
              type="button"
              className="sat-about-btn-prim"
              onClick={() => {
                onClose();
                onExplore();
              }}
            >
              <IconRocket size={16} stroke={2} />
              <span>Launch Platform</span>
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
export default AboutModal;
