import { useMemo, useState } from "react";
import type { LogEvent, Prediction } from "./types";

const demoEvents: LogEvent[] = [
  {
    timestamp: new Date().toISOString(),
    host: "web-01",
    service: "nginx",
    level: "error",
    message: "502 upstream timeout",
  },
  {
    timestamp: new Date().toISOString(),
    host: "api-02",
    service: "payments",
    level: "warning",
    message: "latency p95 > 900ms",
  },
];

function mockPredict(events: LogEvent[]): Prediction {
  const critical = events.filter((e) => ["error", "critical"].includes(e.level.toLowerCase()));
  const score = Math.min(0.2 * events.length + 0.15 * critical.length, 1);
  const label = score > 0.5 ? "degraded" : "normal";
  return {
    score: parseFloat(score.toFixed(2)),
    label,
    notes: label === "normal" ? "No anomalies detected in sample." : "Elevated risk based on errors.",
  };
}

export default function App() {
  const [events, setEvents] = useState<LogEvent[]>(demoEvents);
  const [prediction, setPrediction] = useState<Prediction>(() => mockPredict(demoEvents));

  const headline = useMemo(
    () => (prediction.label === "normal" ? "Systems steady" : "Investigate now"),
    [prediction.label],
  );

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Predictive Ops</p>
          <h1>Log signals into early incident warnings</h1>
          <p className="lede">
            Send logs from your fleet, score them with a model, and surface
            risks before they become incidents.
          </p>
          <div className="actions">
            <button
              className="primary"
              onClick={() => setPrediction(mockPredict(events))}
            >
              Run sample scoring
            </button>
            <button
              className="secondary"
              onClick={() => {
                const newer = [
                  ...events,
                  {
                    timestamp: new Date().toISOString(),
                    host: "db-01",
                    service: "postgres",
                    level: "critical",
                    message: "replication lag 30s",
                  },
                ];
                setEvents(newer);
                setPrediction(mockPredict(newer));
              }}
            >
              Simulate spike
            </button>
          </div>
        </div>
        <div className="card stack">
          <div className="pill">Current status</div>
          <h2>{headline}</h2>
          <p className="metric">
            Risk score <span>{prediction.score}</span>
          </p>
          <p className="note">{prediction.notes}</p>
          <div className="chips">
            {events.slice(-3).map((event, idx) => (
              <span className="chip" key={`${event.service}-${idx}`}>
                {event.service} · {event.level.toUpperCase()}
              </span>
            ))}
          </div>
        </div>
      </header>

      <section className="panel">
        <div>
          <h3>Latest events</h3>
          <p className="subtext">
            Replace this mock with real calls to the FastAPI endpoint at
            <code>/predict</code>.
          </p>
        </div>
        <div className="logs">
          {events.map((event, index) => (
            <div className="log-row" key={`${event.timestamp}-${index}`}>
              <span className={`badge ${event.level.toLowerCase()}`}>{event.level}</span>
              <span className="host">{event.host}</span>
              <span className="service">{event.service}</span>
              <span className="message">{event.message}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

