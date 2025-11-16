export default function Contact() {
    return (
        <div className="container mx-auto px-4">
            <h1 className="text-3xl font-bold mb-4">Contact Us</h1>
            <p className="mb-4">
                If you have any questions, feel free to reach out to us!
            </p>
            <form className="space-y-4 max-w-lg">
                <div>
                    <label className="block text-sm font-medium mb-1" htmlFor="name">
                        Name
                    </label>
                    <input
                        type="text"
                        id="name"
                        className="w-full border border-gray-300 rounded-md p-2"
                        placeholder="Your Name"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium mb-1" htmlFor="email">
                        Email
                    </label>
                    <input
                        type="email"
                        id="email"
                        className="w-full border border-gray-300 rounded-md peer-invalid:p-2"
                        placeholder="Your Email"
                        required
                    />
                    <p className="mt-1 text-sm text-red-600 invisible peer-invalid:visible">
                        Please enter a valid email address.
                    </p>
                </div>
                <div>
                    <label className="block text-sm font-medium mb-1" htmlFor="message">
                        Message
                    </label>
                    <textarea
                        id="message"
                        className="w-full border border-gray-300 rounded-md p-2"
                        rows={5}
                        placeholder="Your Message"
                    ></textarea>
                </div>
                <button
                    type="submit"
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
                >
                    Send Message
                </button>
            </form>
        </div>
    );
}   