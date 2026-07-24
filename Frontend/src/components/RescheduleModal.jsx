import { useCallback, useEffect, useState } from "react";
import { rescheduleAppointment } from "../lib/api/appointments.js";
import { getSlots } from "../lib/api/schedules.js";
import { errorText } from "../lib/api/errorText.js";
import { clock, isoDate } from "../lib/format.js";
import { useI18n } from "../lib/i18n.jsx";
import { useToast } from "../lib/toast.jsx";
import Button from "./Button.jsx";
import Skeleton from "./Skeleton.jsx";

export default function RescheduleModal({ appointment, onClose, onDone }) {
  const { t } = useI18n();
  const toast = useToast();
  const [date, setDate] = useState(isoDate(new Date()));
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTime, setSelectedTime] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const todayIso = isoDate(new Date());
  const nowTime = `${String(new Date().getHours()).padStart(2, "0")}:${String(
    new Date().getMinutes()
  ).padStart(2, "0")}`;

  const loadSlots = useCallback(() => {
    setLoading(true);
    setSelectedTime("");
    return getSlots(appointment.doctor_id, date)
      .then(setSlots)
      .catch(() => setSlots([]))
      .finally(() => setLoading(false));
  }, [appointment.doctor_id, date]);

  useEffect(() => {
    loadSlots();
  }, [loadSlots]);

  const visibleSlots = slots.filter(
    (slot) => date !== todayIso || String(slot.time).slice(0, 5) > nowTime
  );

  const onConfirm = async () => {
    if (!selectedTime) return;
    setSubmitting(true);
    try {
      await rescheduleAppointment(appointment.id, { date, time: selectedTime });
      toast.success(t("common.saved"));
      onDone();
    } catch (e) {
      if (e.code === "SLOT_TAKEN" || e.code === "SLOT_NOT_AVAILABLE") {
        toast.error(t("booking.slotTaken"));
        loadSlots();
      } else if (e.code === "ALREADY_BOOKED") {
        toast.error(t("booking.alreadyBooked"));
      } else {
        toast.error(errorText(t, e));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-md"
      onClick={onClose}
    >
      <div
        className="flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden rounded-t-2xl border border-outline-variant bg-surface-container-lowest sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-outline-variant p-md">
          <h2 className="text-headline-md font-semibold text-on-surface">
            {t("account.reschedule")}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t("common.close")}
            className="grid h-10 w-10 place-items-center rounded-full text-on-surface-variant hover:bg-surface-container"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-md">
          <label
            htmlFor="reschedule-date"
            className="mb-xs block text-label-md font-semibold text-on-surface-variant"
          >
            {t("booking.date")}
          </label>
          <input
            id="reschedule-date"
            type="date"
            min={todayIso}
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="mb-md min-h-11 w-full rounded-xl border border-outline-variant bg-surface-container-lowest px-4 py-2.5 text-body-md focus:border-primary focus:outline-none"
          />

          {loading ? (
            <div className="grid grid-cols-3 gap-sm sm:grid-cols-4">
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12" />
              ))}
            </div>
          ) : visibleSlots.length === 0 ? (
            <p className="py-lg text-center text-body-md text-on-surface-variant">
              {t("booking.noSlots")}
            </p>
          ) : (
            <div className="grid grid-cols-3 gap-sm sm:grid-cols-4">
              {visibleSlots.map((slot) => {
                const isActive = selectedTime === slot.time;
                return (
                  <button
                    key={slot.time}
                    type="button"
                    onClick={() => setSelectedTime(slot.time)}
                    className={`rounded-lg py-3 text-body-md font-bold transition-all ${
                      isActive
                        ? "border-2 border-primary bg-primary-container/10 text-primary"
                        : "border border-outline-variant text-on-surface hover:bg-surface-container"
                    }`}
                  >
                    {clock(slot.time)}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex gap-sm border-t border-outline-variant p-md">
          <Button type="button" variant="outline" onClick={onClose} className="flex-1">
            {t("common.cancel")}
          </Button>
          <Button
            type="button"
            onClick={onConfirm}
            loading={submitting}
            disabled={!selectedTime}
            className="flex-1"
          >
            {t("common.confirm")}
          </Button>
        </div>
      </div>
    </div>
  );
}
