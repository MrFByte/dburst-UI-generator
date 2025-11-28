import { User } from 'lucide-react'


const UserProfile = ({ userName, onUserClick }) => (
  <div
    className="flex items-center space-x-2 p-2 cursor-pointer transition duration-150 ease-in-out rounded-lg border border-gray-800 hover:bg-gray-800 hover:border-gray-500"
    onClick={onUserClick}
  >
    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold text-sm shadow-md">
      {userName.charAt(0)}
    </div>
    <span className="hidden md:inline text-sm font-medium text-gray-200">{userName}</span>
    <User className="w-4 h-4 text-gray-500 hidden md:block" />
  </div>
);

export default UserProfile;
