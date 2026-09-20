export type Mode = "single" | "bitemporal" | "fusion";

export type TaskKind = "scene-VQA" | "change-VQA" | "grounding" | "fusion-VQA";

export type AgentResult = {
  query: string;
  mode: Mode;
  task: TaskKind;
  model: string;
  answer: string;
  confidence: number;
  parameters: Record<string, string | number>;
  timestamp: string;
  changeHighlight: boolean;
};

export const MODES: { id: Mode; label: string; slots: number }[] = [
  { id: "single", label: "Single image", slots: 1 },
  { id: "bitemporal", label: "Bi-temporal (before/after)", slots: 2 },
  { id: "fusion", label: "Optical + SAR pair", slots: 2 },
];

export const EXAMPLE_QUERIES = [
  "Describe the land-cover and major objects visible in this image.",
  "Highlight the water body referred to in the query.",
  "What changed between these two dates, and where did the change occur?",
  "Use the optical and SAR images together to identify built-up and water-covered regions.",
  "Has the built-up area increased, decreased, or remained unchanged?",
];

export const MODEL_REGISTRY = [
  { id: "rs-vqa-v2", task: "scene-VQA" as TaskKind },
  { id: "rs-change-vqa-v1", task: "change-VQA" as TaskKind },
  { id: "sar-fusion-v1", task: "fusion-VQA" as TaskKind },
  { id: "grounding-v1", task: "grounding" as TaskKind },
];

export const AGENT_STEPS = [
  "Validating inputs",
  "Classifying task",
  "Running model",
  "Combining evidence",
];

const CHANGE_WORDS = [
  "change",
  "changed",
  "increase",
  "increased",
  "decrease",
  "decreased",
  "unchanged",
  "compare",
  "between these two",
  "grown",
  "expansion",
];

const GROUND_WORDS = ["highlight", "where is", "locate", "point to", "mark the", "segment"];

function hashConfidence(seed: string, min: number, max: number) {
  let h = 0;
  for (let i = 0; i < seed.length; i += 1) h = (h * 31 + seed.charCodeAt(i)) % 100000;
  return min + (h % ((max - min) * 10)) / 10;
}

export function classify(query: string, mode: Mode): TaskKind {
  const q = query.toLowerCase();
  if (mode === "fusion") return "fusion-VQA";
  if (GROUND_WORDS.some((w) => q.includes(w))) return "grounding";
  if (mode === "bitemporal" && CHANGE_WORDS.some((w) => q.includes(w))) return "change-VQA";
  if (CHANGE_WORDS.some((w) => q.includes(w)) && mode === "bitemporal") return "change-VQA";
  return "scene-VQA";
}

const MODEL_FOR: Record<TaskKind, string> = {
  "scene-VQA": "rs-vqa-v2",
  "change-VQA": "rs-change-vqa-v1",
  "fusion-VQA": "sar-fusion-v1",
  grounding: "grounding-v1",
};

const PARAMS_FOR: Record<TaskKind, Record<string, string | number>> = {
  "scene-VQA": { tile_size: 512, bands: "R,G,B,NIR", top_k: 5, temperature: 0.2 },
  "change-VQA": {
    tile_size: 512,
    change_threshold: 0.34,
    coregistration: "phase-correlation",
    bands: "R,G,B,NIR",
  },
  "fusion-VQA": {
    tile_size: 384,
    fusion: "late-attention",
    sar_polarisation: "VV+VH",
    speckle_filter: "refined-lee",
  },
  grounding: { tile_size: 512, box_threshold: 0.28, mask_iou: 0.61, max_regions: 3 },
};

function answerFor(task: TaskKind, query: string): string {
  switch (task) {
    case "change-VQA":
      return "Comparing the two acquisitions, the dominant change is built-up expansion along the north-eastern edge of the settlement: approximately 4.1 ha of bare soil and low vegetation has been converted to impervious surface (+12.6% built-up area). The water body in the south-west has contracted slightly (-0.7 ha), consistent with seasonal drawdown rather than structural change. Vegetated parcels in the western third of the scene remain stable. Highest change activity is concentrated in the dashed region marked on the after image.";
    case "grounding":
      return "The referenced water body is localised in the lower-left quadrant of the scene, spanning roughly 320 x 210 m with an irregular southern shoreline. Its spectral signature (low NIR reflectance, high NDWI ~0.48) confirms open water rather than shadow. A secondary narrow channel extends north-east from the main body and is included in the returned region mask at reduced confidence.";
    case "fusion-VQA":
      return "Fusing the optical scene with the co-registered SAR acquisition: built-up regions appear as high-backscatter clusters (VV > -6 dB) coinciding with bright, geometrically regular optical parcels, concentrated in the central and eastern blocks. Water-covered regions show specular low backscatter (VV < -18 dB) plus low NIR reflectance, isolating the south-western basin and a narrow channel. SAR resolves two built-up patches obscured by thin cloud in the optical band, which optical-only inference would have missed.";
    default:
      return `The scene is a mixed peri-urban landscape. Land cover is roughly 46% vegetation (agricultural parcels with regular field boundaries in the west), 29% built-up impervious surface forming a dense block in the centre-east, 14% bare soil along transitional edges, and 11% open water in the south-west. Major objects include a road corridor bisecting the settlement, several large-roof structures likely industrial or storage, and a linear embankment along the water margin.${query.trim().endsWith("?") ? "" : ""}`;
  }
}

export function runAgent(query: string, mode: Mode): AgentResult {
  const task = classify(query, mode);
  return {
    query: query.trim(),
    mode,
    task,
    model: MODEL_FOR[task],
    answer: answerFor(task, query),
    confidence: Number(hashConfidence(query + mode + task, 82, 96).toFixed(1)),
    parameters: PARAMS_FOR[task],
    timestamp: new Date().toISOString(),
    changeHighlight: mode === "bitemporal" && task === "change-VQA",
  };
}

export function buildReport(result: AgentResult) {
  return JSON.stringify(
    {
      product: "SatQuery AI",
      generated_at: result.timestamp,
      mode: result.mode,
      query: result.query,
      task: result.task,
      model: result.model,
      parameters: result.parameters,
      confidence_percent: result.confidence,
      answer: result.answer,
    },
    null,
    2,
  );
}
