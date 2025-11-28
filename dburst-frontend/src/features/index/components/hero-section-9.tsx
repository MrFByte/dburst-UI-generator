import { Sparkles, Zap, Download } from 'lucide-react';
import { Button } from '@/shared/ui/button';
import { useEffect, useState } from 'react';
import { motion } from "framer-motion";

const words = [
  "Define",
  "Design",
  "Develop",
  "Debug",
  "Deliver",
];

interface HeroSectionProps {
  onStartBuilding: () => void;
  onViewDemo: () => void;
}

export function HeroSection9({ onStartBuilding, onViewDemo }: HeroSectionProps) {
  const [wordIndex, setWordIndex] = useState(0);
  const [displayText, setDisplayText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const currentWord = words[wordIndex];

    let typeSpeed = isDeleting ? 90 : 120;

    const timeout = setTimeout(() => {
      if (!isDeleting) {
        // typing forward
        if (displayText.length < currentWord.length) {
          setDisplayText(currentWord.slice(0, displayText.length + 1));
        } else {
          // pause before deleting
          setTimeout(() => setIsDeleting(true), 900);
        }
      } else {
        // deleting
        if (displayText.length > 0) {
          setDisplayText(currentWord.slice(0, displayText.length - 1));
        } else {
          setIsDeleting(false);
          setWordIndex((prev) => (prev + 1) % words.length);
        }
      }
    }, typeSpeed);

    return () => clearTimeout(timeout);
  }, [displayText, isDeleting, wordIndex]);

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-b from-zinc-900 via-zinc-900 to-zinc-950">
      <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1920&q=80')] bg-cover bg-center opacity-10" />

      <div className="absolute inset-0 bg-gradient-to-t from-zinc-900 via-transparent to-transparent" />

      <div className="relative z-10 container mx-auto px-4 py-20">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-800/50 border border-zinc-700 mb-8 backdrop-blur-sm">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-zinc-300">AI-Powered Design Tools</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-zinc-100 mb-6 leading-tight flex flex-wrap gap-3 justify-center items-center">
            {/* Typing Word */}
            <motion.span
              key={wordIndex}
              className="inline-block text-zinc-50"
            >
              {displayText}
              <span className="inline-block w-[2px] h-10 md:h-14 bg-blue-400 ml-1 animate-pulse" />
            </motion.span>

            {/* “with” little italic */}
            <span className="text-xl italic text-zinc-300 mt-2">
              with
            </span>

            {/* Burst Gradient */}
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Burst
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-zinc-400 mb-12 max-w-3xl mx-auto leading-relaxed">
            Create futuristic interfaces with AI-powered design tools.
            Build, edit stunning UIs in an easy-to-use workflow.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
            <Button
              size="lg"
              className="text-base px-8 py-6 bg-blue-600 hover:bg-blue-700 text-white"
              onClick={onStartBuilding}
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Start Building
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="text-base px-8 py-6"
              onClick={onViewDemo}
            >
              View Demo
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <FeatureCard
              icon={<Sparkles className="w-8 h-8 text-blue-400" />}
              title="AI-Assisted Design"
              description="Let AI help you create beautiful interfaces instantly"
            />
            <FeatureCard
              icon={<Zap className="w-8 h-8 text-yellow-400" />}
              title="Real-Time Editing"
              description="See your changes come to life as you build"
            />
            <FeatureCard
              icon={<Download className="w-8 h-8 text-green-400" />}
              title="One-Click Export"
              description="Export production-ready code in seconds"
            />
          </div>
        </div>

        <div className="mt-20 max-w-6xl mx-auto">
          <div className="relative rounded-2xl overflow-hidden border border-zinc-800 shadow-2xl">
            <div className="absolute inset-0 bg-gradient-to-tr from-blue-600/10 to-purple-600/10" />
            <img
              src="https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1920&q=80"
              alt="DBurst Interface"
              className="w-full h-auto"
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="p-6 rounded-xl bg-zinc-800/50 border border-zinc-700 backdrop-blur-sm hover:bg-zinc-800/70 transition-all duration-300 hover:scale-105">
      <div className="mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-zinc-100 mb-2">{title}</h3>
      <p className="text-sm text-zinc-400">{description}</p>
    </div>
  );
}
