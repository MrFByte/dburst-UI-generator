import { useNavigate } from 'react-router-dom';
import { HeroSection9 } from '@/features/index/components/hero-section-9';


interface HomeProps {
  onStartBuilding: () => void;
}

export default function Home({ onStartBuilding }: HomeProps) {
  const navigate = useNavigate();

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
