"use client";

import { Badge } from "@/components/ui/badge";
import { FailureType } from "@/lib/types";
import { cn } from "@/lib/utils";
import { CheckCircle2, AlertTriangle, XCircle, Info } from "lucide-react";

interface PredictionBadgeProps {
  type: FailureType;
  confidence: number;
  className?: string;
}

export function PredictionBadge({ type, confidence, className }: PredictionBadgeProps) {
  const isHealthy = type === 'No Failure';
  const confidencePercent = Math.round(confidence * 100);

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="flex items-center gap-2">
        <Badge 
          className={cn(
            "px-3 py-1 text-sm font-semibold flex items-center gap-2",
            isHealthy ? "bg-emerald-500 hover:bg-emerald-600" : "bg-destructive hover:bg-destructive/90"
          )}
        >
          {isHealthy ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
          {type}
        </Badge>
        <span className="text-xs text-muted-foreground font-medium">
          {confidencePercent}% Confidence
        </span>
      </div>
      <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
        <div 
          className={cn(
            "h-full transition-all duration-500",
            isHealthy ? "bg-emerald-500" : "bg-destructive"
          )}
          style={{ width: `${confidencePercent}%` }}
        />
      </div>
    </div>
  );
}
