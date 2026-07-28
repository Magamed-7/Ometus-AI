import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { searchDoctors } from "../lib/api/doctors.js";
import { getFilials } from "../lib/api/filials.js";
import { getReviews } from "../lib/api/reviews.js";
import { formatDate } from "../lib/format.js";
import { useI18n } from "../lib/i18n.jsx";
import Card from "../components/Card.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ErrorState from "../components/ErrorState.jsx";
import LoadingStatus from "../components/LoadingStatus.jsx";
import Skeleton from "../components/Skeleton.jsx";

function Stars({ rating, label }) {
  return (
    <span className="flex items-center gap-0.5" role="img" aria-label={label}>
      {[1, 2, 3, 4, 5].map((star) => (
        <span
          key={star}
          aria-hidden="true"
          className={`material-symbols-outlined text-lg ${
            star <= rating ? "filled text-tertiary" : "text-outline-variant"
          }`}
        >
          star
        </span>
      ))}
    </span>
  );
}

export default function Reviews() {
  const { t, lang } = useI18n();
  const [data, setData] = useState(null);
  const [doctors, setDoctors] = useState([]);
  const [filials, setFilials] = useState([]);
  const [doctorId, setDoctorId] = useState("");
  const [filialId, setFilialId] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    searchDoctors()
      .then(setDoctors)
      .catch(() => {});
    getFilials()
      .then(setFilials)
      .catch(() => {});
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return getReviews({ doctor_id: doctorId, filial_id: filialId, page })
      .then(setData)
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [doctorId, filialId, page]);

  useEffect(() => {
    load();
  }, [load]);

  const reset = () => {
    setDoctorId("");
    setFilialId("");
    setPage(1);
  };

  const summary = data?.summary;
  const items = data?.items || [];
  const pages = data?.pages || 0;

  return (
    <div className="mx-auto max-w-7xl px-md py-lg md:px-lg">
      <div className="flex flex-col justify-between gap-md md:flex-row md:items-start">
        <div>
          <h1 className="text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
            {t("reviews.title")}
          </h1>
          <p className="mt-sm max-w-note text-body-lg text-on-surface-variant">
            {t("reviews.intro")}
          </p>
        </div>
        {/* средняя оценка считается по опубликованным отзывам; пока их нет,
            звёзд и числа не показываем вовсе — рисовать «4.9» не из чего */}
        {summary?.average != null && (
          <Card className="shrink-0 p-md text-center">
            <p className="text-headline-lg-mobile font-bold text-on-surface md:text-headline-lg">
              {summary.average.toFixed(1)}
            </p>
            <div className="mt-xs flex justify-center">
              <Stars
                rating={Math.round(summary.average)}
                label={t("reviews.ratingLabel", { value: summary.average })}
              />
            </div>
            <p className="mt-xs text-label-md text-on-surface-variant">
              {t("reviews.count", { count: summary.total })}
            </p>
          </Card>
        )}
      </div>

      <Card className="mt-lg flex flex-wrap items-end gap-sm p-md">
        <span className="flex items-center gap-xs text-label-md font-bold text-on-surface">
          <span aria-hidden="true" className="material-symbols-outlined text-lg">
            filter_list
          </span>
          {t("reviews.filter")}
        </span>
        <label className="flex flex-col gap-0.5">
          <span className="text-label-md text-on-surface-variant">{t("reviews.byFilial")}</span>
          <select
            value={filialId}
            onChange={(event) => {
              setFilialId(event.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-outline-variant bg-surface-container-lowest px-sm py-2 text-body-md text-on-surface"
          >
            <option value="">{t("reviews.allFilials")}</option>
            {filials.map((filial) => (
              <option key={filial.id} value={filial.id}>
                {filial.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-0.5">
          <span className="text-label-md text-on-surface-variant">{t("reviews.byDoctor")}</span>
          <select
            value={doctorId}
            onChange={(event) => {
              setDoctorId(event.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-outline-variant bg-surface-container-lowest px-sm py-2 text-body-md text-on-surface"
          >
            <option value="">{t("reviews.allDoctors")}</option>
            {doctors.map((doctor) => (
              <option key={doctor.id} value={doctor.id}>
                {doctor.full_name}
              </option>
            ))}
          </select>
        </label>
        {(doctorId || filialId) && (
          <button
            type="button"
            onClick={reset}
            className="rounded-lg border border-outline-variant px-md py-2 text-label-md font-semibold text-on-surface transition-all hover:bg-surface-container"
          >
            {t("reviews.reset")}
          </button>
        )}
      </Card>

      <div className="mt-lg">
        {error ? (
          <ErrorState error={error} onRetry={load} />
        ) : loading ? (
          <div className="grid grid-cols-1 gap-md md:grid-cols-3">
            <LoadingStatus />
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-56" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon="chat"
            title={t("reviews.emptyTitle")}
            text={t("reviews.emptyText")}
            action={
              <Link
                to="/doctors"
                className="mt-sm rounded-xl bg-primary px-lg py-3 font-bold text-on-primary transition-all hover:opacity-90"
              >
                {t("reviews.leave")}
              </Link>
            }
          />
        ) : (
          <div className="grid grid-cols-1 gap-md md:grid-cols-3">
            {items.map((review) => (
              <Card key={review.id} className="flex flex-col p-md">
                <div className="flex items-start justify-between gap-sm">
                  <div>
                    <p className="text-body-lg font-bold text-on-surface">{review.author}</p>
                    <p className="text-label-md text-on-surface-variant">
                      {formatDate(review.created_at.slice(0, 10), lang)}
                    </p>
                  </div>
                  <Stars
                    rating={review.rating}
                    label={t("reviews.ratingLabel", { value: review.rating })}
                  />
                </div>
                {review.doctor_name && (
                  <p className="mt-sm flex items-center gap-xs text-label-md text-primary">
                    <span aria-hidden="true" className="material-symbols-outlined text-base">
                      stethoscope
                    </span>
                    {review.doctor_name}
                  </p>
                )}
                {review.text && (
                  <p className="mt-sm flex-1 text-body-md text-on-surface-variant">
                    {review.text}
                  </p>
                )}
                {review.filial_name && (
                  <p className="mt-md flex items-center gap-xs text-label-md text-on-surface-variant">
                    <span aria-hidden="true" className="material-symbols-outlined text-base">
                      location_on
                    </span>
                    {review.filial_name}
                  </p>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      {pages > 1 && (
        <nav className="mt-lg flex justify-center gap-xs" aria-label={t("reviews.pagination")}>
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((prev) => prev - 1)}
            aria-label={t("reviews.prevPage")}
            className="grid h-10 w-10 place-items-center rounded-full text-on-surface-variant transition-all hover:bg-surface-container disabled:cursor-not-allowed disabled:opacity-40"
          >
            <span aria-hidden="true" className="material-symbols-outlined">chevron_left</span>
          </button>
          {Array.from({ length: pages }, (_, index) => index + 1).map((number) => (
            <button
              key={number}
              type="button"
              aria-current={number === page ? "page" : undefined}
              onClick={() => setPage(number)}
              className={`h-10 w-10 rounded-full text-label-md font-semibold transition-all ${
                number === page
                  ? "bg-primary text-on-primary"
                  : "text-on-surface-variant hover:bg-surface-container"
              }`}
            >
              {number}
            </button>
          ))}
          <button
            type="button"
            disabled={page >= pages}
            onClick={() => setPage((prev) => prev + 1)}
            aria-label={t("reviews.nextPage")}
            className="grid h-10 w-10 place-items-center rounded-full text-on-surface-variant transition-all hover:bg-surface-container disabled:cursor-not-allowed disabled:opacity-40"
          >
            <span aria-hidden="true" className="material-symbols-outlined">chevron_right</span>
          </button>
        </nav>
      )}
    </div>
  );
}
