import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { bookAppointment } from "../lib/api/appointments.js";
import { getDoctor, getDoctorDepartments } from "../lib/api/doctors.js";
import { getDoctorSchedule, getSlots } from "../lib/api/schedules.js";
import { errorText } from "../lib/api/errorText.js";
import { useAuth } from "../lib/auth/AuthContext.jsx";
import { clock, formatDate, isoDate, weekdayIndex } from "../lib/format.js";
import { avatarAccent } from "../lib/mocks/doctors.js";
import { useI18n } from "../lib/i18n.jsx";
import { useToast } from "../lib/toast.jsx";
import Card from "../components/Card.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ErrorState from "../components/ErrorState.jsx";
import Skeleton from "../components/Skeleton.jsx";

function initials(name) {
  return (name || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function startOfWeek(value) {
  const date = new Date(value);
  const index = (date.getDay() + 6) % 7;
  date.setDate(date.getDate() - index);
  date.setHours(0, 0, 0, 0);
  return date;
}

function addDays(value, days) {
  const date = new Date(value);
  date.setDate(date.getDate() + days);
  return date;
}

export default function Booking() {
  const { t, lang } = useI18n();
  const { doctorId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const [doctor, setDoctor] = useState(null);
  const [loading, setLoading] = useState(Boolean(doctorId));
  const [error, setError] = useState(false);
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()));
  const [selectedDate, setSelectedDate] = useState(() => isoDate(new Date()));

  const [slots, setSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [slotsError, setSlotsError] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [departments, setDepartments] = useState({});
  const [workdays, setWorkdays] = useState(new Set());
  const [booking, setBooking] = useState(false);
  const [booked, setBooked] = useState(null);

  const todayIso = isoDate(new Date());
  const shorts = t("weekdays.short");
  const weekDays = [0, 1, 2, 3, 4, 5, 6].map((offset) => addDays(weekStart, offset));

  const loadSlots = useCallback(() => {
    if (!doctorId) return Promise.resolve();
    setSlotsLoading(true);
    setSlotsError(false);
    return getSlots(doctorId, selectedDate)
      .then(setSlots)
      .catch(() => setSlotsError(true))
      .finally(() => setSlotsLoading(false));
  }, [doctorId, selectedDate]);

  useEffect(() => {
    loadSlots();
  }, [loadSlots]);

  useEffect(() => {
    setSelectedSlot(null);
  }, [selectedDate]);

  useEffect(() => {
    if (!doctorId) return;
    getDoctorDepartments(doctorId)
      .then((deps) => setDepartments(Object.fromEntries(deps.map((d) => [d.id, d.name]))))
      .catch(() => {});
    getDoctorSchedule(doctorId)
      .then((rows) => setWorkdays(new Set(rows.map((row) => row.weekday))))
      .catch(() => {});
  }, [doctorId]);

  const showAbsence =
    !slotsLoading && !slotsError && visibleSlots.length === 0 && workdays.has(weekdayIndex(selectedDate));

  const onConfirm = async () => {
    if (!user) {
      navigate("/login", { state: { from: location } });
      return;
    }
    if (!selectedSlot) return;
    setBooking(true);
    try {
      const appointment = await bookAppointment({
        doctor_id: Number(doctorId),
        date: selectedDate,
        time: selectedSlot.time,
      });
      setBooked(appointment);
    } catch (e) {
      toast.error(errorText(t, e));
    } finally {
      setBooking(false);
    }
  };

  const nowTime = `${String(new Date().getHours()).padStart(2, "0")}:${String(
    new Date().getMinutes()
  ).padStart(2, "0")}`;
  const visibleSlots = slots.filter(
    (slot) => selectedDate !== todayIso || String(slot.time).slice(0, 5) > nowTime
  );

  const load = useCallback(() => {
    if (!doctorId) return Promise.resolve();
    setLoading(true);
    setError(false);
    return getDoctor(doctorId)
      .then(setDoctor)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [doctorId]);

  useEffect(() => {
    load();
  }, [load]);

  if (!doctorId) {
    return (
      <div className="mx-auto max-w-3xl px-md py-xl md:px-lg">
        <EmptyState
          icon="event"
          title={t("booking.pickDoctor")}
          action={
            <Link
              to="/doctors"
              className="mt-sm rounded-xl bg-primary px-lg py-3 font-bold text-on-primary transition-all hover:opacity-90"
            >
              {t("booking.toDoctors")}
            </Link>
          }
        />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
        <Skeleton className="h-32" />
        <Skeleton className="mt-md h-64" />
      </div>
    );
  }

  if (error || !doctor) {
    return (
      <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
        <ErrorState onRetry={load} />
      </div>
    );
  }

  if (booked) {
    return (
      <div className="mx-auto max-w-lg px-md py-xl text-center md:px-lg">
        <span className="material-symbols-outlined text-6xl text-primary">check_circle</span>
        <h1 className="mt-md text-headline-md font-bold text-on-surface">
          {t("booking.successTitle")}
        </h1>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
      <h1 className="mb-md text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
        {t("booking.title")}
      </h1>
      <div className="grid grid-cols-1 gap-md lg:grid-cols-3">
        <div className="flex flex-col gap-md lg:col-span-2">
          <Card className="flex flex-col items-center gap-md p-md sm:flex-row sm:items-start">
            <div
              className={`grid h-24 w-24 shrink-0 place-items-center rounded-xl bg-gradient-to-br text-on-primary ${avatarAccent(
                doctor.id
              )}`}
            >
              <span className="text-headline-lg font-bold">{initials(doctor.full_name)}</span>
            </div>
            <div className="text-center sm:text-left">
              <span className="mb-xs inline-block w-fit rounded-full bg-secondary-container px-3 py-1 text-label-md font-semibold text-on-secondary-container">
                {doctor.specialization}
              </span>
              <h2 className="text-headline-md font-semibold text-on-surface">{doctor.full_name}</h2>
            </div>
          </Card>
          <Card className="p-md">
            <div className="mb-md flex items-center justify-between">
              <h3 className="text-headline-md font-semibold text-on-surface">{t("booking.week")}</h3>
              <div className="flex gap-xs">
                <button
                  type="button"
                  disabled={isoDate(weekStart) <= isoDate(startOfWeek(new Date()))}
                  onClick={() => setWeekStart((prev) => addDays(prev, -7))}
                  aria-label={t("booking.prevWeek")}
                  className="grid h-10 w-10 place-items-center rounded-full text-on-surface-variant transition-all hover:bg-surface-container disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <span className="material-symbols-outlined">chevron_left</span>
                </button>
                <button
                  type="button"
                  onClick={() => setWeekStart((prev) => addDays(prev, 7))}
                  aria-label={t("booking.nextWeek")}
                  className="grid h-10 w-10 place-items-center rounded-full text-on-surface-variant transition-all hover:bg-surface-container"
                >
                  <span className="material-symbols-outlined">chevron_right</span>
                </button>
              </div>
            </div>
            <div className="grid grid-cols-7 gap-xs md:gap-sm">
              {weekDays.map((date) => {
                const iso = isoDate(date);
                const isPast = iso < todayIso;
                const isSelected = iso === selectedDate;
                const isToday = iso === todayIso;
                return (
                  <button
                    key={iso}
                    type="button"
                    disabled={isPast}
                    onClick={() => setSelectedDate(iso)}
                    className={`flex flex-col items-center rounded-lg border p-xs transition-all md:p-sm ${
                      isSelected
                        ? "border-2 border-primary bg-primary-container/10 text-primary"
                        : isPast
                          ? "cursor-not-allowed border-outline-variant bg-surface-container opacity-50"
                          : "border-outline-variant hover:border-primary"
                    }`}
                  >
                    <span className="text-label-md font-semibold text-on-surface-variant">
                      {shorts[(date.getDay() + 6) % 7]}
                    </span>
                    <span className="text-body-lg font-bold">{date.getDate()}</span>
                    {isToday && <span className="mt-0.5 h-1 w-1 rounded-full bg-primary" />}
                  </button>
                );
              })}
            </div>
          </Card>
          <Card className="p-md">
            <h3 className="mb-md text-headline-md font-semibold text-on-surface">
              {t("booking.slots")}
            </h3>
            {slotsError ? (
              <ErrorState onRetry={loadSlots} />
            ) : slotsLoading ? (
              <div className="grid grid-cols-2 gap-sm sm:grid-cols-4 md:grid-cols-5">
                {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => (
                  <Skeleton key={i} className="h-12" />
                ))}
              </div>
            ) : showAbsence ? (
              <div className="flex items-center gap-sm rounded-lg bg-tertiary-container p-sm text-on-tertiary-container">
                <span className="material-symbols-outlined">info</span>
                <p className="text-body-md">{t("booking.absence")}</p>
              </div>
            ) : visibleSlots.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-xl text-center">
                <span className="material-symbols-outlined mb-sm text-6xl text-outline">
                  event_busy
                </span>
                <p className="text-headline-md font-semibold text-on-surface-variant">
                  {t("booking.noSlots")}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-sm sm:grid-cols-4 md:grid-cols-5">
                {visibleSlots.map((slot) => {
                  const isActive = selectedSlot && selectedSlot.time === slot.time;
                  return (
                    <button
                      key={slot.time}
                      type="button"
                      onClick={() => setSelectedSlot(slot)}
                      className={`rounded-lg py-3 text-body-md font-bold transition-all ${
                        isActive
                          ? "border-2 border-primary bg-primary-container/10 text-primary shadow-sm"
                          : "border border-outline-variant text-on-surface hover:bg-surface-container"
                      }`}
                    >
                      {clock(slot.time)}
                    </button>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
        <div className="lg:col-span-1">
          <div className="sticky top-24">
            <Card className="bg-surface-container-high p-md">
              <h3 className="mb-md text-label-md font-semibold uppercase tracking-widest text-primary">
                {t("booking.summary")}
              </h3>
              <div className="space-y-sm">
                <div className="flex items-start gap-sm">
                  <span className="material-symbols-outlined text-primary">person</span>
                  <div>
                    <p className="text-label-md text-on-surface-variant">{t("booking.doctor")}</p>
                    <p className="text-body-md font-bold text-on-surface">{doctor.full_name}</p>
                  </div>
                </div>
                <div className="flex items-start gap-sm">
                  <span className="material-symbols-outlined text-primary">event</span>
                  <div>
                    <p className="text-label-md text-on-surface-variant">{t("booking.date")}</p>
                    <p className="text-body-md font-bold text-on-surface">
                      {formatDate(selectedDate, lang)}
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-sm">
                  <span className="material-symbols-outlined text-primary">schedule</span>
                  <div>
                    <p className="text-label-md text-on-surface-variant">{t("booking.time")}</p>
                    <p className="text-body-md font-bold text-on-surface">
                      {selectedSlot ? clock(selectedSlot.time) : t("booking.pickSlot")}
                    </p>
                  </div>
                </div>
                {selectedSlot && departments[selectedSlot.department_id] && (
                  <div className="flex items-start gap-sm">
                    <span className="material-symbols-outlined text-primary">meeting_room</span>
                    <div>
                      <p className="text-label-md text-on-surface-variant">
                        {t("booking.department")}
                      </p>
                      <p className="text-body-md font-bold text-on-surface">
                        {departments[selectedSlot.department_id]}
                      </p>
                    </div>
                  </div>
                )}
              </div>
              <hr className="my-md border-outline-variant" />
              <button
                type="button"
                onClick={onConfirm}
                disabled={!selectedSlot || booking}
                className="w-full rounded-lg bg-primary py-4 text-headline-md font-semibold text-on-primary shadow-md transition-all hover:opacity-90 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {booking ? t("booking.booking") : t("booking.confirm")}
              </button>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
