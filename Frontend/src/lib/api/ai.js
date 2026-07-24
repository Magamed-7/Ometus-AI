import { client } from "./client.js";

export const askAssistant = (payload) => client.post("/api/ai/ask", payload);
