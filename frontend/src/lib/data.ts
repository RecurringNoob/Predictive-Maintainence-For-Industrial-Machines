import type { User, SensorMapping, SensorReading, Prediction, Alert } from '@/lib/types';
import { PlaceHolderImages } from '@/lib/placeholder-images';

export const users: User[] = [
  { name: 'Utkarsh Bansal', email: 'utkarsh@machinewise.com', role: 'Admin', avatar: PlaceHolderImages[0]?.imageUrl ?? 'https://picsum.photos/seed/1/40/40' },
  { name: 'Operator Joe', email: 'operator.joe@machinewise.com', role: 'Operator', avatar: PlaceHolderImages[1]?.imageUrl ?? 'https://picsum.photos/seed/2/40/40' },
];

export const latestReading: SensorReading = {
  id: 'R-001',
  recordedAt: new Date().toISOString(),
  machineType: 'M',
  airTempK: 301.2,
  processTempK: 311.5,
  rpm: 1500,
  torqueNm: 42.8,
  toolWearMin: 124,
  source: 'iot',
  assumedFeatures: ['Process Temperature', 'Torque', 'RPM']
};

export const latestPrediction: Prediction = {
  id: 'P-001',
  readingId: 'R-001',
  predictedAt: new Date().toISOString(),
  failureType: 'No Failure',
  confidence: 0.94,
  modelVersion: 'v1'
};

export const historicalReadings: SensorReading[] = Array.from({ length: 50 }, (_, i) => ({
    id: `R-HIST-${i}`,
    recordedAt: new Date(Date.now() - (50 - i) * 60 * 60 * 1000).toISOString(),
    machineType: 'M',
    airTempK: 300 + Math.random() * 5,
    processTempK: 310 + Math.random() * 10,
    rpm: 1450 + Math.random() * 100,
    torqueNm: 38 + Math.random() * 10,
    toolWearMin: i * 5 % 250,
    source: 'iot'
}));

export const sensorMappings: SensorMapping[] = [
    { id: 'S-001', deviceId: 'ESP32-DHT11-IOT', machineId: 'M-001' },
];

export const alerts: Alert[] = [
  {
    id: 'A-001',
    machineId: 'M-001',
    severity: 'Critical',
    message: 'High heat dissipation detected. Cooling required.',
    timestamp: new Date().toISOString(),
    status: 'Active',
  },
  {
    id: 'A-002',
    machineId: 'M-001',
    severity: 'Medium',
    message: 'Increased torque variance observed.',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    status: 'Acknowledged',
    notes: 'Scheduled inspection for next week.',
  },
];
