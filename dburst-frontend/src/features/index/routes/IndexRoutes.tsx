import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import IndexLayout from '@/features/index/indexLayout';
import Home from "@/features/index/pages/Home";
const Demo = lazy(() => import('@/features/index/pages/Demo'));
const About = lazy(() => import('@/features/index/pages/About'));
const Contact = lazy(() => import('@/features/index/pages/Contact'));
const GithubCallback = lazy(() => import('@/features/index/pages/GithubCallback'));
const GoogleCallback = lazy(() => import('@/features/index/pages/GoogleCallback'));
const SignIn = lazy(() => import('@/features/index/pages/SignIn'));
const SignUp = lazy(() => import('@/features/index/pages/SignUp'));

export default function IndexRoutes() {
  return (
    <Suspense fallback={null}>
    <Routes>
      {/* OAuth callback pages — rendered bare, intentionally no layout.
          IndexLayout renders Header → useUserProfile → 401s → logout()
          while login is in progress, causing a race condition.  */}
      <Route path="/auth/google/callback" element={<GoogleCallback />} />
      <Route path="/auth/github/callback" element={<GithubCallback />} />

      {/* Auth pages — rendered bare, no landing Header/Footer, so the
          nav's Login/Get Started buttons don't show up on top of them. */}
      <Route path="/login" element={<SignIn />} />
      <Route path="/signup" element={<SignUp />} />

      <Route path="/" element={<IndexLayout />}>
        <Route index element={<Home />} />
        <Route path="/demo" element={<Demo />} />
        <Route path="/about" element={<About />} />
        <Route path="/contact" element={<Contact />} />
      </Route>
    </Routes>
    </Suspense>
  );
};