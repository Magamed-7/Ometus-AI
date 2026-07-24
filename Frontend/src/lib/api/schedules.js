import { isoDate } from "../format.js";
import { client } from "./client.js";

export const getSlots = (doctorId, day) =>
  client.get(`/api/schedules/doctors/${doctorId}/slots?day=${day}`, { auth: false });

export async function findNearestSlot(doctorId, days = 14) {
  const now = new Date();
  const nowTime = `${String(now.getHours()).padStart(2, "0")}:${String(
    now.getMinutes()
  ).padStart(2, "0")}`;

  for (let offset = 0; offset < days; offset += 1) {
    const date = new Date(now);
    date.setDate(now.getDate() + offset);
    const day = isoDate(date);

    let slots;
    try {
      slots = await getSlots(doctorId, day);
    } catch (e) {
      return null;
    }

    const available = slots.filter((slot) => offset > 0 || String(slot.time).slice(0, 5) > nowTime);
    if (available.length) return { day, ...available[0] };
  }

  return null;
}
