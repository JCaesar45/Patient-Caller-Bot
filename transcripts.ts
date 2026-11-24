export type Speaker = "AGENT" | "PATIENT";

export interface Turn {
  t: number;
  who: Speaker;
  text: string;
}

export interface Stats {
  turns: number;
  durationSec: number;
  agentWords: number;
  patientWords: number;
  avgGapSec: number;
}

const LINE = /^\[(\d+):(\d+(?:\.\d+)?)\]\s+(AGENT|PATIENT\(bot\)):\s*(.*)$/;

const wordCount = (s: string): number => (s.trim() ? s.trim().split(/\s+/).length : 0);

export function parse(raw: string): Turn[] {
  const turns: Turn[] = [];
  for (const line of raw.split("\n")) {
    const m = LINE.exec(line.trim());
    if (!m) continue;
    turns.push({
      t: Number(m[1]) * 60 + Number(m[2]),
      who: m[3] === "AGENT" ? "AGENT" : "PATIENT",
      text: m[4],
    });
  }
  return turns;
}

export function stats(turns: Turn[]): Stats {
  const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
  const gaps: number[] = [];
  for (let i = 1; i < turns.length; i++) {
    if (turns[i].who !== turns[i - 1].who) gaps.push(turns[i].t - turns[i - 1].t);
  }
  return {
    turns: turns.length,
    durationSec: turns.length ? turns[turns.length - 1].t : 0,
    agentWords: sum(turns.filter((x) => x.who === "AGENT").map((x) => wordCount(x.text))),
    patientWords: sum(turns.filter((x) => x.who === "PATIENT").map((x) => wordCount(x.text))),
    avgGapSec: gaps.length ? sum(gaps) / gaps.length : 0,
  };
}
