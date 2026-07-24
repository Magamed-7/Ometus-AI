import { client } from "./client.js";

export const getMyAppointments = (status) =>
  client.get(`/api/appointments/me${status ? `?status=${status}` : ""}`);

export const getAppointment = (id) => client.get(`/api/appointments/${id}`);

export const bookAppointment = (data) => client.post("/api/appointments", data);

export const cancelAppointment = (id) => client.delete(`/api/appointments/${id}`);

export const rescheduleAppointment = (id, data) =>
  client.put(`/api/appointments/${id}/reschedule`, data);
