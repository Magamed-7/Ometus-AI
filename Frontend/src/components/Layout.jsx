import { Outlet } from "react-router-dom";
import BottomNav from "./BottomNav.jsx";
import Footer from "./Footer.jsx";
import TopNav from "./TopNav.jsx";

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <TopNav />
      <main className="flex-1 pb-24 md:pb-0">
        <Outlet />
      </main>
      <Footer />
      <BottomNav />
    </div>
  );
}
