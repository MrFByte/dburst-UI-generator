// src/pages/dashboard/Generate.tsx
import { Sparkles, Wand2 } from "lucide-react";
import { useState } from "react";

export default function Generate() {
  const [prompt, setPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    
    setIsGenerating(true);
    // TODO: Implement AI generation logic
    console.log("Generating:", prompt);
    
    // Simulate generation
    setTimeout(() => {
      setIsGenerating(false);
    }, 2000);
  };

  const templates = [
    { name: "Landing Page", description: "Modern landing page with hero section" },
    { name: "Dashboard", description: "Analytics dashboard with charts" },
    { name: "Login Form", description: "Authentication form with validation" },
    { name: "E-commerce", description: "Product listing with cart" },
  ];

  return (
    <>
      {/* Page Title */}
      <div className="mb-12">
        <h1 className="font-orbitron font-bold text-4xl text-[#F1F1F4] mb-2">
          AI Generation
        </h1>
        <p className="text-[#8F8FA3]">
          Create stunning interfaces with AI assistance
        </p>
      </div>

      {/* Generation Input */}
      <div className="max-w-4xl mx-auto mb-12">
        <div className="rounded-2xl gradient-border glass-effect glow-purple p-8">
          <div className="flex items-start gap-4 mb-6">
            <Sparkles className="w-6 h-6 text-[#B656DC] mt-1" />
            <div className="flex-1">
              <h2 className="font-orbitron font-bold text-xl text-[#F1F1F4] mb-2">
                Describe your vision
              </h2>
              <p className="text-[#8F8FA3] text-sm">
                Tell us what you want to create, and our AI will generate it for you
              </p>
            </div>
          </div>

          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="E.g., Create a dark-themed portfolio website with smooth animations..."
            className="w-full h-32 p-4 rounded-[14px] gradient-border glass-effect text-[#F1F1F4] placeholder:text-[#8F8FA3] focus:outline-none focus:ring-2 focus:ring-[#B656DC] resize-none"
          />

          <button
            onClick={handleGenerate}
            disabled={!prompt.trim() || isGenerating}
            className="mt-4 w-full py-3 rounded-[14px] gradient-border glass-effect glow-purple text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isGenerating ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Wand2 className="w-4 h-4" />
                Generate with AI
              </>
            )}
          </button>
        </div>
      </div>

      {/* Templates */}
      <div>
        <h2 className="font-orbitron font-bold text-2xl text-[#F1F1F4] mb-6">
          Quick Templates
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {templates.map((template, index) => (
            <div
              key={index}
              className="rounded-2xl gradient-border glass-effect p-6 hover:opacity-90 transition-opacity cursor-pointer"
              onClick={() => setPrompt(template.description)}
            >
              <h3 className="font-orbitron font-bold text-lg text-[#F1F1F4] mb-2">
                {template.name}
              </h3>
              <p className="text-[#8F8FA3] text-sm">
                {template.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}