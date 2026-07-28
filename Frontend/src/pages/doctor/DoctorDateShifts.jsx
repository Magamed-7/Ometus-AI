import { useCallback, useEffect, useState } from "react";
import { errorText } from "../../lib/api/errorText.js";
import { deleteMyDateShift, getMyDateShifts } from "../../lib/api/schedules.js";
import { clock, formatDate } from "../../lib/format.js";
import { useI18n } from "../../lib/i18n.jsx";
import { useToast } from "../../lib/toast.jsx";
import Card from "../../components/Card.jsx";
import ConfirmDialog from "../../components/ConfirmDialog.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import LoadingStatus from "../../components/LoadingStatus.jsx";
import Skeleton from "../../components/Skeleton.jsx";

// Только список. Добавляются смены сверху, в той же форме, что и дни недели —
// двух кнопок «добавить расписание» на одной странице быть не должно
export default function DoctorDateShifts({ reloadKey, onChanged }) {
  const { t, lang } = useI18n();
  const toast = useToast();
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
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
  }, [load, reloadKey]);

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
      <h2 className="mb-xs text-headline-md font-bold text-on-surface">
        {t("doctorCabinet.shifts")}
      </h2>
      <p className="mb-md text-body-md text-on-surface-variant">
        {t("doctorCabinet.shiftsHint")}
      </p>

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
