import { client } from "./client.js";

function query(params) {
  const search = new URLSearchParams();

  for (const key in params) {
    if (params[key] !== undefined && params[key] !== null && params[key] !== "") {
      search.set(key, params[key]);
    }
  }

  const text = search.toString();
  return text ? `?${text}` : "";
}

export const getServices = (params = {}) =>
  client.get(`/api/services${query(params)}`, { auth: false });

export const getService = (id) => client.get(`/api/services/${id}`, { auth: false });
