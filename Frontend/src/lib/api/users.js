import { client } from "./client.js";

export const getMe = () => client.get("/api/users/me");

export const updateMe = (data) => client.put("/api/users/me", data);

export const getPatient = () => client.get("/api/users/me/patient");

export const updatePatient = (data) => client.put("/api/users/me/patient", data);
