"use client";

import { useState, useEffect, useRef } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Thermometer,
  Zap,
  Activity,
  Server,
  Gauge,
  History as HistoryIcon,
  PlayCircle,
  AlertTriangle,
  Activity as StatusIcon,
  Wifi,
  WifiOff,
} from "lucide-react";
import Link from "next/link";
import {
  latestReading as initialReading,
  latestPrediction as initialPrediction,
} from "@/lib/data";
import { GaugeCard } from "@/components/dashboard/gauge-card";
import { PredictionBadge } from "@/components/dashboard/prediction-badge";
import { cn } from "@/lib/utils";
import {
  connectSSE,
  fetchLatestReading,
  fetchLatestPrediction,
  fetchMachineStatus,
} from "@/lib/api";
import type { SensorReading, Prediction } from "@/lib/types";

// Assumed feature keys that come back from the backend (snake_case field names)
const ASSUMED_FEATURE_LABELS: Record<string, string> = {
  process_temp_k: "Process Temperature",
  rpm: "RPM",
  torque_nm: "Torque",
  tool_wear_min: "Tool Wear",
};

function formatAssumedFeatures(features?: string[]): string[] {
  if (!features) return [];
  return features.map((f) => ASSUMED_FEATURE_LABELS[f] ?? f);
}

export default function DashboardPage() {
  const [reading, setReading] = useState<SensorReading>(initialReading);
  const [prediction, setPrediction] = useState<Prediction>(initialPrediction);
  const [isLive, setIsLive] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [machineStatus, setMachineStatus] = useState("Connecting...");
  const [lastStatusUpdate, setLastStatusUpdate] = useState<string | null>(null);
  const [sseError, setSseError] = useState(false);

  const cleanupSSE = useRef<(() => void) | null>(null);

  // ── Machine Status polling (every 2 minutes) ───────────────────────────────
  useEffect(() => {
    const poll = async () => {
      const status = await fetchMachineStatus();
      if (status) {
        setMachineStatus(status);
      } else {
        // Simulation fallback
        const statuses = ["Healthy", "Operational", "Warning", "Attention Required"];
        setMachineStatus(statuses[Math.floor(Math.random() * statuses.length)]);
      }
      setLastStatusUpdate(new Date().toLocaleTimeString());
    };

    poll();
    const id = setInterval(poll, 120_000);
    return () => clearInterval(id);
  }, []);

  // ── Seed from REST on mount so there's real data immediately ──────────────
  useEffect(() => {
    (async () => {
      const [r, p] = await Promise.all([
        fetchLatestReading(),
        fetchLatestPrediction(),
      ]);
      if (r) setReading(r);
      if (p) setPrediction(p);
      if (r || p) setLastSync(new Date().toLocaleTimeString());
    })();
  }, []);

  // ── SSE connection ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isLive) {
      cleanupSSE.current?.();
      cleanupSSE.current = null;
      setIsConnected(false);
      return;
    }

    const cleanup = connectSSE({
      onReading: (r) => {
        setReading(r);
        setLastSync(new Date().toLocaleTimeString());
        setIsConnected(true);
        setSseError(false);
      },
      onPrediction: (p) => {
        setPrediction(p);
      },
      onError: () => {
        setIsConnected(false);
        setSseError(true);
        // Fall back to REST polling when SSE fails
        startRestFallback();
      },
    });

    cleanupSSE.current = cleanup;
    return () => {
      cleanup();
      cleanupSSE.current = null;
    };
  }, [isLive]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── REST fallback polling (only active when SSE is down) ──────────────────
  const restFallbackRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function startRestFallback() {
    if (restFallbackRef.current) return; // already running
    restFallbackRef.current = setInterval(async () => {
      const [r, p] = await Promise.all([
        fetchLatestReading(),
        fetchLatestPrediction(),
      ]);
      if (r) {
        setReading(r);
        setLastSync(new Date().toLocaleTimeString());
      }
      if (p) setPrediction(p);
    }, 15_000);
  }

  // Clean up fallback when SSE reconnects or component unmounts
  useEffect(() => {
    if (!sseError && restFallbackRef.current) {
      clearInterval(restFallbackRef.current);
      restFallbackRef.current = null;
    }
  }, [sseError]);

  useEffect(() => {
    return () => {
      if (restFallbackRef.current) clearInterval(restFallbackRef.current);
    };
  }, []);

  const displayedAssumedFeatures = formatAssumedFeatures(reading.assumedFeatures);

  return (
    <div className="space-y-6">
      {/* Header row */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Live Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time status of Machine M-001 via ThingSpeak IoT.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* SSE connection indicator */}
          {isLive && (
            <span title={isConnected ? "SSE connected" : sseError ? "SSE failed — polling" : "Connecting…"}>
              {isConnected ? (
                <Wifi className="h-4 w-4 text-emerald-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-amber-500" />
              )}
            </span>
          )}
          <Badge
            variant={isLive ? "default" : "secondary"}
            className={cn(isLive && isConnected && "bg-emerald-500 animate-pulse")}
          >
            {isLive ? (isConnected ? "Live Stream Active" : "Connecting…") : "Stream Paused"}
          </Badge>
          <span className="text-xs text-muted-foreground tabular-nums">
            Sync: {lastSync ?? "..."}
          </span>
        </div>
      </div>

      {/* Cards grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Machine Status */}
        <Card className="border-accent/20 bg-accent/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Machine Status</CardTitle>
            <StatusIcon className="h-4 w-4 text-accent" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{machineStatus}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Last Poll: {lastStatusUpdate ?? "Connecting..."}
            </p>
          </CardContent>
        </Card>

        {/* Latest ML Prediction */}
        <Card className="md:col-span-2 lg:col-span-2 border-primary/20 bg-primary/5">
          <CardHeader>
            <CardTitle className="text-lg">Latest ML Prediction</CardTitle>
            <CardDescription>
              Generated by {prediction.modelVersion} engine
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <PredictionBadge
              type={prediction.failureType}
              confidence={prediction.confidence}
            />
            {displayedAssumedFeatures.length > 0 && (
              <div className="flex items-start gap-2 p-3 rounded-md bg-amber-50 border border-amber-200 text-amber-800 text-xs dark:bg-amber-950/30 dark:border-amber-800 dark:text-amber-400">
                <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Incomplete Sensor Data</p>
                  <p>
                    Prediction uses assumed values for:{" "}
                    {displayedAssumedFeatures.join(", ")}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Gauge cards */}
        <GaugeCard
          title="Air Temperature"
          value={reading.airTempK}
          unit="K"
          icon={Thermometer}
          progress={((reading.airTempK - 290) / 20) * 100}
          description="Ambient range: 290K – 310K"
        />
        <GaugeCard
          title="Process Temperature"
          value={reading.processTempK}
          unit="K"
          icon={Zap}
          isAssumed={reading.assumedFeatures?.includes("process_temp_k")}
          progress={((reading.processTempK - 300) / 40) * 100}
          description="Operating range: 300K – 340K"
        />
        <GaugeCard
          title="Rotational Speed"
          value={reading.rpm}
          unit="RPM"
          icon={Gauge}
          isAssumed={reading.assumedFeatures?.includes("rpm")}
          progress={(reading.rpm / 3000) * 100}
          description="Max rated: 3000 RPM"
        />
        <GaugeCard
          title="Torque"
          value={reading.torqueNm}
          unit="Nm"
          icon={Activity}
          isAssumed={reading.assumedFeatures?.includes("torque_nm")}
          progress={(reading.torqueNm / 80) * 100}
          description="Peak torque: 80 Nm"
        />
        <GaugeCard
          title="Tool Wear"
          value={reading.toolWearMin}
          unit="min"
          icon={Server}
          progress={(reading.toolWearMin / 250) * 100}
          description="Replace at: 250 min"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-3">
            <Button asChild variant="outline" className="gap-2">
              <Link href="/history">
                <HistoryIcon className="h-4 w-4" /> View History
              </Link>
            </Button>
            <Button asChild variant="outline" className="gap-2">
              <Link href="/predict">
                <PlayCircle className="h-4 w-4" /> Manual Prediction
              </Link>
            </Button>
            <Button variant="ghost" onClick={() => setIsLive((v) => !v)}>
              {isLive ? "Pause Stream" : "Resume Stream"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}