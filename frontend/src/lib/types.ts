export type MachineType = 'L' | 'M' | 'H';

export type FailureType = 
  | 'No Failure'
  | 'Heat Dissipation Failure'
  | 'Power Failure'
  | 'Overstrain Failure'
  | 'Tool Wear Failure'
  | 'Random Failures';

export type SensorReading = {
  id: string;
  recordedAt: string;
  machineType: MachineType;
  airTempK: number;
  processTempK: number;
  rpm: number;
  torqueNm: number;
  toolWearMin: number;
  source: 'iot' | 'manual';
  assumedFeatures?: string[];
};

export type Prediction = {
  id: string;
  readingId: string;
  predictedAt: string;
  failureType: FailureType;
  confidence: number;
  modelVersion: string;
};

export type User = {
  name: string;
  email: string;
  role: 'Admin' | 'Operator' | 'Viewer';
  avatar: string;
};

export type SensorMapping = {
    id: string;
    deviceId: string;
    machineId: string;
};

export type AlertSeverity = 'Critical' | 'High' | 'Medium' | 'Low';
export type AlertStatus = 'Active' | 'Acknowledged';

export type Alert = {
  id: string;
  machineId: string;
  severity: AlertSeverity;
  message: string;
  timestamp: string;
  status: AlertStatus;
  notes?: string;
};
