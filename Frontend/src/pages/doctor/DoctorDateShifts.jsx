import { useCallback, useEffect, useState } from "react";
import { errorText } from "../../lib/api/errorText.js";
import {
  createMyDateShift,
  deleteMyDateShift,
  getMyDateShifts,
} from "../../lib/api/schedules.js";
import { clock, formatDate, isoDate } from "../../lib/format.js";
import { useI18n } from "../../lib/i18n.jsx";
import { useToast } from "../../lib/toast.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ConfirmDialog from "../../components/ConfirmDialog.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Field, Select } from "../../components/Field.jsx";
import LoadingStatus from "../../components/LoadingStatus.jsx";
import Skeleton from "../../components/Skeleton.jsx";

const today = () => isoDate(new Date());

const emptyForm = () => ({
  department_id: "",
  date: today(),
  start_time: "09:00",
  end_time: "17:00",
  slot_duration: 30,
  buffer_duration: 0,
});

// Разовые смены умел только бэкенд: эндпоинты `/api/schedules/me/dates` появились
// вместе с зонами роста, а формы к ним не было. Из-за этого в расписании стоял
// один «день недели» без единой даты, а в легенде календаря висел статус
// «разовая смена», который врач не мог создать никаким способом.
export default function DoctorDateShifts({ departments, onChanged }) {
  const { t, lang } = useI18n();
  const toast = useToast();
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(null);
  const [confirming, setConfirming] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return getMyDateShifts()
      .then(setShifts)
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (departments.length === 1) {
      setForm((prev) => ({ ...prev, department_id: String(departments[0].id) }));
    }
  }, [departments]);

  const change = (name) => (e) => setForm((prev) => ({ ...prev, [name]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      await createMyDateShift({
        department_id: Number(form.department_id),
        date: form.date,
        start_time: `${form.start_time}:00`,
        end_time: `${form.end_time}:00`,
        slot_duration: Number(form.slot_duration),
        buffer_duration: Number(form.buffer_duration),
      });
      toast.success(t("common.saved"));
      setForm(emptyForm());
      setOpen(false);
      await load();
      onChanged?.();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    setRemoving(confirming.id);

    try {
      await deleteMyDateShift(confirming.id);
      toast.success(t("doctorCabinet.shiftDeleted"));
      setConfirming(null);
      await load();
      onChanged?.();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setRemoving(null);
    }
  };

  const sorted = [...shifts].sort((a, b) => String(a.date).localeCompare(String(b.date)));

  return (
    <section className="mt-xl">
      <div className="mb-xs flex flex-wrap items-center justify-between gap-sm">
        <h2 className="text-headline-md font-bold text-on-surface">
          {t("doctorCabinet.shifts")}
        </h2>
        <Button
          variant={open ? "outline" : "primary"}
          icon={open ? "close" : "add"}
          onClick={() => setOpen((prev) => !prev)}
        >
          {open ? t("common.cancel") : t("doctorCabinet.addShift")}
        </Button>
      </div>
      <p className="mb-md text-body-md text-on-surface-variant">
        {t("doctorCabinet.shiftsHint")}
      </p>

      {open && (
        <Card as="form" onSubmit={submit} className="mb-md space-y-md p-md">
          <div className="grid gap-sm sm:grid-cols-2">
            <Select
              label={t("doctorCabinet.department")}
              required
              value={form.department_id}
              onChange={change("department_id")}
            >
              <option value="">{t("doctorCabinet.pickDepartment")}</option>
              {departments.map((department) => (
                <option key={department.id} value={department.id}>
                  {department.name}
                </option>
              ))}
            </Select>
            <Field
              label={t("doctorCabinet.date")}
              type="date"
              required
              min={today()}
              value={form.date}
              onChange={change("date")}
            />
            <Field
              label={t("doctorCabinet.startTime")}
              type="time"
              required
              value={form.start_time}
              onChange={change("start_time")}
            />
            <Field
              label={t("doctorCabinet.endTime")}
              type="time"
              required
              value={form.end_time}
              onChange={change("end_time")}
            />
            <Field
              label={t("doctorCabinet.slotDuration")}
              type="number"
              min={5}
              max={240}
              required
              value={form.slot_duration}
              onChange={change("slot_duration")}
            />
            <Field
              label={t("doctorCabinet.bufferDuration")}
              type="number"
              min={0}
              max={120}
              value={form.buffer_duration}
              onChange={change("buffer_duration")}
            />
          </div>
          <Button type="submit" icon="save" loading={saving}>
            {t("common.save")}
          </Button>
        </Card>
      )}

      {error ? (
        <ErrorState error={error} onRetry={load} />
      ) : loading ? (
        <div className="space-y-sm">
          <LoadingStatus />
          {[0, 1].map((i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <EmptyState
          icon="edit_calendar"
          title={t("doctorCabinet.noShifts")}
          text={t("doctorCabinet.noShiftsText")}
        />
      ) : (
        <div className="space-y-sm">
          {sorted.map((shift) => (
            <Card key={shift.id} className="flex flex-wrap items-center justify-between gap-sm p-md">
              <div className="flex items-center gap-md">
                <span aria-hidden="true" className="material-symbols-outlined text-tertiary">
                  edit_calendar
                </span>
                <div>
                  <p className="font-bold text-on-surface">{formatDate(shift.date, lang)}</p>
                  <p className="text-label-md text-on-surface-variant">
                    {clock(shift.start_time)} – {clock(shift.end_time)} ·{" "}
                    {t("doctorCabinet.slotMinutes", { count: shift.slot_duration })}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setConfirming(shift)}
                disabled={removing === shift.id}
                aria-label={t("common.delete")}
                className="grid h-9 w-9 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-error-container hover:text-error disabled:opacity-50"
              >
                <span aria-hidden="true" className="material-symbols-outlined text-lg">delete</span>
              </button>
            </Card>
          ))}
        </div>
      )}

      {confirming && (
        <ConfirmDialog
          title={t("doctorCabinet.shifts")}
          text={t("doctorCabinet.deleteShiftConfirm")}
          loading={removing === confirming.id}
          onConfirm={remove}
          onClose={() => setConfirming(null)}
        />
      )}
    </section>
  );
}
