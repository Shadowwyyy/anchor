const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type AskResult = {
  answer: string;
  is_refusal: boolean;
  sources: string[];
  is_confident: boolean;
  best_distance: number | null;
};

export async function askQuestion(question: string): Promise<AskResult> {
  const response = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}