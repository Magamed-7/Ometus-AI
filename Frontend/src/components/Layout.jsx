import { Outlet } from "react-router-dom";
import { useT } from "../lib/i18n.jsx";
import BottomNav from "./BottomNav.jsx";
import Footer from "./Footer.jsx";
import TopNav from "./TopNav.jsx";

export default function Layout() {
  const t = useT();

  return (
    <div className="relative flex min-h-screen flex-col">
      <a href="#main" className="skip-link">
        {t("common.skipToContent")}
      </a>
      <TopNav />
      <main id="main" tabIndex={-1} className="flex-1 pb-24 md:pb-0">
        <Outlet />
      </main>
      <Footer />
      <BottomNav />
    </div>
  );
}
