import { Outlet } from "react-router-dom";
import Header from "@/components/common/Header";
import Footer from "@/components/common/Footer";

export default function MainLayout() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <Header />

      <main className="relative z-10 pt-4 pb-20">
        <Outlet />
      </main>

      <Footer />
    </div>
  );
}
