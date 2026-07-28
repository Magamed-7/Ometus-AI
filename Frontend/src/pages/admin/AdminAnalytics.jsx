import { useCallback, useEffect, useState } from "react";
import { Bar, Line } from "react-chartjs-2";
import {
  getAiCosts,
  getAiDaily,
  getAiFeedback,
  getDailyReport,
  getWorkloadReport,
} from "../../lib/api/admin.js";
import { formatDateShort, isoDate } from "../../lib/format.js";
import { useI18n } from "../../lib/i18n.jsx";
import {
  BAR_MARK,
  baseOptions,
  chartInk,
  LINE_MARK,
  palette,
  STATUS_ORDER,
} from "../../lib/charts.js";
import Card from "../../components/Card.jsx";
import ChartCard from "../../components/ChartCard.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import LoadingStatus from "../../components/LoadingStatus.jsx";
import Skeleton from "../../components/Skeleton.jsx";
import { Field } from "../../components/Field.jsx";

function daysAgo(count) {
  const date = new Date();
  date.setDate(date.getDate() - count);
  return isoDate(date);
}

function Tile({ icon, label, value, note, tone = "text-on-surface" }) {
  return (
    <Card className="p-md">
      <div className="flex items-center gap-2 text-on-surface-variant">
        <span aria-hidden="true" className="material-symbols-outlined text-lg">
          {icon}
        </span>
        <span className="text-label-md">{label}</span>
      </div>
      <p className={`mt-1 text-headline-lg-mobile font-bold ${tone}`}>{value}</p>
      {note && <p className="text-label-md text-on-surface-variant">{note}</p>}
    </Card>
  );
}

export default function AdminAnalytics() {
  const { t, lang } = useI18n();
  const [dateFrom, setDateFrom] = useState(() => daysAgo(29));
  const [dateTo, setDateTo] = useState(() => isoDate(new Date()));
  const [daily, setDaily] = useState([]);
  const [workload, setWorkload] = useState([]);
  const [aiDaily, setAiDaily] = useState([]);
  const [costs, setCosts] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // тема может смениться, пока страница открыта: цвета графиков берутся из токенов,
  // поэтому при переключении их надо перерисовать, а не оставить светлые на тёмном
  const [themeTick, setThemeTick] = useState(0);

  useEffect(() => {
    const observer = new MutationObserver(() => setThemeTick((prev) => prev + 1));
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return Promise.all([
      getDailyReport(dateFrom, dateTo),
      getWorkloadReport({ date_from: dateFrom, date_to: dateTo }),
      getAiDaily(dateFrom, dateTo),
      getAiCosts(dateFrom, dateTo),
      getAiFeedback(dateFrom, dateTo),
    ])
      .then(([days, load_, ai, cost, marks]) => {
        setDaily(days);
        setWorkload(load_);
        setAiDaily(ai);
        setCosts(cost);
        setFeedback(marks);
      })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [dateFrom, dateTo]);

  useEffect(() => {
    load();
  }, [load]);

  const colors = palette();
  const ink = chartInk();
  const labels = daily.map((day) => formatDateShort(day.date, lang));

  const appointmentsData = {
    labels,
    datasets: STATUS_ORDER.map((status, index) => ({
      label: t(`status.${status}`),
      data: daily.map((day) => day[status]),
      backgroundColor: colors[index],
      borderColor: ink.surface,
      ...BAR_MARK,
    })),
  };

  // топ-10, а не все 50: полсотни подписей по вертикали превращаются в кашу,
  // полный список остаётся во вкладке «Отчёты»
  const topDoctors = [...workload].sort((a, b) => b.total - a.total).slice(0, 10);

  const workloadData = {
    labels: topDoctors.map((row) => row.full_name),
    datasets: [
      {
        label: t("analytics.appointments"),
        data: topDoctors.map((row) => row.total),
        backgroundColor: colors[0],
        borderColor: ink.surface,
        ...BAR_MARK,
      },
    ],
  };

  const costData = {
    labels: aiDaily.map((day) => formatDateShort(day.date, lang)),
    datasets: [
      {
        label: t("analytics.spent"),
        data: aiDaily.map((day) => Number(day.cost_usd)),
        borderColor: colors[3],
        backgroundColor: `${colors[3]}22`,
        fill: true,
        ...LINE_MARK,
      },
    ],
  };

  const callsData = {
    labels: aiDaily.map((day) => formatDateShort(day.date, lang)),
    datasets: [
      {
        label: t("analytics.succeeded"),
        data: aiDaily.map((day) => day.succeeded),
        backgroundColor: colors[1],
        borderColor: ink.surface,
        ...BAR_MARK,
      },
      {
        label: t("analytics.failed"),
        data: aiDaily.map((day) => day.failed),
        backgroundColor: colors[2],
        borderColor: ink.surface,
        ...BAR_MARK,
      },
    ],
  };

  const totalAppointments = daily.reduce((sum, day) => sum + day.total, 0);
  const totalCalls = aiDaily.reduce((sum, day) => sum + day.calls, 0);
  const avgLatency = totalCalls
    ? Math.round(
        aiDaily.reduce((sum, day) => sum + day.avg_duration_ms * day.calls, 0) / totalCalls
      )
    : 0;

  return (
    <div className="space-y-lg">
      <div className="flex flex-wrap items-end gap-sm">
        <Field
          label={t("admin.dateFrom")}
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
        />
        <Field
          label={t("admin.dateTo")}
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
        />
      </div>

      {error ? (
        <ErrorState error={error} onRetry={load} />
      ) : loading ? (
        <div className="space-y-md">
          <LoadingStatus />
          <div className="grid grid-cols-2 gap-md lg:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-md lg:grid-cols-4">
            <Tile
              icon="event_note"
              label={t("analytics.appointments")}
              value={totalAppointments}
              note={t("analytics.forPeriod")}
            />
            <Tile
              icon="smart_toy"
              label={t("analytics.aiCalls")}
              value={totalCalls}
              note={avgLatency ? t("analytics.avgLatency", { ms: avgLatency }) : undefined}
            />
            <Tile
              icon="payments"
              label={t("analytics.aiSpent")}
              value={`$${Number(costs?.total_usd || 0).toFixed(4)}`}
              note={
                costs?.budget_used_percent != null
                  ? t("analytics.ofBudget", {
                      percent: costs.budget_used_percent,
                      budget: Number(costs.budget_usd).toFixed(2),
                    })
                  : undefined
              }
              tone={costs?.over_budget ? "text-error" : "text-on-surface"}
            />
            <Tile
              icon="thumb_up"
              label={t("analytics.helpfulRate")}
              value={
                feedback?.helpful_rate != null
                  ? `${Math.round(feedback.helpful_rate * 100)}%`
                  : "—"
              }
              note={t("analytics.ratings", { count: feedback?.total || 0 })}
            />
          </div>

          {costs && !costs.prices_configured && (
            <p className="rounded-xl bg-secondary-container px-md py-3 text-body-md text-on-secondary-container">
              {t("analytics.noPrices")}
            </p>
          )}

          <ChartCard
            title={t("analytics.appointmentsByDay")}
            hint={t("analytics.appointmentsByDayHint")}
            columns={[
              t("analytics.date"),
              ...STATUS_ORDER.map((status) => t(`status.${status}`)),
              t("admin.total"),
            ]}
            rows={daily.map((day) => [
              day.date,
              ...STATUS_ORDER.map((status) => day[status]),
              day.total,
            ])}
            height={300}
          >
            <Bar
              key={`appointments-${themeTick}`}
              data={appointmentsData}
              options={baseOptions({ stacked: true })}
            />
          </ChartCard>

          <ChartCard
            title={t("analytics.doctorLoad")}
            hint={t("analytics.doctorLoadHint")}
            columns={[t("nav.adminDoctors"), t("doctors.specialization"), t("admin.total")]}
            rows={topDoctors.map((row) => [row.full_name, row.specialization, row.total])}
            height={340}
          >
            <Bar
              key={`workload-${themeTick}`}
              data={workloadData}
              options={{
                ...baseOptions(),
                indexAxis: "y",
                plugins: {
                  ...baseOptions().plugins,
                  // одна серия — легенда не нужна, её называет заголовок карточки
                  legend: { display: false },
                },
              }}
            />
          </ChartCard>

          <div className="grid grid-cols-1 gap-md xl:grid-cols-2">
            <ChartCard
              title={t("analytics.aiSpentByDay")}
              hint={t("analytics.aiSpentByDayHint")}
              columns={[t("analytics.date"), t("analytics.spent"), t("analytics.aiCalls")]}
              rows={aiDaily.map((day) => [
                day.date,
                `$${Number(day.cost_usd).toFixed(4)}`,
                day.calls,
              ])}
            >
              <Line
                key={`cost-${themeTick}`}
                data={costData}
                options={{
                  ...baseOptions({ currency: true }),
                  plugins: { ...baseOptions({ currency: true }).plugins, legend: { display: false } },
                }}
              />
            </ChartCard>

            <ChartCard
              title={t("analytics.aiCallsByDay")}
              hint={t("analytics.aiCallsByDayHint")}
              columns={[
                t("analytics.date"),
                t("analytics.succeeded"),
                t("analytics.failed"),
                t("analytics.latency"),
              ]}
              rows={aiDaily.map((day) => [
                day.date,
                day.succeeded,
                day.failed,
                `${day.avg_duration_ms} мс`,
              ])}
            >
              <Bar
                key={`calls-${themeTick}`}
                data={callsData}
                options={baseOptions({ stacked: true })}
              />
            </ChartCard>
          </div>

          {feedback?.recent_complaints?.length > 0 && (
            <Card className="p-md">
              <h3 className="mb-sm text-body-lg font-bold text-on-surface">
                {t("analytics.complaints")}
              </h3>
              <ul className="space-y-sm">
                {feedback.recent_complaints.map((item, index) => (
                  <li
                    key={index}
                    className="rounded-xl border border-outline-variant p-sm text-body-md text-on-surface-variant"
                  >
                    {item.comment || item.question || "—"}
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
