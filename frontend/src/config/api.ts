export const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

export const API_V1 = `${API_URL}/api/v1`;

export const WS_URL =
  import.meta.env.VITE_WS_URL ||
  API_URL.replace(/^http/, "ws");