import { X } from 'lucide-react';

export default function PanelPlaceholder({ title, side, isOpen, onClose }) {
  if (!isOpen) return null;

  // Header height is h-16 (4rem or 64px)
  const HEADER_HEIGHT_CLASS = 'top-[4rem]';
  const PANEL_HEIGHT_CLASS = 'h-[calc(100vh-4rem)]';

  const transformClass = side === 'left' ?
    (isOpen ? 'translate-x-0' : '-translate-x-full') :
    (isOpen ? 'translate-x-0' : 'translate-x-full');

  return (
    <div
      // Adjusted top position and height to sit below the h-16 header
      className={`fixed ${HEADER_HEIGHT_CLASS} ${side === 'left' ? 'left-0' : 'right-0'} ${PANEL_HEIGHT_CLASS} w-80 bg-gray-900 border-${side === 'left' ? 'r' : 'l'} border-gray-800 shadow-2xl z-40 transform transition-transform duration-300 ${transformClass}`}
    >
      <div className="p-4 flex flex-col h-full">
        <div className="flex justify-between items-center pb-4 border-b border-gray-800">
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <X className="w-6 h-6 text-gray-400 cursor-pointer hover:text-white" onClick={onClose} />
        </div>
        <div className="pt-4 text-gray-400">
          Content for the {title} panel goes here (e.g., Code Structure / Chat History).
        </div>
      </div>
    </div>
  );
};