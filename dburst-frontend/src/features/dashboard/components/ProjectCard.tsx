import { ChevronRight, FileText } from 'lucide-react'

const formatDate = (isoString: string): string => {
  const date = new Date(isoString);

  const day = date.toLocaleString("en-US", { day: "2-digit" });
  const month = date.toLocaleString("en-US", { month: "short" });
  const year = date.getFullYear();

  return `${day} ${month} ${year}`;
};

const ProjectCard = ({ project }: { project: any }) =>{ 
    return (
      <div className="bg-gray-800/50 p-4 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-800 hover:border-gray-600 cursor-pointer flex flex-col justify-between h-full">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-gray-800 rounded-full"><FileText /></div>
          <h3 className="text-lg font-semibold text-gray-100 truncate">{project?.title}</h3>
        </div>
        <div className="flex justify-between items-end">
          <p className="text-xs text-gray-400">Last accessed: {formatDate(project?.updated_at)}</p>
          <ChevronRight className="w-4 h-4 text-gray-500 transition group-hover:text-white" />
        </div>
      </div>
  );
}

export default ProjectCard;