import './App.css';
import { useCockpit } from './hooks/useCockpit';
import HUD from './components/HUD';
import GodBar from './components/GodBar';
import MacroCanvas from './components/macro/MacroCanvas';

function App() {
  const { snapshot, connected, sendCommand } = useCockpit();

  if (!connected || !snapshot) {
      return (
        <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
            <div className="animate-pulse flex flex-col items-center gap-4">
                <div className="w-12 h-12 rounded-full border-4 border-primary border-t-transparent animate-spin"/>
                <div className="text-primary font-mono">
                    {!connected ? "Connecting to Watchtower..." : "Awaiting Snapshot..."}
                </div>
            </div>
        </div>
      )
  }

  return (
    <div className="h-screen bg-background text-foreground flex flex-col relative overflow-hidden">

      {/* HUD (Heads-Up Display) - Sticky Top */}
      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur border-b border-border/50 px-4 py-2">
         <HUD data={snapshot} />
      </header>

      {/* Main Content: Macro Canvas - Scrollable Area */}
      <main className="flex-1 overflow-y-auto p-4 md:p-6">
        <MacroCanvas />
      </main>

      {/* God Bar (Command Center) - Sticky Bottom */}
      <footer className="sticky bottom-0 z-50 bg-background/95 backdrop-blur border-t border-border/50 px-4 py-2">
         <GodBar sendCommand={sendCommand} status={snapshot.status} />
      </footer>

    </div>
  )
}

export default App
