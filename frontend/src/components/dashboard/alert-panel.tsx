"use client";

import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { alerts as initialAlerts } from "@/lib/data";
import type { Alert } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

const severityVariantMap = {
  Critical: "destructive",
  High: "destructive",
  Medium: "secondary",
  Low: "outline",
} as const;

export function AlertPanel({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [alerts, setAlerts] = useState<Alert[]>(initialAlerts);

  const handleAcknowledge = (alertId: string) => {
    setAlerts((prevAlerts) =>
      prevAlerts.map((alert) =>
        alert.id === alertId ? { ...alert, status: "Acknowledged" } : alert
      )
    );
  };
  
  const handleSaveNote = (alertId: string, note: string) => {
    setAlerts((prevAlerts) =>
      prevAlerts.map((alert) =>
        alert.id === alertId ? { ...alert, notes: note, status: 'Acknowledged' } : alert
      )
    );
  };

  const activeAlerts = alerts.filter((alert) => alert.status === "Active");
  const historicalAlerts = alerts.filter(
    (alert) => alert.status === "Acknowledged"
  );

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg p-0">
        <SheetHeader className="p-6">
          <SheetTitle>Alerts</SheetTitle>
          <SheetDescription>
            View and manage active and historical system alerts.
          </SheetDescription>
        </SheetHeader>
        <Tabs defaultValue="active" className="w-full">
          <TabsList className="grid w-full grid-cols-2 rounded-none">
            <TabsTrigger value="active">Active</TabsTrigger>
            <TabsTrigger value="historical">Historical</TabsTrigger>
          </TabsList>
          <ScrollArea className="h-[calc(100vh-150px)]">
            <TabsContent value="active" className="p-6 pt-4">
                {activeAlerts.length > 0 ? (
                    <div className="space-y-4">
                        {activeAlerts.map((alert) => (
                            <AlertCard 
                              key={alert.id} 
                              alert={alert} 
                              onAcknowledge={handleAcknowledge} 
                              onSaveNote={handleSaveNote} 
                            />
                        ))}
                    </div>
                ) : (
                    <p className="text-center text-muted-foreground py-8">No active alerts.</p>
                )}
            </TabsContent>
            <TabsContent value="historical" className="p-6 pt-4">
                 {historicalAlerts.length > 0 ? (
                    <div className="space-y-4">
                        {historicalAlerts.map((alert) => (
                            <AlertCard key={alert.id} alert={alert} />
                        ))}
                    </div>
                ) : (
                    <p className="text-center text-muted-foreground py-8">No historical alerts.</p>
                )}
            </TabsContent>
          </ScrollArea>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}

function AlertCard({ 
  alert, 
  onAcknowledge, 
  onSaveNote 
}: { 
  alert: Alert, 
  onAcknowledge?: (id: string) => void, 
  onSaveNote?: (id: string, note: string) => void 
}) {
    const [note, setNote] = useState(alert.notes ?? "");

    return (
        <Card>
            <CardHeader>
                <div className="flex justify-between items-start">
                    <CardTitle className="text-lg">{alert.machineId}</CardTitle>
                    <Badge variant={severityVariantMap[alert.severity]}>{alert.severity}</Badge>
                </div>
                <CardDescription>{alert.message}</CardDescription>
            </CardHeader>
            <CardContent>
                <p className="text-sm text-muted-foreground">{new Date(alert.timestamp).toLocaleString()}</p>
                {alert.status === 'Active' && onAcknowledge && onSaveNote && (
                    <div className="mt-4 space-y-2">
                        <Textarea 
                          placeholder="Add maintenance notes..." 
                          value={note} 
                          onChange={(e) => setNote(e.target.value)} 
                        />
                    </div>
                )}
                 {alert.status === 'Acknowledged' && alert.notes && (
                    <div className="mt-4 p-3 bg-muted rounded-md">
                        <p className="text-sm font-semibold">Notes:</p>
                        <p className="text-sm text-muted-foreground">{alert.notes}</p>
                    </div>
                )}
            </CardContent>
            {alert.status === 'Active' && onAcknowledge && onSaveNote && (
                 <CardFooter className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => onAcknowledge(alert.id)}>Acknowledge</Button>
                    <Button onClick={() => onSaveNote(alert.id, note)} disabled={!note.trim()}>Save Note</Button>
                 </CardFooter>
            )}
        </Card>
    )
}
