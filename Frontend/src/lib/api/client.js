import { API_URL } from "../config.js";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "../auth/tokens.js";
import { fromEnvelope, networkError } from "./errors.js";

async function parseBody(response) {
  if (response.status === 204) return null;

  try {
    return await response.json();
  } catch (e) {
    return null;
  }
}

async function send(path, { method = "GET", body, auth = true, signal } = {}) {
  const headers = {};
  const isFormData = body instanceof FormData;

  if (body !== undefined && !isFormData) headers["Content-Type"] = "application/json";

  const token = getAccessToken();
  if (auth && token) headers["Authorization"] = `Bearer ${token}`;

  if (navigator.onLine === false) throw networkError();

  let response;

  try {
    response = await fetch(API_URL + path, {
      method,
      headers,
      signal,
      body: body === undefined ? undefined : isFormData ? body : JSON.stringify(body),
    });
  } catch (e) {
    if (e.name === "AbortError") throw e;
    throw networkError();
  }

  const parsed = await parseBody(response);

  if (!response.ok) throw fromEnvelope(parsed, response.status);

  return parsed;
}

let refreshing = null;

async function refreshAccessToken() {
  const refresh_token = getRefreshToken();
  if (!refresh_token) return false;

  if (!refreshing) {
    refreshing = send("/api/auth/refresh", {
      method: "POST",
      body: { refresh_token },
      auth: false,
    })
      .then((tokens) => {
        setTokens(tokens);
        return true;
      })
      .catch(() => false)
      .finally(() => {
        refreshing = null;
      });
  }

  return refreshing;
}

export async function request(path, options = {}) {
  try {
    return await send(path, options);
  } catch (e) {
    const authorized = options.auth !== false;

    if (e.status !== 401 || !authorized) throw e;

    const renewed = await refreshAccessToken();

    if (!renewed) {
      clearTokens();
      throw e;
    }

    try {
      return await send(path, options);
    } catch (retryError) {
      if (retryError.status === 401) clearTokens();
      throw retryError;
    }
  }
}

export const client = {
  get: (path, options) => request(path, { ...options, method: "GET" }),
  post: (path, body, options) => request(path, { ...options, method: "POST", body }),
  put: (path, body, options) => request(path, { ...options, method: "PUT", body }),
  patch: (path, body, options) => request(path, { ...options, method: "PATCH", body }),
  delete: (path, options) => request(path, { ...options, method: "DELETE" }),
};
