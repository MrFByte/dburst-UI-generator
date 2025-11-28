import {X} from 'lucide-react';


const FeedbackModal = ({ isOpen, onClose }) => {
    if (!isOpen) return null;
  
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 p-4" onClick={onClose}>
        <div
          className="bg-white rounded-xl shadow-2xl w-full max-w-lg transform transition-all duration-300 scale-100"
          onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside
        >
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center justify-between">
              Send Feedback
              <X className="w-6 h-6 text-gray-400 cursor-pointer hover:text-gray-600" onClick={onClose} />
            </h2>
            <p className="text-gray-600 mb-4">Help us improve D-burst! What are your thoughts?</p>
            <textarea
              className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 resize-none text-gray-700"
              placeholder="I love the new Code Writer feature, but..."
            ></textarea>
            <div className="mt-4 flex justify-end">
              <button
                className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg shadow-md hover:bg-indigo-700 transition duration-150"
                onClick={() => {
                  // Placeholder for submission logic
                  console.log('Feedback submitted');
                  onClose();
                }}
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

export default FeedbackModal;