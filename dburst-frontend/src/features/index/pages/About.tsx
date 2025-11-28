import { Target, Users, Rocket, Heart } from 'lucide-react';

export default function About() {
  return (
    <div className="pt-16 min-h-screen bg-zinc-950">
      <div className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl font-bold text-zinc-100 mb-6">
              About DBurst
            </h1>
            <p className="text-xl text-zinc-400">
              Empowering designers and developers to create exceptional interfaces
            </p>
          </div>

          <div className="prose prose-invert max-w-none">
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 mb-8">
              <h2 className="text-2xl font-bold text-zinc-100 mb-4">Our Mission</h2>
              <p className="text-zinc-400 leading-relaxed">
                At DBurst, we believe that creating beautiful, functional user interfaces
                should be accessible to everyone. Our AI-powered platform combines the
                latest in machine learning with intuitive design tools to help you build
                stunning UIs faster than ever before.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
              <ValueCard
                icon={<Target className="w-8 h-8 text-blue-400" />}
                title="Our Vision"
                description="To democratize UI design and make professional-grade tools accessible to creators worldwide."
              />
              <ValueCard
                icon={<Users className="w-8 h-8 text-purple-400" />}
                title="Our Community"
                description="Join thousands of designers and developers building the future of web interfaces."
              />
              <ValueCard
                icon={<Rocket className="w-8 h-8 text-green-400" />}
                title="Innovation First"
                description="We're constantly pushing boundaries with cutting-edge AI and design technology."
              />
              <ValueCard
                icon={<Heart className="w-8 h-8 text-red-400" />}
                title="Built with Care"
                description="Every feature is crafted with attention to detail and user experience in mind."
              />
            </div>

            <div className="bg-gradient-to-br from-blue-600/10 to-purple-600/10 border border-zinc-800 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-zinc-100 mb-4">Part of MindBurst</h2>
              <p className="text-zinc-400 leading-relaxed">
                DBurst is a proud product of MindBurst, a company dedicated to creating
                innovative tools that enhance creativity and productivity. We're committed
                to building the next generation of design and development platforms.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ValueCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="p-6 rounded-xl bg-zinc-900 border border-zinc-800">
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-zinc-100 mb-2">{title}</h3>
      <p className="text-sm text-zinc-400">{description}</p>
    </div>
  );
}
