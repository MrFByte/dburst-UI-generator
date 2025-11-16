import { Play, Code, Palette, Layers } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useNavigate } from 'react-router-dom';

export default function Demo() {
  const navigate = useNavigate();

  return (
    <div className="pt-16 min-h-screen bg-zinc-950">
      <div className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl font-bold text-zinc-100 mb-6">
              See DBurst in Action
            </h1>
            <p className="text-xl text-zinc-400 mb-8">
              Watch how our AI-powered design tools transform your ideas into reality
            </p>
          </div>

          <div className="aspect-video bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden mb-12 relative">
            <img
              src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1920&q=80"
              alt="Demo"
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
                <Play className="w-6 h-6 mr-2" />
                Play Demo
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            <DemoFeature
              icon={<Code className="w-8 h-8 text-blue-400" />}
              title="Code Generation"
              description="Generate clean, production-ready code instantly"
            />
            <DemoFeature
              icon={<Palette className="w-8 h-8 text-purple-400" />}
              title="Theme Customization"
              description="Customize colors, fonts, and styles with ease"
            />
            <DemoFeature
              icon={<Layers className="w-8 h-8 text-green-400" />}
              title="Component Library"
              description="Access hundreds of pre-built components"
            />
            <DemoFeature
              icon={<Play className="w-8 h-8 text-yellow-400" />}
              title="Live Preview"
              description="See changes in real-time as you build"
            />
          </div>

          <div className="text-center">
            <Button
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white px-8"
              onClick={() => navigate('/')}
            >
              Get Started Now
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function DemoFeature({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="p-6 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition-all">
      <div className="mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-zinc-100 mb-2">{title}</h3>
      <p className="text-sm text-zinc-400">{description}</p>
    </div>
  );
}
