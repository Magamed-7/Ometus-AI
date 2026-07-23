const ACCESS_KEY = "ometus-access-token";
const REFRESH_KEY = "ometus-refresh-token";

let listeners = [];

export function getAccessToken() {
  try {
    return localStorage.getItem(ACCESS_KEY);
  } catch (e) {
    return null;
  }
}

export function getRefreshToken() {
  try {
    return localStorage.getItem(REFRESH_KEY);
  } catch (e) {
    return null;
  }
}

export function setTokens({ access_token, refresh_token }) {
  try {
    if (access_token !== undefined) localStorage.setItem(ACCESS_KEY, access_token);
    if (refresh_token !== undefined) localStorage.setItem(REFRESH_KEY, refresh_token);
  } catch (e) {}
}

export function clearTokens() {
  try {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  } catch (e) {}

  listeners.forEach((l) => l());
}

export const hasSession = () => Boolean(getAccessToken());

export function onTokensCleared(listener) {
  listeners.push(listener);
  return () => {
    listeners = listeners.filter((l) => l !== listener);
  };
}
