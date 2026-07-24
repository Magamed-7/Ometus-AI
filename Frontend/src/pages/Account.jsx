import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { updateMe } from "../lib/api/users.js";
import { errorText } from "../lib/api/errorText.js";
import { useAuth } from "../lib/auth/AuthContext.jsx";
import { useT } from "../lib/i18n.jsx";
import { useToast } from "../lib/toast.jsx";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import { Field } from "../components/Field.jsx";
import ProfileSidebar from "../components/ProfileSidebar.jsx";

export default function Account() {
  const t = useT();
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [tab, setTab] = useState("active");
  const [editing, setEditing] = useState(false);
  const [profileForm, setProfileForm] = useState({ first_name: "", last_name: "", phone: "" });
  const [savingProfile, setSavingProfile] = useState(false);

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
    }
    setEditing((v) => !v);
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
            {tab === "active" && <Card className="p-md" />}
            {tab === "history" && <Card className="p-md" />}
            {tab === "documents" && <Card className="p-md" />}
          </div>
        </div>
      </div>
    </div>
  );
}
