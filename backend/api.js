const API_BASE = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";

// NOTE: This is the access token for the N-Agent Backend, NOT the Gemini/OpenAI key.
// The actual LLM keys are stored securely on the server side.
const BACKEND_ACCESS_TOKEN = "nagent-dev-key";

export const submitWorkflow = async (objective, provider = "google", model = "gemini-1.5-flash") => {
  const response = await fetch(`${API_BASE}/workflows`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": BACKEND_ACCESS_TOKEN,
    },
    body: JSON.stringify({ objective, provider, model }),
  });
  if (!response.ok) throw new Error("Failed to submit workflow");
  return response.json();
};

export const getWorkflowState = async (sessionId) => {
  const response = await fetch(`${API_BASE}/workflows/${sessionId}`, {
    headers: {
      "X-API-Key": BACKEND_ACCESS_TOKEN,
    },
  });
  if (!response.ok) throw new Error("Failed to fetch workflow state");
  return response.json();
};

export const connectToWorkflowEvents = (sessionId, onMessage, onError) => {
  const ws = new WebSocket(`${WS_BASE}/workflows/${sessionId}/events?api_key=${BACKEND_ACCESS_TOKEN}`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  ws.onerror = (error) => onError && onError(error);
  return ws;
};