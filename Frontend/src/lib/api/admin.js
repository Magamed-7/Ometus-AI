import { client } from "./client.js";

export const getDailyReport = (dateFrom, dateTo) =>
  client.get(`/api/admin/reports/daily?date_from=${dateFrom}&date_to=${dateTo}`);

export const getAiDaily = (dateFrom, dateTo) =>
  client.get(`/api/admin/ai-daily?date_from=${dateFrom}&date_to=${dateTo}`);

export const getAiCosts = (dateFrom, dateTo) =>
  client.get(`/api/admin/ai-costs?date_from=${dateFrom}&date_to=${dateTo}`);

export const getAiFeedback = (dateFrom, dateTo) =>
  client.get(`/api/admin/ai-feedback?date_from=${dateFrom}&date_to=${dateTo}`);

function query(params) {
  const search = new URLSearchParams();

  for (const name in params) {
    const value = params[name];
    if (value !== undefined && value !== null && value !== "") search.set(name, value);
  }

  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const createFilial = (data) => client.post("/api/admin/filials", data);

export const updateFilial = (id, data) => client.put(`/api/admin/filials/${id}`, data);

export const deleteFilial = (id) => client.delete(`/api/admin/filials/${id}`);

export const createDepartment = (data) => client.post("/api/admin/departments", data);

export const updateDepartment = (id, data) => client.put(`/api/admin/departments/${id}`, data);

export const deleteDepartment = (id) => client.delete(`/api/admin/departments/${id}`);

export const createDoctor = (data) => client.post("/api/admin/doctors", data);

export const updateDoctor = (id, data) => client.put(`/api/admin/doctors/${id}`, data);

export const assignDepartment = (doctorId, departmentId) =>
  client.post(`/api/admin/doctors/${doctorId}/departments`, { department_id: departmentId });

export const unassignDepartment = (doctorId, departmentId) =>
  client.delete(`/api/admin/doctors/${doctorId}/departments/${departmentId}`);

export const addSpecialization = (doctorId, name) =>
  client.post(`/api/admin/doctors/${doctorId}/specializations`, { name });

export const removeSpecialization = (doctorId, name) =>
  client.delete(`/api/admin/doctors/${doctorId}/specializations/${encodeURIComponent(name)}`);

export const getDoctorSchedules = (doctorId) =>
  client.get(`/api/admin/doctors/${doctorId}/schedules`);

export const createDoctorSchedule = (doctorId, data) =>
  client.post(`/api/admin/doctors/${doctorId}/schedules`, data);

export const updateDoctorSchedule = (doctorId, scheduleId, data) =>
  client.put(`/api/admin/doctors/${doctorId}/schedules/${scheduleId}`, data);

export const deleteDoctorSchedule = (doctorId, scheduleId) =>
  client.delete(`/api/admin/doctors/${doctorId}/schedules/${scheduleId}`);

export const getAllAppointments = (filters = {}) =>
  client.get(`/api/admin/appointments${query(filters)}`);

export const getWorkloadReport = (filters) =>
  client.get(`/api/admin/reports/workload${query(filters)}`);

export const getSummaryReport = (filters) =>
  client.get(`/api/admin/reports/summary${query(filters)}`);

export const getUsers = (role) => client.get(`/api/admin/users${query({ role })}`);

export const setUserRole = (userId, role) =>
  client.put(`/api/admin/users/${userId}/role`, { role });
