import { useState } from 'react';
import {
  Send,
  Code
} from 'lucide-react';
import FormField from './FormFiled';


export default function AdvancedPromptForm({ onGenerate }) {
  const [formData, setFormData] = useState({
    instructions: 'Create a responsive landing page for a tech news website.',
    page_title: 'TechNews Home',
    description: 'A modern landing page showcasing the latest tech news and articles.',
    design_style: 'modern, minimalist',
    components: 'navbar, hero section, news grid, contact form',
    layout: 'single column with sidebar',
    responsive: 'true',
    primary_color: '#1e1e1e',
    secondary_color: '#2c2c2c',
    typography: 'Roboto, sans-serif',
    interactions: 'hover effects on buttons, form validation',
    output_format: 'HTML, CSS, JavaScript',
    examples: 'https://example.com/technews',
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.id]: e.target.value,
    });
  };

  const constructXmlPayload = () => {
    let xml = '<advanced_prompt>';
    
    // Helper to wrap text fields in XML tags
    const wrap = (tag, content) => content ? `<${tag}>${content}</${tag}>` : '';

    xml += wrap('instructions', formData.instructions);
    xml += wrap('page_title', formData.page_title);
    xml += wrap('description', formData.description);
    xml += wrap('design_style', formData.design_style);
    
    // Components (assuming comma-separated list for simplicity)
    if (formData.components) {
      xml += '<components>';
      formData.components.split(',').map(c => c.trim()).forEach(c => {
        if (c) xml += `<component>${c}</component>`;
      });
      xml += '</components>';
    }

    xml += wrap('layout', formData.layout);
    xml += wrap('responsive', formData.responsive);

    // Color Scheme (Assuming separate fields for primary/secondary)
    if (formData.primary_color || formData.secondary_color) {
      xml += '<color_scheme>';
      xml += wrap('primary', formData.primary_color);
      xml += wrap('secondary', formData.secondary_color);
      xml += '</color_scheme>';
    }

    xml += wrap('typography', formData.typography);

    xml += wrap('interactions', formData.interactions);
    xml += wrap('output_format', formData.output_format);

    // Examples (assuming comma-separated list for simplicity)
    if (formData.examples) {
      xml += '<examples>';
      formData.examples.split(',').map(e => e.trim()).forEach(e => {
        if (e) xml += `<example>${e}</example>`;
      });
      xml += '</examples>';
    }

    xml += '</advanced_prompt>';
    return xml;
  };

  const handleAdvancedGenerate = () => {
    const xmlPayload = constructXmlPayload();
    // Check if at least one field is filled, otherwise disable button
    const isFormEmpty = Object.values(formData).every(value => !value.trim());

    if (!isFormEmpty) {
        onGenerate(xmlPayload, 'xml');
    }
  };

  const isFormValid = Object.values(formData).some(value => value.trim());

  return (
    <div className="w-full max-w-4xl bg-gray-800/50 p-8 rounded-xl shadow-2xl border border-gray-800">
      <div className="flex items-center space-x-3 mb-4">
        <Code className="w-6 h-6 text-gray-400" />
        <h2 className="text-xl font-bold text-white">Advanced Structured Prompting</h2>
      </div>
      <p className="text-gray-400 mb-4 bg-gray-800 p-3 rounded-lg border border-gray-700">
        **Disclaimer:** All fields below are optional. Use them to provide precise direction for generation.
      </p>
      
      <div className="max-h-[60vh] overflow-y-auto pr-2">
        <FormField 
          label="Instructions (Core Prompt)" 
          id="instructions" 
          value={formData.instructions} 
          onChange={handleChange} 
          placeholder="A detailed prompt describing the required UI." 
          type="textarea"
          rows={3}
        />
        <FormField 
          label="Page Title" 
          id="page_title" 
          value={formData.page_title} 
          onChange={handleChange} 
          placeholder="e.g., Landing Page, User Dashboard"
        />
        <FormField 
          label="Description" 
          id="description" 
          value={formData.description} 
          onChange={handleChange} 
          placeholder="A high-level summary of the page's purpose."
        />
        <FormField 
          label="Design Style" 
          id="design_style" 
          value={formData.design_style} 
          onChange={handleChange} 
          placeholder="e.g., modern, brutalist, flat, 90s nostalgia"
        />
        <FormField 
          label="Components (Comma-separated)" 
          id="components" 
          value={formData.components} 
          onChange={handleChange} 
          placeholder="e.g., Navbar, Hero section, Pricing table"
        />
        <FormField 
          label="Layout" 
          id="layout" 
          value={formData.layout} 
          onChange={handleChange} 
          placeholder="e.g., single column, grid, with sidebar"
        />
        <FormField 
          label="Responsive" 
          id="responsive" 
          value={formData.responsive} 
          onChange={handleChange} 
          placeholder="true/false (or 'mobile only', 'desktop first')"
        />

        <h3 className="text-lg font-semibold text-white mt-6 mb-3 border-t border-gray-800 pt-4">Color & Typography</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField 
            label="Primary Color (Hex)" 
            id="primary_color" 
            value={formData.primary_color} 
            onChange={handleChange} 
            placeholder="#1e1e1e"
          />
          <FormField 
            label="Secondary Color (Hex)" 
            id="secondary_color" 
            value={formData.secondary_color} 
            onChange={handleChange} 
            placeholder="#2c2c2c"
          />
        </div>
        <FormField 
          label="Typography" 
          id="typography" 
          value={formData.typography} 
          onChange={handleChange} 
          placeholder="e.g., Roboto, sans-serif"
        />

        <FormField 
          label="Interactions" 
          id="interactions" 
          value={formData.interactions} 
          onChange={handleChange} 
          placeholder="e.g., hover effects on buttons, form validation"
        />
        <FormField 
          label="Output Format" 
          id="output_format" 
          value={formData.output_format} 
          onChange={handleChange} 
          placeholder="e.g., HTML/Tailwind CSS, React/Styled Components"
        />
        <FormField 
          label="Example Links (Comma-separated)" 
          id="examples" 
          value={formData.examples} 
          onChange={handleChange} 
          placeholder="e.g., https://example.com/demo"
        />
      </div> {/* End scroll container */}


      <div className="mt-6 flex justify-end">
        <button
          className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl shadow-lg hover:bg-blue-700 transition transform duration-200 flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
          onClick={handleAdvancedGenerate}
          disabled={!isFormValid}
        >
          <Send className="w-5 h-5" />
          <span>Generate Structured UI</span>
        </button>
      </div>
    </div>
  );
};