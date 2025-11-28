import { Mail, MessageSquare, MapPin, Send } from 'lucide-react';
import { Button } from '@/shared/ui/button';
import { useState } from 'react';
import { toast } from '@/shared/hooks/useToast';

export default function Contact() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    toast.success('Message sent! We\'ll get back to you soon.');
    setFormData({ name: '', email: '', message: '' });
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <div className="pt-16 min-h-screen bg-zinc-950">
      <div className="container mx-auto px-4 py-20">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl font-bold text-zinc-100 mb-6">
              Get in Touch
            </h1>
            <p className="text-xl text-zinc-400">
              Have questions? We'd love to hear from you.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label
                    htmlFor="name"
                    className="block text-sm font-medium text-zinc-300 mb-2"
                  >
                    Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-lg text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                    placeholder="John Doe"
                  />
                </div>

                <div>
                  <label
                    htmlFor="email"
                    className="block text-sm font-medium text-zinc-300 mb-2"
                  >
                    Email
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-lg text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                    placeholder="john@example.com"
                  />
                </div>

                <div>
                  <label
                    htmlFor="message"
                    className="block text-sm font-medium text-zinc-300 mb-2"
                  >
                    Message
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    rows={6}
                    className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-lg text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent resize-none"
                    placeholder="Tell us how we can help..."
                  />
                </div>

                <Button
                  type="submit"
                  size="lg"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <Send className="w-5 h-5 mr-2" />
                  Send Message
                </Button>
              </form>
            </div>

            <div className="space-y-8">
              <ContactInfo
                icon={<Mail className="w-6 h-6 text-blue-400" />}
                title="Email"
                content="hello@dburst.com"
                description="Send us an email anytime"
              />
              <ContactInfo
                icon={<MessageSquare className="w-6 h-6 text-purple-400" />}
                title="Live Chat"
                content="Available 24/7"
                description="Get instant support from our team"
              />
              <ContactInfo
                icon={<MapPin className="w-6 h-6 text-green-400" />}
                title="Office"
                content="San Francisco, CA"
                description="Visit us at our headquarters"
              />

              <div className="bg-gradient-to-br from-blue-600/10 to-purple-600/10 border border-zinc-800 rounded-2xl p-8">
                <h3 className="text-xl font-semibold text-zinc-100 mb-3">
                  Need immediate help?
                </h3>
                <p className="text-zinc-400 mb-4">
                  Check out our documentation or join our community forum for quick answers.
                </p>
                <Button variant="outline" size="sm">
                  Visit Help Center
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ContactInfo({
  icon,
  title,
  content,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  content: string;
  description: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="flex-shrink-0 w-12 h-12 bg-zinc-900 border border-zinc-800 rounded-lg flex items-center justify-center">
        {icon}
      </div>
      <div>
        <h3 className="text-lg font-semibold text-zinc-100 mb-1">{title}</h3>
        <p className="text-zinc-300 font-medium mb-1">{content}</p>
        <p className="text-sm text-zinc-500">{description}</p>
      </div>
    </div>
  );
}
