import { client } from "./client.js";

export const getDepartments = (filialId) =>
  client.get(`/api/departments${filialId ? `?filial_id=${filialId}` : ""}`, { auth: false });

export const getDepartment = (id) => client.get(`/api/departments/${id}`, { auth: false });
