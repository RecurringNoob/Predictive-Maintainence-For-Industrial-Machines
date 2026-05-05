/**
 * lib/api.ts — Centralized API client for MachineWise.
 *
 * Maps snake_case backend responses → camelCase frontend types.
 * All functions return null on failure so callers can fall back gracefully.
 */

import type { SensorReading, Prediction, FailureType, MachineType } from '@/lib/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

// ── Raw backend shapes ────────────────────────────────────────────────────────

interface RawReading {
  id: string;
  recorded_at: string;
  machine_type: string;
  air_temp_k: number;
  process_temp_k: number;
  rpm: number;
  torque_nm: number;
  tool_wear_min: number;
  source: 'iot' | 'manual';
  assumed_features?: string[] | null;
}

interface RawPrediction {
  id: string;
  reading_id: string;
  predicted_at: string;
  failure_type: string;
  confidence: number;
  model_version: string;
}

interface RawPredictResponse {
  reading: RawReading;
  prediction: RawPrediction;
}

interface RawStatus {
  status: string;
}

// ── Mappers ───────────────────────────────────────────────────────────────────

function mapReading(r: RawReading): SensorReading {
  return {
    id: r.id,
    recordedAt: r.recorded_at,
    machineType: r.machine_type as MachineType,
    airTempK: r.air_temp_k,
    processTempK: r.process_temp_k,
    rpm: r.rpm,
    torqueNm: r.torque_nm,
    toolWearMin: r.tool_wear_min,
    source: r.source,
    assumedFeatures: r.assumed_features ?? [],
  };
}

function mapPrediction(p: RawPrediction): Prediction {
  return {
    id: p.id,
    readingId: p.reading_id,
    predictedAt: p.predicted_at,
    failureType: p.failure_type as FailureType,
    confidence: p.confidence,
    modelVersion: p.model_version,
  };
}

// ── API calls ─────────────────────────────────────────────────────────────────

async function get<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${BASE_URL}${path}`, { cache: 'no-store' });
    if (!res.ok) return null;
    return res.json() as Promise<T>;
  } catch {
    return null;
  }
}

export async function fetchLatestReading(): Promise<SensorReading | null> {
  const raw = await get<RawReading>('/v1/readings/latest');
  return raw ? mapReading(raw) : null;
}

export async function fetchLatestPrediction(): Promise<Prediction | null> {
  const raw = await get<RawPrediction>('/v1/predictions/latest');
  return raw ? mapPrediction(raw) : null;
}

export async function fetchMachineStatus(): Promise<string | null> {
  const raw = await get<RawStatus>('/v1/status');
  return raw?.status ?? null;
}

export async function fetchHistoricalReadings(
  from?: string,
  to?: string,
  limit = 500,
): Promise<SensorReading[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (from) params.set('from', from);
  if (to) params.set('to', to);

  const raw = await get<{ data: RawReading[]; total: number }>(
    `/v1/readings?${params}`,
  );
  return raw?.data.map(mapReading) ?? [];
}

export interface ManualPredictPayload {
  machine_type: MachineType;
  air_temp_k: number;
  process_temp_k: number;
  rpm: number;
  torque_nm: number;
  tool_wear_min: number;
  source: 'manual';
}

export async function runManualPrediction(
  payload: ManualPredictPayload,
): Promise<{ reading: SensorReading; prediction: Prediction } | null> {
  try {
    const res = await fetch(`${BASE_URL}/v1/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) return null;
    const raw: RawPredictResponse = await res.json();
    return {
      reading: mapReading(raw.reading),
      prediction: mapPrediction(raw.prediction),
    };
  } catch {
    return null;
  }
}

// ── SSE helper ────────────────────────────────────────────────────────────────

export interface SSEHandlers {
  onReading: (r: SensorReading) => void;
  onPrediction: (p: Prediction) => void;
  onError?: () => void;
}

/**
 * Opens an SSE connection to /v1/stream.
 * Returns a cleanup function — call it to close the EventSource.
 */
export function connectSSE(handlers: SSEHandlers): () => void {
  const es = new EventSource(`${BASE_URL}/v1/stream`);

  es.addEventListener('reading', (e) => {
    try {
      const raw: RawReading = JSON.parse((e as MessageEvent).data);
      handlers.onReading(mapReading(raw));
    } catch {
      // malformed JSON — ignore
    }
  });

  es.addEventListener('prediction', (e) => {
    try {
      const raw: RawPrediction = JSON.parse((e as MessageEvent).data);
      handlers.onPrediction(mapPrediction(raw));
    } catch {
      // malformed JSON — ignore
    }
  });

  es.onerror = () => {
    handlers.onError?.();
  };

  return () => es.close();
}