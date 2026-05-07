import { Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import IndexLayout from '@/features/index/indexLayout';
import Home from "@/features/index/pages/Home";
import Demo from '@/features/index/pages/Demo';
import About from '@/features/index/pages/About';
import Contact from '@/features/index/pages/Contact';
import GithubCallback from '@/features/index/pages/GithubCallback';
import GoogleCallback from '@/features/index/pages/GoogleCallback';

export default function IndexRoutes() {
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  const handleLoginClick = () => {
    setIsLoginModalOpen(true);
  };

  const handleCloseLoginModal = () => {
    setIsLoginModalOpen(false);
  };

  const handleStartBuilding = () => {
    setIsLoginModalOpen(true);
  };

  return (
    <Routes>
      {/* OAuth callback pages — rendered bare, intentionally no layout.
          IndexLayout renders Header → useUserProfile → 401s → logout()
          while login is in progress, causing a race condition.  */}
      <Route path="/auth/google/callback" element={<GoogleCallback />} />
      <Route path="/auth/github/callback" element={<GithubCallback />} />

      <Route path="/" element={<IndexLayout />}>
        <Route index element={<Home onStartBuilding={handleStartBuilding} />} />
        <Route path="/demo" element={<Demo />} />
        <Route path="/about" element={<About />} />
        <Route path="/contact" element={<Contact />} />
      </Route>
    </Routes>
  );
};