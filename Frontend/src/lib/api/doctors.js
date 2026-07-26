import { client } from "./client.js";

export function searchDoctors({ specialization, department_id, filial_id } = {}) {
  const params = new URLSearchParams();
  if (specialization) params.set("specialization", specialization);
  if (department_id) params.set("department_id", department_id);
  if (filial_id) params.set("filial_id", filial_id);
  const qs = params.toString();

  return client.get(`/api/doctors${qs ? `?${qs}` : ""}`, { auth: false });
}

export const getDoctor = (id) => client.get(`/api/doctors/${id}`, { auth: false });

export const getDoctorDepartments = (id) =>
  client.get(`/api/doctors/${id}/departments`, { auth: false });

export async function findMyDoctor(userId) {
  const doctors = await searchDoctors();
  return doctors.find((doctor) => doctor.user_id === userId) || null;
}
