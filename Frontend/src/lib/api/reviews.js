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

export const getReviews = (params = {}) =>
  client.get(`/api/reviews${query(params)}`, { auth: false });

export const getReviewSummary = (params = {}) =>
  client.get(`/api/reviews/summary${query(params)}`, { auth: false });

export const leaveReview = (body) => client.post("/api/reviews", body);
