import { useNavigate, useOutletContext } from 'react-router-dom';
import { HeroSection9 } from '@/features/index/components/hero-section-9';
import type { IndexOutletContext } from '@/features/index/indexLayout';

export default function Home() {
  const navigate = useNavigate();
  const { onStartBuilding } = useOutletContext<IndexOutletContext>();

  const handleViewDemo = () => {
    navigate('/demo');
  };

  return (
    <>    
    <div className="pt-16">
      <HeroSection9
        onStartBuilding={onStartBuilding}
        onViewDemo={handleViewDemo}
      />
    </div>
    </>
  );
}
