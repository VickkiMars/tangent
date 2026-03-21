const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, '');
const WS_URL = (import.meta.env.VITE_WS_URL || "ws://localhost:8000").replace(/\/$/, '');

// NOTE: This is the access token for the N-Agent Backend, NOT the Gemini/OpenAI key.
// The actual LLM keys are stored securely on the server side.
const BACKEND_ACCESS_TOKEN = import.meta.env.VITE_API_KEY || "nagent-dev-key";

export const submitWorkflow = async (objective, provider = "google", model = "gemini-1.5-flash") => {
  const response = await fetch(`${API_URL}/workflows`, {
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
  const response = await fetch(`${API_URL}/workflows/${sessionId}`, {
    headers: {
      "X-API-Key": BACKEND_ACCESS_TOKEN,
    },
  });
  if (!response.ok) throw new Error("Failed to fetch workflow state");
  return response.json();
};

export const getCostsSummary = async () => {
  const response = await fetch(`${API_URL}/analytics/costs/summary`, {
    headers: {
      "X-API-Key": BACKEND_ACCESS_TOKEN,
    },
  });
  if (!response.ok) throw new Error("Failed to fetch costs summary");
  return response.json();
};

export const authSignup = async (email, password, first_name, last_name) => {
  const response = await fetch(`${API_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, first_name, last_name }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Signup failed");
  return data;
};

export const authLogin = async (email, password) => {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Login failed");
  return data;
};

export const authGetMe = async (token) => {
  const response = await fetch(`${API_URL}/auth/me?token=${token}`);
  if (!response.ok) throw new Error("Invalid token");
  return response.json();
};

export const connectToWorkflowEvents = (sessionId, onMessage, onError) => {
  const ws = new WebSocket(`${WS_URL}/workflows/${sessionId}/events?api_key=${BACKEND_ACCESS_TOKEN}`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  ws.onerror = (error) => onError && onError(error);
  return ws;
};