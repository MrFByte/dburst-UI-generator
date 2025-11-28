export default function FormField({ label, id, value, onChange, placeholder, type = 'text', rows = 1 }) {
    return (
        <div className="mb-4">
            <label htmlFor={id} className="block text-sm font-medium text-gray-300 mb-1">
            {label}
            </label>
            {type === 'textarea' ? (
            <textarea
                id={id}
                rows={rows}
                className="w-full p-3 border border-gray-700 rounded-lg focus:ring-blue-600 focus:border-blue-600 bg-gray-800 text-white placeholder-gray-500 resize-none transition duration-200"
                placeholder={placeholder}
                value={value}
                onChange={onChange}
            />
            ) : (
            <input
                type={type}
                id={id}
                className="w-full p-3 border border-gray-700 rounded-lg focus:ring-blue-600 focus:border-blue-600 bg-gray-800 text-white placeholder-gray-500 transition duration-200"
                placeholder={placeholder}
                value={value}
                onChange={onChange}
            />
            )}
        </div>
    );
}