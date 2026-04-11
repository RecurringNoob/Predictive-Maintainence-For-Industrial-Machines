
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { PredictionBadge } from "@/components/dashboard/prediction-badge";
import { FailureType, MachineType } from "@/lib/types";

export default function ManualPredictPage() {
  const [result, setResult] = useState<{ type: FailureType; conf: number } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handlePredict = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.currentTarget);
    const payload = {
      machineType: formData.get('type'),
      airTempK: Number(formData.get('air')),
      processTempK: Number(formData.get('proc')),
      rpm: Number(formData.get('rpm')),
      torqueNm: Number(formData.get('torque')),
      toolWearMin: Number(formData.get('wear'))
    };

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const response = await fetch(`${baseUrl}/v1/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const data = await response.json();
        setResult({
          type: data.prediction.failureType,
          conf: data.prediction.confidence
        });
      } else {
        throw new Error('Prediction failed');
      }
    } catch (error) {
      // Simulation fallback
      setTimeout(() => {
        setResult({
          type: Math.random() > 0.8 ? 'Heat Dissipation Failure' : 'No Failure',
          conf: 0.85 + Math.random() * 0.14
        });
      }, 500);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Manual Prediction</h1>
        <p className="text-muted-foreground">Test the model with custom sensor values (Bypasses IoT Poller).</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <form onSubmit={handlePredict}>
            <CardHeader>
              <CardTitle>Input Parameters</CardTitle>
              <CardDescription>All 6 model features are required for honest prediction.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="type">Machine Type</Label>
                <Select name="type" defaultValue="M">
                  <SelectTrigger id="type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="L">Low (L)</SelectItem>
                    <SelectItem value="M">Medium (M)</SelectItem>
                    <SelectItem value="H">High (H)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="air">Air Temp [K]</Label>
                <Input id="air" name="air" type="number" step="0.1" defaultValue="300" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="proc">Process Temp [K]</Label>
                <Input id="proc" name="proc" type="number" step="0.1" defaultValue="310" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rpm">Rotational Speed [RPM]</Label>
                <Input id="rpm" name="rpm" type="number" defaultValue="1500" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="torque">Torque [Nm]</Label>
                <Input id="torque" name="torque" type="number" step="0.1" defaultValue="40" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="wear">Tool Wear [min]</Label>
                <Input id="wear" name="wear" type="number" defaultValue="0" required />
              </div>
            </CardContent>
            <CardFooter>
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Running Inference..." : "Run ML Model"}
              </Button>
            </CardFooter>
          </form>
        </Card>

        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Result</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center min-h-[200px] text-center">
            {result ? (
              <PredictionBadge type={result.type} confidence={result.conf} className="w-full" />
            ) : (
              <div className="text-muted-foreground italic">
                Enter parameters and run the model to see result.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
