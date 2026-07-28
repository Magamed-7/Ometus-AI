import { client } from "./client.js";

export const askAssistant = (payload) => client.post("/api/ai/ask", payload);

export const askAsDoctor = (payload) => client.post("/api/ai/doctor/ask", payload);

export const askAsAdmin = (payload) => client.post("/api/ai/admin/ask", payload);

export const listConversations = () => client.get("/api/ai/conversations");

export const startConversation = () => client.post("/api/ai/conversations");

export const renameConversation = (id, title) =>
  client.put(`/api/ai/conversations/${id}`, { title });

export const deleteConversation = (id) => client.delete(`/api/ai/conversations/${id}`);

export const getConversationHistory = (id) => client.get(`/api/ai/history/${id}`);

export const rateReply = (messageId, feedback) =>
  client.post("/api/ai/feedback", { message_id: messageId, feedback });
