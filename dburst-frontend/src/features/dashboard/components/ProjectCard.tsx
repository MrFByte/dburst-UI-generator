import { ChevronRight } from 'lucide-react'


const ProjectCard = ({ project }) =>{ 
    
    return (
    <div className="bg-white p-4 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-100 cursor-pointer flex flex-col justify-between h-full">
      <div className="flex items-center space-x-3 mb-4">
        <div className="p-2 bg-gray-50 rounded-full">{project.icon}</div>
        <h3 className="text-lg font-semibold text-gray-800 truncate">{project.name}</h3>
      </div>
      <div className="flex justify-between items-end">
        <p className="text-xs text-gray-500">Last accessed: {project.date}</p>
        <ChevronRight className="w-4 h-4 text-indigo-500" />
      </div>
    </div>
  );
}

export default ProjectCard;