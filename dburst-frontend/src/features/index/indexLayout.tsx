import { Outlet, useNavigate } from 'react-router-dom';
import Header from '@/shared/components/Header';
import { Footer } from '@/shared/components/Footer';

export type IndexOutletContext = {
  onStartBuilding: () => void;
};

export default function IndexLayout() {
  const navigate = useNavigate();

  return (
    <>
      <Header
        mode="landing"
        onLoginClick={() => navigate('/login')}
        onGetStartedClick={() => navigate('/signup')}
      />

      <Outlet context={{ onStartBuilding: () => navigate('/signup') } satisfies IndexOutletContext} />

      <Footer />
    </>
  );
}
