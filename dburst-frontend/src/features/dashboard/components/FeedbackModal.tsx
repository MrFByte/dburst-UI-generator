import { useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { api } from '@/core/api/axiosConfig';
import { toast } from '@/shared/hooks/useToast';

const CATEGORIES = [
  'Generated Output',
  'Performance',
  'Bug report',
  'Feature request',
  'UI / Design',
  'Other'
];

const RATINGS = [
  { value: 1, emoji: "😞", label: "Poor",     animation: "animate-wiggle" },
  { value: 2, emoji: "😐", label: "Fair",     animation: "animate-pulse"  },
  { value: 3, emoji: "🙂", label: "Good",     animation: "animate-bounce" },
  { value: 4, emoji: "😄", label: "Great",    animation: "animate-bounce" },
  { value: 5, emoji: "🤩", label: "Loved it", animation: "animate-spin"   },
];

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const FeedbackModal = ({ isOpen, onClose }: FeedbackModalProps) => {
  const [category, setCategory] = useState('Generated Output');
  const [rating, setRating] = useState('ok');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    if (!description.trim()) {
      toast.error('Please enter a description');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post('feedback/', {
        category,
        rating,
        description: description.trim()
      });
      toast.success('Thank you for your feedback!');
      setDescription('');
      onClose();
    } catch (error: any) {
      console.error('Feedback submission error:', error);
      toast.error(error.response?.data?.error || 'Failed to send feedback');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
     <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0,0,0,0.85)", backdropFilter: "blur(4px)" }}
      onClick={onClose}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');
 
        .fm-root { font-family: 'DM Sans', sans-serif; }
 
        @keyframes wiggle {
          0%, 100% { transform: rotate(-3deg); }
          50%       { transform: rotate(3deg);  }
        }
        .animate-wiggle { animation: wiggle 0.5s ease-in-out infinite; }
      `}</style>
 
      {/* Modal box */}
      <div
        className="fm-root w-full max-w-[800px] max-h-[550px] rounded-2xl overflow-y-auto"
        style={{ background: "#171717", border: "1px solid #2a2a2a" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* ── Header ── */}
        <div
          className="relative px-7 pt-7 pb-6"
          style={{ borderBottom: "1px solid #222" }}
        >
          <p
            className="mb-1 text-[11px] font-medium uppercase tracking-widest"
            style={{ color: "#666" }}
          >
            Feedback
          </p>
          <h2 className="text-[22px] font-semibold" style={{ color: "#f5f5f5" }}>
            Help us improve
          </h2>
          <p className="mt-1 text-[13px] leading-relaxed" style={{ color: "#888" }}>
            Your feedback shapes what we build next.
          </p>
 
          <button
            onClick={onClose}
            className="absolute top-6 right-6 flex items-center justify-center w-8 h-8 rounded-lg transition-colors"
            style={{ background: "#252525", border: "1px solid #2e2e2e", color: "#999" }}
            onMouseEnter={(e) => { e.currentTarget.style.background = "#2e2e2e"; e.currentTarget.style.color = "#f5f5f5"; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = "#252525"; e.currentTarget.style.color = "#999"; }}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
 
        {/* ── Body ── */}
        <div className="px-7 pt-6 pb-7 flex flex-col gap-5">
 
          {/* Category chips */}
          <div>
            <label
              className="block mb-2.5 text-[11px] font-medium uppercase tracking-wider"
              style={{ color: "#666" }}
            >
              Category
            </label>
            <div className="flex flex-wrap gap-1">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategory(cat)}
                  className="px-3.5 py-1.5 cursor-pointer rounded-full text-[13px] font-medium transition-all"
                  style={
                    category === cat
                      ? { background: "#e8f0ff", border: "1px solid #e8f0ff", color: "#1a3080" }
                      : { background: "#1e1e1e", border: "1px solid #2a2a2a", color: "#999" }
                  }
                  onMouseEnter={(e) => {
                    if (category !== cat) {
                      e.currentTarget.style.borderColor = "#3a3a3a";
                      e.currentTarget.style.color = "#ccc";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (category !== cat) {
                      e.currentTarget.style.borderColor = "#2a2a2a";
                      e.currentTarget.style.color = "#999";
                    }
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
 
          <hr style={{ border: "none", borderTop: "1px solid #1f1f1f" }} />
 
          {/* Rating */}
          <div>
            <label
              className="block mb-2.5 text-[11px] font-medium uppercase tracking-wider"
              style={{ color: "#666" }}
            >
              Experience
            </label>
            <div className="flex gap-2">
              {RATINGS.map((r) => (
                <button
                  key={r.value}
                  onClick={() => setRating(r.value)}
                  className="flex-1 flex cursor-pointer flex-col items-center gap-1.5 py-3 rounded-xl transition-all"
                  style={
                    rating === r.value
                      ? { background: "#0d1a40", border: "1px solid #3a5cf5" }
                      : { background: "#1c1c1c", border: "1px solid #242424" }
                  }
                  onMouseEnter={(e) => {
                    if (rating !== r.value) {
                      e.currentTarget.style.borderColor = "#333";
                      e.currentTarget.style.background = "#222";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (rating !== r.value) {
                      e.currentTarget.style.borderColor = "#242424";
                      e.currentTarget.style.background = "#1c1c1c";
                    }
                  }}
                >
                  <span
                    className={`text-[26px] leading-none transition-transform duration-200 ${
                      rating === r.value ? `${r.animation} scale-110` : "grayscale-[40%]"
                    }`}
                  >
                    {r.emoji}
                  </span>
                  <span
                    className="text-[11px] font-medium"
                    style={{ color: rating === r.value ? "#7b9aff" : "#555" }}
                  >
                    {r.label}
                  </span>
                </button>
              ))}
            </div>
          </div>
 
          <hr style={{ border: "none", borderTop: "1px solid #1f1f1f" }} />
 
          {/* Textarea */}
          <div>
            <div className="flex justify-between items-end mb-2">
              <label
                className="text-[11px] font-medium uppercase tracking-wider"
                style={{ color: "#666" }}
              >
                Details
              </label>
              <span
                className="text-[10px]"
                style={{
                  fontFamily: "'DM Mono', monospace",
                  color: description.length > 450 ? "#e05454" : "#444",
                }}
              >
                {description.length}/500
              </span>
            </div>
            <textarea
              className="w-full h-28 rounded-xl text-[14px] resize-none outline-none transition-colors leading-relaxed"
              style={{
                background: "#1c1c1c",
                border: "1px solid #272727",
                padding: "14px 16px",
                color: "#e8e8e8",
                fontFamily: "'DM Sans', sans-serif",
              }}
              placeholder="Tell us what you liked or what we could do better..."
              value={description}
              onChange={(e) => setDescription(e.target.value.slice(0, 500))}
              onFocus={(e)  => { e.target.style.borderColor = "#3a5cf5"; }}
              onBlur={(e)   => { e.target.style.borderColor = "#272727"; }}
            />
          </div>
 
          {/* Actions */}
          <div className="flex gap-2.5 pt-1">
            <button
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 py-2.5 cursor-pointer rounded-xl text-[14px] font-medium transition-all"
              style={{ background: "transparent", border: "1px solid #2a2a2a", color: "#888" }}
              onMouseEnter={(e) => { e.currentTarget.style.background = "#1e1e1e"; e.currentTarget.style.color = "#ccc"; e.currentTarget.style.borderColor = "#333"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#888"; e.currentTarget.style.borderColor = "#2a2a2a"; }}
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !description.trim()}
              className="flex-[2] cursor-pointer py-2.5 rounded-xl text-[14px] font-semibold transition-all flex items-center justify-center gap-2"
              style={{ background: "#3a5cf5", color: "#fff", border: "none" }}
              onMouseEnter={(e) => { if (!e.currentTarget.disabled) e.currentTarget.style.background = "#4f6ef7"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = "#3a5cf5"; }}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Sending...
                </>
              ) : (
                "Submit feedback"
              )}
            </button>
          </div>
 
        </div>
      </div>
    </div>
  );
};

export default FeedbackModal;