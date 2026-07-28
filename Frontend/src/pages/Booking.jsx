import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { bookAppointment } from "../lib/api/appointments.js";
import { getDoctor, getDoctorDepartments } from "../lib/api/doctors.js";
import { getDoctorCalendar, getSlots } from "../lib/api/schedules.js";
import { errorText } from "../lib/api/errorText.js";
import { useAuth } from "../lib/auth/AuthContext.jsx";
import { clock, formatDate, isoDate } from "../lib/format.js";
import DoctorAvatar from "../components/DoctorAvatar.jsx";
import { useI18n } from "../lib/i18n.jsx";
import { nextIndex } from "../lib/roving.js";
import { useToast } from "../lib/toast.jsx";
import Card from "../components/Card.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ErrorState from "../components/ErrorState.jsx";
import LoadingStatus from "../components/LoadingStatus.jsx";
import Skeleton from "../components/Skeleton.jsx";


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
  const [calendar, setCalendar] = useState({});
  const [booking, setBooking] = useState(false);
  const [booked, setBooked] = useState(null);

  const todayIso = isoDate(new Date());
  const shorts = t("weekdays.short");
  const weekDays = [0, 1, 2, 3, 4, 5, 6].map((offset) => addDays(weekStart, offset));
  const weekIsos = weekDays.map(isoDate);

  // день доступен, пока календарь не сказал обратного: пока он грузится, неизвестный
  // день считаем рабочим, иначе лента на секунду становится полностью серой
  const dayStatus = (iso) => calendar[iso]?.status;
  const isBookable = (iso) => iso >= todayIso && !["absent", "off"].includes(dayStatus(iso));

  // клавиатуре нужна живая кнопка: если выбранный день оказался отпуском, он отключён,
  // и tabIndex=0 на нём увёл бы фокус в никуда
  const tabDayIso =
    (weekIsos.includes(selectedDate) && isBookable(selectedDate) && selectedDate) ||
    weekIsos.find(isBookable) ||
    weekIsos.find((iso) => iso >= todayIso) ||
    weekIsos[0];
  const dayRefs = useRef({});
  const slotRefs = useRef({});
  const [pendingFocus, setPendingFocus] = useState(null);

  useEffect(() => {
    if (!pendingFocus) return;
    const element = dayRefs.current[pendingFocus];
    if (element) element.focus();
    setPendingFocus(null);
  }, [pendingFocus, weekStart]);

  const selectDay = (date) => {
    const iso = isoDate(date);
    if (!isBookable(iso)) return;
    if (isoDate(startOfWeek(date)) !== isoDate(weekStart)) setWeekStart(startOfWeek(date));
    setSelectedDate(iso);
    setPendingFocus(iso);
  };

  // стрелками перешагиваем отпуска и выходные: вставать на день, на который нельзя
  // записаться, некуда — кнопка там отключена и фокус на неё не встанет
  const selectNearestDay = (from, step) => {
    for (let shift = 1; shift <= 60; shift += 1) {
      const candidate = addDays(from, step * shift);
      if (isBookable(isoDate(candidate))) {
        selectDay(candidate);
        return;
      }
    }
  };

  const onDayKeyDown = (event, date) => {
    const steps = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
    if (event.key in steps) {
      event.preventDefault();
      selectNearestDay(date, steps[event.key]);
      return;
    }
    if (event.key === "Home") {
      event.preventDefault();
      const first = weekDays.find((day) => isBookable(isoDate(day)));
      if (first) selectDay(first);
    }
    if (event.key === "End") {
      event.preventDefault();
      const last = [...weekDays].reverse().find((day) => isBookable(isoDate(day)));
      if (last) selectDay(last);
    }
  };

  const onSlotKeyDown = (event, index) => {
    const target = nextIndex(event.key, index, visibleSlots.length);
    if (target === null) return;
    event.preventDefault();
    const slot = visibleSlots[target];
    setSelectedSlot(slot);
    const element = slotRefs.current[slot.time];
    if (element) element.focus();
  };

  // даты переключают быстро, а ответы приходят вразнобой: без счётчика запросов
  // медленный ответ по вчерашней дате затирал слоты уже выбранного дня
  const slotsRequest = useRef(0);

  const loadSlots = useCallback(() => {
    if (!doctorId) return Promise.resolve();
    const request = ++slotsRequest.current;
    const isCurrent = () => request === slotsRequest.current;

    setSlotsLoading(true);
    setSlotsError(false);
    return getSlots(doctorId, selectedDate)
      .then((data) => {
        if (isCurrent()) setSlots(data);
      })
      .catch((e) => {
        if (isCurrent()) setSlotsError(e);
      })
      .finally(() => {
        if (isCurrent()) setSlotsLoading(false);
      });
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
  }, [doctorId]);

  // раньше лента знала только сетку по дням недели, поэтому день отпуска выглядел
  // рабочим и на него можно было нажать. Теперь спрашиваем разбор по датам:
  // отпуск и выходной приходят готовыми статусами
  useEffect(() => {
    if (!doctorId) return;
    const from = isoDate(weekStart);
    const to = isoDate(addDays(weekStart, 6));
    getDoctorCalendar(doctorId, from, to)
      .then((days) => {
        setCalendar((prev) => ({
          ...prev,
          ...Object.fromEntries(days.map((day) => [day.date, day])),
        }));
      })
      .catch(() => {});
  }, [doctorId, weekStart]);

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
      if (e.code === "SLOT_TAKEN" || e.code === "SLOT_NOT_AVAILABLE") {
        toast.error(t("booking.slotTaken"));
        setSelectedSlot(null);
        loadSlots();
      } else if (e.code === "ALREADY_BOOKED") {
        toast.error(t("booking.alreadyBooked"));
      } else {
        toast.error(errorText(t, e));
      }
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

  const tabSlotTime =
    selectedSlot && visibleSlots.some((slot) => slot.time === selectedSlot.time)
      ? selectedSlot.time
      : visibleSlots.length > 0
        ? visibleSlots[0].time
        : null;

  // раньше это была догадка «день недели рабочий, а слотов нет — значит отпуск»,
  // и полностью занятый день показывался как отпуск. Теперь статус приходит с сервера
  const showAbsence = dayStatus(selectedDate) === "absent";

  const load = useCallback(() => {
    if (!doctorId) return Promise.resolve();
    setLoading(true);
    setError(false);
    return getDoctor(doctorId)
      .then(setDoctor)
      .catch((e) => setError(e))
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
        <LoadingStatus />
        <Skeleton className="h-32" />
        <Skeleton className="mt-md h-64" />
      </div>
    );
  }

  if (error || !doctor) {
    return (
      <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
        <ErrorState error={error} onRetry={load} />
      </div>
    );
  }

  if (booked) {
    return (
      <div className="mx-auto max-w-dialog px-md py-xl md:px-lg">
        <Card className="flex flex-col items-center p-lg text-center">
          <span aria-hidden="true" className="material-symbols-outlined text-6xl text-primary">check_circle</span>
          <h1 className="mt-md text-headline-md font-bold text-on-surface">
            {t("booking.successTitle")}
          </h1>
          <p className="mt-sm text-body-md text-on-surface-variant">{t("booking.successText")}</p>
          <div className="mt-md flex flex-col items-center gap-xs rounded-xl bg-surface-container-low px-md py-sm">
            <p className="text-body-md font-bold text-on-surface">{doctor.full_name}</p>
            <p className="text-label-md text-on-surface-variant">
              {formatDate(booked.date, lang)}, {clock(booked.time)}
            </p>
          </div>
          <Link
            to="/account"
            className="mt-lg w-full rounded-xl bg-primary py-3 font-bold text-on-primary transition-all hover:opacity-90 active:scale-95"
          >
            {t("booking.toAccount")}
          </Link>
        </Card>
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
            <DoctorAvatar
              doctor={doctor}
              className="h-24 w-24 rounded-xl"
              textClass="text-headline-lg"
            />
            <div className="text-center sm:text-left">
              <span className="mb-xs inline-block w-fit rounded-full bg-secondary-container px-3 py-1 text-label-md font-semibold text-on-secondary-container">
                {doctor.specialization}
              </span>
              <h2 className="text-headline-md font-semibold text-on-surface">{doctor.full_name}</h2>
            </div>
          </Card>
          <Card className="p-md">
            <div className="mb-md flex items-center justify-between">
              <h3 id="week-heading" className="text-headline-md font-semibold text-on-surface">
                {t("booking.week")}
              </h3>
              <div className="flex gap-xs">
                <button
                  type="button"
                  disabled={isoDate(weekStart) <= isoDate(startOfWeek(new Date()))}
                  onClick={() => setWeekStart((prev) => addDays(prev, -7))}
                  aria-label={t("booking.prevWeek")}
                  className="grid h-10 w-10 place-items-center rounded-full text-on-surface-variant transition-all hover:bg-surface-container disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <span aria-hidden="true" className="material-symbols-outlined">chevron_left</span>
                </button>
                <button
                  type="button"
                  onClick={() => setWeekStart((prev) => addDays(prev, 7))}
                  aria-label={t("booking.nextWeek")}
                  className="grid h-10 w-10 place-items-center rounded-full text-on-surface-variant transition-all hover:bg-surface-container"
                >
                  <span aria-hidden="true" className="material-symbols-outlined">chevron_right</span>
                </button>
              </div>
            </div>
            <div
              role="radiogroup"
              aria-labelledby="week-heading"
              className="grid grid-cols-7 gap-xs md:gap-sm"
            >
              {weekDays.map((date) => {
                const iso = isoDate(date);
                const isPast = iso < todayIso;
                const isSelected = iso === selectedDate;
                const isToday = iso === todayIso;
                const status = dayStatus(iso);
                const isAbsent = !isPast && status === "absent";
                const isOff = !isPast && status === "off";
                const disabled = isPast || isAbsent || isOff;

                // цвет не единственный признак: у отпуска и выходного свой значок
                // и своя подпись для скринридера, иначе состояние не различить
                // ни в чёрно-белой печати, ни при дальтонизме
                const look = isSelected
                  ? "border-2 border-primary bg-primary-container/10 text-primary"
                  : isAbsent
                    ? "cursor-not-allowed border-error/40 bg-error-container/40 text-on-surface-variant"
                    : isOff
                      ? "cursor-not-allowed border-outline-variant bg-surface-container-low text-on-surface-variant"
                      : isPast
                        ? "cursor-not-allowed border-outline-variant bg-surface-container opacity-50"
                        : "border-outline-variant hover:border-primary";

                const note = isAbsent
                  ? t("booking.dayAbsent")
                  : isOff
                    ? t("booking.dayOff")
                    : null;

                return (
                  <button
                    key={iso}
                    type="button"
                    ref={(element) => {
                      dayRefs.current[iso] = element;
                    }}
                    role="radio"
                    aria-checked={isSelected}
                    aria-label={note ? `${formatDate(iso, lang)} — ${note}` : formatDate(iso, lang)}
                    tabIndex={iso === tabDayIso ? 0 : -1}
                    disabled={disabled}
                    onClick={() => selectDay(date)}
                    onKeyDown={(event) => onDayKeyDown(event, date)}
                    className={`flex flex-col items-center rounded-lg border p-xs transition-all md:p-sm ${look}`}
                  >
                    <span className="text-label-md font-semibold text-on-surface-variant">
                      {shorts[(date.getDay() + 6) % 7]}
                    </span>
                    <span className="text-body-lg font-bold">{date.getDate()}</span>
                    {isAbsent ? (
                      <span aria-hidden="true" className="material-symbols-outlined text-base text-error">
                        beach_access
                      </span>
                    ) : isOff ? (
                      <span aria-hidden="true" className="material-symbols-outlined text-base text-outline">
                        event_busy
                      </span>
                    ) : isToday ? (
                      <span className="mt-0.5 h-1 w-1 rounded-full bg-primary" />
                    ) : null}
                  </button>
                );
              })}
            </div>
          </Card>
          <Card className="p-md">
            <h3 id="slots-heading" className="mb-md text-headline-md font-semibold text-on-surface">
              {t("booking.slots")}
            </h3>
            {slotsError ? (
              <ErrorState error={slotsError} onRetry={loadSlots} />
            ) : slotsLoading ? (
              <div className="grid grid-cols-2 gap-sm sm:grid-cols-4 md:grid-cols-5">
                <LoadingStatus />
                {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => (
                  <Skeleton key={i} className="h-12" />
                ))}
              </div>
            ) : showAbsence ? (
              <div className="flex items-center gap-sm rounded-lg bg-tertiary-container p-sm text-on-tertiary-container">
                <span aria-hidden="true" className="material-symbols-outlined">info</span>
                <p className="text-body-md">{t("booking.absence")}</p>
              </div>
            ) : visibleSlots.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-xl text-center">
                <span aria-hidden="true" className="material-symbols-outlined mb-sm text-6xl text-outline">
                  event_busy
                </span>
                <p className="text-headline-md font-semibold text-on-surface-variant">
                  {t("booking.noSlots")}
                </p>
              </div>
            ) : (
              <div
                role="radiogroup"
                aria-labelledby="slots-heading"
                className="grid grid-cols-2 gap-sm sm:grid-cols-4 md:grid-cols-5"
              >
                {visibleSlots.map((slot, index) => {
                  const isActive = selectedSlot && selectedSlot.time === slot.time;
                  return (
                    <button
                      key={slot.time}
                      type="button"
                      ref={(element) => {
                        slotRefs.current[slot.time] = element;
                      }}
                      role="radio"
                      aria-checked={Boolean(isActive)}
                      tabIndex={slot.time === tabSlotTime ? 0 : -1}
                      onClick={() => setSelectedSlot(slot)}
                      onKeyDown={(event) => onSlotKeyDown(event, index)}
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
          <div className="below-header">
            <Card className="bg-surface-container-high p-md">
              <h3 className="mb-md text-label-md font-semibold uppercase tracking-widest text-primary">
                {t("booking.summary")}
              </h3>
              <div className="space-y-sm">
                <div className="flex items-start gap-sm">
                  <span aria-hidden="true" className="material-symbols-outlined text-primary">person</span>
                  <div>
                    <p className="text-label-md text-on-surface-variant">{t("booking.doctor")}</p>
                    <p className="text-body-md font-bold text-on-surface">{doctor.full_name}</p>
                  </div>
                </div>
                <div className="flex items-start gap-sm">
                  <span aria-hidden="true" className="material-symbols-outlined text-primary">event</span>
                  <div>
                    <p className="text-label-md text-on-surface-variant">{t("booking.date")}</p>
                    <p className="text-body-md font-bold text-on-surface">
                      {formatDate(selectedDate, lang)}
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-sm">
                  <span aria-hidden="true" className="material-symbols-outlined text-primary">schedule</span>
                  <div>
                    <p className="text-label-md text-on-surface-variant">{t("booking.time")}</p>
                    <p className="text-body-md font-bold text-on-surface">
                      {selectedSlot ? clock(selectedSlot.time) : t("booking.pickSlot")}
                    </p>
                  </div>
                </div>
                {selectedSlot && departments[selectedSlot.department_id] && (
                  <div className="flex items-start gap-sm">
                    <span aria-hidden="true" className="material-symbols-outlined text-primary">meeting_room</span>
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
