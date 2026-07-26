import { useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useT } from "../lib/i18n.jsx";
import BottomNav from "./BottomNav.jsx";
import Footer from "./Footer.jsx";
import OfflineBar from "./OfflineBar.jsx";
import TopNav from "./TopNav.jsx";

export default function Layout() {
  const t = useT();
  const location = useLocation();

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [location.pathname]);

  return (
    <div className="relative flex min-h-screen flex-col">
      <a href="#main" className="skip-link">
        {t("common.skipToContent")}
      </a>
      <OfflineBar />
      <TopNav />
      <main id="main" tabIndex={-1} className="flex-1 pb-24 md:pb-0">
        <div key={location.pathname} className="page-enter">
          <Outlet />
        </div>
      </main>
      <Footer />
      <BottomNav />
    </div>
  );
}
