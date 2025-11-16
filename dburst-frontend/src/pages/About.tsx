import Header from "@/components/common/Header";
import Footer from "@/components/common/Footer";


export default function About() {
    return (
        <div className="relative min-h-screen overflow-hidden">
            <Header />
            <main className="px-6 pt-12 pb-20 md:px-20 md:pt-20 md:pb-32">
                <h1 className="text-4xl font-bold mb-6">About DBurst</h1>
                <p className="text-lg mb-4">
                    DBurst is a cutting-edge data visualization platform designed to help users make sense of complex datasets through intuitive and interactive visual representations.
                </p>
                <p className="text-lg mb-4">
                    Our mission is to empower individuals and organizations to unlock the full potential of their data by providing powerful tools that facilitate analysis, exploration, and storytelling.
                </p>
                <p className="text-lg">
                    Whether you're a data scientist, business analyst, or just someone passionate about data, DBurst offers the features and flexibility you need to turn raw data into actionable insights.
                </p>
            </main>
            <Footer />
        </div>
    );
}