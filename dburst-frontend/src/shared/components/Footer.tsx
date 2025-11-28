const todayYear = new Date().getFullYear()

export function Footer() {
  return (
    <footer className="bg-zinc-900 border-t border-zinc-800 py-8 mt-auto">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-zinc-400 text-sm">
            © DBurst. All rights reserved {todayYear}.
          </div>

          <div className="flex items-center gap-6">
            
          </div>

          <div className="text-zinc-500 text-sm">
            A product of <span className="text-zinc-300 font-medium">MindBurst</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
