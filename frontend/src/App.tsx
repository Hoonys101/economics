import './App.css';
import { useCockpit } from './hooks/useCockpit';
import HUD from './components/HUD';
import GodBar from './components/GodBar';

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
    <div className="min-h-screen bg-background text-foreground flex flex-col p-4 md:p-6 gap-4 md:gap-6 relative pb-24">

      {/* HUD (Heads-Up Display) */}
      <HUD data={snapshot} />

      {/* Main Content Placeholder */}
      <main className="flex-1 glass-card rounded-2xl p-6 md:p-8 relative overflow-hidden flex flex-col items-center justify-center text-center">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />
        <h1 className="text-3xl font-bold mb-4">Cockpit 2.0 Under Construction</h1>
        <p className="text-muted-foreground max-w-md">
            The foundation has been laid. Detailed views for Population, Politics, Finance, and Macroeconomics will be implemented in subsequent updates.
        </p>
        <div className="mt-8 grid grid-cols-2 gap-4 text-left">
            <div className="p-4 bg-white/5 rounded border border-white/10">
                <div className="text-xs text-muted-foreground">Ruling Party</div>
                <div className="font-bold">{snapshot.politics.status.ruling_party}</div>
            </div>
            <div className="p-4 bg-white/5 rounded border border-white/10">
                <div className="text-xs text-muted-foreground">M2 Supply</div>
                <div className="font-bold">{snapshot.finance.supply.m2.toLocaleString()}</div>
            </div>
        </div>
      </main>

      {/* God Bar (Command Center) */}
      <GodBar sendCommand={sendCommand} status={snapshot.status} />

    </div>
  )
}

export default App
