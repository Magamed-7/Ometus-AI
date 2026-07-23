import { client } from "./client.js";

export const register = (data) => client.post("/api/auth/register", data, { auth: false });

export const login = (email, password) =>
  client.post("/api/auth/login", { email, password }, { auth: false });

export const verifyEmail = (email, code) =>
  client.post("/api/auth/verify-email", { email, code }, { auth: false });
