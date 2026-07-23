import { client } from "./client.js";

export const getFilials = (city) =>
  client.get(`/api/filials${city ? `?city=${encodeURIComponent(city)}` : ""}`, { auth: false });

export const getFilial = (id) => client.get(`/api/filials/${id}`, { auth: false });
