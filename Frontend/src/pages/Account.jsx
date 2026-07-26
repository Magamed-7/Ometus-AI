import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { cancelAppointment, getMyAppointments } from "../lib/api/appointments.js";
import { getDepartments } from "../lib/api/departments.js";
import { searchDoctors } from "../lib/api/doctors.js";
import { getFilials } from "../lib/api/filials.js";
import { getPatient, updateMe, updatePatient } from "../lib/api/users.js";
import { errorText } from "../lib/api/errorText.js";
import { useAuth } from "../lib/auth/AuthContext.jsx";
import { useI18n } from "../lib/i18n.jsx";
import { useToast } from "../lib/toast.jsx";
import AppointmentCard from "../components/AppointmentCard.jsx";
import Button from "../components/Button.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import RescheduleModal from "../components/RescheduleModal.jsx";
import Card from "../components/Card.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ErrorState from "../components/ErrorState.jsx";
import { Field } from "../components/Field.jsx";
import ProfileSidebar from "../components/ProfileSidebar.jsx";
import LoadingStatus from "../components/LoadingStatus.jsx";
import Skeleton from "../components/Skeleton.jsx";

export default function Account() {
  const { t } = useI18n();
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [tab, setTab] = useState("active");
  const [editing, setEditing] = useState(false);
  const [rescheduling, setRescheduling] = useState(null);
  const [cancelTarget, setCancelTarget] = useState(null);
  const [cancelling, setCancelling] = useState(false);
  const [profileForm, setProfileForm] = useState({ first_name: "", last_name: "", phone: "" });
  const [savingProfile, setSavingProfile] = useState(false);
  const [patient, setPatient] = useState(null);
  const [patientForm, setPatientForm] = useState({ full_name: "", date_of_birth: "", phone: "" });
  const [savingPatient, setSavingPatient] = useState(false);

  const [appointments, setAppointments] = useState([]);
  const [doctors, setDoctors] = useState({});
  const [departments, setDepartments] = useState({});
  const [filials, setFilials] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    getPatient()
      .then(setPatient)
      .catch(() => {});
  }, []);

  const loadAppointments = useCallback(() => {
    setLoading(true);
    setError(false);
    return Promise.all([getMyAppointments(), searchDoctors(), getDepartments(), getFilials()])
      .then(([appts, docs, deps, fils]) => {
        setAppointments(appts);
        setDoctors(Object.fromEntries(docs.map((d) => [d.id, d])));
        setDepartments(Object.fromEntries(deps.map((d) => [d.id, d])));
        setFilials(Object.fromEntries(fils.map((f) => [f.id, f])));
      })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadAppointments();
  }, [loadAppointments]);

  const activeAppointments = appointments.filter((a) => a.status === "booked");
  const historyAppointments = appointments.filter((a) => a.status !== "booked");

  const onCancel = async () => {
    setCancelling(true);
    try {
      await cancelAppointment(cancelTarget.id);
      setCancelTarget(null);
      await loadAppointments();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setCancelling(false);
    }
  };

  const onLogout = () => {
    logout();
    navigate("/");
  };

  const onToggleEdit = () => {
    if (!editing) {
      setProfileForm({
        first_name: user.first_name || "",
        last_name: user.last_name || "",
        phone: user.phone || "",
      });
      setPatientForm({
        full_name: patient?.full_name || "",
        date_of_birth: patient?.date_of_birth || "",
        phone: patient?.phone || "",
      });
    }
    setEditing((v) => !v);
  };

  const savePatient = async (e) => {
    e.preventDefault();
    setSavingPatient(true);
    try {
      const updated = await updatePatient({
        full_name: patientForm.full_name || null,
        date_of_birth: patientForm.date_of_birth || null,
        phone: patientForm.phone || null,
      });
      setPatient(updated);
      toast.success(t("common.saved"));
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setSavingPatient(false);
    }
  };

  const saveProfile = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await updateMe(profileForm);
      await refreshUser();
      toast.success(t("common.saved"));
      setEditing(false);
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setSavingProfile(false);
    }
  };

  const tabs = [
    { id: "active", label: t("account.tabActive") },
    { id: "history", label: t("account.tabHistory") },
    { id: "documents", label: t("account.tabDocuments") },
  ];

  return (
    <div className="mx-auto max-w-7xl px-sm py-md md:px-lg">
      <div className="grid grid-cols-1 items-start gap-md lg:grid-cols-12">
        <aside className="lg:col-span-4 lg:sticky lg:top-24">
          <ProfileSidebar
            user={user}
            editing={editing}
            onToggleEdit={onToggleEdit}
            onLogout={onLogout}
          />
        </aside>

        <div className="lg:col-span-8">
          {editing && (
            <Card className="mb-md p-md">
              <h2 className="mb-md text-headline-md font-semibold text-on-surface">
                {t("account.editProfile")}
              </h2>
              <form onSubmit={saveProfile} className="grid gap-sm sm:grid-cols-2">
                <Field
                  label={t("auth.firstName")}
                  value={profileForm.first_name}
                  onChange={(e) => setProfileForm((f) => ({ ...f, first_name: e.target.value }))}
                />
                <Field
                  label={t("auth.lastName")}
                  value={profileForm.last_name}
                  onChange={(e) => setProfileForm((f) => ({ ...f, last_name: e.target.value }))}
                />
                <Field
                  label={t("auth.phone")}
                  value={profileForm.phone}
                  onChange={(e) => setProfileForm((f) => ({ ...f, phone: e.target.value }))}
                  className="sm:col-span-2"
                />
                <div className="flex gap-sm sm:col-span-2">
                  <Button type="submit" loading={savingProfile}>
                    {t("common.save")}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => setEditing(false)}>
                    {t("common.cancel")}
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {editing && (
            <Card className="mb-md p-md">
              <h2 className="mb-md text-headline-md font-semibold text-on-surface">
                {t("account.patientCard")}
              </h2>
              <form onSubmit={savePatient} className="grid gap-sm sm:grid-cols-2">
                <Field
                  label={t("account.fullName")}
                  value={patientForm.full_name}
                  onChange={(e) => setPatientForm((f) => ({ ...f, full_name: e.target.value }))}
                  className="sm:col-span-2"
                />
                <Field
                  label={t("account.dateOfBirth")}
                  type="date"
                  value={patientForm.date_of_birth}
                  onChange={(e) => setPatientForm((f) => ({ ...f, date_of_birth: e.target.value }))}
                />
                <Field
                  label={t("auth.phone")}
                  value={patientForm.phone}
                  onChange={(e) => setPatientForm((f) => ({ ...f, phone: e.target.value }))}
                />
                <div className="sm:col-span-2">
                  <Button type="submit" loading={savingPatient}>
                    {t("common.save")}
                  </Button>
                </div>
              </form>
            </Card>
          )}

          <div className="no-scrollbar mb-md flex gap-xs overflow-x-auto pb-2">
            {tabs.map((tb) => (
              <button
                key={tb.id}
                type="button"
                onClick={() => setTab(tb.id)}
                className={`whitespace-nowrap rounded-full px-md py-sm font-bold transition-all ${
                  tab === tb.id
                    ? "bg-primary-container text-on-primary-container shadow-sm"
                    : "bg-surface-container-high text-on-surface-variant hover:bg-surface-container"
                }`}
              >
                {tb.label}
              </button>
            ))}
          </div>

          <div className="space-y-md">
            {tab === "active" &&
              (error ? (
                <ErrorState error={error} onRetry={loadAppointments} />
              ) : loading ? (
                <div className="space-y-md">
                  <LoadingStatus />
                  {[0, 1].map((i) => (
                    <Skeleton key={i} className="h-48" />
                  ))}
                </div>
              ) : activeAppointments.length === 0 ? (
                <EmptyState icon="event_available" title={t("account.noActive")} />
              ) : (
                activeAppointments.map((a) => (
                  <AppointmentCard
                    key={a.id}
                    appointment={a}
                    doctor={doctors[a.doctor_id]}
                    department={departments[a.department_id]}
                    filial={filials[departments[a.department_id]?.filial_id]}
                  >
                    <div className="flex flex-wrap gap-sm">
                      <Button
                        variant="outline"
                        icon="edit_calendar"
                        onClick={() => setRescheduling(a)}
                        className="flex-1"
                      >
                        {t("account.reschedule")}
                      </Button>
                      <Button
                        variant="danger"
                        icon="close"
                        onClick={() => setCancelTarget(a)}
                        className="flex-1"
                      >
                        {t("account.cancel")}
                      </Button>
                    </div>
                  </AppointmentCard>
                ))
              ))}
            {tab === "history" &&
              (error ? (
                <ErrorState error={error} onRetry={loadAppointments} />
              ) : loading ? (
                <div className="space-y-md">
                  <LoadingStatus />
                  {[0, 1].map((i) => (
                    <Skeleton key={i} className="h-48" />
                  ))}
                </div>
              ) : historyAppointments.length === 0 ? (
                <EmptyState icon="history" title={t("account.noHistory")} />
              ) : (
                historyAppointments.map((a) => (
                  <AppointmentCard
                    key={a.id}
                    appointment={a}
                    doctor={doctors[a.doctor_id]}
                    department={departments[a.department_id]}
                    filial={filials[departments[a.department_id]?.filial_id]}
                  />
                ))
              ))}
            {tab === "documents" && (
              <EmptyState
                icon="folder_open"
                title={t("account.noDocuments")}
                text={t("account.documentsHint")}
              />
            )}
          </div>
        </div>
      </div>

      {cancelTarget && (
        <ConfirmDialog
          title={t("account.cancel")}
          text={t("account.cancelConfirm")}
          confirmLabel={t("account.cancel")}
          loading={cancelling}
          onConfirm={onCancel}
          onClose={() => setCancelTarget(null)}
        />
      )}

      {rescheduling && (
        <RescheduleModal
          appointment={rescheduling}
          onClose={() => setRescheduling(null)}
          onDone={() => {
            setRescheduling(null);
            loadAppointments();
          }}
        />
      )}
    </div>
  );
}
