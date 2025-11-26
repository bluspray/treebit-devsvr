export type LogEvent = {
  timestamp: string;
  host: string;
  service: string;
  level: string;
  message: string;
};

export type Prediction = {
  score: number;
  label: "normal" | "degraded";
  notes?: string;
};

