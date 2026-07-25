import { client } from "./client.js";

export const getMyAppointments = (status) =>
  client.get(`/api/appointments/me${status ? `?status=${status}` : ""}`);

export const getAppointment = (id) => client.get(`/api/appointments/${id}`);

export const bookAppointment = (data) => client.post("/api/appointments", data);

export const cancelAppointment = (id) => client.delete(`/api/appointments/${id}`);

export const rescheduleAppointment = (id, data) =>
  client.put(`/api/appointments/${id}/reschedule`, data);

export const getDoctorToday = () => client.get("/api/appointments/doctor/me/today");

export function getDoctorAppointments({ day, status } = {}) {
  const params = new URLSearchParams();
  if (day) params.set("day", day);
  if (status) params.set("status", status);
  const qs = params.toString();

  return client.get(`/api/appointments/doctor/me${qs ? `?${qs}` : ""}`);
}

export const completeAppointment = (id) =>
  client.put(`/api/appointments/doctor/me/${id}/complete`);

export const noShowAppointment = (id) =>
  client.put(`/api/appointments/doctor/me/${id}/no-show`);
