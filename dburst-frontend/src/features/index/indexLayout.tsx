import { Outlet } from 'react-router-dom';
import { useState } from 'react';
import Header from '@/shared/components/Header';
import { Footer } from '@/shared/components/Footer';
import { AuthModal } from "@/features/index/components/AuthModal";

export type IndexOutletContext = {
  onStartBuilding: () => void;
};

export default function IndexLayout() {
  const [isLoginModalOpen, setLoginModalOpen] = useState(false);
  const [isGetStartedOpen, setGetStartedOpen] = useState(false);

  return (
    <>
    <Header
      mode="landing"
      onLoginClick={() => setLoginModalOpen(true)}
      onGetStartedClick={() => setGetStartedOpen(true)}
    />

    <Outlet />

    <Footer />

    {/* Login Modal */}
    <AuthModal
      isOpen={isLoginModalOpen}
      onClose={() => setLoginModalOpen(false)}
      title="Login"
    />

    {/* Get Started Modal */}
    <AuthModal
      isOpen={isGetStartedOpen}
      onClose={() => setGetStartedOpen(false)}
      title="Get Started"
    />
  </>
);
}