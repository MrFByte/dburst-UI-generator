import DBurstLoaderSVG from '@/assets/dburst-loader.svg';

interface LoaderProps {
    size?: 'sm' | 'md' | 'lg' | 'xl';
    text?: string;
    className?: string;
}

const sizeMap = {
    sm: 'w-16 h-16',
    md: 'w-24 h-24',
    lg: 'w-32 h-32',
    xl: 'w-40 h-40',
};

export default function Loader({ size = 'md', text, className = '' }: LoaderProps) {
    return (
        <div className={`flex flex-col items-center justify-center gap-4 ${className}`}>
            <img
                src={DBurstLoaderSVG}
                alt="Loading..."
                className={`${sizeMap[size]} animate-pulse`}
            />
            {text && (
                <p className="text-gray-400 text-sm animate-pulse">{text}</p>
            )}
        </div>
    );
}
