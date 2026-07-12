// Shared types for the DesignCalc frontend — mirror the /api/generate request + response.

export type Units = "ft" | "m";

export interface Position {
  depth_m: number;
  lateral_m: number;
  depth_ft: number;
  lateral_ft: number;
}

export interface Subsystem {
  id: string;
  role: string;          // "Mains", "Sub Array", "Delay 1", ...
  side: "L" | "R" | "C";
  label: string;         // "Mains L"
  box_model: string;     // "KSL", "V-Series", "SL-SUB", "A-Series"
  box_count: number;
  position: Position;
  aim_deg: number | null;
  lowest_edge_ft: number | null;
  delay_ms: number | null;
  source_label: string;
}

export interface PartLine {
  category: string;
  item: string;
  qty: number;
}

export interface Venue {
  width_ft: number;
  depth_ft: number;
  width_m: number;
  depth_m: number;
  front_offset_m: number;
}

export interface Design {
  venue: Venue;
  subsystems: Subsystem[];
  parts: PartLine[];
}

export interface DelayRing {
  ring: number;
  x_m: number;
  system: string;
  delay_ms: number;
  covers_to_m: number;
  lcr: boolean;
}

export interface Meta {
  integrity: string;
  frame_angle: number;
  lowest_edge_ft: number;
  mains_coverage_end_m: number;
  coverage_end_is_estimate: boolean;
  out_fills: boolean;
  delay_rings: DelayRing[];
  venue: string;
}

export interface Notice {
  field: string;
  requested: number;
  applied: number;
  message: string;
}

export interface DelayRingOverride {
  distance_ft: number;
  boxes_per_side?: number | null;
}

export interface AdvancedMains {
  spread_ft?: number | null;
  boxes_per_side?: number | null;
}

export interface AdvancedSubs {
  stacks?: number | null;
  spacing_ft?: number | null;
}

export interface AdvancedOutFills {
  enabled?: boolean | null;
  boxes_per_side?: number | null;
}

export interface AdvancedFrontFills {
  enabled?: boolean | null;
  count?: number | null;
}

export interface AdvancedDelays {
  mode?: "auto" | "manual";
  rings?: DelayRingOverride[];
}

export interface AdvancedInput {
  mains?: AdvancedMains;
  subs?: AdvancedSubs;
  out_fills?: AdvancedOutFills;
  front_fills?: AdvancedFrontFills;
  delays?: AdvancedDelays;
  sources?: Record<string, string>;
}

export interface EffectiveDelays {
  mode?: "auto" | "manual";
  rings?: { distance_ft: number; boxes_per_side: number }[];
}

export interface Effective {
  mains?: { spread_ft?: number; boxes_per_side?: number };
  subs?: { stacks?: number; spacing_ft?: number };
  out_fills?: { enabled?: boolean; boxes_per_side?: number | null };
  front_fills?: { enabled?: boolean; count?: number };
  delays?: EffectiveDelays;
}

export interface GenerateRequest {
  width_ft: number;
  depth_ft: number;
  units?: Units;
  advanced?: AdvancedInput;
}

export interface GenerateResponse {
  design: Design;
  meta: Meta;
  effective: Effective;
  notices: Notice[];
  dbpr_base64: string;
  filename: string;
}

export interface ApiError {
  error: string;
  messages?: string[];
  message?: string;
  detail?: string;
}
