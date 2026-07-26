import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../../lib/auth/AuthContext.jsx";
import { findMyDoctor, getDoctorDepartments } from "../../lib/api/doctors.js";
import { errorText } from "../../lib/api/errorText.js";
import { createMySchedule, getMySchedule } from "../../lib/api/schedules.js";
import { clock } from "../../lib/format.js";
import { useI18n } from "../../lib/i18n.jsx";
import { useToast } from "../../lib/toast.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Field, Select } from "../../components/Field.jsx";
import Skeleton from "../../components/Skeleton.jsx";

const EMPTY_FORM = {
  department_id: "",
  weekday: "0",
  start_time: "09:00",
  end_time: "17:00",
  slot_duration: "20",
  buffer_duration: "0",
};

export default function DoctorSchedule() {
  const { t } = useI18n();
  const { user } = useAuth();
  const toast = useToast();
  const [schedule, setSchedule] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [names, setNames] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return Promise.all([getMySchedule(), findMyDoctor(user.id)])
      .then(async ([rows, doctor]) => {
        const own = doctor ? await getDoctorDepartments(doctor.id) : [];
        setSchedule(rows);
        setDepartments(own);
        setNames(Object.fromEntries(own.map((d) => [d.id, d.name])));
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [user.id]);

  useEffect(() => {
    load();
  }, [load]);

  const change = (name) => (e) => setForm((prev) => ({ ...prev, [name]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      await createMySchedule({
        department_id: Number(form.department_id),
        weekday: Number(form.weekday),
        start_time: form.start_time,
        end_time: form.end_time,
        slot_duration: Number(form.slot_duration),
        buffer_duration: Number(form.buffer_duration),
      });
      toast.success(t("common.saved"));
      setForm(EMPTY_FORM);
      setOpen(false);
      await load();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setSaving(false);
    }
  };

  const fulls = t("weekdays.full");
  const sorted = [...schedule].sort(
    (a, b) => a.weekday - b.weekday || String(a.start_time).localeCompare(String(b.start_time))
  );

  return (
    <div className="mx-auto max-w-5xl px-sm py-md md:px-lg">
      <div className="mb-md flex flex-wrap items-center justify-between gap-sm">
        <h1 className="text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
          {t("doctorCabinet.scheduleTitle")}
        </h1>
        <Button
          variant={open ? "outline" : "primary"}
          icon={open ? "close" : "add"}
          onClick={() => setOpen((prev) => !prev)}
        >
          {open ? t("common.cancel") : t("doctorCabinet.addSchedule")}
        </Button>
      </div>

      {open && (
        <Card as="form" onSubmit={submit} className="mb-md space-y-md p-md">
          {departments.length === 0 && !loading && (
            <p className="rounded-xl bg-error-container px-4 py-3 text-body-md text-on-error-container">
              {t("doctorCabinet.noDepartments")}
            </p>
          )}
          <div className="grid gap-sm sm:grid-cols-2">
            <Select
              label={t("doctorCabinet.department")}
              required
              value={form.department_id}
              onChange={change("department_id")}
            >
              <option value="">{t("doctorCabinet.pickDepartment")}</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </Select>
            <Select
              label={t("doctorCabinet.weekday")}
              value={form.weekday}
              onChange={change("weekday")}
            >
              {fulls.map((name, index) => (
                <option key={name} value={index}>
                  {name}
                </option>
              ))}
            </Select>
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
              min="5"
              max="240"
              required
              value={form.slot_duration}
              onChange={change("slot_duration")}
            />
            <Field
              label={t("doctorCabinet.bufferDuration")}
              type="number"
              min="0"
              max="120"
              value={form.buffer_duration}
              onChange={change("buffer_duration")}
            />
          </div>
          <Button type="submit" icon="save" loading={saving} disabled={!form.department_id}>
            {t("common.save")}
          </Button>
        </Card>
      )}

      {error ? (
        <ErrorState onRetry={load} />
      ) : loading ? (
        <div className="space-y-sm">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <EmptyState icon="calendar_month" title={t("doctorCabinet.noSchedule")} />
      ) : (
        <div className="space-y-sm">
          {sorted.map((row) => (
            <Card key={row.id} className="flex flex-wrap items-center justify-between gap-sm p-md">
              <div className="flex items-center gap-md">
                <span className="w-24 font-bold text-on-surface">{fulls[row.weekday]}</span>
                <span className="text-body-md text-on-surface">
                  {clock(row.start_time)} – {clock(row.end_time)}
                </span>
              </div>
              <div className="flex items-center gap-sm text-label-md text-on-surface-variant">
                <span className="rounded-full bg-secondary-container px-2.5 py-1 text-on-secondary-container">
                  {names[row.department_id] || `#${row.department_id}`}
                </span>
                <span>
                  {row.slot_duration}
                  {row.buffer_duration ? ` +${row.buffer_duration}` : ""} {t("doctorCabinet.minShort")}
                </span>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
