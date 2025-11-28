import React, { useState } from "react";
import {
  MessageSquare,
  PanelLeft,
  Settings,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import PanelPlaceholder from "../components/PanelPlaceholder";
import AdvancedPromptForm from "../components/AdvancedPromptForm";
import SimplePromptForm from "../components/SimplePromptForm";
import { SchemaRenderer } from "../lib/renderer";
import { generatedData } from "../sampleData/SampleUIGenerator";
import { normalizeSchema } from "../lib/normalizeSchema";

export default function UIGenerator() {
  const [isEditPanelOpen, setIsEditPanelOpen] = useState(false);
  const [isChatPanelOpen, setIsChatPanelOpen] = useState(false);
  const [isAdvancedMode, setIsAdvancedMode] = useState(false);
  const [isUiGenerated, setIsUiGenerated] = useState(false);
  const [generatedSchema, setGeneratedSchema] = useState(null);

  // Simulated generation
  const handleGenerate = (prompt, mode = "simple") => {
    setGeneratedSchema(normalizeSchema(generatedData.schema));
    setIsUiGenerated(true);
  };

  const toggleAdvancedMode = () => {
    setIsAdvancedMode(!isAdvancedMode);
  };

  const renderContent = () => {
    // When UI is generated — render schema preview
    if (isUiGenerated && generatedSchema) {
      return (
        <div className="w-full h-full flex flex-col p-4 bg-gray-900 overflow-auto">
            {/* 1. Live Preview */}
            <div className="flex-1 border border-gray-700 p-4 bg-white/5 rounded-lg mb-4 flex items-start justify-center overflow-auto">
                {/* The component that renders the live UI */}
                <SchemaRenderer schema={{ 
                    ...generatedSchema, 
                    // Adjust class for better presentation in the preview box
                    class: "w-full max-w-5xl mx-auto bg-white/5" 
                }} />
            </div>
            
            {/* 2. Raw Code Display */}
            <h3 className="text-gray-300 font-medium mb-2">Generated React Code:</h3>
            <div className="h-64 border border-gray-700 bg-gray-950 rounded-lg p-3 overflow-y-scroll text-sm font-mono text-gray-300 whitespace-pre-wrap shadow-inner">
                <pre>{generatedSchema}</pre>
            </div>
        </div>
      );
    }

    // Prompt form (default view)
    return (
      <div className="flex flex-col items-center justify-center w-full max-w-5xl px-4">
        {isAdvancedMode ? (
          <AdvancedPromptForm onGenerate={handleGenerate} />
        ) : (
          <SimplePromptForm onGenerate={handleGenerate} />
        )}

        <button
          onClick={toggleAdvancedMode}
          className="mt-6 flex items-center text-gray-400 font-medium text-sm hover:text-white transition cursor-pointer"
        >
          {isAdvancedMode ? (
            <>
              <ChevronUp className="w-4 h-4 mr-1" />
              Switch to Simple Prompt
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4 mr-1" />
              Advanced Prompting (XML)
            </>
          )}
        </button>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] font-sans flex flex-col overflow-hidden">
      {/* Top Navbar */}
      <header className="flex justify-between items-center h-16 px-4 border-b border-gray-800 bg-gray-900/90 backdrop-blur-sm z-50">
        <div className="text-2xl font-extrabold tracking-tight text-white">D-burst</div>
        <div className="text-sm font-medium text-gray-500">AI Frontend Generator</div>
        <div className="flex items-center space-x-2">
          <Settings className="w-5 h-5 text-gray-400 hover:text-white cursor-pointer transition" />
        </div>
      </header>

      {/* Main layout */}
      <div className="grow flex relative">
        {/* Left Panel Toggle */}
        <div className="fixed left-0 top-1/2 transform -translate-y-1/2 z-30">
          <button
            className="p-3 bg-gray-800 border border-gray-700 rounded-r-lg shadow-lg hover:bg-gray-700 transition cursor-pointer"
            onClick={() => {
              setIsEditPanelOpen(true);
              setIsChatPanelOpen(false);
            }}
          >
            <PanelLeft className="w-6 h-6 text-gray-300" />
          </button>
        </div>

        {/* Right Panel Toggle */}
        <div className="fixed right-0 top-1/2 transform -translate-y-1/2 z-30">
          <button
            className="p-3 bg-gray-800 border border-gray-700 rounded-l-lg shadow-lg hover:bg-gray-700 transition cursor-pointer"
            onClick={() => {
              setIsChatPanelOpen(true);
              setIsEditPanelOpen(false);
            }}
          >
            <MessageSquare className="w-6 h-6 text-gray-300" />
          </button>
        </div>

        {/* Center Area */}
        <main className="grow flex items-center justify-center p-8">
          {renderContent()}
        </main>

        {/* Left Edit Panel */}
        <PanelPlaceholder
          title="Edit Structure & Properties"
          side="left"
          isOpen={isEditPanelOpen}
          onClose={() => setIsEditPanelOpen(false)}
        />

        {/* Right Chat Panel */}
        <PanelPlaceholder
          title="AI Chat & Refinements"
          side="right"
          isOpen={isChatPanelOpen}
          onClose={() => setIsChatPanelOpen(false)}
        />
      </div>
    </div>
  );
}
