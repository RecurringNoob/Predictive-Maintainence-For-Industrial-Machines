"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { LucideIcon, AlertCircle } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface GaugeCardProps {
  title: string;
  value: number | string;
  unit: string;
  icon: LucideIcon;
  progress?: number;
  isAssumed?: boolean;
  description?: string;
}

export function GaugeCard({ title, value, unit, icon: Icon, progress, isAssumed, description }: GaugeCardProps) {
  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="flex items-center gap-2">
          {isAssumed && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <AlertCircle className="h-4 w-4 text-amber-500" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Assumed feature (No real-time sensor)</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
          <Icon className="h-4 w-4 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {value}<span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>
        </div>
        {progress !== undefined && (
          <div className="mt-3 space-y-1">
            <Progress value={progress} className="h-1" />
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{description}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
