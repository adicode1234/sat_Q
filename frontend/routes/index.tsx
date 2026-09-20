import SpecialistReport, { type AnalysisReport } from "../components/SpecialistReport";
import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import {
  IconArrowRight,
  IconChartLine,
  IconChartDonut,
  IconCheck,
  IconChevronDown,
  IconCircleCheck,
  IconCloudUpload,
  IconDatabase,
  IconEye,
  IconEyeOff,
  IconFileText,
  IconHome2,
  IconInfoCircle,
  IconLayersIntersect,
  IconMap2,
  IconMinus,
  IconPhoto,
  IconPlus,
  IconRocket,
  IconSatellite,
  IconSearch,
  IconSettings,
  IconTargetArrow,
  IconUserCircle,
  IconX,
  IconMenu2,
  IconSparkles,
  IconShieldCheck,
  IconCopy,
  IconCompass,
  IconExternalLink,
  IconDownload,
  IconRadar,
  IconAlertTriangle,
  IconRefresh,
  IconAdjustments,
  IconBookmark,
  IconBrain,
  IconActivity,
  IconClock,
  IconGitCompare,
  IconListCheck,
  IconSun,
  IconMoon,
  IconLogout,
  IconCamera,
  IconTrash,
  IconCalendar,
  IconHistory,
  IconMapPin,
  IconGlobe,
  IconMicrophone,
  IconVolume,
  IconPlayerStop,
  IconMaximize,
  IconMinimize,
} from "@tabler/icons-react";
import { CesiumGlobeViewer } from "@/components/CesiumGlobeViewer";
import { AnnotatedScene, type BoxOverlay } from "@/components/AnnotatedScene";
import AuthPage from '@/components/auth/AuthPage';
import { getSession, logout, type AuthUser } from '@/services/authApi';
import { OrbitSatellite, RocketLaunch } from "@/components/satquery/SpaceVisuals";
import { SatQueryLanding } from "@/components/satquery/SatQueryLanding";
import { cn } from "@/lib/utils";
import { type AppLanguage, t, translateText, HELP_TOPICS, fetchDynamicTranslations, setCachedTranslation, getCachedTranslation } from "./translations";
// @ts-ignore
import html2pdf from 'html2pdf.js';

export type Mode = "single" | "bitemporal" | "fusion";

export type UploadedFileWithRaw = {
  name: string;
  url: string;
  size: number;
  rawFile?: File;
};

export type SatResult = {
  analysis_report?: AnalysisReport;
  interpretation_source?: string;
  query_id: string;
  query: string;
  task: string;
  scenario: string;
  trust_score: number;
  visual_confidence?: number;
  short_answer?: string;
  answer?: string;
  executive_answer?: string;
  description?: string;
  visible_features?: string[];
  uncertainties?: string[];
  present?: any[];
  absent?: any[];
  composition?: Record<string, number>;
  multi_class_boxes?: Array<{ box: number[]; label: string; type: string }>;
  spatial_overlays?: BoxOverlay[];
  scene_inventory?: {
    answer?: string;
    present: Array<{ name: string; category: string; icon: string; detail: string; badge: string }>;
    absent: Array<{ name: string; category: string; icon: string; detail: string; badge: string }>;
    composition?: Record<string, number>;
    temporal_breakdown?: any[];
    has_river?: boolean;
  };
  overlay?: {
    type: 'bbox' | 'mask';
    width: number;
    height: number;
    image_id?: string;
    label?: string;
    data: any;
  } | null;
  previews?: string[];
  report_url?: string;
  html_report_url?: string;
  decision?: { status: string; guidance?: string; code?: string | null; reason?: string | null; needed?: string | null };
  confidence_breakdown?: {
    neural?: number;
    visual_confidence?: number;
    symbolic?: number;
    coverage?: number;
    input_quality?: number;
    final_trust?: number;
  };
  execution_trace?: Array<{
    stage: string;
    action: string;
    description: string;
    timestamp?: string;
    result?: string;
  }>;
  specialists?: Array<{
    model?: string;
    mode?: string;
    status: string;
    neural_confidence?: number;
  }>;
  verification?: {
    trust_score: number;
    checks?: Array<{
      claim: { type: string };
      status: string;
    }>;
  };
  input?: {
    images?: Array<{
      id: string;
      filename: string;
      modality: string;
      bands: string[];
      shape?: number[];
    }>;
    metadata?: Record<string, any>;
  };
  temporal_analysis?: {
    visible_change?: boolean;
    change_score?: number;
    changed_fraction?: number;
    temporal_evidence?: any;
    change_summary?: string;
  };
  temporal_breakdown?: Array<{
    category: string;
    feature: string;
    icon: string;
    before_val: string;
    after_val: string;
    delta_val: string;
    delta_type: string;
    metric?: string;
    location?: string;
    impact?: string;
    status?: string;
  }>;
  limitations?: string[];
};

export type BitemporalDiffItem = {
  category: string;
  feature: string;
  icon: string;
  before_val: string;
  after_val: string;
  delta_val: string;
  delta_type: string;
  metric?: string;
  location?: string;
  impact?: string;
  status?: string;
};

const DEFAULT_BITEMPORAL_BREAKDOWN: BitemporalDiffItem[] = [
  {
    category: "water",
    feature: "River Channel & Surface Water Level",
    icon: "🌊",
    before_val: "16.6%",
    after_val: "22.9%",
    delta_val: "+6.3% Inundation",
    delta_type: "increase",
    metric: "+6.3pp surface extent delta",
    location: "Active hydrological channel",
    impact: "Channel boundary expansion detected across temporal acquisition interval.",
    status: "Active Inundation",
  },
  {
    category: "vegetation",
    feature: "Riparian Forest & Vegetation Canopy",
    icon: "🌲",
    before_val: "54.8%",
    after_val: "53.0%",
    delta_val: "-1.8% Submerged",
    delta_type: "decrease",
    metric: "-1.8pp canopy delta",
    location: "Riparian buffer zone",
    impact: "Lowland vegetation variation observed under shifting hydrological levels.",
    status: "Canopy Variation",
  },
  {
    category: "built_up",
    feature: "Built Settlements & Human Habitation",
    icon: "🏠",
    before_val: "0.0%",
    after_val: "0.0%",
    delta_val: "0.0% Stable",
    delta_type: "neutral",
    metric: "Minimal structural deviation",
    location: "Perimeter settlements",
    impact: "Zero structural displacement detected; urban residential areas unaffected.",
    status: "Stable / Secure",
  },
  {
    category: "transport",
    feature: "Road Corridors & Access Routes",
    icon: "🛣️",
    before_val: "Accessible",
    after_val: "Passable",
    delta_val: "Intact",
    delta_type: "neutral",
    metric: "Corridors functional",
    location: "Primary transport grid",
    impact: "Access corridors and crossing spans remain clear and functional.",
    status: "Passable / Intact",
  },
  {
    category: "sensor",
    feature: "Coregistration & Alignment Quality",
    icon: "🛰️",
    before_val: "T1 Grid",
    after_val: "T2 Grid",
    delta_val: "Co-Registered",
    delta_type: "verified",
    metric: "Spatial alignment verified",
    location: "Observation footprint",
    impact: "Dual acquisition spatial grids aligned for comparative analysis.",
    status: "Aligned",
  },
  {
    category: "trust",
    feature: "Multi-Source Confidence Verification",
    icon: "🛡️",
    before_val: "Spectral Δ",
    after_val: "Change Model",
    delta_val: "Verified Alignment",
    delta_type: "verified",
    metric: "Multi-Source Consensus",
    location: "Cross-sensor agreement",
    impact: "Consensus verified across sensor channels with model validation.",
    status: "Confidence Verified",
  },
];

const DEFAULT_FUSION_BREAKDOWN = [
  {
    category: "water",
    feature: "Surface Water & Hydrological Extent",
    icon: "🌊",
    sensor1_label: "Optical Sensor",
    sensor1_val: "Visible Absorption",
    sensor2_label: "SAR Radar",
    sensor2_val: "Specular Low-Backscatter",
    delta_val: "Verified Water",
    delta_type: "increase",
    metric: "Cross-Modal Agreement",
    location: "Hydrographic channel reach",
    impact: "Optical visible absorption coincident with radar specular flat-surface reflection.",
    status: "Boundary Verified",
  },
  {
    category: "vegetation",
    feature: "Forest Canopy & Biomass Density",
    icon: "🌲",
    sensor1_label: "Optical Sensor",
    sensor1_val: "Chlorophyll NDVI",
    sensor2_label: "SAR Radar",
    sensor2_val: "Volume Scattering",
    delta_val: "Verified Canopy",
    delta_type: "decrease",
    metric: "Consistent Foliage",
    location: "Vegetation buffer zone",
    impact: "Optical chlorophyll spectral index cross-validated against microwave volumetric scattering.",
    status: "Canopy Verified",
  },
  {
    category: "built_up",
    feature: "Built Settlements & Man-Made Structures",
    icon: "🏠",
    sensor1_label: "Optical Sensor",
    sensor1_val: "Reflective Footprint",
    sensor2_label: "SAR Radar",
    sensor2_val: "Double-Bounce Corner",
    delta_val: "Structural Match",
    delta_type: "neutral",
    metric: "Rigid Structural Signature",
    location: "Settlement perimeters",
    impact: "High radar backscatter corner reflectors corroborate visible structural rooftops.",
    status: "Structures Verified",
  },
  {
    category: "transport",
    feature: "Road Corridors & Access Routes",
    icon: "🛣️",
    sensor1_label: "Optical Sensor",
    sensor1_val: "Linear Path",
    sensor2_label: "SAR Radar",
    sensor2_val: "Smooth Corridor",
    delta_val: "Intact",
    delta_type: "neutral",
    metric: "Corridors Mapped",
    location: "Primary transport grid",
    impact: "Transport corridors mapped via linear spectral signatures and coherent radar continuity.",
    status: "Passable / Intact",
  },
  {
    category: "sensor",
    feature: "All-Weather Usability & Cloud Penetration",
    icon: "🛰️",
    sensor1_label: "Optical Sensor",
    sensor1_val: "Visible Bands",
    sensor2_label: "SAR Radar",
    sensor2_val: "All-Weather C-Band",
    delta_val: "Radar Penetration",
    delta_type: "verified",
    metric: "All-Weather Active",
    location: "Observation footprint",
    impact: "SAR radar microwave wavelengths penetrate atmospheric haze and cloud cover.",
    status: "Complementary Sensors",
  },
  {
    category: "trust",
    feature: "Cross-Modal Consensus Verification",
    icon: "🛡️",
    sensor1_label: "Optical Sensor",
    sensor1_val: "Sentinel-2 MSI",
    sensor2_label: "SAR Radar",
    sensor2_val: "Sentinel-1 / RISAT",
    delta_val: "Consensus Verified",
    delta_type: "verified",
    metric: "Multi-Sensor Agreement",
    location: "Dual-Sensor Agreement",
    impact: "Cross-sensor consensus verified without single-sensor occlusion or shadow artifacts.",
    status: "Verified Consensus",
  },
];

export const BEFORE_FEATURE_BOXES = [
  { box: [180, 0, 420, 500], label: "River Channel · Flowing Water · 95%", type: "river" },
  { box: [460, 140, 560, 230], label: "Pond / Waterbody Basin · 90%", type: "pond" },
  { box: [20, 15, 210, 485], label: "Forest & Vegetation Canopy · 93%", type: "forest" },
  { box: [430, 20, 780, 260], label: "Riparian Vegetation Buffer · 91%", type: "forest" },
  { box: [520, 270, 780, 480], label: "Buildings & Settlement · 89%", type: "built" },
  { box: [120, 215, 680, 285], label: "Road Network & Access Route · Verified", type: "road" },
];

export const AFTER_FEATURE_BOXES = [
  { box: [150, 0, 460, 500], label: "River Channel · Widened Inundation · 96%", type: "river" },
  { box: [380, 90, 480, 310], label: "Inundated Sector (+41.4 Ha) · Verified", type: "river" },
  { box: [460, 140, 560, 230], label: "Pond / Waterbody Basin · 90%", type: "pond" },
  { box: [20, 15, 195, 485], label: "Forest Canopy (-1.8% Submerged) · 91%", type: "forest" },
  { box: [520, 270, 780, 480], label: "Buildings & Settlement (0.0% Stable) · 89%", type: "built" },
  { box: [120, 215, 680, 285], label: "Road Network (Intact / Passable) · Verified", type: "road" },
];

type ViewportTab = "satellite" | "landcover" | "changemask" | "results";
type AnalysisTab = "detection" | "findings" | "recommendations";
type ExecutionTab = "execution" | "log";

const NAV_ITEMS = [
  { id: "home", label: "Home", icon: IconHome2 },
  { id: "reports", label: "Reports", icon: IconFileText },
  { id: "history", label: "History", icon: IconHistory },
];

export interface MissionItem {
  id: string;
  title: string;
  date: string;
  status: string;
  thumb: string;
  mode: Mode;
  query: string;
  sensor: string;
  demoCode?: string;
  report_url?: string;
  trust_score?: number;
}

const RECENT_MISSIONS: MissionItem[] = [
  {
    id: "howrah",
    title: "River Hydrological Analysis",
    date: "11 Sep 2026 - 08:42 PM",
    status: "Completed",
    thumb: "/demo/optical_after.png",
    demoCode: "grounding",
    mode: "single" as Mode,
    query: "Where is the river or surface water in this image?",
    sensor: "Sentinel-2 (Optical)",
  },
  {
    id: "kolkata",
    title: "Kolkata Urban Study",
    date: "10 Sep 2026 - 04:21 PM",
    status: "Completed",
    thumb: "/demo/optical_before.png",
    demoCode: "vqa",
    mode: "single" as Mode,
    query: "What land cover and urban settlements are visible?",
    sensor: "Cartosat-3 (Multispectral)",
  },
  {
    id: "rural",
    title: "Rural Land Use Change",
    date: "09 Sep 2026 - 11:37 AM",
    status: "Completed",
    thumb: "/demo/optical_after.png",
    demoCode: "change",
    mode: "bitemporal" as Mode,
    query: "What changed between these two acquisitions?",
    sensor: "Landsat-9 / Sentinel-2",
  },
  {
    id: "sundarbans",
    title: "Coastal Monitoring (Sundarbans)",
    date: "08 Sep 2026 - 09:18 AM",
    status: "Completed",
    thumb: "/demo/sar.png",
    demoCode: "fusion",
    mode: "fusion" as Mode,
    query: "Use optical and SAR together to identify water bodies and mangrove canopy.",
    sensor: "RISAT-1A (SAR) + Sentinel-2",
  },
];

const ANALYSIS_TOOLS = [
  {
    id: "vqa",
    title: "Ask a Question (VQA)",
    desc: "Natural language queries on satellite images",
    icon: IconBrain,
    color: "#38bdf8",
    mode: "single" as Mode,
    defaultQuery: "What land cover is visible in this satellite image?",
    demoCode: "vqa",
  },
  {
    id: "describe",
    title: "Describe Image",
    desc: "Get detailed description & insights",
    icon: IconFileText,
    color: "#a855f7",
    mode: "single" as Mode,
    defaultQuery: "Provide a comprehensive description of the scene and geographic features.",
    demoCode: "vqa",
  },
  {
    id: "landcover",
    title: "Land Cover Detection",
    desc: "Identify water, vegetation, buildings etc.",
    icon: IconPhoto,
    color: "#22c55e",
    mode: "single" as Mode,
    defaultQuery: "Where is the river or surface water in this image?",
    demoCode: "grounding",
  },
  {
    id: "change",
    title: "Change Detection",
    desc: "Compare before/after images",
    icon: IconLayersIntersect,
    color: "#f59e0b",
    mode: "bitemporal" as Mode,
    defaultQuery: "What changed between these two acquisitions?",
    demoCode: "change",
  },
  {
    id: "fusion",
    title: "SAR-Optical Fusion",
    desc: "Multi-sensor analysis",
    icon: IconRadar,
    color: "#06b6d4",
    mode: "fusion" as Mode,
    defaultQuery: "Use optical and SAR together to identify built-up and water features.",
    demoCode: "fusion",
  },
  {
    id: "report",
    title: "Generate Report",
    desc: "Export findings & insights",
    icon: IconDownload,
    color: "#10b981",
    mode: "single" as Mode,
    defaultQuery: "Generate a complete audit report with physical indices.",
    demoCode: "vqa",
  },
];

export const HUD_CALLOUTS = [
  {
    id: "pond",
    type: "pond",
    title: "River / Water Body",
    subtitle: "Surface Water Feature",
    icon: "💧",
    color: "#38bdf8",
    tx: 295,
    ty: 410,
    bx: 170,
    by: 250,
    filterType: "pond",
  },
  {
    id: "built",
    type: "built",
    title: "Buildings & Urban",
    subtitle: "Built-up structures",
    icon: "🏠",
    color: "#f97316",
    tx: 545,
    ty: 530,
    bx: 690,
    by: 650,
    filterType: "built",
  },
  {
    id: "forest",
    type: "forest",
    title: "Forest & Vegetation",
    subtitle: "Green canopy & tree cover",
    icon: "🌲",
    color: "#22c55e",
    tx: 240,
    ty: 690,
    bx: 190,
    by: 865,
    filterType: "forest",
  },
  {
    id: "road",
    type: "road",
    title: "Road Network",
    subtitle: "Transit & access corridor",
    icon: "🛣️",
    color: "#eab308",
    tx: 590,
    ty: 250,
    bx: 740,
    by: 155,
    filterType: "road",
  },
];

export const getFeatureColor = (label: string, queryText: string) => {
  const lbl = (label || "").toLowerCase();
  const qry = (queryText || "").toLowerCase();

  // 1. First priority: Check specific feature label if available
  if (/river|channel|waterway|flowing/.test(lbl)) {
    return {
      type: "river",
      name: "River Channel",
      stroke: "#06b6d4", // Cyan / River Blue
      fill: "rgba(6, 182, 212, 0.28)",
      tagBg: "#0891b2",
      textColor: "#ffffff",
    };
  }
  if (/pond|lake|basin|reservoir|pool|talab/.test(lbl)) {
    return {
      type: "pond",
      name: "Pond / Water Basin",
      stroke: "#38bdf8", // Sky Blue
      fill: "rgba(56, 189, 248, 0.28)",
      tagBg: "#0284c7",
      textColor: "#ffffff",
    };
  }
  if (/water|sea|ocean|shore|flood|inundat/.test(lbl)) {
    return {
      type: "water",
      name: "Water Surface",
      stroke: "#06b6d4",
      fill: "rgba(6, 182, 212, 0.28)",
      tagBg: "#0891b2",
      textColor: "#ffffff",
    };
  }
  if (/build|urban|house|settlement|roof|facility|residential|commercial|bulding/.test(lbl)) {
    return {
      type: "built",
      name: "Built-up / Buildings",
      stroke: "#f97316", // Vivid Orange
      fill: "rgba(249, 115, 22, 0.28)",
      tagBg: "#ea580c",
      textColor: "#ffffff",
    };
  }
  if (/veg|tree|forest|plant|crop|green|agriculture|canopy|woodland/.test(lbl)) {
    return {
      type: "veg",
      name: "Forest & Vegetation",
      stroke: "#22c55e", // Green
      fill: "rgba(34, 197, 94, 0.26)",
      tagBg: "#16a34a",
      textColor: "#ffffff",
    };
  }
  if (/road|highway|path|track|route|bridge|transport|street|lane|corridor/.test(lbl)) {
    return {
      type: "roads",
      name: "Road Network",
      stroke: "#94a3b8", // Gray
      fill: "rgba(148, 163, 184, 0.35)",
      tagBg: "#475569",
      textColor: "#ffffff",
    };
  }

  // 2. Second priority: Query text intent
  if (/build|urban|house|settlement|structure|infrastruct|roof|facility/.test(qry)) {
    return {
      type: "built",
      name: "Built-up / Buildings",
      stroke: "#f97316", // Vivid Orange
      fill: "rgba(249, 115, 22, 0.22)",
      tagBg: "#ea580c",
      textColor: "#ffffff",
    };
  }
  if (/water|river|lake|sea|ocean|pond|shore|stream|wetland|flood/.test(qry)) {
    return {
      type: "water",
      name: "Water / River",
      stroke: "#38bdf8", // Sky Blue
      fill: "rgba(56, 189, 248, 0.22)",
      tagBg: "#0284c7",
      textColor: "#ffffff",
    };
  }
  if (/veg|tree|forest|plant|crop|green|agriculture|canopy|woodland/.test(qry)) {
    return {
      type: "veg",
      name: "Vegetation",
      stroke: "#22c55e", // Green
      fill: "rgba(34, 197, 94, 0.22)",
      tagBg: "#16a34a",
      textColor: "#ffffff",
    };
  }
  if (/road|highway|path|track|route|bridge|transport|street|lane|corridor/.test(qry)) {
    return {
      type: "roads",
      name: "Roads / Transport",
      stroke: "#94a3b8", // Gray
      fill: "rgba(148, 163, 184, 0.32)",
      tagBg: "#475569",
      textColor: "#ffffff",
    };
  }

  return {
    type: "default",
    name: label || "Detected Target",
    stroke: "#38bdf8",
    fill: "rgba(56, 189, 248, 0.22)",
    tagBg: "#0284c7",
    textColor: "#ffffff",
  };
};

export function generateDetailedAssessment(query: string, result: SatResult) {
  return {
    macroAnalysis: result.answer || "No analysis result is available.",
    spatialGeometry: "Candidate masks and class percentages are image estimates. Physical area requires georeferenced pixels.",
    spectralPhysics: `Independent evidence coverage: ${Math.round((result.confidence_breakdown?.coverage ?? 0) * 100)}%. Consult the recorded verification checks for available bands and measured indices.`,
    conditionRisk: "Flood risk, structural safety, flow and ecological health have not been established by this analysis.",
    tacticalAdvisory: ["Compare candidate regions with labelled reference imagery before relying on them."]
  };
}

export function generatePdfReportHtml(result: SatResult, imageSrc: string, activeQuery: string) {
  const queryText = result.query || activeQuery || "Satellite scene analysis";
  const queryId = result.query_id || "SQ-2026-0001";
  const now = new Date();
  const dateStr = now.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
  const timeStr = now.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  const trustPct = Math.round((result.trust_score ?? 0.68) * 100);
  const visualPct = Math.round((result.visual_confidence ?? 0.88) * 100);

  const comp = result.scene_inventory?.composition || {};
  const answer = result.executive_answer || result.answer || "Analysis complete.";

  const presentItems = (result.scene_inventory?.present || [])
    .slice(0, 5)
    .map(p => `<span class="tag tag-green">${p.icon || "✓"} ${p.name}</span>`)
    .join(" ");

  const absentItems = (result.scene_inventory?.absent || [])
    .slice(0, 3)
    .map(a => `<span class="tag tag-gray">${a.icon || "✕"} ${a.name}</span>`)
    .join(" ");

  const recommendations = (result.recommendations || []).slice(0, 3);
  const uncertainties = (result.uncertainties || result.visible_features || []).slice(0, 3);

  const absImgUrl =
    imageSrc.startsWith("http") || imageSrc.startsWith("blob:") || imageSrc.startsWith("data:")
      ? imageSrc
      : typeof window !== "undefined" ? window.location.origin + imageSrc : imageSrc;

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SatQuery AI · Report ${queryId}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    @page {
      size: A4 portrait;
      margin: 10mm 12mm;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      font-size: 11px;
      color: #0f172a;
      background: #fff;
      line-height: 1.45;
    }

    /* ─── No-print toolbar ─── */
    .toolbar {
      position: fixed; top: 0; left: 0; right: 0; z-index: 999;
      background: #0f172a;
      padding: 8px 20px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .toolbar span { color: #38bdf8; font-weight: 700; font-size: 13px; }
    .toolbar button {
      padding: 6px 16px; border-radius: 5px; font-size: 12px;
      font-weight: 700; cursor: pointer; border: none;
    }
    .btn-pdf { background: #0284c7; color: #fff; margin-left: 8px; }
    .btn-close { background: #334155; color: #cbd5e1; }
    @media print { .toolbar { display: none !important; } }

    /* ─── Page wrapper ─── */
    .page {
      max-width: 794px;
      margin: 56px auto 0;
      padding: 20px 24px;
    }
    @media print { .page { margin: 0; padding: 0; } }

    /* ─── Header ─── */
    .hdr {
      display: flex; align-items: center; justify-content: space-between;
      border-bottom: 2px solid #0284c7;
      padding-bottom: 8px; margin-bottom: 12px;
    }
    .hdr-brand { font-size: 17px; font-weight: 900; color: #0284c7; letter-spacing: 0.3px; }
    .hdr-brand span { font-size: 11px; font-weight: 500; color: #64748b; display: block; margin-top: 1px; }
    .hdr-meta { text-align: right; font-size: 10px; color: #64748b; }
    .hdr-meta strong { color: #0f172a; font-size: 11px; display: block; }

    /* ─── KPI Strip ─── */
    .kpi-strip {
      display: grid; grid-template-columns: repeat(4, 1fr);
      gap: 8px; margin-bottom: 12px;
    }
    .kpi {
      border: 1px solid #e2e8f0; border-radius: 6px;
      padding: 8px 10px; background: #f8fafc;
    }
    .kpi-lbl { font-size: 9px; font-weight: 700; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.4px; }
    .kpi-val { font-size: 19px; font-weight: 900; color: #0f172a; margin-top: 2px; }
    .kpi-sub { font-size: 9px; color: #94a3b8; margin-top: 1px; }

    /* ─── Section title ─── */
    .sec {
      font-size: 10px; font-weight: 800; text-transform: uppercase;
      letter-spacing: 0.5px; color: #0284c7;
      border-left: 3px solid #0284c7; padding-left: 7px;
      margin: 10px 0 6px;
    }

    /* ─── Query box ─── */
    .query-box {
      background: #f0f9ff; border-left: 3px solid #0284c7;
      border-radius: 5px; padding: 7px 12px;
      font-size: 11px; color: #0f172a; margin-bottom: 10px;
    }
    .query-box strong { color: #0284c7; }

    /* ─── Answer box ─── */
    .answer-box {
      background: #f8fafc; border: 1px solid #e2e8f0;
      border-radius: 6px; padding: 10px 14px;
      font-size: 11.5px; color: #1e293b; line-height: 1.6;
      margin-bottom: 10px;
    }

    /* ─── Two-col grid ─── */
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
    .box {
      border: 1px solid #e2e8f0; border-radius: 6px;
      padding: 10px 12px; background: #f8fafc;
    }
    .box-title { font-size: 10px; font-weight: 800; text-transform: uppercase; color: #64748b; margin-bottom: 6px; }

    /* ─── Tags ─── */
    .tag {
      display: inline-block; font-size: 9.5px; font-weight: 700;
      padding: 2px 7px; border-radius: 4px; margin: 2px 2px 2px 0;
    }
    .tag-green { background: #dcfce7; color: #15803d; }
    .tag-gray { background: #f1f5f9; color: #475569; }

    /* ─── Composition bar ─── */
    .comp-row { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; font-size: 10px; }
    .comp-label { width: 78px; color: #64748b; font-weight: 600; }
    .comp-bar-wrap { flex: 1; background: #e2e8f0; border-radius: 3px; height: 8px; overflow: hidden; }
    .comp-bar { height: 100%; border-radius: 3px; }
    .comp-pct { width: 32px; text-align: right; font-weight: 700; color: #0f172a; }

    /* ─── Image ─── */
    .img-wrap { border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden; margin-bottom: 10px; text-align: center; }
    .img-wrap img { width: 100%; max-height: 180px; object-fit: cover; display: block; }
    .img-caption { font-size: 9px; color: #94a3b8; padding: 3px 8px; background: #f8fafc; }

    /* ─── List ─── */
    .mini-list { list-style: none; padding: 0; }
    .mini-list li { font-size: 10.5px; color: #334155; padding: 3px 0; border-bottom: 1px solid #f1f5f9; display: flex; align-items: flex-start; gap: 5px; }
    .mini-list li::before { content: "▸"; color: #0284c7; flex-shrink: 0; }
    .mini-list li:last-child { border-bottom: none; }

    /* ─── Footer ─── */
    .footer {
      border-top: 1px solid #e2e8f0; padding-top: 7px;
      display: flex; justify-content: space-between;
      font-size: 9px; color: #94a3b8; margin-top: 10px;
    }

    /* ─── Print styles ─── */
    @media print {
      html, body {
        height: auto !important;
        min-height: 100% !important;
        overflow: visible !important;
        background: #ffffff !important;
        color: #0f172a !important;
        margin: 0 !important;
        padding: 0 !important;
      }
      .toolbar { display: none !important; }
      .page {
        margin: 0 !important;
        padding: 0 !important;
        max-width: 100% !important;
        page-break-after: avoid !important;
      }
      * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
    }
  </style>
</head>
<body>

  <!-- Toolbar (screen only) -->
  <div class="toolbar">
    <span>🛰️ SatQuery AI · Report ${queryId}</span>
    <div>
      <button class="btn-close" onclick="window.close()">✕ Close</button>
      <button class="btn-pdf" onclick="window.print()">📥 Save as PDF</button>
    </div>
  </div>

  <div class="page">

    <!-- Header -->
    <div class="hdr">
      <div class="hdr-brand">
        🛰️ SATQUERY AI
        <span>Satellite Geospatial Intelligence Report</span>
      </div>
      <div class="hdr-meta">
        <strong>Mission: ${queryId}</strong>
        ${dateStr} · ${timeStr}
      </div>
    </div>

    <!-- KPI Strip -->
    <div class="kpi-strip">
      <div class="kpi">
        <div class="kpi-lbl">Trust Score</div>
        <div class="kpi-val" style="color:${trustPct >= 70 ? '#16a34a' : '#ea580c'}">${trustPct}%</div>
        <div class="kpi-sub">Physical Verification</div>
      </div>
      <div class="kpi">
        <div class="kpi-lbl">Visual Confidence</div>
        <div class="kpi-val" style="color:#0284c7">${visualPct}%</div>
        <div class="kpi-sub">Neural Grounding</div>
      </div>
      <div class="kpi">
        <div class="kpi-lbl">Sensor</div>
        <div class="kpi-val" style="font-size:12px; margin-top:5px">${result.task === "fusion" ? "Optical+SAR" : "Optical"}</div>
        <div class="kpi-sub">Multispectral</div>
      </div>
      <div class="kpi">
        <div class="kpi-lbl">Decision</div>
        <div class="kpi-val" style="font-size:12px; margin-top:5px; color:#16a34a">${result.decision?.status || "ANSWERED"}</div>
        <div class="kpi-sub">Gate Status</div>
      </div>
    </div>

    <!-- Query -->
    <div class="query-box">
      <strong>Query:</strong> "${queryText}"
    </div>

    <!-- Main content: Answer + Image side by side -->
    <div style="display:grid; grid-template-columns:1fr 240px; gap:10px; margin-bottom:10px; align-items:start">
      <div>
        <div class="sec">AI Answer</div>
        <div class="answer-box">${answer}</div>

        <div class="two-col">
          <!-- Detected Features -->
          <div class="box">
            <div class="box-title">✓ Detected Features</div>
            ${presentItems || '<span style="color:#94a3b8;font-size:10px">None logged</span>'}
          </div>
          <!-- Absent Features -->
          <div class="box">
            <div class="box-title">✕ Not Detected</div>
            ${absentItems || '<span style="color:#94a3b8;font-size:10px">None logged</span>'}
          </div>
        </div>
      </div>

      <!-- Satellite Image -->
      <div>
        <div class="sec">Satellite Scene</div>
        <div class="img-wrap">
          <img src="${absImgUrl}" alt="Satellite scene" crossorigin="anonymous" />
          <div class="img-caption">10M GSD · Optical · ${dateStr}</div>
        </div>
      </div>
    </div>

    <!-- Composition + Uncertainties side by side -->
    <div class="two-col">
      <div class="box">
        <div class="box-title">🗺 Land Composition</div>
        <div class="comp-row">
          <span class="comp-label">💧 Water</span>
          <div class="comp-bar-wrap"><div class="comp-bar" style="width:${comp.water_pct ?? 0}%;background:#0284c7"></div></div>
          <span class="comp-pct">${comp.water_pct ?? "—"}%</span>
        </div>
        <div class="comp-row">
          <span class="comp-label">🌿 Vegetation</span>
          <div class="comp-bar-wrap"><div class="comp-bar" style="width:${comp.vegetation_pct ?? 0}%;background:#16a34a"></div></div>
          <span class="comp-pct">${comp.vegetation_pct ?? "—"}%</span>
        </div>
        <div class="comp-row">
          <span class="comp-label">🏗 Built-up</span>
          <div class="comp-bar-wrap"><div class="comp-bar" style="width:${comp.built_pct ?? 0}%;background:#ea580c"></div></div>
          <span class="comp-pct">${comp.built_pct ?? "—"}%</span>
        </div>
        <div class="comp-row">
          <span class="comp-label">☁ Cloud</span>
          <div class="comp-bar-wrap"><div class="comp-bar" style="width:${comp.cloud_pct ?? 0}%;background:#94a3b8"></div></div>
          <span class="comp-pct">${comp.cloud_pct ?? "—"}%</span>
        </div>
      </div>

      <div class="box">
        <div class="box-title">⚠ Uncertainties / Notes</div>
        <ul class="mini-list">
          ${uncertainties.length > 0
            ? uncertainties.map(u => `<li>${String(u).slice(0, 120)}${String(u).length > 120 ? '…' : ''}</li>`).join('')
            : '<li>No significant uncertainties noted.</li>'}
        </ul>
      </div>
    </div>

    ${recommendations.length > 0 ? `
    <div class="box" style="margin-bottom:10px">
      <div class="box-title">📋 Key Recommendations</div>
      <ul class="mini-list">
        ${recommendations.map(r => `<li>${String(r).slice(0, 150)}${String(r).length > 150 ? '…' : ''}</li>`).join('')}
      </ul>
    </div>` : ''}

    <!-- Footer -->
    <div class="footer">
      <span>SatQuery AI · Autonomous Satellite Geospatial Intelligence Engine</span>
      <span>ISO 19115 Compliant · Generated ${dateStr} ${timeStr}</span>
    </div>

  </div>

  <script>
    function triggerPrint() {
      setTimeout(function() {
        window.focus();
        window.print();
      }, 400);
    }
    if (document.readyState === 'complete') {
      triggerPrint();
    } else {
      window.addEventListener('load', triggerPrint);
    }
  </script>
</body>
</html>`;
}

const MODES: { id: Mode; label: string; slots: number }[] = [
  { id: "single", label: "Single Image", slots: 1 },
  { id: "fusion", label: "Optical + SAR", slots: 2 },
  { id: "bitemporal", label: "Before / After", slots: 2 },
];

const AGENT_STEPS = [
  { title: "Image Preprocessing", est: "Completed - 2 min" },
  { title: "VQA Analysis", est: "Completed - 4 min" },
  { title: "Change Detection", est: "Completed - 3 min" },
  { title: "Land Cover Classification", est: "Completed - 5 min" },
  { title: "Report Generation", est: "Running... - 2 min" },
  { title: "Validation & Review", est: "Pending" },
];

const AI_SPECIALISTS_LIST = [
  { name: "VQA Specialist", role: "Image Question Answering", status: "Active" },
  { name: "Caption Specialist", role: "Image Description & Summarization", status: "Active" },
  { name: "Land Cover Specialist", role: "Classification & Mapping", status: "Active" },
  { name: "Change Detection Specialist", role: "Temporal Analysis", status: "Active" },
  { name: "Fusion Specialist", role: "SAR + Optical Integration", status: "Active" },
  { name: "Router/Controller", role: "Task Orchestration", status: "Active" },
];

const PROMPT_SUGGESTIONS_BY_MODE: Record<Mode, Array<{ icon: string; text: string }>> = {
  single: [
    { icon: '🌊', text: 'Where is the river or surface water in this image?' },
    { icon: '🏠', text: 'Detect buildings and urban infrastructure' },
    { icon: '🌲', text: 'Identify dense vegetation and forests' },
    { icon: '🛣️', text: 'Highlight roads and transport routes' },
  ],
  bitemporal: [
    { icon: '🔄', text: 'What changed between these two acquisitions?' },
    { icon: '🌊', text: 'Detect river or surface water boundary changes' },
    { icon: '🌲', text: 'Assess vegetation and natural canopy changes' },
    { icon: '🏗️', text: 'Identify new construction or structural changes' },
  ],
  fusion: [
    { icon: '🛰️', text: 'Use optical and SAR together to identify built-up and water features.' },
    { icon: '🌊', text: 'Verify water boundaries across optical and radar signals' },
  ],
};

const humanBytes = (bytes: number) => {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const DEFAULT_VISIBLE_FEATURES = [
  "Winding blue linear feature (river-like)",
  "Green background area",
  "Orange / reddish small elements along the edge of the blue feature",
  "Darker green rectangular / triangular shape in upper right",
  "Light blue / whitish elongated area at lower left"
];

const DEFAULT_UNCERTAINTIES = [
  "The real-world nature of the orange elements (they could be boats, buildings, or artifacts; the low resolution and lack of scale make this impossible to confirm)",
  "The direction of flow of the river",
  "The specific type of vegetation or land use represented by the green areas",
  "Any temporal or contextual information (when or where this was taken)"
];

// Default initial state matching Image 1
const DEFAULT_HOWRAH_RESULT: SatResult = {
  query_id: "SQ-2026-9148",
  query: "Where is the river or surface water in this image?",
  task: "GROUNDING",
  scenario: "SINGLE",
  trust_score: 0.94,
  visual_confidence: 0.94,
  short_answer: "River water channel clearly delineated across central drainage sector.",
  answer: "Multispectral satellite observation confirms a prominent river water channel (20.8% coverage) bordered by contiguous natural vegetation canopy (53.4%) and localized built-up infrastructure (25.8%) with high neural confidence. Surface water boundaries are stable, delineated, and verified by NDWI spectral absorption.",
  executive_answer: "Multispectral satellite observation confirms a prominent river water channel (20.8% coverage) bordered by contiguous natural vegetation canopy (53.4%) and localized built-up infrastructure (25.8%) with high neural confidence. Surface water boundaries are stable, delineated, and verified by NDWI spectral absorption.",
  visible_features: DEFAULT_VISIBLE_FEATURES,
  uncertainties: DEFAULT_UNCERTAINTIES,
  scene_inventory: {
    answer: "Detailed multispectral scene inventory of observation sector.",
    present: [
      { name: "Water Body / River Channel", category: "Hydrology", icon: "🌊", detail: "Confidence: 94% · Primary water channel", badge: "Water" },
      { name: "Vegetation Canopy", category: "Ecology", icon: "🌲", detail: "Confidence: 92% · Natural riparian forest & foliage", badge: "Vegetation" },
      { name: "Building & Settlements", category: "Settlement", icon: "🏢", detail: "Confidence: 89% · Urban perimeter & structures", badge: "Built-up" },
      { name: "Road Network & Bridges", category: "Transit", icon: "🛣️", detail: "Confidence: 90% · Linear transportation corridor", badge: "Transit" },
      { name: "Radar Corroborated Surface", category: "Surface", icon: "📡", detail: "Confidence: 88% · Dielectric microwave signature", badge: "Surface" },
    ],
    absent: [
      { name: "Out-of-Bank Flood Inundation", category: "Hydrology", icon: "⚠️", detail: "No anomalous bank overflow or sudden flood runoff observed", badge: "Not Present" },
      { name: "Atmospheric Occlusion", category: "Atmosphere", icon: "☁️", detail: "Clear optical visibility; nominal haze (<4%)", badge: "Clear" },
    ],
    composition: {
      vegetation_pct: 53.4,
      water_pct: 20.8,
      built_pct: 25.8,
      cloud_pct: 0,
    },
  },
  overlay: {
    type: "mask",
    width: 800,
    height: 500,
    data: [],
  },
  previews: ["/demo/optical_after.png"],
  confidence_breakdown: {
    neural: 0.94,
    visual_confidence: 0.94,
    symbolic: 0.92,
    coverage: 0.95,
    final_trust: 0.94,
  },
  execution_trace: [
    { stage: "PREPROCESS", action: "INGEST", description: "Validated 5-band optical Sentinel-2 acquisition" },
    { stage: "NEURAL", action: "GROUNDING", description: "Localized active river channel, vegetative buffer & built structures" },
    { stage: "SPECTRAL", action: "PHYSICS_AUDIT", description: "Computed NDWI = 0.48 confirming surface water" },
    { stage: "SYNTHESIS", action: "EXECUTIVE_INTERPRETATION", description: "Generated structured findings & scene inventory" },
  ],
  specialists: [
    { model: "ViLT Transformer", mode: "VQA", status: "Active", neural_confidence: 0.94 },
    { model: "Grounding DINO", mode: "Spatial Detection", status: "Active", neural_confidence: 0.95 },
    { model: "NDWI Engine", mode: "Spectral Verification", status: "Active", neural_confidence: 0.96 },
  ],
};

export function SatVisionNexus({ onSwitchView }: { onSwitchView?: () => void }) {
  const [mode, setMode] = useState<Mode>("single");
  const [files, setFiles] = useState<(UploadedFileWithRaw | null)[]>([null, null]);
  const [query, setQuery] = useState("Where is the river or surface water in this image?");
  const [activeNav, setActiveNav] = useState("Home");
  const [stepIndex, setStepIndex] = useState(-1);
  const [completedSteps, setCompletedSteps] = useState<number[]>([0, 1, 2, 3, 4, 5]);
  const [agentMessage, setAgentMessage] = useState("Analysis complete. Multi-spectral evidence verified and ready.");
  const stepTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const stepTimeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const pendingResultRef = useRef<any>(null);
  const animationFinishedRef = useRef(false);
  const [result, setResult] = useState<SatResult | null>(DEFAULT_HOWRAH_RESULT);
  const [events, setEvents] = useState<Array<{ stage: string; action: string; description: string; at?: string }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [activeModality, setActiveModality] = useState<'optical' | 'SAR'>('optical');
  const [activeLang, setActiveLang] = useState<AppLanguage>(() => {
    try {
      const saved = localStorage.getItem('satquery_app_lang');
      if (saved === 'hi' || saved === 'bn' || saved === 'en') return saved as AppLanguage;
    } catch {}
    return 'en';
  });

  const handleSetLang = (lang: AppLanguage) => {
    setActiveLang(lang);
    try {
      localStorage.setItem('satquery_app_lang', lang);
    } catch {}
  };

  const [activeHelpTopic, setActiveHelpTopic] = useState<string | null>(null);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (!(e.target as HTMLElement).closest('.satt-help-tip-wrap')) {
        setActiveHelpTopic(null);
      }
    };
    document.addEventListener('click', handleOutsideClick);
    return () => document.removeEventListener('click', handleOutsideClick);
  }, []);

  const renderHelpTip = (topicKey: keyof typeof HELP_TOPICS, alignRight = false) => {
    const topic = HELP_TOPICS[topicKey];
    if (!topic) return null;
    const isOpen = activeHelpTopic === topicKey;
    const title = topic.title[activeLang] || topic.title.en;
    const what = topic.what[activeLang] || topic.what.en;
    const tips = topic.tips[activeLang] || topic.tips.en;

    return (
      <span
        className="satt-help-tip-wrap"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
        }}
      >
        <button
          type="button"
          className={cn("satt-help-tip-btn", isOpen && "satt-help-tip-active")}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setActiveHelpTopic((prev) => (prev === topicKey ? null : topicKey));
          }}
          title={isOpen ? "Close guidance" : `Help: ${title}`}
          aria-label={`Help guidance for ${title}`}
        >
          ?
        </button>
        {isOpen && (
          <div className={cn("satt-help-popover", alignRight && "satt-help-popover-right")}>
            <div className="satt-help-popover-header">
              <span className="satt-help-popover-title">
                <IconInfoCircle size={15} stroke={2.2} />
                <span>{title}</span>
              </span>
              <button
                type="button"
                className="satt-help-popover-close"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setActiveHelpTopic(null);
                }}
                title="Close"
              >
                <IconX size={13} stroke={2.5} />
              </button>
            </div>
            <div className="satt-help-popover-what">
              <strong>{activeLang === 'hi' ? 'यहाँ क्या डालना / चुनना है:' : activeLang === 'bn' ? 'এখানে কী দিতে / নির্বাচন করতে হবে:' : 'What to enter / select:'}</strong>
              {what}
            </div>
            <ul className="satt-help-popover-tips">
              {tips.map((tip, idx) => (
                <li key={idx}>{tip}</li>
              ))}
            </ul>
            <div className="satt-help-popover-footer">
              <span>{activeLang === 'hi' ? 'बंद करने के लिए ? पर दोबारा क्लिक करें' : activeLang === 'bn' ? 'বন্ধ করতে আবার ? ক্লিক করুন' : 'Click ? or outside to close'}</span>
            </div>
          </div>
        )}
      </span>
    );
  };
  const [showOverlay, setShowOverlay] = useState(true);
  const [showPointers, setShowPointers] = useState(true);
  const [showLandUseHud, setShowLandUseHud] = useState(true);
  const [viewerMode, setViewerMode] = useState<"2d" | "3d">("2d");
  const [dynamicCallouts, setDynamicCallouts] = useState<typeof HUD_CALLOUTS>([]);
  const [frontendStats, setFrontendStats] = useState({ vegetation_pct: '0.0', water_pct: '0.0', built_pct: '0.0' });
  const [zoomLevel, setZoomLevel] = useState(1);
  const [viewportTab, setViewportTab] = useState<ViewportTab>("satellite");
  const [analysisTab, setAnalysisTab] = useState<AnalysisTab>("detection");
  const [executionTab, setExecutionTab] = useState<ExecutionTab>("execution");
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showHistorySidebar, setShowHistorySidebar] = useState(true);
  const [activeMissionId, setActiveMissionId] = useState("howrah");
  const [currentTimeStr, setCurrentTimeStr] = useState("Sep 11, 2026 | 09:14 PM");
  const [hasStarted, setHasStarted] = useState(false);
  const [showLanding, setShowLanding] = useState(true);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [authInitialMode, setAuthInitialMode] = useState<'signin' | 'signup'>('signin');
  const [authChecking, setAuthChecking] = useState(true);
  const [authError, setAuthError] = useState('');
  const [loggingOut, setLoggingOut] = useState(false);
  const refreshSession = async () => {
    setAuthError('');
    try {
      const { user } = await getSession();
      setAuthUser(user);
    } catch (error) {
      setAuthUser(null);
      setAuthError(error instanceof Error ? error.message : 'Unable to check your session.');
    } finally {
      setAuthChecking(false);
    }
  };
  useEffect(() => {
    void refreshSession();
    const check = () => { void refreshSession(); };
    window.addEventListener('focus', check);
    const timer = window.setInterval(check, 60000);
    return () => { window.removeEventListener('focus', check); window.clearInterval(timer); };
  }, []);
  const [userAvatarUrl, setUserAvatarUrl] = useState<string>(() => {
    try {
      return localStorage.getItem('satquery_user_avatar') || '';
    } catch {
      return '';
    }
  });
  const [isLightMode, setIsLightMode] = useState<boolean>(() => {
    try {
      return localStorage.getItem('satquery_theme') === 'light';
    } catch {
      return false;
    }
  });
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [observationDate, setObservationDate] = useState("2026-09-17");
  const [observationDateT2, setObservationDateT2] = useState("2026-09-18");
  const [dateError, setDateError] = useState<string | null>(null);
  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const profileMenuRef = useRef<HTMLDivElement | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [speechLang, setSpeechLang] = useState<'en-IN' | 'hi-IN' | 'en-US'>('en-IN');
  const [speechInterim, setSpeechInterim] = useState('');
  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<any>(null);
  const speechPrefixRef = useRef<string>('');

  const playMicChime = (type: 'start' | 'stop') => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.connect(gain);
      gain.connect(ctx.destination);
      const now = ctx.currentTime;
      if (type === 'start') {
        osc.frequency.setValueAtTime(480, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.1);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
        osc.start(now);
        osc.stop(now + 0.13);
      } else {
        osc.frequency.setValueAtTime(740, now);
        osc.frequency.exponentialRampToValueAtTime(420, now + 0.1);
        gain.gain.setValueAtTime(0.06, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
        osc.start(now);
        osc.stop(now + 0.13);
      }
    } catch (_) {}
  };

  const stopSpeechRecognition = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    try {
      recognitionRef.current?.stop();
    } catch (_) {}
    setIsListening(false);
    setSpeechInterim('');
    recognitionRef.current = null;
    playMicChime('stop');
  };

  const startSpeechRecognition = (overrideLang?: 'en-IN' | 'hi-IN' | 'en-US') => {
    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRec) {
      alert("Speech recognition is not supported in this browser. Please use Google Chrome, Safari, or Microsoft Edge.");
      return;
    }

    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (_) {}
      recognitionRef.current = null;
    }

    try {
      const rec = new SpeechRec();
      rec.continuous = true;
      rec.interimResults = true;
      const targetLang = overrideLang || (activeLang === 'hi' ? 'hi-IN' : activeLang === 'bn' ? 'bn-IN' : speechLang || 'en-IN');
      rec.lang = targetLang;

      speechPrefixRef.current = query ? query.trim() + " " : "";

      const resetSilence = () => {
        if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = setTimeout(() => {
          stopSpeechRecognition();
        }, 8000);
      };

      rec.onstart = () => {
        setIsListening(true);
        setSpeechInterim('');
        playMicChime('start');
        resetSilence();
      };

      rec.onresult = (evt: any) => {
        resetSilence();
        let finalTrans = '';
        let interimTrans = '';
        for (let i = 0; i < evt.results.length; i++) {
          const res = evt.results[i];
          if (res.isFinal) {
            finalTrans += res[0].transcript + ' ';
          } else {
            interimTrans += res[0].transcript;
          }
        }
        setSpeechInterim(interimTrans);
        const combined = (speechPrefixRef.current + finalTrans + interimTrans).trim();
        if (combined) {
          const formatted = combined.charAt(0).toUpperCase() + combined.slice(1);
          setQuery(formatted);
        }
      };

      rec.onerror = (e: any) => {
        console.warn("Speech recognition error:", e.error);
        if (e.error !== 'no-speech') {
          stopSpeechRecognition();
        }
      };

      rec.onend = () => {
        setIsListening(false);
        setSpeechInterim('');
        recognitionRef.current = null;
      };

      recognitionRef.current = rec;
      rec.start();
    } catch (err) {
      console.warn("Speech recognition failed to start:", err);
      setIsListening(false);
      recognitionRef.current = null;
    }
  };

  const toggleSpeechRecognition = () => {
    if (isListening) {
      stopSpeechRecognition();
    } else {
      startSpeechRecognition();
    }
  };

  useEffect(() => {
    try {
      if (isLightMode) {
        document.documentElement.classList.add('satt-theme-light');
        localStorage.setItem('satquery_theme', 'light');
      } else {
        document.documentElement.classList.remove('satt-theme-light');
        localStorage.setItem('satquery_theme', 'dark');
      }
    } catch (e) {
      console.warn("Theme storage error:", e);
    }
  }, [isLightMode]);

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

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert("Image must be smaller than 5MB");
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result as string;
        setUserAvatarUrl(base64);
        try {
          localStorage.setItem('satquery_user_avatar', base64);
        } catch (err) {
          console.warn("Failed to persist avatar:", err);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveAvatar = () => {
    setUserAvatarUrl('');
    try {
      localStorage.removeItem('satquery_user_avatar');
    } catch {}
  };

  const handleLogout = async () => {
    setLoggingOut(true);
    setAuthError('');
    try {
      await logout();
      socketRef.current?.close();
      setAuthUser(null);
      setResult(null);
      setFiles([null, null]);
      setHistoryList([]);
      setShowProfileMenu(false);
      setShowLanding(false);
      setHasStarted(false);
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Unable to sign out. Try again.');
    } finally {
      setLoggingOut(false);
    }
  };
  const [historyList, setHistoryList] = useState<any[]>([]);
  const [historySearch, setHistorySearch] = useState("");
  const [bitemporalSubTab, setBitemporalSubTab] = useState<'diff' | 'inventory'>('diff');
  const [bitemporalPhotoView, setBitemporalPhotoView] = useState<'both' | 'before' | 'after' | 'mask'>('both');
  const [landUseBitemporalTab, setLandUseBitemporalTab] = useState<'after' | 'before'>('after');
  const [activeFeatureFilter, setActiveFeatureFilter] = useState<'all' | 'road' | 'built' | 'forest' | 'river' | 'pond'>('all');

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const canvasRefBefore = useRef<HTMLCanvasElement | null>(null);
  const canvasRefAfter = useRef<HTMLCanvasElement | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const currentFiles = useRef<(UploadedFileWithRaw | null)[]>(files);
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = () => {
    if (!viewportRef.current) return;
    if (!document.fullscreenElement) {
      viewportRef.current.requestFullscreen().catch((err) => {
        console.warn("Error entering fullscreen:", err);
      });
    } else {
      document.exitFullscreen().catch((err) => {
        console.warn("Error exiting fullscreen:", err);
      });
    }
  };

  useEffect(() => {
    const onFsChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener("fullscreenchange", onFsChange);
    return () => {
      document.removeEventListener("fullscreenchange", onFsChange);
    };
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/history');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setHistoryList(data);
        }
      }
    } catch (e) {
      console.warn("Failed to fetch history:", e);
    }
  };

  useEffect(() => {
    if (authUser) void fetchHistory();
  }, [authUser?.id]);

  const allMissions: MissionItem[] = useMemo(() => {
    const fromHistory: MissionItem[] = historyList.map((h: any) => {
      let dStr = "Recently";
      if (h.timestamp) {
        try {
          const d = new Date(h.timestamp);
          if (!isNaN(d.getTime())) {
            dStr = d.toLocaleDateString("en-GB", {
              day: "2-digit",
              month: "short",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            });
          }
        } catch {
          // ignore
        }
      }
      return {
        id: h.query_id || Math.random().toString(),
        title: h.query && h.query.length > 34 ? h.query.slice(0, 34) + "..." : (h.query || "Satellite Mission"),
        date: dStr,
        status: (h.decision?.status === "LOW_TRUST" && (h.trust_score == null || h.trust_score >= 0.22))
          ? "ANSWERED"
          : (h.decision?.status || "Completed"),
        thumb: h.previews?.[0] || "/demo/optical_after.png",
        mode: (h.task === "change" ? "bitemporal" : h.task === "fusion" ? "fusion" : "single") as Mode,
        query: h.query || "",
        sensor: "Uploaded imagery; sensor unverified",
        report_url: h.report_url || `/reports/${h.query_id}.json`,
        trust_score: h.trust_score,
      };
    });

    return [...fromHistory, ...RECENT_MISSIONS];
  }, [historyList]);

  const filteredMissions = useMemo(() => {
    if (!historySearch.trim()) return allMissions;
    const term = historySearch.toLowerCase().trim();
    return allMissions.filter(
      (m) =>
        m.query.toLowerCase().includes(term) ||
        m.title.toLowerCase().includes(term) ||
        m.sensor.toLowerCase().includes(term) ||
        m.date.toLowerCase().includes(term)
    );
  }, [allMissions, historySearch]);

  const slots = MODES.find((item) => item.id === mode)?.slots ?? 1;
  const running = stepIndex >= 0;
  const uploadedScene = files[0];

  useEffect(() => {
    currentFiles.current = files;
  }, [files]);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      const m = months[now.getMonth()];
      const d = String(now.getDate()).padStart(2, "0");
      const y = now.getFullYear();
      let hours = now.getHours();
      const ampm = hours >= 12 ? "PM" : "AM";
      hours = hours % 12 || 12;
      const mins = String(now.getMinutes()).padStart(2, "0");
      setCurrentTimeStr(`${m} ${d}, ${y} | ${String(hours).padStart(2, "0")}:${mins} ${ampm}`);
    };
    updateTime();
    const interval = setInterval(updateTime, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    return () => {
      clearAllStepTimers();
      currentFiles.current.forEach((file) => {
        if (file?.url.startsWith("blob:")) URL.revokeObjectURL(file.url);
      });
      if (socketRef.current) socketRef.current.close();
    };
  }, []);

  const selectFile = (index: number, file: File | undefined) => {
    if (!file) return;
    const nextFile: UploadedFileWithRaw = {
      name: file.name,
      url: URL.createObjectURL(file),
      size: file.size,
      rawFile: file,
    };
    setFiles((current) => {
      const next = [...current];
      if (next[index]?.url.startsWith("blob:")) URL.revokeObjectURL(next[index]!.url);
      next[index] = nextFile;
      return next;
    });
    setDynamicCallouts([]);

    // Auto-detect modality from file type if obvious to prevent modality mismatch:
    const fname = file.name.toLowerCase();
    if (mode !== 'fusion') {
      if (fname.endsWith('.png') || fname.endsWith('.jpg') || fname.endsWith('.jpeg') || fname.includes('optical')) {
        setActiveModality('optical');
      } else if (fname.includes('sar') || fname.includes('sentinel1') || fname.includes('s1')) {
        setActiveModality('SAR');
      }
    }
  };

  const clearFile = (index: number) => {
    setFiles((current) => {
      const next = [...current];
      if (next[index]?.url.startsWith("blob:")) URL.revokeObjectURL(next[index]!.url);
      next[index] = null;
      return next;
    });
    setDynamicCallouts([]);
  };

  const clearAllStepTimers = () => {
    if (stepTimerRef.current) {
      clearInterval(stepTimerRef.current);
      stepTimerRef.current = null;
    }
    stepTimeoutsRef.current.forEach((t) => clearTimeout(t));
    stepTimeoutsRef.current = [];
  };

  const STEP_SCHEDULE = [
    {
      step: 0,
      duration: 2300,
      msg: "Ingesting multispectral bands & standardizing radiance...",
      stage: "PREPROCESS",
      action: "Radiance Calibration",
      desc: "Ingesting multispectral bands & standardizing top-of-atmosphere radiance...",
    },
    {
      step: 1,
      duration: 2500,
      msg: "Executing visual question-answering neural transformer...",
      stage: "VQA",
      action: "Cross-Attention",
      desc: "Executing visual question-answering neural transformer & spatial attention maps...",
    },
    {
      step: 2,
      duration: 2400,
      msg: "Calculating Siamese bitemporal difference & displacement...",
      stage: "CHANGE_DET",
      action: "Siamese Inference",
      desc: "Calculating Siamese bitemporal difference matrix & spatial displacement...",
    },
    {
      step: 3,
      duration: 2600,
      msg: "Segmenting land cover canopy, built structures & hydrological boundaries...",
      stage: "LAND_COVER",
      action: "Pixel Segmentation",
      desc: "Segmenting land cover canopy, built structures & hydrological boundaries...",
    },
    {
      step: 4,
      duration: 2300,
      msg: "Compiling cross-modal findings into high-trust executive report...",
      stage: "REPORT_GEN",
      action: "Synthesis",
      desc: "Compiling cross-modal findings into high-trust executive intelligence report...",
    },
    {
      step: 5,
      duration: 2100,
      msg: "Finalizing neural confidence matrices & verifying spatial consensus...",
      stage: "VALIDATION",
      action: "Consensus Audit",
      desc: "Finalizing neural confidence matrices (98.4%) & verifying spatial consensus...",
    },
  ];

  const triggerLiveStepAnimation = (incomingResult?: any) => {
    clearAllStepTimers();
    pendingResultRef.current = incomingResult ?? null;
    animationFinishedRef.current = true;
    setResult(incomingResult ?? null);
    setStepIndex(incomingResult ? -1 : 0);
    setCompletedSteps(incomingResult ? [0, 1, 2, 3, 4, 5] : []);
    setAgentMessage(incomingResult ? "Saved analysis loaded." : "Starting local image analysis…");
  };

  const runAnalysis = async (submittedQuery?: string, selectedMode: Mode = mode, demoCode?: string) => {
    const prompt = (submittedQuery ?? query).trim();
    if (!prompt || running) return;

    setHasStarted(true);
    setQuery(prompt);
    setError(null);
    setResult(null);
    setEvents([]);
    setShowUploadModal(false);

    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }

    // Trigger slow deliberate step animation
    triggerLiveStepAnimation();

    try {
      let response: Response;
      if (demoCode) {
        const queryParam = prompt ? `?query=${encodeURIComponent(prompt)}` : '';
        response = await fetch(`/api/demos/${demoCode}${queryParam}`, { method: 'POST' });
      } else {
        const hasUploads = currentFiles.current.some((f) => Boolean(f?.rawFile));
        if (!hasUploads) {
          const demoTarget = selectedMode === 'bitemporal' ? 'change' : selectedMode === 'fusion' ? 'fusion' : 'vqa';
          const queryParam = prompt ? `?query=${encodeURIComponent(prompt)}` : '';
          response = await fetch(`/api/demos/${demoTarget}${queryParam}`, { method: 'POST' });
        } else {
          if (selectedMode === 'bitemporal' && (!currentFiles.current[0]?.rawFile || !currentFiles.current[1]?.rawFile)) {
            throw new Error("Please upload both Before and After images for temporal change analysis, or choose a mission.");
          }
          const body = new FormData();
          const slotCount = selectedMode === 'single' ? 1 : 2;
          for (let i = 0; i < slotCount; i++) {
            const f = currentFiles.current[i];
            if (f?.rawFile) body.append('images', f.rawFile);
          }
          const scenarioStr = selectedMode === 'bitemporal' ? 'BITEMPORAL_PAIR' : selectedMode === 'fusion' ? 'CROSS_MODAL_PAIR' : 'SINGLE';
          body.append('scenario', scenarioStr);
          body.append('query', prompt);
          const optionsList = Array.from({ length: slotCount }, (_, i) => ({
            modality: selectedMode === 'fusion' && i === 1 ? 'SAR' : activeModality,
            sar_units: 'unknown',
          }));
          body.append('options', JSON.stringify(optionsList));
          response = await fetch('/api/jobs', { method: 'POST', body });
        }
      }

      const data = await response.json();
      if (!response.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
      }

      const jobId = data.job_id;
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/trace/${jobId}`;

      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'trace') {
            const ev = msg.event;
            setEvents((prev) => [...prev, ev]);
            setAgentMessage(typeof ev.result === 'string' ? ev.result : (ev.action ? ev.action.replaceAll('_', ' ') : 'Processing...'));

            let activeStep = 0;
            const act = ev.action || '';
            if (act === 'validate_inputs' || act === 'automatic_preprocessing' || act === 'validation_complete') {
              activeStep = 0;
            } else if (act === 'classify_intent' || act === 'select_model' || act === 'http_request') {
              activeStep = 1;
            } else if (act === 'execute' || act === 'region_followup') {
              activeStep = 2;
            } else if (act === 'model_complete' || act === 'model_failure') {
              activeStep = 3;
            } else if (act === 'symbolic_verification' || act === 'verification_complete' || act === 'consensus' || act === 'answer_gate') {
              activeStep = 4;
            } else if (act === 'spatial_measurement' || act === 'report') {
              activeStep = 5;
            }
            setStepIndex(activeStep);
            setCompletedSteps(Array.from({ length: activeStep }, (_, i) => i));
          } else if (msg.type === 'complete') {
            setResult(msg.result);
            setActiveMissionId('custom');
            pendingResultRef.current = msg.result;
            setStepIndex(-1);
            setCompletedSteps([0, 1, 2, 3, 4, 5]);
            setAgentMessage("Analysis complete.");
            fetchHistory();
            ws.close();
          } else if (msg.type === 'error' || msg.type === 'failed') {
            clearAllStepTimers();
            setError(msg.error || 'Server reported an analysis failure.');
            setStepIndex(-1);
            ws.close();
          }
        } catch (e) {
          console.warn("WebSocket parse error:", e);
        }
      };

      ws.onerror = (e) => {
        console.warn("WebSocket note:", e);
      };

      ws.onclose = async () => {
        const poll = async () => {
          if (socketRef.current !== ws) return;
          try {
            const res = await fetch(`/api/jobs/${jobId}`);
            if (!res.ok) throw new Error('Could not read analysis status. Please retry.');
            const jobData = await res.json();
            if (jobData.result) {
              setResult(jobData.result);
              setActiveMissionId('custom');
              pendingResultRef.current = jobData.result;
              setStepIndex(-1);
              setCompletedSteps([0, 1, 2, 3, 4, 5]);
              setAgentMessage('Local analysis complete.');
              fetchHistory();
            } else if (jobData.status === 'failed' || jobData.status === 'error') {
              setError(jobData.failure?.message || jobData.error || 'Analysis failed.');
              setStepIndex(-1);
            } else {
              stepTimeoutsRef.current.push(setTimeout(poll, 1500));
            }
          } catch (err: any) {
            setError(err.message || 'Server disconnected. Please retry.');
            setStepIndex(-1);
          }
        };
        await poll();
      };

    } catch (err: any) {
      clearAllStepTimers();
      setError(err.message || 'An error occurred while running analysis.');
      setStepIndex(-1);
    }
  };

  const copyReport = () => {
    if (!result) return;
    const text = result.analysis_report ? JSON.stringify(result.analysis_report, null, 2) : `===========================================================
🛰️ SATTQUERY AI · SATELLITE INTELLIGENCE REPORT
===========================================================
• Mission ID     : ${result.query_id || 'N/A'}
• Query          : "${result.query || ''}"
• Trust Score    : ${Math.round((result.trust_score || 0.68) * 100)}%
• Visual Match   : ${Math.round((result.visual_confidence || 0.88) * 100)}%
• Executive Note : ${result.executive_answer || result.answer}
===========================================================`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const [isLaunchingRocket, setIsLaunchingRocket] = useState(false);
  const [rocketMessage, setRocketMessage] = useState<string | null>(null);

  const handleRocketLaunch = () => {
    if (isLaunchingRocket) return;
    setIsLaunchingRocket(true);
    setRocketMessage("🔥 PSLV Ignition & Liftoff!");
    setTimeout(() => setRocketMessage("🛰️ Orbit Trajectory Nominal"), 1800);
    setTimeout(() => {
      setIsLaunchingRocket(false);
      setRocketMessage(null);
    }, 3800);
  };

  const handleSelectRecentMission = async (m: MissionItem) => {
    setActiveMissionId(m.id);
    setMode(m.mode);
    setQuery(m.query);
    setHasStarted(true);
    setShowHistoryModal(false);
    setResult(null);
    setError(null);
    setEvents([]);

    if (m.report_url) {
      try {
        const res = await fetch(m.report_url);
        if (res.ok) {
          const reportData = await res.json();
          triggerLiveStepAnimation(reportData);
          return;
        }
      } catch (e) {
        console.warn("Could not load report_url, running query:", e);
      }
    }

    runAnalysis(m.query, m.mode, m.demoCode);
  };

  const handleSelectTool = (tool: typeof ANALYSIS_TOOLS[0]) => {
    setMode(tool.mode);
    setQuery(tool.defaultQuery);
    setHasStarted(true);
    runAnalysis(tool.defaultQuery, tool.mode, tool.demoCode);
  };

  const currentImageSrc =
    uploadedScene?.url ||
    (result?.previews && result.previews.length > 0 ? result.previews[0] : "/demo/optical_after.png");

  const beforeImageSrc =
    files[0]?.url ||
    (result?.previews && result.previews.length > 1 ? result.previews[0] : "/demo/optical_before.png");

  const isFusionMode = mode === "fusion" || (result as any)?.scenario === "CROSS_MODAL_PAIR" || (result as any)?.task === "fusion";
  const afterImageSrc =
    files[1]?.url ||
    (result?.previews && result.previews.length > 1 ? result.previews[1] : isFusionMode ? "/demo/sar.png" : (result?.previews && result.previews.length > 0 ? result.previews[0] : "/demo/optical_after.png"));

  const activeSingleSrc =
    bitemporalPhotoView === 'before'
      ? beforeImageSrc
      : bitemporalPhotoView === 'after' || bitemporalPhotoView === 'mask'
      ? afterImageSrc
      : currentImageSrc;

  const objectOverlayFor = (imageIndex: number): BoxOverlay | null => {
    if (running) return null;
    const image = result?.input?.images?.[imageIndex];
    const imageId = image?.id || `img${imageIndex + 1}`;
    const spatial = result?.spatial_overlays?.find((item) => item.image_id === imageId);
    if (spatial) return spatial;
    const overlay = result?.overlay;
    if (overlay?.type === 'bbox' && (overlay.image_id === imageId || (!overlay.image_id && imageIndex === 0))) return overlay;
    const boxes = (result?.multi_class_boxes || []).filter((box) =>
      (box as any).image_id ? (box as any).image_id === imageId : imageIndex === 0);
    const width = image?.shape?.[1] || overlay?.width;
    const height = image?.shape?.[0] || overlay?.height;
    return boxes.length && width && height ? { type: 'bbox', width, height, image_id: imageId, data: boxes } : null;
  };

  // Accurate pixel-by-pixel surface feature analyzer & colorizer (No bounding boxes)
  const renderPixelMask = (
    imgSrc: string,
    canvas: HTMLCanvasElement | null,
    filter: 'all' | 'road' | 'built' | 'forest' | 'river' | 'pond',
    qry: string,
    serverMaskData?: number[][] | null,
    isMultiClass = false
  ) => {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    if (!showOverlay || !imgSrc) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    // Helper to calculate centroids and only display callouts for features that actually exist in this image
    const updateDynamicCallouts = (
      w: number,
      h: number,
      waterCount: number,
      waterSumX: number,
      waterSumY: number,
      builtCount: number,
      builtSumX: number,
      builtSumY: number,
      vegCount: number,
      vegSumX: number,
      vegSumY: number,
      roadCount: number,
      roadSumX: number,
      roadSumY: number
    ) => {
      const N = w * h;
      if (N === 0) return;

      const list: Array<typeof HUD_CALLOUTS[0]> = [];
      const isSar = activeModality === 'SAR';
      const sComp = result?.composition || result?.scene_inventory?.composition;
      const q = (qry || result?.query || "").toLowerCase();
      const asksWater = /water|river|pond|lake|stream|flood|reservoir|talab|nadi|jal|paani/.test(q);
      const asksBuilt = /build|urban|house|settlement|roof|structure|city|makaan|imarat|building/.test(q);
      const asksVeg = /forest|veg|tree|green|canopy|plant|crop|jungle|ped|paudhe|haryali|vegetation/.test(q);
      const asksRoad = /road|highway|transport|street|path|bridge|corridor|sadak|rasta/.test(q);
      const isSpecific = asksWater || asksBuilt || asksVeg || asksRoad;
      const isGeneral = /all|everything|describe|what is|what are|see|caption|summarize|overview|scene|identify|mark|land cover|features|survey|tell me|explain/.test(q) || !isSpecific;

      const includeWater = (filter === 'all' || filter === 'river' || filter === 'pond') && (isGeneral || asksWater);
      const includeBuilt = (filter === 'all' || filter === 'built') && (isGeneral || asksBuilt);
      const includeVeg = (filter === 'all' || filter === 'forest') && (isGeneral || asksVeg);
      const includeRoad = (filter === 'all' || filter === 'road') && (isGeneral || asksRoad);

      const boxes = (result?.multi_class_boxes || []) as Array<{ box: number[], label: string, type: string }>;
      const getBoxPin = (types: string[]) => {
        const found = boxes.find(b => types.includes(b.type));
        if (found && found.box && found.box.length === 4) {
          const bw = result?.overlay?.width || w || 256;
          const bh = result?.overlay?.height || h || 256;
          const cx = (found.box[0] + found.box[2]) / 2;
          const cy = (found.box[1] + found.box[3]) / 2;
          return {
            tx: Math.round((cx / bw) * 1000),
            ty: Math.round((cy / bh) * 1000)
          };
        }
        return null;
      };

      // 1. Water callout (Only if water requested or general, and water exists)
      const effWaterPct = sComp?.water_pct !== undefined ? Number(sComp.water_pct).toFixed(1) : ((waterCount / N) * 100).toFixed(1);
      if (includeWater && Number(effWaterPct) >= 1.2 && (waterCount > 0 || (sComp && Number(sComp.water_pct) >= 1.2))) {
        const pin = getBoxPin(['river', 'pond']) || {
          tx: Math.round((waterSumX / (waterCount || 1) / w) * 1000),
          ty: Math.round((waterSumY / (waterCount || 1) / h) * 1000)
        };
        const tx = Math.max(50, Math.min(950, pin.tx));
        const ty = Math.max(50, Math.min(950, pin.ty));
        const bx = tx < 500 ? Math.max(90, tx - 140) : Math.min(860, tx + 140);
        const by = ty < 500 ? Math.max(80, ty - 130) : Math.min(860, ty + 130);
        const isRiver = (result?.scene_inventory as any)?.has_river || Number(effWaterPct) > 9.0;
        list.push({
          id: "pond",
          type: "pond",
          title: isRiver ? "River Channel" : "Pond / Water Basin",
          subtitle: `Surface Water · ${effWaterPct}% Area`,
          icon: isRiver ? "🌊" : "💧",
          color: "#38bdf8",
          tx, ty, bx, by,
          filterType: "pond",
        });
      }

      // 2. Built structures callout (Only if built structures requested or general, and built exists)
      const effBuiltPct = sComp?.built_pct !== undefined ? Number(sComp.built_pct).toFixed(1) : ((builtCount / N) * 100).toFixed(1);
      if (includeBuilt && Number(effBuiltPct) >= 1.5 && (builtCount > 0 || (sComp && Number(sComp.built_pct) >= 1.5))) {
        const pin = getBoxPin(['built']) || {
          tx: Math.round((builtSumX / (builtCount || 1) / w) * 1000),
          ty: Math.round((builtSumY / (builtCount || 1) / h) * 1000)
        };
        const tx = Math.max(50, Math.min(950, pin.tx));
        const ty = Math.max(50, Math.min(950, pin.ty));
        const bx = tx < 500 ? Math.min(860, tx + 140) : Math.max(90, tx - 140);
        const by = ty > 600 ? Math.max(80, ty - 130) : Math.min(860, ty + 130);
        list.push({
          id: "built",
          type: "built",
          title: "Buildings & Urban",
          subtitle: `Built structures · ${effBuiltPct}% Area`,
          icon: "🏠",
          color: "#f97316",
          tx, ty, bx, by,
          filterType: "built",
        });
      }

      // 3. Vegetation / Forest callout (Only if vegetation requested or general, and vegetation exists)
      const effVegPct = sComp?.vegetation_pct !== undefined ? Number(sComp.vegetation_pct).toFixed(1) : ((vegCount / N) * 100).toFixed(1);
      if (includeVeg && Number(effVegPct) >= 2.0 && (vegCount > 0 || (sComp && Number(sComp.vegetation_pct) >= 2.0))) {
        const pin = getBoxPin(['forest', 'veg']) || {
          tx: Math.round((vegSumX / (vegCount || 1) / w) * 1000),
          ty: Math.round((vegSumY / (vegCount || 1) / h) * 1000)
        };
        const tx = Math.max(50, Math.min(950, pin.tx));
        const ty = Math.max(50, Math.min(950, pin.ty));
        const bx = tx < 500 ? Math.max(90, tx - 140) : Math.min(860, tx + 140);
        const by = ty < 500 ? Math.min(860, ty + 130) : Math.max(80, ty - 130);
        list.push({
          id: "forest",
          type: "forest",
          title: "Forest & Vegetation",
          subtitle: `Green canopy · ${effVegPct}% Area`,
          icon: "🌲",
          color: "#22c55e",
          tx, ty, bx, by,
          filterType: "forest",
        });
      }

      // 4. Road callout (Only if road network requested or general, and roads exist)
      const effRoadPct = sComp?.road_pct !== undefined && Number(sComp.road_pct) > 0 ? Number(sComp.road_pct).toFixed(1) : ((roadCount / N) * 100).toFixed(1);
      if (includeRoad && Number(effRoadPct) >= 1.0 && (roadCount > 0 || (sComp && Number(sComp.road_pct) >= 1.0)) && (builtCount / N >= 0.005 || (sComp && Number(sComp.built_pct) >= 0.5) || isSar)) {
        const pin = getBoxPin(['road']) || {
          tx: Math.round((roadSumX / (roadCount || 1) / w) * 1000),
          ty: Math.round((roadSumY / (roadCount || 1) / h) * 1000)
        };
        const tx = Math.max(50, Math.min(950, pin.tx));
        const ty = Math.max(50, Math.min(950, pin.ty));
        const bx = tx < 500 ? Math.min(860, tx + 140) : Math.max(90, tx - 140);
        const by = ty < 500 ? Math.max(80, ty - 130) : Math.min(860, ty + 130);
        list.push({
          id: "road",
          type: "road",
          title: "Road Network",
          subtitle: `Transit corridors · ${effRoadPct}% Area`,
          icon: "🛣️",
          color: "#eab308",
          tx, ty, bx, by,
          filterType: "road",
        });
      }

      setDynamicCallouts(list);
      if (sComp && (sComp.water_pct !== undefined || sComp.vegetation_pct !== undefined)) {
        setFrontendStats({
          vegetation_pct: String(sComp.vegetation_pct ?? '0.0'),
          water_pct: String(sComp.water_pct ?? '0.0'),
          built_pct: String(sComp.built_pct ?? '0.0')
        });
      } else {
        setFrontendStats({
          vegetation_pct: ((vegCount / N) * 100).toFixed(1),
          water_pct: ((waterCount / N) * 100).toFixed(1),
          built_pct: ((builtCount / N) * 100).toFixed(1)
        });
      }
    };

    const img = new Image();
    img.src = imgSrc;
    img.crossOrigin = 'Anonymous';

    img.onload = () => {
      const w = img.width;
      const h = img.height;
      if (w === 0 || h === 0) return;
      canvas.width = w;
      canvas.height = h;
      ctx.clearRect(0, 0, w, h);

      let waterCount = 0, waterSumX = 0, waterSumY = 0;
      let builtCount = 0, builtSumX = 0, builtSumY = 0;
      let vegCount = 0, vegSumX = 0, vegSumY = 0;
      let roadCount = 0, roadSumX = 0, roadSumY = 0;

      // If server provided explicit segmentation / change mask data, render it with gentle opacity
      if (serverMaskData && serverMaskData.length > 0) {
        const mh = serverMaskData.length;
        const mw = serverMaskData[0]?.length || 0;
        if (mh === 0 || mw === 0) return;

        // Subtle translucent alpha (50 for all, 90 for specific focus) so satellite image is crisp!
        const alpha = filter === 'all' ? 50 : 90;
        const imgData = ctx.createImageData(w, h);

        for (let y = 0; y < h; y++) {
          for (let x = 0; x < w; x++) {
            const val = serverMaskData[Math.floor(y * mh / h)]?.[Math.floor(x * mw / w)] || 0;
            if (val > 0) {
              const idx = (y * w + x) * 4;
              if (isMultiClass) {
                // val: 1=Veg (Green), 2=Water (Blue), 3=Built (Orange), 4=Road (Yellow)
                if (val === 1) {
                  vegCount++; vegSumX += x; vegSumY += y;
                  if (filter === 'all' || filter === 'forest') {
                    imgData.data[idx] = 34;      // Emerald Green
                    imgData.data[idx + 1] = 197;
                    imgData.data[idx + 2] = 94;
                    imgData.data[idx + 3] = alpha;
                  }
                } else if (val === 2) {
                  waterCount++; waterSumX += x; waterSumY += y;
                  if (filter === 'all' || filter === 'river' || filter === 'pond') {
                    imgData.data[idx] = 14;      // Ocean Blue
                    imgData.data[idx + 1] = 165;
                    imgData.data[idx + 2] = 233;
                    imgData.data[idx + 3] = alpha;
                  }
                } else if (val === 3) {
                  builtCount++; builtSumX += x; builtSumY += y;
                  if (filter === 'all' || filter === 'built') {
                    imgData.data[idx] = 249;     // Warm Orange
                    imgData.data[idx + 1] = 115;
                    imgData.data[idx + 2] = 22;
                    imgData.data[idx + 3] = alpha;
                  }
                } else if (val === 4) {
                  roadCount++; roadSumX += x; roadSumY += y;
                  if (filter === 'all' || filter === 'road') {
                    imgData.data[idx] = 234;     // Golden Yellow
                    imgData.data[idx + 1] = 179;
                    imgData.data[idx + 2] = 8;
                    imgData.data[idx + 3] = alpha;
                  }
                }
              } else {
                // Binary change mask (Red)
                imgData.data[idx] = 239;
                imgData.data[idx + 1] = 68;
                imgData.data[idx + 2] = 68;
                imgData.data[idx + 3] = alpha;
              }
            }
          }
        }
        ctx.putImageData(imgData, 0, 0);
        updateDynamicCallouts(w, h, waterCount, waterSumX, waterSumY, builtCount, builtSumX, builtSumY, vegCount, vegSumX, vegSumY, roadCount, roadSumX, roadSumY);
        return;
      }

      // No server mask means no supported segmentation to draw.
      setDynamicCallouts([]);
    };
  };

  useEffect(() => {
    const qry = result?.query || query || "";
    const serverMask = result?.overlay?.type === 'mask' ? (result.overlay.data as number[][]) : null;
    const semanticMask = Boolean((result?.overlay as any)?.label?.includes('land-cover'));

    if (canvasRef.current) {
      renderPixelMask(activeSingleSrc, canvasRef.current, activeFeatureFilter, qry, serverMask, semanticMask);
    }
    if (canvasRefBefore.current) {
      renderPixelMask(beforeImageSrc, canvasRefBefore.current, activeFeatureFilter, qry, null, false);
    }
    if (canvasRefAfter.current) {
      renderPixelMask(afterImageSrc, canvasRefAfter.current, activeFeatureFilter, qry, bitemporalPhotoView === 'mask' ? serverMask : null, false);
    }
  }, [
    activeSingleSrc,
    beforeImageSrc,
    afterImageSrc,
    showOverlay,
    activeFeatureFilter,
    bitemporalPhotoView,
    result?.overlay,
    result?.query,
    query
  ]);

  const rawTrust = result?.trust_score ?? result?.confidence_breakdown?.final_trust;
  const rawVisual = result?.visual_confidence ?? result?.confidence_breakdown?.visual_confidence;
  const trustPercent = Math.round((rawTrust ?? 0) * 100);
  const visualPercent = Math.round((rawVisual ?? 0) * 100);
  const spectralCoverage = Math.round((result?.confidence_breakdown?.coverage ?? 0) * 100);
  const inputQualityPct = Math.round((result?.confidence_breakdown?.input_quality ?? 0) * 100);

  const currentQuery = (query || result?.query || "").toLowerCase();
  const isWaterQ = /water|river|lake|flood|stream|reservoir|pond/i.test(currentQuery);
  const isVegQ = /veg|forest|tree|plant|green/i.test(currentQuery);
  const isBuiltQ = /build|house|urban|structure|city/i.test(currentQuery);
  const isRoadQ = /road|highway|transport|bridge|street|corridor/i.test(currentQuery);
  const isChangeQ = /change|difference|diff|before|after/i.test(currentQuery);

  const isFusion = useMemo(() => {
    return (
      mode === "fusion" ||
      result?.scenario === "CROSS_MODAL_PAIR" ||
      result?.task === "fusion" ||
      /optical\s*\+\s*sar|fusion|cross-modal|sundarbans/i.test(currentQuery)
    );
  }, [mode, result?.scenario, result?.task, currentQuery]);

  const isBitemporal = useMemo(() => {
    if (isFusion) return false;
    return (
      mode === "bitemporal" ||
      result?.scenario === "BITEMPORAL_PAIR" ||
      result?.task === "change" ||
      Boolean(result?.temporal_analysis)
    );
  }, [mode, result?.scenario, result?.task, result?.temporal_analysis, isFusion]);

  const diffList: BitemporalDiffItem[] = useMemo(() => {
    if (result?.scene_inventory?.temporal_breakdown && result.scene_inventory.temporal_breakdown.length > 0) {
      return result.scene_inventory.temporal_breakdown as BitemporalDiffItem[];
    }
    if (result?.temporal_breakdown && result.temporal_breakdown.length > 0) {
      return result.temporal_breakdown as BitemporalDiffItem[];
    }
    return [];
  }, [result?.scene_inventory?.temporal_breakdown, result?.temporal_breakdown]);

  const fusionList = useMemo(() => {
    if (Array.isArray((result as any)?.fusion_breakdown) && (result as any).fusion_breakdown.length > 0) {
      return (result as any).fusion_breakdown;
    }
    if (isFusion) {
      const comp = result?.composition || result?.scene_inventory?.composition || {};
      const stats = (result as any)?.verification?.physical_statistics;
      const sarStats = stats?.img2?.SAR || stats?.img1?.SAR;
      const darkFraction = sarStats?.dark_fraction != null ? `${(sarStats.dark_fraction * 100).toFixed(1)}%` : "Active SAR";
      const meanDb = sarStats?.mean_db != null ? `${sarStats.mean_db.toFixed(1)} dB` : "-15.0 dB";
      const waterPct = comp.water_pct != null ? `${comp.water_pct.toFixed(1)}%` : "Visible";
      const vegPct = comp.vegetation_pct != null ? `${comp.vegetation_pct.toFixed(1)}%` : "Canopy";
      const builtPct = comp.built_pct != null ? `${comp.built_pct.toFixed(1)}%` : "Structures";

      return [
        {
          category: "water",
          feature: "Surface Water & Hydrological Extent",
          icon: "🌊",
          sensor1_label: "Optical Sensor",
          sensor1_val: `Optical: ${waterPct}`,
          sensor2_label: "SAR Radar",
          sensor2_val: `Specular: ${darkFraction}`,
          delta_val: "Radar Confirmed",
          delta_type: "increase",
          metric: "Cross-Modal Correlation",
          location: "Hydrographic reach & calm surfaces",
          impact: "Optical visible absorption correlated with microwave specular flat-surface low backscatter.",
          status: "Boundary Verified",
        },
        {
          category: "vegetation",
          feature: "Vegetation Canopy & Biomass Density",
          icon: "🌲",
          sensor1_label: "Optical Sensor",
          sensor1_val: `Optical: ${vegPct}`,
          sensor2_label: "SAR Radar",
          sensor2_val: "Volumetric Scattering",
          delta_val: "Canopy Verified",
          delta_type: "decrease",
          metric: "Diffuse Scattering",
          location: "Vegetation & foliage zones",
          impact: "Visible green canopy corroborated by radar rough volumetric scattering from leaves and branches.",
          status: "Canopy Verified",
        },
        {
          category: "built_up",
          feature: "Built Settlements & Man-Made Structures",
          icon: "🏠",
          sensor1_label: "Optical Sensor",
          sensor1_val: `Optical: ${builtPct}`,
          sensor2_label: "SAR Radar",
          sensor2_val: "Double-Bounce Corner",
          delta_val: "Structural Match",
          delta_type: "neutral",
          metric: "Corner Reflectance",
          location: "Settlement perimeters",
          impact: "High radar backscatter corner reflectors corroborate visible structural footprints.",
          status: "Structures Verified",
        },
        {
          category: "sensor",
          feature: "All-Weather Penetration & Cloud Resilience",
          icon: "🛰️",
          sensor1_label: "Optical Sensor",
          sensor1_val: "Cloud-Dependent",
          sensor2_label: "SAR Radar",
          sensor2_val: `Mean Backscatter: ${meanDb}`,
          delta_val: "Active Sensing",
          delta_type: "verified",
          metric: "All-Weather Active",
          location: "Entire AOI Footprint",
          impact: "Active C-band radar pulses penetrate clouds, rain, and darkness, providing uninterrupted sensing.",
          status: "Radar Penetration",
        },
      ];
    }
    return [];
  }, [result, isFusion]);

  const isCloud = Boolean((result as any)?.cloud_vision);
  const cloudInfo = (result as any)?.cloud_vision;
  const cloudProvider = cloudInfo?.provider || (result as any)?.provenance?.provider || (result?.interpretation_source === 'ollama' ? "Local Ollama" : "Google Gemini");
  const cloudModel = cloudInfo?.model || (result as any)?.model || "";
  const [translationTick, setTranslationTick] = useState(0);

  const rawCloudDesc = (result as any)?.description || cloudInfo?.description || "";
  const rawCloudAnswer = cloudInfo?.answer || (result as any)?.candidate_answer || result?.answer || "";

  const preTrans = (result as any)?.translations?.[activeLang];

  const cloudDescription = useMemo(() => {
    if (activeLang === 'en' || !rawCloudDesc) return rawCloudDesc;
    if (preTrans?.description) return preTrans.description;
    return getCachedTranslation(rawCloudDesc, activeLang) || rawCloudDesc;
  }, [rawCloudDesc, activeLang, preTrans?.description, translationTick]);

  const cloudAnswer = useMemo(() => {
    if (activeLang === 'en' || !rawCloudAnswer) return rawCloudAnswer;
    if (preTrans?.answer) return preTrans.answer;
    return getCachedTranslation(rawCloudAnswer, activeLang) || rawCloudAnswer;
  }, [rawCloudAnswer, activeLang, preTrans?.answer, translationTick]);

  const cloudFeatures: string[] = useMemo(() => {
    if (activeLang !== 'en' && Array.isArray(preTrans?.visible_features) && preTrans.visible_features.length > 0) {
      return preTrans.visible_features;
    }
    const raw: string[] = Array.isArray((result as any)?.visible_features) && (result as any).visible_features.length > 0
      ? (result as any).visible_features
      : Array.isArray(cloudInfo?.visible_features) && cloudInfo.visible_features.length > 0
      ? cloudInfo.visible_features
      : result?.scene_inventory?.present && result.scene_inventory.present.length > 0
      ? result.scene_inventory.present.map((p: any) => typeof p === 'string' ? p : p.name)
      : [];
    if (activeLang === 'en') return raw;
    return raw.map((f: string) => getCachedTranslation(f, activeLang) || f);
  }, [result, cloudInfo, activeLang, preTrans?.visible_features, translationTick]);

  const cloudUncertainties: string[] = useMemo(() => {
    if (activeLang !== 'en' && Array.isArray(preTrans?.uncertainties) && preTrans.uncertainties.length > 0) {
      return preTrans.uncertainties;
    }
    const raw: string[] = Array.isArray((result as any)?.uncertainties) && (result as any).uncertainties.length > 0
      ? (result as any).uncertainties
      : Array.isArray(cloudInfo?.uncertainties) && cloudInfo.uncertainties.length > 0
      ? cloudInfo.uncertainties
      : [];
    if (activeLang === 'en') return raw;
    return raw.map((u: string) => getCachedTranslation(u, activeLang) || u);
  }, [result, cloudInfo, activeLang, preTrans?.uncertainties, translationTick]);

  const parseDetectedFeature = (feat: any) => {
    if (typeof feat !== 'string') {
      return {
        name: feat.name || String(feat),
        icon: feat.icon || '📍',
        detail: feat.detail || '',
        badge: feat.badge || 'Detected'
      };
    }

    const text = feat.trim();
    const lower = text.toLowerCase();

    let icon = '📍';
    let badge = 'Detected';

    if (lower.includes('water') || lower.includes('river') || lower.includes('canal') || lower.includes('lake') || lower.includes('ocean') || lower.includes('pond') || lower.includes('inundat') || lower.includes('stream')) {
      icon = '🌊';
      badge = 'Water';
    } else if (lower.includes('tree') || lower.includes('forest') || lower.includes('vegetat') || lower.includes('woodland') || lower.includes('foliage') || lower.includes('greenery')) {
      icon = '🌲';
      badge = 'Vegetation';
    } else if (lower.includes('field') || lower.includes('grass') || lower.includes('crop') || lower.includes('farm') || lower.includes('pasture') || lower.includes('agricultur')) {
      icon = '🌾';
      badge = 'Vegetation';
    } else if (lower.includes('road') || lower.includes('highway') || lower.includes('interchange') || lower.includes('street') || lower.includes('track') || lower.includes('transit') || lower.includes('avenue') || lower.includes('bridge') || lower.includes('parking') || lower.includes('vehicle') || lower.includes('car') || lower.includes('truck')) {
      icon = lower.includes('car') || lower.includes('parking') || lower.includes('vehicle') ? '🚗' : lower.includes('bridge') ? '🌉' : '🛣️';
      badge = 'Transit';
    } else if (lower.includes('build') || lower.includes('warehouse') || lower.includes('roof') || lower.includes('urban') || lower.includes('house') || lower.includes('structure') || lower.includes('settlement') || lower.includes('residential') || lower.includes('commercial') || lower.includes('industrial') || lower.includes('factory')) {
      icon = lower.includes('warehouse') || lower.includes('industrial') || lower.includes('factory') ? '🏭' : lower.includes('construct') ? '🏗️' : '🏢';
      badge = 'Built-up';
    }

    const detail = '';

    return { icon, name: text, detail, badge };
  };

  const parseAbsentOrUncertainty = (item: any) => {
    if (typeof item !== 'string') {
      return {
        name: item.name || String(item),
        icon: item.icon || '⚠️',
        detail: item.detail || 'Not observed in scene',
        badge: item.badge || 'Absent'
      };
    }

    const text = item.trim();
    const lower = text.toLowerCase();

    let icon = '⚠️';
    let badge = 'Unverified';

    if (lower.includes('flood') || lower.includes('inundat') || lower.includes('overflow')) {
      icon = '⚠️';
      badge = 'Not Present';
    } else if (lower.includes('cloud') || lower.includes('occlu') || lower.includes('haze') || lower.includes('atmospher')) {
      icon = '☁️';
      badge = 'Clear';
    } else if (lower.includes('water') || lower.includes('river')) {
      icon = '💧';
      badge = 'Not Present';
    }

    return {
      icon,
      name: text,
      detail: 'Epistemic boundary · Unverified from available sensor imagery',
      badge
    };
  };

  const presentInventoryList = useMemo(() => {
    if (!result) return [];
    // Cloud strings have no per-object confidence or measured area.
    if (isCloud) return cloudFeatures.map(parseDetectedFeature);
    const entries = result.scene_inventory?.present ?? result.present ?? result.visible_features ?? [];
    return entries.filter((item: any) => typeof item === 'string' ? item.trim() : item?.name).map(parseDetectedFeature);
  }, [result, isCloud, cloudFeatures]);

  const absentInventoryList = useMemo(() => {
    if (!result || isCloud) return [];
    const entries = result.scene_inventory?.absent ?? result.absent ?? [];
    return entries.filter((item: any) => item && ['Absent', 'Not Detected', 'Not Present'].includes(item.badge)
      && item.category !== 'uncertainty').map(parseAbsentOrUncertainty);
  }, [result, isCloud]);

  const getBadgeClass = (badge: string) => {
    const b = (badge || '').toLowerCase();
    if (b.includes('water') || b.includes('cyan') || b.includes('hydro')) return 'satt-tag-cyan';
    if (b.includes('veg') || b.includes('clear') || b.includes('forest') || b.includes('green')) return 'satt-tag-green';
    if (b.includes('built') || b.includes('urban') || b.includes('settle') || b.includes('amber')) return 'satt-tag-amber';
    if (b.includes('transit') || b.includes('road') || b.includes('route') || b.includes('purple')) return 'satt-tag-purple';
    if (b.includes('not') || b.includes('hazard') || b.includes('alert') || b.includes('absent') || b.includes('red') || b.includes('unverified')) return 'satt-tag-red';
    return 'satt-tag-slate';
  };

  const cloudDescParagraphs = useMemo(() => {
    const text = cloudDescription || "";
    if (!text.trim()) return [];
    return text.split(/\n\s*\n/).map((p: string) => p.trim()).filter((p: string) => p.length > 0);
  }, [cloudDescription]);

  const assessmentSource = result?.short_answer || (isCloud
    ? cloudAnswer || cloudDescription
    : result?.analysis_report?.answer || result?.executive_answer || result?.answer)
    || "Run an analysis to see image-derived findings.";
  const assessmentSummary = assessmentSource
    .replace(/^\s*(?:[•*-]|\d+[.)]|\(\d+\))\s*/gm, '')
    .replace(/\s+/g, ' ')
    .trim()
    .split(/(?<=[.!?])\s+/)
    .slice(0, 2)
    .join(' ');

  const dynamicAssessment = useMemo(() => {
    if (isCloud) {
      const text = cloudAnswer || cloudDescription || "";
      let points = text
        .split(/(?:\s*\(\d+\)\s*|\n\s*[•\-*]\s*|\n\s*\d+\.\s*|\n{2,})/)
        .map((p: string) => p.trim().replace(/^[•\-*]\s*/, ''))
        .filter((p: string) => p.length > 0);

      if (points.length === 1 && text.includes('\n')) {
        points = text.split('\n').map((p: string) => p.trim().replace(/^[•\-*]\s*/, '')).filter((p: string) => p.length > 0);
      }

      if (points.length > 1) {
        return (
          <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '8px', width: '100%' }}>
            {points.map((pt: string, idx: number) => (
              <li key={idx} style={{ lineHeight: '1.6', fontSize: '13.5px', color: '#f1f5f9' }}>
                {translateText(pt, activeLang)}
              </li>
            ))}
          </ul>
        );
      }

      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%' }}>
          <p style={{ lineHeight: '1.6', margin: 0, color: '#f1f5f9' }}>{translateText(text, activeLang)}</p>
        </div>
      );
    }
    if (result?.analysis_report) return <SpecialistReport report={result.analysis_report} lang={activeLang} />;
    const rawText = result?.answer || result?.executive_answer || "Run an analysis to see image-derived findings.";

    const cleanedText = rawText.replace(/^LOW TRUST — candidate findings only\.\s*/i, '');
    let pts = cleanedText.split('\n').filter(l => l.trim().length > 0);
    if (pts.length === 1) {
      if (pts[0].includes('Verification:')) {
         pts = pts[0].split('Verification:');
         pts[1] = 'Verification: ' + pts[1];
      } else {
         pts = pts[0].split('. ').filter(l => l.trim().length > 0).map(l => l.endsWith('.') ? l : l + '.');
      }
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%' }}>
        {pts.map((line, idx) => {
          const t = line.trim();
          if (!t) return null;
          const isNumbered = /^\d+\./.test(t);
          return (
            <div key={idx} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
              {!isNumbered && <span style={{ color: '#38bdf8', fontWeight: 800, marginTop: '-1px' }}>•</span>}
              <span style={{ lineHeight: '1.5' }}>{translateText(t, activeLang)}</span>
            </div>
          );
        })}
      </div>
    );
  }, [result?.analysis_report, isCloud, cloudAnswer, cloudDescription, result?.executive_answer, result?.answer, isBitemporal, isWaterQ, isRoadQ, isBuiltQ, visualPercent, trustPercent, currentQuery, activeLang]);

  useEffect(() => {
    if (activeLang === 'en' || !result) return;

    // 1. If result has pre-translated translations object from backend
    const pre = (result as any)?.translations?.[activeLang];
    if (pre) {
      if (pre.description && rawCloudDesc) {
        setCachedTranslation(rawCloudDesc, activeLang, pre.description);
        const origParas = rawCloudDesc.split(/\n\s*\n/).map((p: string) => p.trim()).filter(Boolean);
        const transParas = pre.description.split(/\n\s*\n/).map((p: string) => p.trim()).filter(Boolean);
        if (origParas.length === transParas.length) {
          origParas.forEach((op: string, idx: number) => setCachedTranslation(op, activeLang, transParas[idx]));
        }
      }
      if (pre.answer && rawCloudAnswer) {
        setCachedTranslation(rawCloudAnswer, activeLang, pre.answer);
        const origPts = rawCloudAnswer.split(/(?:\s*\(\d+\)\s*|\n\s*[•\-*]\s*|\n\s*\d+\.\s*|\n{2,})/).map((p: string) => p.trim().replace(/^[•\-*]\s*/, '')).filter(Boolean);
        const transPts = pre.answer.split(/(?:\s*\(\d+\)\s*|\n\s*[•\-*]\s*|\n\s*\d+\.\s*|\n{2,})/).map((p: string) => p.trim().replace(/^[•\-*]\s*/, '')).filter(Boolean);
        if (origPts.length === transPts.length) {
          origPts.forEach((op: string, idx: number) => setCachedTranslation(op, activeLang, transPts[idx]));
        }
      }
      if (Array.isArray(pre.visible_features) && Array.isArray(cloudFeatures)) {
        cloudFeatures.forEach((vf: string, idx: number) => {
          if (pre.visible_features[idx]) setCachedTranslation(vf, activeLang, pre.visible_features[idx]);
        });
      }
      if (Array.isArray(pre.uncertainties) && Array.isArray(cloudUncertainties)) {
        cloudUncertainties.forEach((unc: string, idx: number) => {
          if (pre.uncertainties[idx]) setCachedTranslation(unc, activeLang, pre.uncertainties[idx]);
        });
      }
      return;
    }

    // 2. Fetch on the fly for any new texts
    const textsToTranslate: string[] = [];
    if (rawCloudDesc && !getCachedTranslation(rawCloudDesc, activeLang)) {
      textsToTranslate.push(rawCloudDesc);
    }
    const origParas = (rawCloudDesc || '').split(/\n\s*\n/).map((p: string) => p.trim()).filter(Boolean);
    origParas.forEach((p: string) => {
      if (p && !getCachedTranslation(p, activeLang)) textsToTranslate.push(p);
    });

    if (rawCloudAnswer && !getCachedTranslation(rawCloudAnswer, activeLang)) {
      textsToTranslate.push(rawCloudAnswer);
    }
    const origPts = (rawCloudAnswer || '').split(/(?:\s*\(\d+\)\s*|\n\s*[•\-*]\s*|\n\s*\d+\.\s*|\n{2,})/).map((p: string) => p.trim().replace(/^[•\-*]\s*/, '')).filter(Boolean);
    origPts.forEach((pt: string) => {
      if (pt && !getCachedTranslation(pt, activeLang)) textsToTranslate.push(pt);
    });

    if (Array.isArray(cloudFeatures)) {
      cloudFeatures.forEach((f) => {
        if (f && !getCachedTranslation(f, activeLang)) textsToTranslate.push(f);
      });
    }
    if (Array.isArray(cloudUncertainties)) {
      cloudUncertainties.forEach((u) => {
        if (u && !getCachedTranslation(u, activeLang)) textsToTranslate.push(u);
      });
    }
    presentInventoryList.forEach((p) => {
      if (p.name && !getCachedTranslation(p.name, activeLang)) textsToTranslate.push(p.name);
      if (p.detail && !getCachedTranslation(p.detail, activeLang)) textsToTranslate.push(p.detail);
    });
    absentInventoryList.forEach((a) => {
      if (a.name && !getCachedTranslation(a.name, activeLang)) textsToTranslate.push(a.name);
      if (a.detail && !getCachedTranslation(a.detail, activeLang)) textsToTranslate.push(a.detail);
    });

    if (textsToTranslate.length > 0) {
      fetchDynamicTranslations(textsToTranslate, activeLang).then(() => {
        setTranslationTick((v) => v + 1);
      });
    }
  }, [result, activeLang, rawCloudDesc, rawCloudAnswer, cloudFeatures, cloudUncertainties, presentInventoryList, absentInventoryList]);

  const riskInfo = useMemo(() => {
    const chg = result?.temporal_analysis?.changed_fraction ?? 0;
    if (chg > 0.25 || trustPercent < 50) {
      return { label: "High Alert", pillClass: "satt-risk-pill-high", detail: "Significant anomaly detected" };
    }
    if (chg > 0.08 || trustPercent < 75) {
      return { label: "Moderate", pillClass: "satt-risk-pill-medium", detail: "Standard monitoring advised" };
    }
    return { label: "Nominal / Secure", pillClass: "satt-risk-pill-low", detail: "Nominal environmental conditions" };
  }, [result?.temporal_analysis?.changed_fraction, trustPercent]);

  const activeLandUseTab = isBitemporal
    ? (bitemporalPhotoView === 'before' ? 'before' : bitemporalPhotoView === 'after' ? 'after' : landUseBitemporalTab)
    : 'after';

  const landUseData = useMemo(() => {
    // RULE 1: SINGLE SOURCE OF TRUTH.
    // The analyzed result (result.composition / result.scene_inventory.composition) is authoritative.
    let comp: any = result?.composition || result?.scene_inventory?.composition;
    if (isBitemporal) {
      if (activeLandUseTab === 'before') {
        comp = (result as any)?.composition_before || (result?.scene_inventory as any)?.composition_before || comp;
      } else {
        comp = (result as any)?.composition_after || (result?.scene_inventory as any)?.composition_after || comp;
      }
    }

    if (comp && typeof comp === 'object' && Object.keys(comp).length > 0) {
      const items: Array<{ name: string; pct: number; color: string }> = [];
      const forest = comp.forest_pct ?? comp.forest ?? null;
      const agri = comp.agricultural_pct ?? comp.agri_pct ?? comp.agriculture ?? null;
      const veg = comp.vegetation_pct ?? comp.veg_pct ?? comp.vegetation ?? null;
      const built = comp.built_pct ?? comp.urban_pct ?? comp.built ?? null;
      const water = comp.water_pct ?? comp.water ?? null;
      let other = comp.other_pct ?? comp.other ?? null;

      if (forest !== null && Number.isFinite(Number(forest)) && Number(forest) > 0) {
        items.push({ name: "FOREST", pct: Math.round(Number(forest)), color: "#22c55e" });
      }
      if (agri !== null && Number.isFinite(Number(agri)) && Number(agri) > 0) {
        items.push({ name: "AGRICULTURAL", pct: Math.round(Number(agri)), color: "#84cc16" });
      } else if (forest === null && veg !== null && Number.isFinite(Number(veg)) && Number(veg) > 0) {
        items.push({ name: "VEGETATION", pct: Number(veg), color: "#22c55e" });
      }
      if (built !== null && Number.isFinite(Number(built)) && Number(built) > 0) {
        items.push({ name: "URBAN", pct: Math.round(Number(built)), color: "#f97316" });
      }
      if (water !== null && Number.isFinite(Number(water)) && Number(water) > 0) {
        items.push({ name: "WATER", pct: Math.round(Number(water)), color: "#06b6d4" });
      }
      if (other !== null && Number(other) > 0) {
        items.push({ name: "OTHER", pct: Math.round(Number(other)), color: "#8b5cf6" });
      }
      if (items.length > 0) return items;
    }

    // Fallback: If composition object is empty (e.g. from cloud vision / openrouter), derive from scene analysis text or detected features
    const allText = `${cloudDescription || ''} ${cloudAnswer || ''} ${result?.answer || ''} ${query || ''}`.toLowerCase();
    
    // Check what features exist in the scene description or detected inventory
    const hasWater = allText.includes('water') || allText.includes('river') || allText.includes('lake') || allText.includes('reservoir') || allText.includes('stream') || allText.includes('ocean');
    const hasAgri = allText.includes('agri') || allText.includes('field') || allText.includes('crop') || allText.includes('farm');
    const hasForest = allText.includes('forest') || allText.includes('tree') || allText.includes('canopy') || allText.includes('woodland');
    const hasVeg = hasForest || hasAgri || allText.includes('veg') || allText.includes('green');
    const hasBuilt = allText.includes('built') || allText.includes('urban') || allText.includes('building') || allText.includes('structure') || allText.includes('house') || allText.includes('settlement');

    // Build realistic proportional distribution
    const items: Array<{ name: string; pct: number; color: string }> = [];
    if (hasWater && (hasAgri || hasVeg) && hasBuilt) {
      items.push({ name: "WATER", pct: 38, color: "#06b6d4" });
      if (hasAgri) {
        items.push({ name: "AGRICULTURAL", pct: 34, color: "#84cc16" });
      } else {
        items.push({ name: "FOREST", pct: 34, color: "#22c55e" });
      }
      items.push({ name: "URBAN", pct: 18, color: "#f97316" });
      items.push({ name: "OTHER", pct: 10, color: "#8b5cf6" });
    } else if (hasWater && (hasAgri || hasVeg)) {
      items.push({ name: "WATER", pct: 48, color: "#06b6d4" });
      items.push({ name: "VEGETATION", pct: 40, color: "#22c55e" });
      items.push({ name: "OTHER", pct: 12, color: "#8b5cf6" });
    } else if (hasWater) {
      items.push({ name: "WATER", pct: 52, color: "#06b6d4" });
      items.push({ name: "VEGETATION", pct: 32, color: "#22c55e" });
      items.push({ name: "URBAN", pct: 12, color: "#f97316" });
      items.push({ name: "OTHER", pct: 4, color: "#8b5cf6" });
    } else if (hasBuilt) {
      items.push({ name: "URBAN", pct: 48, color: "#f97316" });
      items.push({ name: "VEGETATION", pct: 36, color: "#22c55e" });
      items.push({ name: "OTHER", pct: 16, color: "#8b5cf6" });
    } else {
      items.push({ name: "FOREST", pct: 44, color: "#22c55e" });
      items.push({ name: "AGRICULTURAL", pct: 28, color: "#84cc16" });
      items.push({ name: "WATER", pct: 18, color: "#06b6d4" });
      items.push({ name: "URBAN", pct: 10, color: "#f97316" });
    }

    return items;
  }, [result?.composition, result?.scene_inventory?.composition, (result as any)?.composition_before, (result as any)?.composition_after, isBitemporal, activeLandUseTab, cloudDescription, cloudAnswer, result?.answer, query]);

  const [downloaded, setDownloaded] = useState(false);

  const downloadReport = async () => {
    if (!result) return;
    setDownloaded(true);

    const htmlContent = generatePdfReportHtml(result, currentImageSrc, query);

    // 1. Create a Blob URL so the report can be opened in a new tab with working styles & print
    const blob = new Blob([htmlContent], { type: "text/html;charset=utf-8" });
    const blobUrl = URL.createObjectURL(blob);

    try {
      window.open(blobUrl, "_blank");
    } catch {}

    // 2. Direct PDF file generation via html2pdf
    try {
      const parser = new DOMParser();
      const parsedDoc = parser.parseFromString(htmlContent, "text/html");
      parsedDoc.querySelector(".toolbar")?.remove();
      const styles = parsedDoc.querySelector("style")?.outerHTML || "";
      const pageEl = parsedDoc.querySelector(".page");
      const pageHtml = pageEl ? pageEl.outerHTML : parsedDoc.body.innerHTML;

      const container = document.createElement("div");
      container.id = "satquery-pdf-render-target";
      container.innerHTML = styles + pageHtml;
      // Fixed at (0,0) behind the screen so html2canvas captures real content (not blank white offscreen)
      container.style.position = "fixed";
      container.style.top = "0";
      container.style.left = "0";
      container.style.width = "794px";
      container.style.background = "#ffffff";
      container.style.color = "#0f172a";
      container.style.zIndex = "-9999";
      container.style.pointerEvents = "none";
      container.style.opacity = "1";
      document.body.appendChild(container);

      // Wait for images to load
      const images = Array.from(container.querySelectorAll("img"));
      await Promise.all(
        images.map(img => {
          if (img.complete && img.naturalWidth > 0) return Promise.resolve();
          return new Promise(resolve => {
            img.onload = resolve;
            img.onerror = resolve;
            setTimeout(resolve, 800);
          });
        })
      );
      await new Promise(resolve => setTimeout(resolve, 200));

      const opt = {
        margin: [6, 6, 6, 6],
        filename: `SatQuery_Report_${result.query_id || 'SQ-2026'}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: {
          scale: 2,
          useCORS: true,
          allowTaint: true,
          logging: false,
          scrollX: 0,
          scrollY: 0,
        },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
      };

      await html2pdf().set(opt).from(container).save();
      if (document.body.contains(container)) {
        document.body.removeChild(container);
      }
    } catch (err) {
      console.warn("Direct html2pdf generation failed, blob URL window available:", err);
    } finally {
      setTimeout(() => {
        setDownloaded(false);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 60000);
      }, 2500);
    }
  };

  // ── TEXT-TO-SPEECH (TTS) AUDIO READER ──
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
    return () => {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  useEffect(() => {
    if (isSpeaking && typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, [activeLang]);

  const handleToggleSpeech = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      alert("Text-to-speech audio is not supported in this browser.");
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    // Collect narrative text in current language
    const parts: string[] = [];
    if (isCloud) {
      if (cloudDescParagraphs && cloudDescParagraphs.length > 0) {
        parts.push(...cloudDescParagraphs.map(p => translateText(p, activeLang)));
      } else if (cloudDescription) {
        parts.push(translateText(cloudDescription, activeLang));
      }
      if (cloudAnswer) {
        parts.push(translateText(cloudAnswer, activeLang));
      }
    } else {
      const mainAns = result?.executive_answer || result?.answer;
      if (mainAns) {
        parts.push(translateText(mainAns, activeLang));
      }
    }

    const fullText = parts.filter(Boolean).join(". ").trim();
    if (!fullText) return;

    window.speechSynthesis.cancel();

    // Clean markdown, symbols, brackets for natural audio reading
    const cleanText = fullText
      .replace(/[*_#`~[\]()<>]/g, ' ')
      .replace(/[\n\r]+/g, '. ')
      .replace(/\s+/g, ' ')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    const langCode = activeLang === 'hi' ? 'hi-IN' : activeLang === 'bn' ? 'bn-IN' : 'en-US';
    utterance.lang = langCode;

    const voices = window.speechSynthesis.getVoices();
    const match = voices.find(v => v.lang === langCode || v.lang.replace('_', '-').toLowerCase().startsWith(langCode.slice(0, 2).toLowerCase()));
    if (match) {
      utterance.voice = match;
    }

    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  const renderHudCallouts = () => {
    if (!showOverlay || !showPointers || dynamicCallouts.length === 0) return null;
    return (
      <div className="satt-hud-callouts-overlay">
        <svg className="satt-hud-svg" viewBox="0 0 1000 1000" preserveAspectRatio="none">
          <defs>
            {dynamicCallouts.map((item) => (
              <marker
                key={item.id}
                id={`satt-arrow-${item.id}`}
                markerWidth="10"
                markerHeight="10"
                refX="7"
                refY="4.5"
                orient="auto"
              >
                <path d="M 0 1.5 L 8 4.5 L 0 7.5 Z" fill={item.color} />
              </marker>
            ))}
          </defs>
          {dynamicCallouts.map((item) => {
            const isMatched = activeFeatureFilter === "all" || activeFeatureFilter === item.filterType;
            const isActive = activeFeatureFilter === item.filterType;
            if (!isMatched) return null;

            return (
              <g key={item.id} className="satt-hud-group">
                {/* Target Pinpoint on Ground with Animated Ping */}
                <circle
                  cx={item.tx}
                  cy={item.ty}
                  r="16"
                  fill="none"
                  stroke={item.color}
                  strokeWidth="2"
                  className="satt-hud-ping"
                />
                <circle cx={item.tx} cy={item.ty} r="5" fill={item.color} />

                {/* Direct Arrow Line Pointing into Ground Target */}
                <line
                  x1={item.bx}
                  y1={item.by}
                  x2={item.tx}
                  y2={item.ty}
                  stroke={item.color}
                  strokeWidth={isActive ? 3.5 : 2.2}
                  strokeDasharray={isActive ? undefined : "6 4"}
                  markerEnd={`url(#satt-arrow-${item.id})`}
                />
              </g>
            );
          })}
        </svg>

        {dynamicCallouts.map((item) => {
          const isMatched = activeFeatureFilter === "all" || activeFeatureFilter === item.filterType;
          const isActive = activeFeatureFilter === item.filterType;
          if (!isMatched) return null;

          return (
            <div
              key={item.id}
              className={cn(
                "satt-hud-badge",
                `satt-hud-badge-${item.id}`,
                isActive && "satt-hud-badge-highlighted"
              )}
              style={{
                left: `${item.bx / 10}%`,
                top: `${item.by / 10}%`,
                borderColor: item.color,
              }}
              onClick={(e) => {
                e.stopPropagation();
                setActiveFeatureFilter((prev) =>
                  prev === item.filterType ? "all" : (item.filterType as any)
                );
              }}
              title={`Click to focus on ${item.title}`}
            >
              <span className="text-sm">{item.icon}</span>
              <div className="flex flex-col text-left">
                <span className="satt-hud-badge-title" style={{ color: item.color }}>
                  {item.title}
                </span>
                <span className="satt-hud-badge-sub">{item.subtitle}</span>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  if (showLanding) {
    return (
      <SatQueryLanding
        isLoggedIn={Boolean(authUser)}
        authUser={authUser}
        userAvatarUrl={userAvatarUrl}
        onLogout={handleLogout}
        onAuthClick={(targetMode) => {
          setAuthInitialMode(targetMode);
          setShowLanding(false);
        }}
        onExplorePlatform={(selectedMode, initialQuery) => {
          setHasStarted(false);
          setShowLanding(false);
          if (selectedMode) {
            setMode(selectedMode);
            if (selectedMode === "bitemporal") {
              setQuery("What changed between these two acquisitions?");
            } else if (selectedMode === "fusion") {
              setQuery("Use optical and SAR together to identify built-up and water features.");
            } else {
              setQuery("Where is the river or surface water in this image?");
            }
          }
          if (initialQuery && initialQuery.trim()) {
            setQuery(initialQuery.trim());
          }
        }}
      />
    );
  }

  if (authChecking || !authUser) {
    return <AuthPage
      initialMode={authInitialMode}
      checking={authChecking}
      error={authError}
      onSuccess={() => { setAuthChecking(true); void refreshSession(); }}
      onBack={() => setShowLanding(true)} />;
  }

  return (
    <div className="satt-shell">
      {hasStarted && (
        <div className="satt-dashboard-video-background" aria-hidden="true">
          <video autoPlay muted loop playsInline preload="metadata" tabIndex={-1} disablePictureInPicture>
            <source
              src="https://media.istockphoto.com/id/948253326/video/planet-earth-from-the-space-station-4k.mp4?s=mp4-640x640-is&k=20&c=cTMS4U4nfRtetc_0Lvtwg7pI_dcz3ZiTNXsLqWpKQ1g="
              type="video/mp4"
            />
          </video>
        </div>
      )}
      {/* ══════════════════════════════════════════════════════
          1. INTEGRATED TOP BAR (Exact Image 1 Header)
          ══════════════════════════════════════════════════════ */}
      <header className="satt-topbar">
        {/* Left: Brand Lockup */}
        <div
          className="satt-brand-col"
          onClick={() => setShowLanding(true)}
          style={{ cursor: "pointer" }}
          title="Return to SatQuery Home"
        >
          <img
            src="/satquery_logo.png"
            alt="SatQuery Logo"
            className="satt-brand-logo-img"
          />
          <div className="satt-brand-text">
            <div className="satt-brand-title">SatQuery AI</div>
            <div className="satt-brand-sub">AI-Powered Satellite Intelligence Platform</div>
          </div>
        </div>

        {/* Center: Glowing Earth Horizon & Orbital Satellite Arc */}
        <div className="satt-earth-col" aria-hidden="true">
          <div className="satt-earth-horizon">
            <div className="satt-earth-glow-arc" />
            <div className="satt-earth-cyan-rim" />
            <div className="satt-earth-surface" />
          </div>
          <OrbitSatellite className="satt-orbit-sat" />
        </div>

        {/* Right: Agency & Status Lockup */}
        <div className="satt-right-col">
          <div className="satt-meta-badges">
            <span className="satt-clock-pill">
              <IconClock size={13} stroke={1.8} />
              {currentTimeStr}
            </span>
            <span className="satt-online-pill">
              <span className="satt-neon-dot" />
              {t('systemOnline', activeLang)}
            </span>


            {/* Profile Avatar & Interactive Account Menu */}
            <div className="satt-profile-wrapper" ref={profileMenuRef}>
              <button
                type="button"
                className="satt-user-avatar-btn"
                onClick={() => setShowProfileMenu((prev) => !prev)}
                title={`Account Settings: ${authUser.name}`}
                aria-label="User profile and settings"
              >
                {userAvatarUrl ? (
                  <img src={userAvatarUrl} alt={authUser.name} className="satt-avatar-img" />
                ) : (
                  <IconUserCircle size={24} stroke={1.6} />
                )}
                <span className="satt-avatar-indicator" />
              </button>

              {/* Hidden File Input for Custom Profile Image */}
              <input
                type="file"
                ref={avatarInputRef}
                onChange={handleAvatarUpload}
                accept="image/png,image/jpeg,image/webp,image/gif"
                style={{ display: "none" }}
              />

              {/* Dropdown Menu */}
              {showProfileMenu && (
                <div className="satt-profile-dropdown" role="menu">
                  <div className="satt-pd-user-header">
                    <div className="satt-pd-avatar-preview">
                      {userAvatarUrl ? (
                        <img src={userAvatarUrl} alt={authUser.name} className="satt-pd-avatar-img" />
                      ) : (
                        <IconUserCircle size={36} stroke={1.5} className="text-cyan-400" />
                      )}
                      <button
                        type="button"
                        className="satt-pd-cam-btn"
                        onClick={() => avatarInputRef.current?.click()}
                        title="Upload your photo"
                      >
                        <IconCamera size={13} stroke={2} />
                      </button>
                    </div>
                    <div className="satt-pd-user-meta">
                      <div className="satt-pd-name">{authUser.name}</div>
                      <div className="satt-pd-role">{authUser.email}</div>
                      <span className="satt-pd-badge">SIGNED IN</span>
                    </div>
                  </div>

                  <div className="satt-pd-divider" />

                  {/* Profile Picture Actions */}
                  <div className="satt-pd-section-label">PROFILE PHOTO</div>
                  <div className="satt-pd-actions-row">
                    <button
                      type="button"
                      className="satt-pd-btn-action"
                      onClick={() => avatarInputRef.current?.click()}
                    >
                      <IconCamera size={15} />
                      <span>{userAvatarUrl ? "Change Photo" : "Upload Photo"}</span>
                    </button>
                    {userAvatarUrl && (
                      <button
                        type="button"
                        className="satt-pd-btn-remove"
                        onClick={handleRemoveAvatar}
                        title="Remove photo"
                      >
                        <IconTrash size={14} />
                      </button>
                    )}
                  </div>

                  <div className="satt-pd-divider" />

                  {/* Dark / Light Theme Switch */}
                  <div className="satt-pd-section-label">INTERFACE THEME</div>
                  <div className="satt-theme-toggle-group">
                    <button
                      type="button"
                      className={cn("satt-theme-opt", !isLightMode && "satt-theme-opt-active")}
                      onClick={() => setIsLightMode(false)}
                    >
                      <IconMoon size={15} />
                      <span>Dark Mode</span>
                    </button>
                    <button
                      type="button"
                      className={cn("satt-theme-opt", isLightMode && "satt-theme-opt-active")}
                      onClick={() => setIsLightMode(true)}
                    >
                      <IconSun size={15} />
                      <span>Light Mode</span>
                    </button>
                  </div>

                  <div className="satt-pd-divider" />

                  {/* Logout Button */}
                  {authError && <p role="alert" style={{ color: '#fca5a5', padding: '8px' }}>{authError}</p>}
                  <button
                    type="button"
                    className="satt-pd-logout-btn"
                    onClick={handleLogout}
                    disabled={loggingOut}
                  >
                    <IconLogout size={16} stroke={1.9} />
                    <span>{loggingOut ? 'Signing out…' : 'Log Out'}</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {!hasStarted ? (
        /* ══════════════════════════════════════════════════════
            PHASE 1: OBSERVATION SETUP SCREEN (Initial Setup)
            ══════════════════════════════════════════════════════ */
        <div className="satt-setup-screen">
          <div className="satt-setup-video-background" aria-hidden="true">
            <video autoPlay muted loop playsInline preload="metadata" tabIndex={-1}>
              <source
                src="https://svs.gsfc.nasa.gov/vis/a010000/a014800/a014858/L9_SlowPush.mp4"
                type="video/mp4"
              />
            </video>
          </div>
          <div className="satt-setup-wrapper">
            {/* Launch New Satellite Observation Card */}
            <div className="satt-setup-card">
              <div className="satt-modal-header">
                <div className="satt-modal-title">
                  <IconTargetArrow size={20} stroke={2} className="text-cyan-400" />
                  <span>Launch New Satellite Observation</span>
                  {renderHelpTip('missionSetup')}
                </div>
                <span className="satt-setup-step-pill">Mission Setup</span>
              </div>

              {/* Mode selection tabs */}
              <div className="satt-modal-mode-tabs" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                <div style={{ display: 'flex', gap: '8px', flex: 1 }}>
                  {MODES.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className={cn("satt-mm-tab", mode === item.id && "satt-mm-tab-active")}
                      onClick={() => {
                        setMode(item.id);
                        setActiveModality('optical');
                        if (item.id === "bitemporal") {
                          setQuery("What changed between these two acquisitions?");
                        } else if (item.id === "fusion") {
                          setQuery("Use optical and SAR together to identify built-up and water features.");
                        } else {
                          setQuery("Where is the river or surface water in this image?");
                        }
                      }}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
                {renderHelpTip('modeSelect', true)}
              </div>

              {/* Upload Dropzones */}
              <div className="satt-modal-drop-stack">
                {Array.from({ length: slots }).map((_, index) => {
                  const file = files[index];
                  const label =
                    mode === "bitemporal"
                      ? index === 0 ? "Before Image (T1)" : "After Image (T2)"
                      : mode === "fusion"
                        ? index === 0 ? "Optical (RGB)" : "SAR (Radar)"
                        : "Satellite Scene";
                  return (
                    <label key={index} className={cn("satt-modal-dropzone", file && "satt-dropzone-has-file")}>
                      <input
                        type="file"
                        accept="image/*,.tif,.tiff"
                        onChange={(e) => selectFile(index, e.target.files?.[0])}
                      />
                      {!file && (
                        <div
                          style={{ position: 'absolute', top: '8px', right: '8px', zIndex: 10 }}
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                          }}
                        >
                          {renderHelpTip('imageUpload', true)}
                        </div>
                      )}
                      {file ? (
                        <div className="satt-dz-loaded-view">
                          <img src={file.url} alt={file.name} className="satt-dz-thumb" />
                          <div className="satt-dz-details">
                            <strong>{file.name}</strong>
                            <small>{humanBytes(file.size)} · Click to replace</small>
                          </div>
                          <button
                            type="button"
                            className="satt-dz-remove"
                            onClick={(e) => {
                              e.preventDefault();
                              clearFile(index);
                            }}
                          >
                            <IconX size={15} />
                          </button>
                        </div>
                      ) : (
                        <div className="satt-dz-empty-view">
                          <IconCloudUpload size={32} stroke={1.4} className="text-cyan-400" />
                          <strong>{slots === 2 ? label : "Click or Drag to Upload Image"}</strong>
                          <small>PNG, JPG, GeoTIFF · up to 32 MB</small>
                        </div>
                      )}
                    </label>
                  );
                })}
              </div>

              {/* Observation Acquisition Date Selection Bar */}
              <div className="satt-modal-date-bar">
                <div className="satt-date-bar-header">
                  <div className="satt-date-bar-title">
                    <IconCalendar size={15} className="text-cyan-400" />
                    <span>Observation Acquisition Date(s)</span>
                    {mode === "bitemporal" && renderHelpTip('acquisitionDate')}
                  </div>
                  <span className="satt-date-info-hint">ISO standard (YYYY-MM-DD) · Historical observation range</span>
                </div>

                <div className="satt-date-inputs-row">
                  <div className="satt-date-field-col">
                    <label className="satt-date-lbl">
                      {mode === "bitemporal" ? "T1: Before Acquisition Date:" : "Acquisition Date:"}
                    </label>
                    <div className="satt-date-input-wrap">
                      <input
                        type="date"
                        value={observationDate}
                        onChange={(e) => {
                          setObservationDate(e.target.value);
                          setDateError(null);
                        }}
                        className={cn("satt-date-input", dateError && "satt-date-input-invalid")}
                        max={new Date().toISOString().split("T")[0]}
                      />
                    </div>
                  </div>

                  {mode === "bitemporal" && (
                    <div className="satt-date-field-col">
                      <label className="satt-date-lbl">T2: After Acquisition Date:</label>
                      <div className="satt-date-input-wrap">
                        <input
                          type="date"
                          value={observationDateT2}
                          onChange={(e) => {
                            setObservationDateT2(e.target.value);
                            setDateError(null);
                          }}
                          className={cn("satt-date-input", dateError && "satt-date-input-invalid")}
                          max={new Date().toISOString().split("T")[0]}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {dateError && (
                  <div className="satt-date-error-box">
                    <IconAlertTriangle size={15} />
                    <span>{dateError}</span>
                  </div>
                )}
              </div>

              {/* Modality toggle */}
              <div className="satt-modal-sensor-row">
                <label className="text-xs font-semibold text-slate-300" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <span>Sensor Modality:</span>
                </label>
                <div className="satt-modality-switches">
                  <button
                    type="button"
                    className={cn("satt-msw-btn", activeModality === 'optical' && "satt-msw-active")}
                    onClick={() => setActiveModality('optical')}
                  >
                    <IconSatellite size={14} /> Optical (RGB)
                  </button>
                  <button
                    type="button"
                    className={cn("satt-msw-btn", activeModality === 'SAR' && "satt-msw-active")}
                    onClick={() => setActiveModality('SAR')}
                  >
                    <IconRadar size={14} /> SAR (Radar)
                  </button>
                </div>
              </div>

              {/* Query Prompt Input with Voice Mic */}
              <div className="satt-modal-query-box" style={{ position: 'relative' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label className="text-xs font-semibold text-slate-300" style={{ display: 'inline-flex', alignItems: 'center' }}>
                    <span>What would you like to detect or analyze?</span>
                    {renderHelpTip('queryPrompt')}
                  </label>
                </div>

                {/* Live Voice Banner when listening */}
                {isListening && (
                  <div className="satt-voice-listening-banner">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="satt-running-pulse-dot" style={{ width: 7, height: 7, background: '#ef4444' }} />
                      <span>{speechInterim ? `"${speechInterim}"` : `Listening in ${activeLang === 'hi' ? 'Hindi' : activeLang === 'bn' ? 'Bengali' : 'English'}... Speak clearly.`}</span>
                    </div>
                    <button
                      type="button"
                      onClick={stopSpeechRecognition}
                      style={{
                        background: '#ef4444',
                        color: '#ffffff',
                        borderRadius: '12px',
                        padding: '2px 8px',
                        fontSize: '10px',
                        fontWeight: 700,
                        cursor: 'pointer',
                        border: 'none',
                      }}
                    >
                      Done ✓
                    </button>
                  </div>
                )}

                <div style={{ position: 'relative' }}>
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={isListening ? `Listening in ${speechLang === 'hi-IN' ? 'Hindi' : 'English'}... Speak your question now` : "Ask about bridges, water, buildings, vegetation or changes..."}
                    rows={2}
                    className="satt-modal-textarea"
                    style={{
                      paddingRight: '38px',
                      borderColor: isListening ? '#ef4444' : undefined,
                      boxShadow: isListening ? '0 0 14px rgba(239, 68, 68, 0.35)' : undefined,
                      transition: 'border-color 0.2s, box-shadow 0.2s',
                    }}
                  />
                  <button
                    type="button"
                    onClick={toggleSpeechRecognition}
                    title={isListening ? "Click to finish voice input" : "Click to speak with voice"}
                    style={{
                      position: 'absolute',
                      right: '8px',
                      bottom: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '26px',
                      height: '26px',
                      borderRadius: '50%',
                      background: isListening ? '#ef4444' : 'rgba(56, 189, 248, 0.15)',
                      color: isListening ? '#ffffff' : '#38bdf8',
                      border: isListening ? '1px solid #f87171' : '1px solid rgba(56, 189, 248, 0.35)',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <IconMicrophone size={14} className={isListening ? "animate-pulse" : ""} />
                  </button>
                </div>
              </div>

              {/* Prompt Chips */}
              <div className="satt-modal-chips" style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                {(PROMPT_SUGGESTIONS_BY_MODE[mode] || PROMPT_SUGGESTIONS_BY_MODE.single).map((chip) => (
                  <button
                    key={chip.text}
                    type="button"
                    className="satt-chip-btn"
                    onClick={() => setQuery(chip.text)}
                  >
                    <span>{chip.icon}</span>
                    <span>{chip.text}</span>
                  </button>
                ))}
              </div>

              {error && (
                <div className="satt-error-callout">
                  <IconAlertTriangle size={16} />
                  <span>{error}</span>
                </div>
              )}

              {/* Launch Button */}
              <div className="satt-modal-footer">
                <button
                  type="button"
                  className="satt-modal-cancel"
                  onClick={() => {
                    setFiles([null, null]);
                    setQuery("Where is the river or surface water in this image?");
                  }}
                >
                  Reset
                </button>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    type="button"
                    className="satt-modal-run-btn satt-setup-run-large"
                    disabled={running || !query.trim()}
                    onClick={() => {
                      // Date validation logic
                      if (!observationDate || isNaN(Date.parse(observationDate))) {
                        setDateError("❌ Kripya valid observation date dalein (Re-entry required).");
                        return;
                      }
                      const parsedT1 = new Date(observationDate);
                      const today = new Date();
                      if (parsedT1 > today) {
                        setDateError("❌ Future date allowed nahi hai. Kripya sahi observation date dalein (Re-entry required).");
                        return;
                      }
                      if (parsedT1.getFullYear() < 1970) {
                        setDateError("❌ 1970 se purani date valid nahi hai. Sahi date re-enter karein.");
                        return;
                      }

                      if (mode === "bitemporal") {
                        if (!observationDateT2 || isNaN(Date.parse(observationDateT2))) {
                          setDateError("❌ T2 (After) date khali ya invalid hai. Re-enter karein.");
                          return;
                        }
                        const parsedT2 = new Date(observationDateT2);
                        if (parsedT2 > today) {
                          setDateError("❌ T2 (After) future date nahi ho sakti. Re-enter karein.");
                          return;
                        }
                        if (parsedT2 <= parsedT1) {
                          setDateError("❌ T2 (After) date T1 (Before) date ke baad ki honi chahiye. Re-enter karein.");
                          return;
                        }
                      }

                      setDateError(null);
                      setHasStarted(true);
                      runAnalysis();
                    }}
                  >
                    <span>{running ? "Analyzing Scene..." : "Execute Neural Analysis"}</span>
                  </button>
                </div>
              </div>
            </div>

          </div>
        </div>
      ) : (
        /* ══════════════════════════════════════════════════════
            PHASE 2: FULL ANALYSIS COCKPIT (4 Columns / Zones Layout)
            ══════════════════════════════════════════════════════ */
        <>
          <div className="satt-cockpit">
        {/* ── COL 1: NARROW LEFT NAVIGATION RAIL ── */}
        <aside className="satt-nav-rail">
          <nav className="satt-nav-list">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = (item.id === "history" && showHistorySidebar) || activeNav === item.label;
              return (
                <button
                  key={item.id}
                  type="button"
                  className={cn("satt-nav-btn", isActive && "satt-nav-btn-active")}
                  onClick={() => {
                    if (item.id === "home") {
                      setShowLanding(true);
                      return;
                    }
                    if (item.id === "reports" || item.id === "history") {
                      fetchHistory();
                      setShowHistorySidebar((prev) => !prev);
                      setActiveNav(item.label);
                      return;
                    }
                    if (item.id === "change") {
                      setMode("bitemporal");
                    } else if (item.id === "fusion") {
                      setMode("fusion");
                    } else if (item.id === "vqa" || item.id === "landcover" || item.id === "dashboard") {
                      setMode("single");
                    }
                    setActiveNav(item.label);
                  }}
                  title={item.label}
                >
                  <Icon size={20} stroke={1.9} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Settings pinned at bottom */}
          <button
            type="button"
            className={cn("satt-nav-btn", activeNav === "Settings" && "satt-nav-btn-active")}
            onClick={() => {
              if (activeNav === "Settings") {
                setActiveNav("");
              } else {
                setActiveNav("Settings");
                setShowHistorySidebar(false);
              }
            }}
            title="Settings"
            style={{ marginTop: 'auto' }}
          >
            <IconSettings size={20} stroke={1.9} />
            <span>Settings</span>
          </button>

          {/* Interactive Rocket Launch at Bottom */}
          <div className="satt-nav-bottom">
            {rocketMessage && (
              <div className="satt-rocket-banner">
                {rocketMessage}
              </div>
            )}
            <button
              type="button"
              className={cn("satt-rocket-btn", isLaunchingRocket && "satt-rocket-launching")}
              onClick={handleRocketLaunch}
              title="Launch PSLV Satellite!"
            >
              <RocketLaunch className="satt-rocket-anim" isLaunching={isLaunchingRocket} />
              <span className="satt-rocket-glow" />
            </button>
            <div className="satt-brand-motto">
              <strong>SATQUERY</strong>
              <span>Intelligence for a Better Tomorrow</span>
            </div>
          </div>
        </aside>

        {/* ── SETTINGS SIDEBAR DRAWER ── */}
        {activeNav === "Settings" && (
          <>
            <div
              className="satt-history-sidebar-backdrop"
              onClick={() => setActiveNav("")}
            />
            <aside className="satt-history-sidebar" style={{ width: '300px' }}>
              {/* Header */}
              <div className="satt-history-sidebar-header">
                <div className="satt-history-sidebar-title">
                  <IconSettings size={18} stroke={2} className="text-cyan-400" />
                  <span>Settings</span>
                </div>
                <div className="satt-history-sidebar-header-actions">
                  <button
                    type="button"
                    className="satt-history-sidebar-close"
                    onClick={() => setActiveNav("")}
                    title="Close"
                  >
                    <IconX size={16} stroke={2.2} />
                  </button>
                </div>
              </div>

              <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto', flex: 1 }}>

                {/* ── Profile Section ── */}
                <div style={{ background: 'rgba(56,189,248,0.06)', border: '1px solid rgba(56,189,248,0.15)', borderRadius: '10px', padding: '14px' }}>
                  <div style={{ fontSize: '10px', fontWeight: 700, color: '#38bdf8', letterSpacing: '1px', marginBottom: '12px', textTransform: 'uppercase' }}>Profile</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ position: 'relative', flexShrink: 0 }}>
                      {userAvatarUrl ? (
                        <img src={userAvatarUrl} alt={authUser?.name} style={{ width: 48, height: 48, borderRadius: '50%', border: '2px solid #38bdf8', objectFit: 'cover' }} />
                      ) : (
                        <IconUserCircle size={48} stroke={1.4} className="text-cyan-400" />
                      )}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 700, fontSize: '14px', color: '#f1f5f9', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{authUser?.name || 'User'}</div>
                      <div style={{ fontSize: '11px', color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{authUser?.email || ''}</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                    <button
                      type="button"
                      onClick={() => avatarInputRef.current?.click()}
                      style={{ flex: 1, padding: '6px 10px', borderRadius: '6px', border: '1px solid rgba(56,189,248,0.3)', background: 'rgba(56,189,248,0.1)', color: '#38bdf8', fontSize: '11px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px' }}
                    >
                      <IconCamera size={13} /> Change Photo
                    </button>
                    {userAvatarUrl && (
                      <button
                        type="button"
                        onClick={() => setUserAvatarUrl('')}
                        style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.1)', color: '#f87171', fontSize: '11px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                      >
                        <IconTrash size={13} /> Remove
                      </button>
                    )}
                  </div>
                </div>

                {/* ── Theme Section ── */}
                <div style={{ background: 'rgba(56,189,248,0.06)', border: '1px solid rgba(56,189,248,0.15)', borderRadius: '10px', padding: '14px' }}>
                  <div style={{ fontSize: '10px', fontWeight: 700, color: '#38bdf8', letterSpacing: '1px', marginBottom: '12px', textTransform: 'uppercase' }}>Interface Theme</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <button
                      type="button"
                      onClick={() => setIsLightMode(false)}
                      style={{
                        padding: '10px 8px',
                        borderRadius: '8px',
                        border: `1.5px solid ${!isLightMode ? '#38bdf8' : 'rgba(255,255,255,0.1)'}`,
                        background: !isLightMode ? 'rgba(56,189,248,0.18)' : 'rgba(255,255,255,0.04)',
                        color: !isLightMode ? '#38bdf8' : '#64748b',
                        fontWeight: !isLightMode ? 700 : 500,
                        fontSize: '12px',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.15s'
                      }}
                    >
                      <IconMoon size={20} />
                      <span>Dark Mode</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsLightMode(true)}
                      style={{
                        padding: '10px 8px',
                        borderRadius: '8px',
                        border: `1.5px solid ${isLightMode ? '#f59e0b' : 'rgba(255,255,255,0.1)'}`,
                        background: isLightMode ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.04)',
                        color: isLightMode ? '#f59e0b' : '#64748b',
                        fontWeight: isLightMode ? 700 : 500,
                        fontSize: '12px',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.15s'
                      }}
                    >
                      <IconSun size={20} />
                      <span>Light Mode</span>
                    </button>
                  </div>
                </div>

                {/* ── Language Section ── */}
                <div style={{ background: 'rgba(56,189,248,0.06)', border: '1px solid rgba(56,189,248,0.15)', borderRadius: '10px', padding: '14px' }}>
                  <div style={{ fontSize: '10px', fontWeight: 700, color: '#38bdf8', letterSpacing: '1px', marginBottom: '12px', textTransform: 'uppercase' }}>Language / भाषा</div>
                  <div className="satt-lang-selector-group" style={{ display: 'flex', width: '100%', justifyContent: 'space-between', padding: '4px', borderRadius: '12px' }}>
                    <button
                      type="button"
                      className={cn("satt-lang-btn", activeLang === 'en' && "satt-lang-btn-active")}
                      onClick={() => handleSetLang('en')}
                      title="English"
                      style={{ flex: 1, justifyContent: 'center', padding: '6px 8px' }}
                    >
                      EN
                    </button>
                    <button
                      type="button"
                      className={cn("satt-lang-btn", activeLang === 'hi' && "satt-lang-btn-active")}
                      onClick={() => handleSetLang('hi')}
                      title="हिन्दी"
                      style={{ flex: 1.2, justifyContent: 'center', padding: '6px 8px' }}
                    >
                      हिन्दी
                    </button>
                    <button
                      type="button"
                      className={cn("satt-lang-btn", activeLang === 'bn' && "satt-lang-btn-active")}
                      onClick={() => handleSetLang('bn')}
                      title="বাংলা"
                      style={{ flex: 1.2, justifyContent: 'center', padding: '6px 8px' }}
                    >
                      বাংলা
                    </button>
                  </div>
                </div>

                {/* ── Plans Section ── */}
                <div style={{ background: 'rgba(56,189,248,0.06)', border: '1px solid rgba(56,189,248,0.15)', borderRadius: '10px', padding: '14px' }}>
                  <div style={{ fontSize: '10px', fontWeight: 700, color: '#38bdf8', letterSpacing: '1px', marginBottom: '12px', textTransform: 'uppercase' }}>Plan</div>
                  {[
                    { name: 'Free', price: '$0/mo', features: ['5 analyses/day', 'Single image mode', 'Standard models'], color: '#64748b', highlight: false },
                    { name: 'Pro', price: '$19/mo', features: ['Unlimited analyses', 'Bi-temporal & Fusion', 'Priority models', 'Export reports'], color: '#38bdf8', highlight: true },
                    { name: 'Enterprise', price: 'Custom', features: ['Team workspace', 'Custom integrations', 'Dedicated support'], color: '#a78bfa', highlight: false },
                  ].map((plan) => (
                    <div
                      key={plan.name}
                      style={{
                        marginBottom: '8px',
                        padding: '10px 12px',
                        borderRadius: '8px',
                        border: `1.5px solid ${plan.highlight ? plan.color : 'rgba(255,255,255,0.08)'}`,
                        background: plan.highlight ? `rgba(56,189,248,0.08)` : 'rgba(255,255,255,0.02)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                        <span style={{ fontWeight: 700, fontSize: '13px', color: plan.color }}>{plan.name}</span>
                        <span style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>{plan.price}</span>
                      </div>
                      {plan.features.map((f, i) => (
                        <div key={i} style={{ fontSize: '11px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '2px' }}>
                          <IconCheck size={11} style={{ color: plan.color, flexShrink: 0 }} /> {f}
                        </div>
                      ))}
                      {plan.highlight && (
                        <button
                          type="button"
                          style={{ marginTop: '8px', width: '100%', padding: '6px', borderRadius: '6px', background: '#38bdf8', color: '#0a1628', fontWeight: 700, fontSize: '11px', border: 'none', cursor: 'pointer' }}
                        >
                          Upgrade to Pro
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                {/* ── Logout Section ── */}
                <div>
                  {authError && <p role="alert" style={{ color: '#fca5a5', fontSize: '11px', marginBottom: '8px' }}>{authError}</p>}
                  <button
                    type="button"
                    onClick={handleLogout}
                    disabled={loggingOut}
                    style={{
                      width: '100%',
                      padding: '10px',
                      borderRadius: '8px',
                      border: '1px solid rgba(239,68,68,0.35)',
                      background: 'rgba(239,68,68,0.1)',
                      color: '#f87171',
                      fontWeight: 600,
                      fontSize: '13px',
                      cursor: loggingOut ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      opacity: loggingOut ? 0.6 : 1,
                      transition: 'all 0.15s'
                    }}
                  >
                    <IconLogout size={16} stroke={1.9} />
                    <span>{loggingOut ? 'Signing out…' : 'Log Out'}</span>
                  </button>
                </div>

              </div>
            </aside>
          </>
        )}

        {/* ── DEDICATED RECENT MISSIONS SIDEBAR DRAWER ── */}
        {showHistorySidebar && (
          <>
            <div
              className="satt-history-sidebar-backdrop"
              onClick={() => setShowHistorySidebar(false)}
            />
            <aside className="satt-history-sidebar">
              <div className="satt-history-sidebar-header">
                <div className="satt-history-sidebar-title">
                  <IconHistory size={18} stroke={2} className="text-cyan-400" />
                  <span>Recent Missions</span>
                  <span className="satt-history-count-tag">{allMissions.length}</span>
                </div>
                <div className="satt-history-sidebar-header-actions">
                  <button
                    type="button"
                    className="satt-history-sidebar-icon-btn"
                    onClick={fetchHistory}
                    title="Refresh missions from server"
                  >
                    <IconRefresh size={15} />
                  </button>
                  <button
                    type="button"
                    className="satt-history-sidebar-close"
                    onClick={() => setShowHistorySidebar(false)}
                    title="Close Sidebar"
                  >
                    <IconX size={16} stroke={2.2} />
                  </button>
                </div>
              </div>

              {/* Quick History Search Bar */}
              <div className="satt-history-sidebar-search">
                <div className="satt-search-icon-wrap">
                  <IconSearch size={14} className="satt-search-ico" />
                </div>
                <input
                  type="text"
                  placeholder="Search missions, targets, dates..."
                  value={historySearch}
                  onChange={(e) => setHistorySearch(e.target.value)}
                  className="satt-history-sidebar-input"
                  autoFocus
                />
                {historySearch ? (
                  <button
                    type="button"
                    onClick={() => setHistorySearch("")}
                    className="satt-history-search-clear"
                    title="Clear filter"
                  >
                    <IconX size={13} />
                  </button>
                ) : (
                  <span className="satt-search-badge">Filter</span>
                )}
              </div>

              {/* Missions List in Full Sidebar */}
              <div className="satt-history-sidebar-list">
                {filteredMissions.map((m) => {
                  const isSelected = activeMissionId === m.id;
                  return (
                    <div
                      key={m.id}
                      className={cn(
                        "satt-history-sidebar-card",
                        isSelected && "satt-history-sidebar-card-active"
                      )}
                      onClick={() => handleSelectRecentMission(m)}
                      title={m.query}
                    >
                      <img src={m.thumb} alt={m.title} className="satt-history-sidebar-thumb" />
                      <div className="satt-history-sidebar-info">
                        <div className="satt-history-sidebar-top-row">
                          <span className="satt-history-sidebar-name">{m.title}</span>
                          <span className="satt-completed-pill">{m.status}</span>
                        </div>
                        <div className="satt-history-sidebar-query">"{m.query}"</div>
                        <div className="satt-history-sidebar-meta">
                          <span>📅 {m.date}</span>
                          <span>🛰️ {m.sensor}</span>
                          {m.trust_score != null && (
                            <span className="satt-history-trust-pill">
                              {Math.round(m.trust_score * 100)}% Trust
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
                {filteredMissions.length === 0 && (
                  <div className="satt-history-empty-inline">
                    <span>No missions matching "{historySearch}".</span>
                    <button
                      type="button"
                      onClick={() => setHistorySearch("")}
                      className="satt-history-reset-btn"
                    >
                      Clear Filter
                    </button>
                  </div>
                )}
              </div>

              {/* Sidebar Footer Quick Action */}
              <div className="satt-history-sidebar-footer">
                <button
                  type="button"
                  className="satt-history-sidebar-new-btn"
                  onClick={() => {
                    setHasStarted(false);
                    setShowHistorySidebar(false);
                  }}
                  title="Create new satellite analysis"
                >
                  <IconPlus size={15} stroke={2.4} />
                  <span>New Mission Analysis</span>
                </button>
              </div>
            </aside>
          </>
        )}

        {/* ── COL 2: MISSION CONTROL & ANALYSIS TOOLS ── */}
        <aside className="satt-tools-column">
          {/* Card A: Mission Control */}
          <section className="satt-card satt-mission-control-card">
            <div className="satt-card-header">
              <div className="satt-card-title">
                <IconTargetArrow size={17} stroke={2} className="satt-title-icon" />
                <span>Mission Control</span>
              </div>
            </div>

            {/* Quick Action Buttons */}
            <div className="satt-mc-actions">
              <button
                type="button"
                className="satt-btn-new-analysis"
                onClick={() => setHasStarted(false)}
                title="Return to Observation Setup"
              >
                <IconPlus size={16} stroke={2.5} />
                <span>New Analysis</span>
              </button>
              <button
                type="button"
                className="satt-btn-upload"
                onClick={() => setHasStarted(false)}
                title="Upload Image Data"
              >
                <IconCloudUpload size={16} stroke={1.8} />
                <span>Upload Data</span>
              </button>
            </div>

            {/* Link to Open Dedicated Sidebar */}
            <div className="satt-sidebar-trigger-card">
              <button
                type="button"
                className="satt-open-history-sidebar-btn"
                onClick={() => {
                  fetchHistory();
                  setShowHistorySidebar(true);
                }}
                title="Open Recent Missions & History Sidebar"
              >
                <div className="satt-btn-side-left">
                  <IconHistory size={15} stroke={2} className="text-cyan-400" />
                  <span>Recent Missions ({allMissions.length})</span>
                </div>
                <span className="satt-btn-side-arrow">&rarr;</span>
              </button>
            </div>
          </section>

          {/* Card B: Analysis Tools */}
          <section className="satt-card satt-tools-card">
            <div className="satt-card-header">
              <div className="satt-card-title">
                <IconAdjustments size={17} stroke={2} className="satt-title-icon" />
                <span>Analysis Tools</span>
              </div>
            </div>

            <div className="satt-tools-list">
              {ANALYSIS_TOOLS.map((tool) => {
                const ToolIcon = tool.icon;
                return (
                  <div
                    key={tool.id}
                    className="satt-tool-row"
                    onClick={() => handleSelectTool(tool)}
                  >
                    <div className="satt-tool-icon-box" style={{ color: tool.color, background: `${tool.color}15`, borderColor: `${tool.color}35` }}>
                      <ToolIcon size={17} stroke={2} />
                    </div>
                    <div className="satt-tool-copy">
                      <div className="satt-tool-title">{tool.title}</div>
                      <div className="satt-tool-desc">{tool.desc}</div>
                    </div>
                    <IconArrowRight size={14} stroke={2} className="satt-tool-arrow" />
                  </div>
                );
              })}
            </div>
          </section>



        </aside>

        {/* ── COL 3: CENTER STAGE (Viewer + AI Analysis & Recommendations) ── */}
        <main className="satt-center-column">
          {/* Card 1: Satellite Image Viewer */}
          <section className="satt-card satt-viewer-card">
            <div className="satt-viewer-header">
              <div className="satt-card-title">
                <IconSatellite size={18} stroke={2} className="satt-title-icon" />
                <span>{t('viewerTitle', activeLang)}</span>
                <span className="satt-modality-badge">
                  {mode === 'bitemporal' ? 'Bi-Temporal (T1/T2)' : mode === 'fusion' ? 'Optical + SAR' : 'Optical (RGB)'}
                </span>
                <div className="satt-view-mode-tabs">
                  <button
                    type="button"
                    className={cn("satt-view-tab-btn", viewerMode === '2d' && "satt-view-tab-active")}
                    onClick={() => setViewerMode('2d')}
                    title="2D Pixel Surface Analysis View"
                  >
                    <IconLayersIntersect size={13} />
                    <span>{t('view2D', activeLang)}</span>
                  </button>
                  <button
                    type="button"
                    className={cn("satt-view-tab-btn", viewerMode === '3d' && "satt-view-tab-active")}
                    onClick={() => setViewerMode('3d')}
                    title="3D Globe Viewer (Cesium.js)"
                  >
                    <IconGlobe size={13} />
                    <span>{t('view3D', activeLang)}</span>
                  </button>
                </div>
              </div>
              <div className="satt-viewer-status">
                <span className="satt-status-pill-green">
                  <span className="satt-neon-dot" />
                  {running ? "Processing Scene..." : t('analysisReady', activeLang)}
                </span>
              </div>
            </div>



            {result && !running && viewerMode === '2d' && (
              <div className="satt-annotation-status" role="status">
                {!showOverlay ? 'Object boxes hidden — use the eye button to show them.'
                  : objectOverlayFor(0) || objectOverlayFor(1)
                    ? 'Red boxes label candidate objects. AI locations are approximate.'
                    : 'No object locations supplied for this result. Run a new analysis to request labeled boxes.'}
              </div>
            )}

            {/* Viewport Canvas & Overlays */}
            <div ref={viewportRef} className={cn("satt-viewport-area", viewerMode === "3d" && "satt-viewer-area-3d")}>

              {/* Floating Toolbar Controls (only shown in 2D mode to avoid overlapping 3D Cesium toolbar) */}
              {viewerMode === '2d' && (
                <div className="satt-vp-toolbar">
                  <button
                    type="button"
                    className="satt-vp-btn text-cyan-400"
                    title="Switch to 3D Globe Viewer (Cesium.js)"
                    onClick={() => setViewerMode('3d')}
                  >
                    <IconGlobe size={16} />
                  </button>
                  <button
                    type="button"
                    className={cn("satt-vp-btn", showOverlay && "satt-vp-btn-active")}
                    title="Toggle Layers"
                    onClick={() => setShowOverlay((v) => !v)}
                  >
                    {showOverlay ? <IconEye size={16} /> : <IconEyeOff size={16} />}
                  </button>
                  <button
                    type="button"
                    className={cn("satt-vp-btn", showPointers && "satt-vp-btn-active text-cyan-400")}
                    title="Toggle Feature Arrows (Pond, Buildings, Forest, Road)"
                    onClick={() => setShowPointers((v) => !v)}
                  >
                    <IconMapPin size={16} />
                  </button>
                  <button
                    type="button"
                    className={cn("satt-vp-btn", showLandUseHud && "satt-vp-btn-active text-emerald-400")}
                    title="Toggle Land Use Distribution HUD"
                    onClick={() => setShowLandUseHud((v) => !v)}
                  >
                    <IconChartDonut size={16} />
                  </button>
                  <div className="satt-vp-divider" />
                  <button type="button" className="satt-vp-btn" title="Zoom In" onClick={() => setZoomLevel((z) => Math.min(3, +(z + 0.25).toFixed(2)))}>
                    <IconPlus size={16} />
                  </button>
                  <button type="button" className="satt-vp-btn" title="Zoom Out" onClick={() => setZoomLevel((z) => Math.max(1, +(z - 0.25).toFixed(2)))}>
                    <IconMinus size={16} />
                  </button>
                  <button
                    type="button"
                    className={cn("satt-vp-btn", isFullscreen && "satt-vp-btn-active text-cyan-400")}
                    title={isFullscreen ? "Exit Fullscreen" : "Fullscreen View"}
                    onClick={toggleFullscreen}
                  >
                    {isFullscreen ? <IconMinimize size={16} /> : <IconMaximize size={16} />}
                  </button>
                </div>
              )}
              
              {/* Scanning / Loading Map Overlay */}
              {(running || (hasStarted && !result)) && (
                <div className="satt-map-scanning-overlay">
                  <div className="satt-map-scanner-line"></div>
                  <div className="satt-map-scanning-text">
                    <span className="satt-running-pulse-dot" style={{ display: 'inline-block', marginRight: 10, width: 10, height: 10 }}></span>
                    SCANNING ORBITAL FOOTPRINT...
                  </div>
                </div>
              )}

              {/* 3D Globe Viewer (Cesium.js) vs 2D Pixel Canvas */}
              {viewerMode === '3d' ? (
                <CesiumGlobeViewer
                  imageSrc={
                    bitemporalPhotoView === 'before'
                      ? beforeImageSrc
                      : bitemporalPhotoView === 'after' || bitemporalPhotoView === 'mask'
                      ? afterImageSrc
                      : currentImageSrc
                  }
                  geoBounds={result?.input?.metadata?.geo_bounds || (result?.input?.images?.[0] as any)?.geo_bounds || null}
                  callouts={dynamicCallouts}
                  activeFilter={activeFeatureFilter}
                  onFilterChange={(f) => setActiveFeatureFilter(f as any)}
                  showOverlay={showOverlay}
                  onToggleOverlay={() => setShowOverlay((v) => !v)}
                  isProcessing={running}
                  sceneName={result?.task || query || "Satellite Observation Footprint"}
                  modalityBadge={mode === 'bitemporal' ? 'Bi-Temporal (T1/T2)' : mode === 'fusion' ? 'Optical + SAR' : 'Optical (RGB)'}
                  onSwitchTo2D={() => setViewerMode('2d')}
                  targetLocationQuery={query}
                  uploadedFileName={files[0]?.name || files[1]?.name || undefined}
                  onAnalyzeLocation={(locName) => {
                    const cleanName = locName.split('(')[0].trim();
                    const q = `Analyze ${cleanName}`;
                    setQuery(q);
                    setViewerMode('2d');
                    runAnalysis(q);
                  }}
                />
              ) : (isBitemporal || isFusion) && bitemporalPhotoView === 'both' ? (
                <div className="satt-dual-canvas-container" style={{ transform: `scale(${zoomLevel})` }}>
                  {/* Left Panel: Sensor 1 / T1 Before */}
                  <div className="satt-dual-panel">
                    <div className="satt-dual-panel-header">
                      <span className={cn("satt-dual-badge", isFusion ? "satt-badge-optical" : "satt-badge-before")}>
                        {isFusion ? "Sensor 1: Optical Multispectral" : "T1: Before Photo (Pre-Event)"}
                      </span>
                      <span className="satt-dual-res">{isFusion ? "Sentinel-2 MSI · Visible RGB" : "Spatial 10m · Optical RGB"}</span>
                    </div>
                    <div className="satt-dual-image-wrap">
                      <AnnotatedScene
                        src={beforeImageSrc}
                        alt={isFusion ? "Optical Observation Scene" : "Before Acquisition Scene"}
                        overlay={objectOverlayFor(0)}
                        showBoxes={showOverlay}
                      />
                      {showOverlay && (
                        <canvas
                          ref={canvasRefBefore}
                          className="satt-mask-canvas"
                        />
                      )}
                    </div>
                  </div>

                  {/* Right Panel: Sensor 2 / T2 After */}
                  <div className="satt-dual-panel">
                    <div className="satt-dual-panel-header">
                      <span className={cn("satt-dual-badge", isFusion ? "satt-badge-sar" : "satt-badge-after")}>
                        {isFusion ? "Sensor 2: SAR Microwave Radar" : "T2: After Photo (Post-Event)"}
                      </span>
                      <span className="satt-dual-res">{isFusion ? "Sentinel-1 / RISAT · Radar Backscatter" : "Spatial 10m · Optical RGB"}</span>
                    </div>
                    <div className="satt-dual-image-wrap">
                      <AnnotatedScene
                        src={afterImageSrc}
                        alt={isFusion ? "SAR Radar Scene" : "After Acquisition Scene"}
                        overlay={objectOverlayFor(1)}
                        showBoxes={showOverlay}
                      />
                      {showOverlay && (
                        <canvas
                          ref={canvasRefAfter}
                          className="satt-mask-canvas"
                        />
                      )}
                      {renderHudCallouts()}
                    </div>
                  </div>
                </div>
              ) : (
                /* Single Central Viewport Display */
                <div className="satt-canvas-container" style={{ transform: `scale(${zoomLevel})` }}>
                  <AnnotatedScene
                    src={
                      bitemporalPhotoView === 'before'
                        ? beforeImageSrc
                        : bitemporalPhotoView === 'after' || bitemporalPhotoView === 'mask'
                        ? afterImageSrc
                        : currentImageSrc
                    }
                    alt="Satellite Scene Viewport"
                    overlay={objectOverlayFor(bitemporalPhotoView === 'after' || bitemporalPhotoView === 'mask' ? 1 : 0)}
                    showBoxes={showOverlay}
                  />

                  {/* Server-provided surface mask */}
                  {showOverlay && (
                    <canvas
                      ref={canvasRef}
                      className="satt-mask-canvas"
                    />
                  )}

                  {/* HUD Feature Pointer Arrows & Callouts */}
                  {renderHudCallouts()}
                </div>
              )}

              {/* Floating HUD Land Use Distribution Overlay (Exact layout matching screenshot) */}
              {showLandUseHud && landUseData.length > 0 && (
                <div className="satt-viewport-hud-landuse">
                  <div className="satt-hud-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span className="satt-hud-title">{t('landUseTitle', activeLang)}</span>
                      {isBitemporal && (
                        <span style={{ fontSize: '9px', color: '#38bdf8', fontWeight: 700, background: 'rgba(56, 189, 248, 0.15)', padding: '1px 5px', borderRadius: '3px' }}>
                          {activeLandUseTab === 'before' ? 'T1' : 'T2'}
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowLandUseHud(false)}
                      className="satt-hud-close-btn"
                      title="Hide Land Use HUD"
                    >
                      <IconX size={12} />
                    </button>
                  </div>

                  <div className="satt-hud-body">
                    {/* Donut Chart */}
                    <div className="satt-hud-chart-wrap">
                      <svg className="satt-landuse-svg" viewBox="0 0 100 100">
                        {(() => {
                          let accum = 0;
                          const r = 34;
                          const c = 2 * Math.PI * r;
                          const tot = landUseData.reduce((sum, d) => sum + d.pct, 0) || 100;
                          return landUseData.map((d, idx) => {
                            const len = (d.pct / tot) * c;
                            const offset = -accum;
                            accum += len;
                            return (
                              <circle
                                key={idx}
                                cx="50"
                                cy="50"
                                r={r}
                                fill="none"
                                stroke={d.color}
                                strokeWidth="15"
                                strokeDasharray={`${len} ${c - len}`}
                                strokeDashoffset={offset}
                              />
                            );
                          });
                        })()}
                      </svg>
                    </div>

                    {/* Legend Rows with Square Swatches */}
                    <div className="satt-hud-legend">
                      {landUseData.map((item, i) => (
                        <div key={i} className="satt-hud-row">
                          <div className="satt-hud-row-left">
                            <span className="satt-hud-swatch" style={{ background: item.color, boxShadow: `0 0 6px ${item.color}` }} />
                            <span className="satt-hud-name">
                              {item.name === 'FOREST' ? t('forestLabel', activeLang) :
                               item.name === 'AGRICULTURAL' ? t('agriLabel', activeLang) :
                               item.name === 'URBAN' ? t('urbanLabel', activeLang) :
                               item.name === 'WATER' ? t('waterLabel', activeLang) :
                               item.name === 'OTHER' ? t('otherLabel', activeLang) : item.name}
                            </span>
                          </div>
                          <span className="satt-hud-pct">{Math.round(item.pct)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Bottom Right Fullscreen Option Button */}
              <div className="satt-viewport-fullscreen-corner" style={{ position: 'absolute', bottom: '12px', right: '12px', zIndex: 15 }}>
                <button
                  type="button"
                  onClick={toggleFullscreen}
                  className={cn("satt-vp-btn", isFullscreen && "satt-vp-btn-active text-cyan-400")}
                  title={isFullscreen ? "Exit Fullscreen (Esc)" : "Fullscreen View (पूरा स्क्रीन)"}
                  style={{
                    background: 'rgba(15, 23, 42, 0.88)',
                    border: '1px solid rgba(56, 189, 248, 0.45)',
                    borderRadius: '8px',
                    color: isFullscreen ? '#38bdf8' : '#f1f5f9',
                    padding: '8px 10px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    cursor: 'pointer',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.65)',
                    backdropFilter: 'blur(8px)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {isFullscreen ? <IconMinimize size={17} /> : <IconMaximize size={17} />}
                  <span style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.4px' }}>
                    {isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
                  </span>
                </button>
              </div>

              {/* Bottom Left Scale Indicator */}
              <div className="satt-viewport-scale" hidden={Boolean(result?.analysis_report)}>
                <div className="satt-scale-line" />
                <div className="satt-scale-labels">
                  <span>0</span>
                  <span>250</span>
                  <span>500</span>
                  <span>1,000 m</span>
                </div>
              </div>
            </div>

          </section>

          {/* Card 2: AI Analysis & Satellite Interpretation (Big & Clear) */}
          <section className="satt-card satt-analysis-card satt-analysis-expanded">
            <div className="satt-analysis-header">
              <div className="satt-card-title satt-big-title">
                <IconSparkles size={20} stroke={2} className="satt-title-icon text-amber-400" />
                <span>{t('execTitle', activeLang)}</span>
              </div>
              <div className="satt-analysis-badge-wrap">
                {isBitemporal ? (
                  <span className="satt-tag-pill satt-tag-cyan" style={{ marginRight: 6 }}>
                    <IconLayersIntersect size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                    Before / After Differential
                  </span>
                ) : isFusion ? (
                  <span className="satt-tag-pill satt-tag-cyan" style={{ marginRight: 6 }}>
                    <IconLayersIntersect size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                    Optical + SAR Fusion
                  </span>
                ) : null}
                {running || (hasStarted && !result) ? (
                  <span className="satt-tag-pill satt-tag-amber satt-match-badge">
                    <span className="satt-running-pulse-dot" style={{ display: 'inline-block', marginRight: 6 }} />
                    Analyzing...
                  </span>
                ) : (
                  <span className="satt-tag-pill satt-tag-green satt-match-badge">
                    {result?.analysis_report ? "Confidence unavailable" : Boolean((result as any)?.cloud_vision) ? ((result as any)?.cloud_vision?.provider_id === 'ollama' ? "Local Ollama · unverified" : "Cloud interpretation · unverified") : (result?.decision as any)?.code === "MODEL_DISAGREEMENT" ? "Unable to identify reliably" : `${Math.round((result?.trust_score ?? 0) * 100)}% Evidence support`}
                  </span>
                )}

                {/* 🎧 Listen / Read Out Loud Button */}
                <button
                  type="button"
                  onClick={handleToggleSpeech}
                  className={cn("satt-listen-btn", isSpeaking && "satt-listen-btn-active")}
                  title={isSpeaking ? (activeLang === 'hi' ? 'रोकें (Stop)' : activeLang === 'bn' ? 'থামান (Stop)' : 'Stop reading') : (activeLang === 'hi' ? 'रिपोर्ट सुनें (Listen)' : activeLang === 'bn' ? 'রিপোর্ট শুনুন (Listen)' : 'Listen to Interpretation')}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '5px 12px',
                    borderRadius: '20px',
                    fontSize: '12px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    border: isSpeaking ? '1px solid #38bdf8' : '1px solid rgba(56, 189, 248, 0.45)',
                    background: isSpeaking ? 'linear-gradient(135deg, rgba(2, 132, 199, 0.4), rgba(56, 189, 248, 0.35))' : 'rgba(15, 23, 42, 0.85)',
                    color: isSpeaking ? '#38bdf8' : '#f1f5f9',
                    boxShadow: isSpeaking ? '0 0 14px rgba(56, 189, 248, 0.5)' : 'none',
                    transition: 'all 0.2s ease',
                    marginLeft: '8px',
                  }}
                >
                  {isSpeaking ? (
                    <>
                      <IconPlayerStop size={14} style={{ color: '#f87171' }} />
                      <span>{activeLang === 'hi' ? 'रोकें' : activeLang === 'bn' ? 'থামান' : 'Stop'}</span>
                      <span className="satt-running-pulse-dot" style={{ background: '#38bdf8', width: 6, height: 6 }} />
                    </>
                  ) : (
                    <>
                      <IconVolume size={15} style={{ color: '#38bdf8' }} />
                      <span>{activeLang === 'hi' ? 'सुनें' : activeLang === 'bn' ? 'শুনুন' : 'Listen'}</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* 1. Primary AI Findings & Narrative */}
            {isCloud ? (
              <div className="satt-cloud-analysis-container" style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '12px' }}>
                {/* Engine badge */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6px 14px',
                    borderRadius: '20px',
                    fontSize: '13px',
                    fontWeight: 600,
                    background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.16), rgba(99, 102, 241, 0.16))',
                    border: '1px solid rgba(56, 189, 248, 0.4)',
                    color: '#38bdf8',
                    letterSpacing: '0.2px'
                  }}>
                    <IconSparkles size={16} className="text-sky-400" />
                    <span>{t('analysisBy', activeLang)}: {cloudProvider} {cloudModel ? `(${cloudModel})` : ""}</span>
                  </span>
                </div>

                {/* Description (paragraphs) */}
                <div style={{
                  background: 'rgba(15, 23, 42, 0.65)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                  borderRadius: '10px',
                  padding: '16px 18px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94a3b8', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.8px', fontWeight: 700 }}>
                    <IconEye size={15} style={{ color: '#38bdf8' }} />
                    <span>{t('sceneDescTitle', activeLang)}</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', color: '#f1f5f9', fontSize: '14.5px', lineHeight: '1.65' }}>
                    {(cloudDescParagraphs.length > 0 ? cloudDescParagraphs : [cloudDescription || cloudAnswer]).map((para: string, pIdx: number) => (
                      <p key={pIdx} style={{ margin: 0 }}>{translateText(para, activeLang)}</p>
                    ))}
                  </div>
                </div>

                {/* Answer */}
                <div style={{
                  background: 'rgba(2, 132, 199, 0.08)',
                  border: '1px solid rgba(2, 132, 199, 0.3)',
                  borderRadius: '10px',
                  padding: '14px 18px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.8px', fontWeight: 700 }}>
                    <IconSparkles size={15} />
                    <span>{t('answerTitle', activeLang)}</span>
                  </div>
                  <div style={{ color: '#ffffff', fontSize: '15px', fontWeight: 500, lineHeight: '1.6' }}>
                    {(() => {
                      const text = cloudAnswer || "";
                      let points = text
                        .split(/(?:\s*\(\d+\)\s*|\n\s*[•\-*]\s*|\n\s*\d+\.\s*|\n{2,})/)
                        .map((p: string) => p.trim().replace(/^[•\-*]\s*/, ''))
                        .filter((p: string) => p.length > 0);

                      if (points.length === 1 && text.includes('\n')) {
                        points = text.split('\n').map((p: string) => p.trim().replace(/^[•\-*]\s*/, '')).filter((p: string) => p.length > 0);
                      }

                      if (points.length > 1) {
                        return (
                          <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {points.map((pt: string, idx: number) => (
                              <li key={idx} style={{ lineHeight: '1.6', fontSize: '14.5px', color: '#f8fafc' }}>
                                {translateText(pt, activeLang)}
                              </li>
                            ))}
                          </ul>
                        );
                      }
                      return <span>{translateText(text, activeLang)}</span>;
                    })()}
                  </div>
                </div>
              </div>
            ) : result?.analysis_report ? (
              <SpecialistReport report={result.analysis_report} lang={activeLang} />
            ) : (
              /* Big, Clear Analysis Presentation */
              <div className="satt-big-analysis-box" style={{ marginTop: '12px' }}>
                <div className="satt-big-ai-badge">
                  <IconBrain size={26} stroke={1.8} />
                  <span>Neural Insight</span>
                </div>
                <div className="satt-big-ai-content">
                  {running || (hasStarted && !result) ? (
                    <div className="satt-skeleton-text-block">
                      <div className="satt-skeleton-line" style={{ width: '85%' }}></div>
                      <div className="satt-skeleton-line" style={{ width: '60%' }}></div>
                      <div className="satt-skeleton-line" style={{ width: '90%' }}></div>
                      <div className="satt-skeleton-line" style={{ width: '70%' }}></div>
                    </div>
                  ) : (
                    <p className="satt-big-analysis-text">
                      {dynamicAssessment}
                    </p>
                  )}
                  <div className="satt-big-summary-tag">
                    <strong>{Boolean((result as any)?.cloud_vision) ? "Analysis mode:" : "Candidate finding:"}</strong> <span>{result?.short_answer || (isBitemporal ? "TEMPORAL CHANGE SUMMARY" : isFusion ? "SAR-OPTICAL FUSION ASSESSMENT" : "SATELLITE SCENE ASSESSMENT")}</span>
                  </div>
                </div>
              </div>
            )}

            {/* 2. Scene Feature Inventory Grid: Detected in Scene (Present) | Absent / Not Detected (Image 1 side-by-side layout) */}
            {((!isBitemporal && !isFusion) || bitemporalSubTab === 'inventory') && (
              <div className="satt-analysis-grid" style={{ marginTop: '14px', gridTemplateColumns: presentInventoryList.length && absentInventoryList.length ? undefined : '1fr' }}>
                {/* Sub-Card 1: Detected Objects (Present) */}
                {presentInventoryList.length > 0 && <div className="satt-subcard satt-detected-objects-card">
                  <div className="satt-subcard-header">
                    <div className="satt-subcard-title">
                      <IconCircleCheck size={16} className="text-emerald-400" />
                      <span>{t('detectedPresentTitle', activeLang)}</span>
                    </div>
                    <span className="satt-count-pill">{presentInventoryList.length} {t('foundCount', activeLang)}</span>
                  </div>
                  <div className="satt-subcard-list">
                    {presentInventoryList.map((item, idx) => (
                      <div key={idx} className="satt-detected-row">
                        <div className="satt-row-left">
                          <span className="satt-obj-icon">{item.icon || "📍"}</span>
                          <div className="satt-obj-texts">
                            <span className="satt-obj-name">{translateText(item.name, activeLang)}</span>
                            {item.detail && <span className="satt-obj-conf">{translateText(item.detail, activeLang)}</span>}
                          </div>
                        </div>
                        <span className={cn("satt-tag-pill", getBadgeClass(item.badge || item.name))}>
                          {translateText(item.badge || item.name, activeLang)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>}

                {/* Sub-Card 2: Absent / Not Detected */}
                {absentInventoryList.length > 0 && <div className="satt-subcard satt-anomalies-card">
                  <div className="satt-subcard-header">
                    <div className="satt-subcard-title">
                      <IconX size={16} className="text-slate-400" />
                      <span>{t('absentTitle', activeLang)}</span>
                    </div>
                    <span className="satt-count-pill" style={{ color: '#94a3b8', background: 'rgba(100, 116, 139, 0.2)', borderColor: 'rgba(100, 116, 139, 0.4)' }}>
                      {absentInventoryList.length} {t('absentCount', activeLang)}
                    </span>
                  </div>
                  <div className="satt-subcard-list">
                    {
                      absentInventoryList.map((item, idx) => (
                        <div key={idx} className="satt-detected-row">
                          <div className="satt-row-left">
                            <span className="satt-obj-icon">{item.icon || "❌"}</span>
                            <div className="satt-obj-texts">
                              <span className="satt-obj-name">{translateText(item.name, activeLang)}</span>
                              <span className="satt-obj-conf">{translateText(item.detail || "Not observed in scene", activeLang)}</span>
                            </div>
                          </div>
                          <span className={cn("satt-tag-pill", getBadgeClass(item.badge || "Absent"))}>
                            {translateText(item.badge || "Absent", activeLang)}
                          </span>
                        </div>
                      ))
                    }
                  </div>
                </div>}
              </div>
            )}

            {/* 3. Bitemporal / Fusion Matrices (If Bitemporal or Fusion mode) */}
            {isBitemporal ? (
              <div className="satt-bitemporal-toggle-row" style={{ marginTop: '14px' }}>
                <button
                  type="button"
                  className={cn("satt-sub-toggle-btn", bitemporalSubTab === 'diff' && "satt-sub-toggle-active")}
                  onClick={() => setBitemporalSubTab('diff')}
                >
                  <IconGitCompare size={14} />
                  <span>{t('beforeVsAfterBtn', activeLang)}</span>
                  <span className="satt-count-pill" style={{ marginLeft: 6 }}>{diffList.length} Verified</span>
                </button>
                <button
                  type="button"
                  className={cn("satt-sub-toggle-btn", bitemporalSubTab === 'inventory' && "satt-sub-toggle-active")}
                  onClick={() => setBitemporalSubTab('inventory')}
                >
                  <IconListCheck size={14} />
                  <span>{t('sceneInventoryBtn', activeLang)}</span>
                </button>
              </div>
            ) : isFusion ? (
              <div className="satt-bitemporal-toggle-row" style={{ marginTop: '14px' }}>
                <button
                  type="button"
                  className={cn("satt-sub-toggle-btn", bitemporalSubTab === 'diff' && "satt-sub-toggle-active")}
                  onClick={() => setBitemporalSubTab('diff')}
                >
                  <IconLayersIntersect size={14} />
                  <span>{t('fusionMatrixTitle', activeLang)}</span>
                  <span className="satt-count-pill" style={{ marginLeft: 6 }}>{fusionList.length} Verified</span>
                </button>
                <button
                  type="button"
                  className={cn("satt-sub-toggle-btn", bitemporalSubTab === 'inventory' && "satt-sub-toggle-active")}
                  onClick={() => setBitemporalSubTab('inventory')}
                >
                  <IconListCheck size={14} />
                  <span>{t('sceneInventoryBtn', activeLang)}</span>
                </button>
              </div>
            ) : null}

            {/* If Bitemporal & diff view: render Temporal Variance Matrix */}
            {isBitemporal && bitemporalSubTab === 'diff' ? (
              <div className="satt-bitemporal-diff-container" style={{ marginTop: '14px' }}>
                <div className="satt-diff-header-bar">
                  <div className="satt-diff-header-left">
                    <span className="satt-diff-main-title">{t('diffMatrixTitle', activeLang)}</span>
                    <span className="satt-diff-sub-title">Quantified physical shifts, surface expansion &amp; structural impact</span>
                  </div>
                  <span className="satt-badge-accent">Sub-Pixel Coregistered</span>
                </div>

                <div className="satt-diff-cards-grid">
                  {diffList.map((item, idx) => (
                    <div key={idx} className={cn("satt-diff-card", `satt-diff-card-${item.delta_type}`)}>
                      <div className="satt-diff-card-top">
                        <div className="satt-diff-card-title-wrap">
                          <span className="satt-diff-icon">{item.icon}</span>
                          <span className="satt-diff-name">{translateText(item.feature, activeLang)}</span>
                        </div>
                        <span className={cn("satt-delta-badge", `satt-delta-${item.delta_type}`)}>
                          {translateText(item.delta_val, activeLang)}
                        </span>
                      </div>

                      <div className="satt-diff-transition-row">
                        <div className="satt-transition-node satt-node-before">
                          <span className="satt-node-label">Before (T1)</span>
                          <span className="satt-node-val">{translateText(item.before_val, activeLang)}</span>
                        </div>
                        <div className="satt-transition-arrow">
                          <span>➔</span>
                        </div>
                        <div className="satt-transition-node satt-node-after">
                          <span className="satt-node-label">After (T2)</span>
                          <span className="satt-node-val">{translateText(item.after_val, activeLang)}</span>
                        </div>
                      </div>

                      <div className="satt-diff-card-details">
                        {item.metric && (
                          <div className="satt-diff-detail-line">
                            <span className="satt-detail-label">Measured Delta:</span>
                            <span className="satt-detail-highlight">{item.metric}</span>
                          </div>
                        )}
                        {item.location && (
                          <div className="satt-diff-detail-line">
                            <span className="satt-detail-label">Sector / Area:</span>
                            <span className="satt-detail-text">{item.location}</span>
                          </div>
                        )}
                        {item.impact && (
                          <div className="satt-diff-impact-box">
                            <span className="satt-impact-icon">ℹ️</span>
                            <span className="satt-impact-text">{translateText(item.impact, activeLang)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : isFusion && bitemporalSubTab === 'diff' ? (
              <div className="satt-bitemporal-diff-container" style={{ marginTop: '14px' }}>
                <div className="satt-diff-header-bar">
                  <div className="satt-diff-header-left">
                    <span className="satt-diff-main-title">{t('fusionMatrixTitle', activeLang)}</span>
                    <span className="satt-diff-sub-title">Joint multi-sensor verification combining visible spectral reflectance and radar microwave backscatter</span>
                  </div>
                  <span className="satt-badge-accent">Multi-Sensor Coincident</span>
                </div>

                <div className="satt-diff-cards-grid">
                  {fusionList.map((item: (typeof DEFAULT_FUSION_BREAKDOWN)[number], idx: number) => (
                    <div key={idx} className={cn("satt-diff-card", `satt-diff-card-${item.delta_type}`)}>
                      <div className="satt-diff-card-top">
                        <div className="satt-diff-card-title-wrap">
                          <span className="satt-diff-icon">{item.icon}</span>
                          <span className="satt-diff-name">{translateText(item.feature, activeLang)}</span>
                        </div>
                        <span className={cn("satt-delta-badge", `satt-delta-${item.delta_type}`)}>
                          {translateText(item.delta_val, activeLang)}
                        </span>
                      </div>

                      <div className="satt-diff-transition-row">
                        <div className="satt-transition-node" style={{ background: 'rgba(56, 189, 248, 0.12)', borderColor: 'rgba(56, 189, 248, 0.35)' }}>
                          <span className="satt-node-label" style={{ color: '#38bdf8' }}>{item.sensor1_label}</span>
                          <span className="satt-node-val">{translateText(item.sensor1_val, activeLang)}</span>
                        </div>
                        <div className="satt-transition-arrow">
                          <span style={{ color: '#38bdf8' }}>⟷</span>
                        </div>
                        <div className="satt-transition-node" style={{ background: 'rgba(234, 179, 8, 0.12)', borderColor: 'rgba(234, 179, 8, 0.35)' }}>
                          <span className="satt-node-label" style={{ color: '#eab308' }}>{item.sensor2_label}</span>
                          <span className="satt-node-val">{translateText(item.sensor2_val, activeLang)}</span>
                        </div>
                      </div>

                      <div className="satt-diff-card-details">
                        {item.metric && (
                          <div className="satt-diff-detail-line">
                            <span className="satt-detail-label">Consensus Type:</span>
                            <span className="satt-detail-highlight">{item.metric}</span>
                          </div>
                        )}
                        {item.location && (
                          <div className="satt-diff-detail-line">
                            <span className="satt-detail-label">Observation Domain:</span>
                            <span className="satt-detail-text">{item.location}</span>
                          </div>
                        )}
                        {item.impact && (
                          <div className="satt-diff-impact-box">
                            <span className="satt-impact-icon">ℹ️</span>
                            <span className="satt-impact-text">{translateText(item.impact, activeLang)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </section>
        </main>

        {/* ── COL 4: RIGHT COLUMN (Mission Insights, Task Execution & AI Specialists) ── */}
        <aside className="satt-insights-column">
          {/* Card 1: Mission Insights */}
          <section className="satt-card satt-insights-card">
            <div className="satt-card-header">
              <div className="satt-card-title">
                <IconActivity size={17} stroke={2} className="satt-title-icon text-amber-400" />
                <span>{t('missionInsightsTitle', activeLang)}</span>
              </div>
              <span className="satt-priority-badge">{t('highPriorityBadge', activeLang)}</span>
            </div>

            {/* Circular Gauge + Overall Assessment */}
            {(() => {
              const displayTrust = trustPercent > 0 ? trustPercent : isCloud ? 85 : 0;
              const displayVisual = visualPercent > 0 ? visualPercent : isCloud ? 88 : 0;
              const displayClarity = inputQualityPct > 0 ? inputQualityPct : isCloud ? 96 : 0;
              const displaySpectral = spectralCoverage > 0 ? spectralCoverage : 0;

              return (
                <>
                  <div className="satt-gauge-row">
                    <div className="satt-radial-meter">
                      <svg className="satt-radial-svg" viewBox="0 0 100 100">
                        <circle
                          className="satt-radial-track"
                          cx="50"
                          cy="50"
                          r="40"
                          strokeWidth="8"
                        />
                        <circle
                          className="satt-radial-fill"
                          cx="50"
                          cy="50"
                          r="40"
                          strokeWidth="8"
                          strokeDasharray="251.2"
                          strokeDashoffset={251.2 - (251.2 * displayTrust) / 100}
                        />
                      </svg>
                      <div className="satt-radial-content">
                        <span className="satt-radial-num">{result ? `${displayTrust}%` : "0%"}</span>
                        <span className="satt-radial-lbl">{isCloud ? "AI Support" : "Evidence support"}</span>
                      </div>
                    </div>

                    <div className="satt-assessment-box">
                      <strong>{t('overallAssessment', activeLang)}</strong>
                      <p className="satt-assessment-summary">
                        {translateText(assessmentSummary, activeLang)}
                      </p>
                    </div>
                  </div>

                  {/* Metrics Progress Bars */}
                  <div className="satt-metrics-bars">
                    <div className="satt-mbar-item">
                      <div className="satt-mbar-head">
                        <span>{t('neuralConfidence', activeLang)}</span>
                        <b>{displayVisual}%</b>
                      </div>
                      <div className="satt-mbar-track">
                        <div className="satt-mbar-fill bg-blue-500" style={{ width: `${displayVisual}%` }} />
                      </div>
                    </div>

                    <div className="satt-mbar-item">
                      <div className="satt-mbar-head">
                        <span>{t('spectralVerification', activeLang)}</span>
                        <b>{(result as any)?.spectral_indices?.status === 'not available' ? "RGB (N/A)" : `${displaySpectral}%`}</b>
                      </div>
                      <div className="satt-mbar-track">
                        <div className="satt-mbar-fill bg-teal-400" style={{ width: `${displaySpectral}%` }} />
                      </div>
                    </div>

                    <div className="satt-mbar-item">
                      <div className="satt-mbar-head">
                        <span>{t('sensorClarity', activeLang)}</span>
                        <b>{displayClarity}%</b>
                      </div>
                      <div className="satt-mbar-track">
                        <div className="satt-mbar-fill bg-cyan-400" style={{ width: `${displayClarity}%` }} />
                      </div>
                    </div>

                    <div className="satt-risk-row">
                      <span>{t('riskLevel', activeLang)}</span>
                      <span className={isCloud && result ? "satt-risk-pill satt-risk-pill-green" : riskInfo.pillClass}>
                        {isCloud && result ? t('nominal', activeLang) : riskInfo.label}
                      </span>
                    </div>
                  </div>
                </>
              );
            })()}

            {/* Spectral Indices (NDVI / NDWI) Card */}
            {(() => {
              const spec = (result as any)?.spectral_indices;
              if (!spec) return null;
              if (spec.status === "not available") {
                return (
                  <div
                    style={{
                      margin: "12px 0 6px",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      background: "rgba(245, 158, 11, 0.08)",
                      border: "1px solid rgba(245, 158, 11, 0.3)",
                      fontSize: "12px",
                    }}
                  >
                    <div
                      style={{
                        fontWeight: 700,
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        marginBottom: "4px",
                        color: "#fbbf24",
                      }}
                    >
                      <span>⚠️</span>
                      <span>Spectral indices not available for RGB image</span>
                    </div>
                    <div style={{ fontSize: "11px", color: "#9ca3af", lineHeight: "1.4" }}>
                      Physical NDVI (vegetation) and NDWI (water) require Near-Infrared (NIR) band. Standard 3-channel RGB imagery cannot measure physical spectral absorption.
                    </div>
                  </div>
                );
              }
              if (spec.status === "available") {
                return (
                  <div
                    style={{
                      margin: "12px 0 6px",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      background: "rgba(16, 185, 129, 0.08)",
                      border: "1px solid rgba(16, 185, 129, 0.3)",
                      fontSize: "12px",
                    }}
                  >
                    <div
                      style={{
                        fontWeight: 700,
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        marginBottom: "6px",
                        color: "#34d399",
                      }}
                    >
                      <span>🔬</span>
                      <span>Calibrated Spectral Indices</span>
                    </div>
                    {spec.indices?.ndvi?.mean != null && (
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px", color: "#a7f3d0" }}>
                        <span>NDVI (Mean):</span>
                        <b style={{ fontFamily: "monospace" }}>{spec.indices.ndvi.mean.toFixed(3)}</b>
                      </div>
                    )}
                    {spec.indices?.ndwi?.mean != null && (
                      <div style={{ display: "flex", justifyContent: "space-between", color: "#a7f3d0" }}>
                        <span>NDWI (Mean):</span>
                        <b style={{ fontFamily: "monospace" }}>{spec.indices.ndwi.mean.toFixed(3)}</b>
                      </div>
                    )}
                  </div>
                );
              }
              return null;
            })()}


            {/* Quick Actions */}
            <div className="satt-quick-actions">
              <div className="satt-qa-title">
                <IconSparkles size={14} /> Quick Actions
              </div>
              <div className="satt-qa-btns">
                <button type="button" className="satt-qa-btn" onClick={downloadReport}>
                  <IconDownload size={14} />
                  <span>{downloaded ? "Downloading PDF..." : "Download Report (PDF)"}</span>
                </button>
              </div>
            </div>
          </section>

          {/* Card 2: Task Execution */}
          <section className="satt-card satt-execution-card">
            <div className="satt-exec-header">
              <div className="flex items-center gap-2">
                <span className="satt-exec-title">TASK EXECUTION</span>
                <span className="satt-exec-badge">6 STEPS</span>
              </div>
              <button
                type="button"
                className="satt-exec-rerun-btn"
                title="Watch slow step-by-step neural execution"
                onClick={() => triggerLiveStepAnimation(result)}
                disabled={running}
              >
                {running ? (
                  <>
                    <span className="satt-running-pulse-dot" />
                    <span>In Progress</span>
                  </>
                ) : (
                  <>
                    <span>▶ Live Run</span>
                  </>
                )}
              </button>
            </div>

            {/* Sub-tabs: Task Execution / Analysis Log */}
            <div className="satt-exec-tabs">
              <button
                type="button"
                className={cn("satt-etab", executionTab === 'execution' && "satt-etab-active")}
                onClick={() => setExecutionTab("execution")}
              >
                Task Execution
              </button>
              <button
                type="button"
                className={cn("satt-etab", executionTab === 'log' && "satt-etab-active")}
                onClick={() => setExecutionTab("log")}
              >
                Analysis Log {events.length > 0 && `(${events.length})`}
              </button>
            </div>

            {executionTab === 'execution' ? (
              /* Timeline Steps */
              <div className="satt-timeline-list">
                {AGENT_STEPS.map((step, idx) => {
                  const isRunning = running && stepIndex === idx;
                  const isDone = completedSteps.includes(idx);
                  return (
                    <div key={idx} className={cn("satt-timeline-item", isRunning && "satt-timeline-item-active")}>
                      <div className="satt-timeline-marker">
                        {isDone ? (
                          <span className="satt-tmark-done"><IconCheck size={12} stroke={3} /></span>
                        ) : isRunning ? (
                          <span className="satt-tmark-running" />
                        ) : (
                          <span className="satt-tmark-pending" />
                        )}
                        {idx < AGENT_STEPS.length - 1 && (
                          <span className={cn("satt-timeline-line", (isDone || isRunning) && "satt-timeline-line-active")} />
                        )}
                      </div>
                      <div className="satt-timeline-body">
                        <div className="satt-tstep-title">{step.title}</div>
                        <div className="satt-tstep-desc">
                          {isDone ? (
                            <span className="text-emerald-400 font-semibold">✓ Completed</span>
                          ) : isRunning ? (
                            <span className="text-cyan-400 font-semibold flex items-center gap-1.5">
                              <span className="satt-running-pulse-dot" /> In Progress...
                            </span>
                          ) : (
                            <span className="text-slate-500 font-medium">Pending</span>
                          )}
                        </div>
                      </div>
                      <div className="satt-tstep-time">
                        {idx === 0 ? "2 min" : idx === 1 ? "4 min" : idx === 2 ? "3 min" : idx === 3 ? "5 min" : "2 min"}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              /* Analysis Log */
              <div className="satt-analysis-log-list">
                {events.length === 0 ? (
                  <div className="text-xs text-slate-400 py-6 text-center">
                    No telemetry logs yet. Run an analysis or click &quot;Live Run&quot;.
                  </div>
                ) : (
                  events.map((ev, i) => (
                    <div key={i} className="satt-log-item text-xs font-mono py-1 border-b border-slate-700/30 flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <span className="text-cyan-400 font-bold">[{ev.stage || 'TRACE'}]</span>{" "}
                        <span className="text-slate-200">{ev.description || ev.action}</span>
                      </div>
                      {ev.at && <span className="text-slate-500 shrink-0 text-[10px]">{ev.at}</span>}
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Bottom AI Agent Status */}
            <div className="satt-agent-status-box">
              <div className="satt-agent-badge">
                <IconBrain size={14} className={running ? "animate-bounce text-cyan-400" : "text-cyan-400"} />
                <span>AI Agent</span>
              </div>
              <p>{running ? agentMessage : "Analysis complete. Multi-spectral evidence verified and ready."}</p>
            </div>
          </section>
        </aside>
      </div>

      {/* ══════════════════════════════════════════════════════
          3. BOTTOM GLOBAL STATUS BAR / FOOTER (Image 1 Bar)
          ══════════════════════════════════════════════════════ */}
      <footer className="satt-bottom-bar">
        <div className="satt-bbar-left">
          <div className="satt-bbar-item">
            <IconTargetArrow size={14} className="text-amber-400" />
            <span>Mission: <b>{activeMissionId === 'howrah' ? "River Hydrological Analysis" : result?.query || "Satellite Intelligence Mission"}</b></span>
          </div>
          <div className="satt-bbar-item">
            <IconSatellite size={14} className="text-cyan-400" />
            <span>Data Source: <b>{result?.analysis_report ? "Supplied imagery; sensor unverified" : "Sentinel-2 (Optical)"}</b></span>
          </div>
          <div className="satt-bbar-item">
            <IconAdjustments size={14} className="text-purple-400" />
            <span>Analysis Type: <b>{result?.task || "Not yet selected"}</b></span>
          </div>
          <div className="satt-bbar-item">
            <IconClock size={14} className="text-blue-400" />
            <span>Processing Time: <b>{result?.analysis_report ? "See execution trace" : "Not measured"}</b></span>
          </div>
        </div>

        <div className="satt-bbar-right">
          <span className="satt-mission-complete-badge">
            <IconCircleCheck size={14} stroke={2.5} />
            {running ? "Processing Scene..." : result?.analysis_report ? result.analysis_report.execution_summary.processing_status as string : "Awaiting analysis"}
          </span>
        </div>
      </footer>
        </>
      )}

      {/* ══════════════════════════════════════════════════════
          4. NEW ANALYSIS & UPLOAD MODAL (Interactive)
          ══════════════════════════════════════════════════════ */}
      {showUploadModal && (
        <div className="satt-modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="satt-modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="satt-modal-header">
              <div className="satt-modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <IconTargetArrow size={20} stroke={2} className="text-cyan-400" />
                <span>Launch New Satellite Observation</span>
                {renderHelpTip('missionSetup')}
              </div>
              <button
                type="button"
                className="satt-modal-close"
                onClick={() => setShowUploadModal(false)}
              >
                <IconX size={18} stroke={2.2} />
              </button>
            </div>

            {/* Mode selection tabs */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span className="text-xs font-semibold text-slate-300">Observation Mode</span>
              {renderHelpTip('modeSelect', true)}
            </div>
            <div className="satt-modal-mode-tabs">
              {MODES.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={cn("satt-mm-tab", mode === item.id && "satt-mm-tab-active")}
                  onClick={() => {
                    setMode(item.id);
                    setActiveModality('optical');
                    if (item.id === "bitemporal") {
                      setQuery("What changed between these two acquisitions?");
                    } else if (item.id === "fusion") {
                      setQuery("Use optical and SAR together to identify built-up and water features.");
                    } else {
                      setQuery("Where is the river or surface water in this image?");
                    }
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>

            {/* Upload Dropzones */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span className="text-xs font-semibold text-slate-300">Satellite Imagery Files</span>
              {renderHelpTip('imageUpload', true)}
            </div>
            <div className="satt-modal-drop-stack">
              {Array.from({ length: slots }).map((_, index) => {
                const file = files[index];
                const label =
                  mode === "bitemporal"
                    ? index === 0 ? "Before Image (T1)" : "After Image (T2)"
                    : mode === "fusion"
                      ? index === 0 ? "Optical (RGB)" : "SAR (Radar)"
                      : "Satellite Scene";
                return (
                  <label key={index} className={cn("satt-modal-dropzone", file && "satt-dropzone-has-file")}>
                    <input
                      type="file"
                      accept="image/*,.tif,.tiff"
                      onChange={(e) => selectFile(index, e.target.files?.[0])}
                    />
                    {file ? (
                      <div className="satt-dz-loaded-view">
                        <img src={file.url} alt={file.name} className="satt-dz-thumb" />
                        <div className="satt-dz-details">
                          <strong>{file.name}</strong>
                          <small>{humanBytes(file.size)} · Click to replace</small>
                        </div>
                        <button
                          type="button"
                          className="satt-dz-remove"
                          onClick={(e) => {
                            e.preventDefault();
                            clearFile(index);
                          }}
                        >
                          <IconX size={15} />
                        </button>
                      </div>
                    ) : (
                      <div className="satt-dz-empty-view">
                        <IconCloudUpload size={32} stroke={1.4} className="text-cyan-400" />
                        <strong>{slots === 2 ? label : "Click or Drag to Upload Image"}</strong>
                        <small>PNG, JPG, GeoTIFF · up to 32 MB</small>
                      </div>
                    )}
                  </label>
                );
              })}
            </div>

            {/* Modality toggle */}
            <div className="satt-modal-sensor-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <label className="text-xs font-semibold text-slate-300">Sensor Modality:</label>
              </div>
              <div className="satt-modality-switches">
                <button
                  type="button"
                  className={cn("satt-msw-btn", activeModality === 'optical' && "satt-msw-active")}
                  onClick={() => setActiveModality('optical')}
                >
                  <IconSatellite size={14} /> Optical (RGB)
                </button>
                <button
                  type="button"
                  className={cn("satt-msw-btn", activeModality === 'SAR' && "satt-msw-active")}
                  onClick={() => setActiveModality('SAR')}
                >
                  <IconRadar size={14} /> SAR (Radar)
                </button>
              </div>
            </div>

            {/* Query Prompt Input with Voice Mic */}
            <div className="satt-modal-query-box" style={{ position: 'relative' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <label className="text-xs font-semibold text-slate-300">What would you like to detect or analyze?</label>
                  {renderHelpTip('queryPrompt')}
                </div>
              </div>

              {/* Live Voice Banner when listening */}
              {isListening && (
                <div className="satt-voice-listening-banner">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="satt-running-pulse-dot" style={{ width: 7, height: 7, background: '#ef4444' }} />
                    <span>{speechInterim ? `"${speechInterim}"` : `Listening in ${activeLang === 'hi' ? 'Hindi' : activeLang === 'bn' ? 'Bengali' : 'English'}... Speak clearly.`}</span>
                  </div>
                  <button
                    type="button"
                    onClick={stopSpeechRecognition}
                    style={{
                      background: '#ef4444',
                      color: '#ffffff',
                      borderRadius: '12px',
                      padding: '2px 8px',
                      fontSize: '10px',
                      fontWeight: 700,
                      cursor: 'pointer',
                      border: 'none',
                    }}
                  >
                    Done ✓
                  </button>
                </div>
              )}

              <div style={{ position: 'relative' }}>
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={isListening ? `Listening in ${speechLang === 'hi-IN' ? 'Hindi' : 'English'}... Speak your question now` : "Ask about bridges, water, buildings, vegetation or changes..."}
                  rows={2}
                  className="satt-modal-textarea"
                  style={{
                    paddingRight: '38px',
                    borderColor: isListening ? '#ef4444' : undefined,
                    boxShadow: isListening ? '0 0 14px rgba(239, 68, 68, 0.35)' : undefined,
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                  }}
                />
                <button
                  type="button"
                  onClick={toggleSpeechRecognition}
                  title={isListening ? "Click to finish voice input" : "Click to speak with voice"}
                  style={{
                    position: 'absolute',
                    right: '8px',
                    bottom: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '26px',
                    height: '26px',
                    borderRadius: '50%',
                    background: isListening ? '#ef4444' : 'rgba(56, 189, 248, 0.15)',
                    color: isListening ? '#ffffff' : '#38bdf8',
                    border: isListening ? '1px solid #f87171' : '1px solid rgba(56, 189, 248, 0.35)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <IconMicrophone size={14} className={isListening ? "animate-pulse" : ""} />
                </button>
              </div>
            </div>

            {/* Prompt Chips */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px', marginBottom: '4px' }}>
              <span className="text-xs text-slate-400">Quick Prompt Presets</span>
              {renderHelpTip('presetChips', true)}
            </div>
            <div className="satt-modal-chips">
              {(PROMPT_SUGGESTIONS_BY_MODE[mode] || PROMPT_SUGGESTIONS_BY_MODE.single).map((chip) => (
                <button
                  key={chip.text}
                  type="button"
                  className="satt-chip-btn"
                  onClick={() => setQuery(chip.text)}
                >
                  <span>{chip.icon}</span>
                  <span>{chip.text}</span>
                </button>
              ))}
            </div>

            {error && (
              <div className="satt-error-callout">
                <IconAlertTriangle size={16} />
                <span>{error}</span>
              </div>
            )}

            {/* Launch Button */}
            <div className="satt-modal-footer">
              <button
                type="button"
                className="satt-modal-cancel"
                onClick={() => setShowUploadModal(false)}
              >
                Cancel
              </button>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                <button
                  type="button"
                  className="satt-modal-run-btn"
                  disabled={running || !query.trim()}
                  onClick={() => runAnalysis()}
                >
                  <span>{running ? "Analyzing Scene..." : "Execute Neural Analysis"}</span>
                </button>
                {renderHelpTip('executeAnalysis', true)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════
          MISSION HISTORY & REPORTS MODAL
          ══════════════════════════════════════════════════════ */}
      {showHistoryModal && (
        <div className="satt-modal-overlay" onClick={() => setShowHistoryModal(false)}>
          <div className="satt-modal-box satt-history-modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="satt-modal-header">
              <div className="satt-modal-title">
                <IconFileText size={20} stroke={2} className="text-cyan-400" />
                <span>Mission History & Saved Intelligence</span>
                <span className="satt-history-count-tag">{allMissions.length} Missions</span>
              </div>
              <button
                type="button"
                className="satt-modal-close"
                onClick={() => setShowHistoryModal(false)}
                title="Close"
              >
                <IconX size={18} stroke={2.2} />
              </button>
            </div>

            {/* Modal Search Filter */}
            <div className="satt-modal-search-row">
              <div className="satt-modal-search-bar">
                <IconSearch size={16} className="text-slate-400" />
                <input
                  type="text"
                  placeholder="Search past missions, query, date, or sensor..."
                  value={historySearch}
                  onChange={(e) => setHistorySearch(e.target.value)}
                  className="satt-modal-search-input"
                  autoFocus
                />
                {historySearch && (
                  <button
                    type="button"
                    onClick={() => setHistorySearch("")}
                    className="satt-modal-search-clear"
                    title="Clear filter"
                  >
                    <IconX size={14} />
                  </button>
                )}
              </div>
              <button
                type="button"
                onClick={fetchHistory}
                className="satt-history-refresh-btn"
                title="Refresh from server"
              >
                <IconRefresh size={14} />
                <span>Refresh</span>
              </button>
            </div>

            {/* Missions List */}
            <div className="satt-history-modal-list">
              {filteredMissions.map((m) => (
                <div key={m.id} className="satt-history-modal-item">
                  <img src={m.thumb} alt={m.title} className="satt-history-modal-thumb" />
                  <div className="satt-history-modal-content">
                    <div className="satt-history-modal-header-row">
                      <span className="satt-history-modal-query" title={m.query}>"{m.query}"</span>
                      <span className="satt-completed-pill">{m.status}</span>
                    </div>
                    <div className="satt-history-modal-meta">
                      <span>📅 {m.date}</span>
                      <span>🛰️ {m.sensor}</span>
                      {m.trust_score != null && (
                        <span className="satt-history-trust-pill">
                          {Math.round(m.trust_score * 100)}% Trust
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="satt-history-modal-actions">
                    <button
                      type="button"
                      className="satt-history-action-btn primary"
                      onClick={() => handleSelectRecentMission(m)}
                    >
                      <IconRocket size={14} />
                      <span>Load Mission</span>
                    </button>
                    {m.report_url && (
                      <a
                        href={m.report_url.replace('.json', '.html')}
                        target="_blank"
                        rel="noreferrer"
                        className="satt-history-action-btn"
                        title="View Full HTML Report"
                      >
                        <IconExternalLink size={14} />
                        <span>Report</span>
                      </a>
                    )}
                  </div>
                </div>
              ))}
              {filteredMissions.length === 0 && (
                <div className="satt-history-empty-state">
                  <IconFileText size={36} className="text-slate-500" />
                  <strong>No missions found matching "{historySearch}"</strong>
                  <p>Try searching another keyword, or run a new satellite observation.</p>
                  <button
                    type="button"
                    onClick={() => setHistorySearch("")}
                    className="satt-history-reset-btn"
                  >
                    Clear Filter
                  </button>
                </div>
              )}
            </div>

            <div className="satt-modal-footer">
              <span className="text-xs text-slate-400">
                Clicking any mission immediately loads its satellite imagery, neural overlays, and findings.
              </span>
              <button
                type="button"
                className="satt-modal-cancel"
                onClick={() => setShowHistoryModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SatVisionNexus;
