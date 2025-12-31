import { useState, ReactNode } from 'react'
import { Users, Landmark, ShoppingCart, TrendingUp } from 'lucide-react'
import './App.css'
import { useSimulation } from './hooks/useSimulation'
import SocietyTab from './components/dashboard/SocietyTab'
import GovernmentTab from './components/dashboard/GovernmentTab'
import MarketTab from './components/dashboard/MarketTab'
import FinanceTab from './components/dashboard/FinanceTab'

interface TabButtonProps {
  id: string;
  label: string;
  icon: ReactNode;
  active: boolean;
  onClick: () => void;
}

// i18n dictionary (can be moved to a separate file later)
const i18n = {
  ko: {
    dashboard_title: "W-2 시뮬레이션 경제 관제탑",
    system_awaiting: "데이터 로딩 중...",
    society: "사회",
    government: "정부",
    market: "시장",
    finance: "금융",
    tick: "틱",
    survival_rate: "생존율",
    employment: "고용률",
    gdp: "GDP",
    avg_wage: "평균 임금",
    gini: "지니계수"
  },
  en: {
    dashboard_title: "W-2 Simulation Economic HUD",
    system_awaiting: "Loading Data...",
    society: "Society",
    government: "Government",
    market: "Market",
    finance: "Finance",
    tick: "Tick",
    survival_rate: "Survival Rate",
    employment: "Employment",
    gdp: "GDP",
    avg_wage: "Avg Wage",
    gini: "Gini Index"
  }
}

const TabButton = ({ label, icon, active, onClick }: TabButtonProps) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-3 py-2 md:px-4 md:py-2 rounded-lg transition-all ${
      active 
        ? 'bg-primary text-white shadow-lg shadow-primary/20' 
        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
    }`}
  >
    {icon}
    <span className="font-medium text-sm md:text-base">{label}</span>
  </button>
)

const Indicator = ({ label, value, unit, color }: { label: string, value: string | number, unit?: string, color: string }) => (
  <div className="glass-card rounded-xl p-3 md:p-4 flex-1 min-w-[120px] md:min-w-[150px]">
    <div className="text-muted-foreground text-[10px] md:text-xs font-semibold uppercase tracking-wider mb-1">{label}</div>
    <div className="flex items-baseline gap-1">
      <span className={`text-xl md:text-2xl font-bold ${color}`}>{value}</span>
      {unit && <span className="text-muted-foreground text-xs md:text-sm">{unit}</span>}
    </div>
  </div>
)

function App() {
  const [activeTab, setActiveTab] = useState('society')
  const [lang, setLang] = useState<'ko' | 'en'>('ko')
  const { data, loading } = useSimulation()
  const t = i18n[lang]

  if (loading || !data) {
      return (
        <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
            <div className="animate-pulse flex flex-col items-center gap-4">
                <div className="w-12 h-12 rounded-full border-4 border-primary border-t-transparent animate-spin"/>
                <div className="text-primary font-mono">{t.system_awaiting}</div>
            </div>
        </div>
      )
  }

  const { global_indicators: hud, tabs } = data

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col p-4 md:p-6 gap-4 md:gap-6">
      {/* Header HUD */}
      <header className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 md:gap-4">
        <Indicator label={t.tick} value={data.tick} color="text-white" />
        <Indicator label={t.survival_rate} value={(100 - hud.death_rate).toFixed(1)} unit="%" color="text-green-400" />
        <Indicator label={t.employment} value={hud.employment_rate.toFixed(1)} unit="%" color="text-blue-400" />
        <Indicator label={t.gdp} value={hud.gdp.toLocaleString()} color="text-yellow-400" />
        <Indicator label={t.avg_wage} value={hud.avg_wage.toFixed(0)} color="text-emerald-400" />
        <Indicator label={t.gini} value={hud.gini.toFixed(3)} color="text-purple-400" />
      </header>

      {/* Navigation & Lang Switcher */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <nav className="flex flex-wrap gap-1 bg-muted/30 p-1 rounded-xl">
          <TabButton 
            id="society" label={t.society} icon={<Users size={18} />} 
            active={activeTab === 'society'} onClick={() => setActiveTab('society')} 
          />
          <TabButton 
            id="government" label={t.government} icon={<Landmark size={18} />} 
            active={activeTab === 'government'} onClick={() => setActiveTab('government')} 
          />
          <TabButton 
            id="market" label={t.market} icon={<ShoppingCart size={18} />} 
            active={activeTab === 'market'} onClick={() => setActiveTab('market')} 
          />
          <TabButton 
            id="finance" label={t.finance} icon={<TrendingUp size={18} />} 
            active={activeTab === 'finance'} onClick={() => setActiveTab('finance')} 
          />
        </nav>
        
        <div className="flex bg-muted/30 p-1 rounded-lg">
          <button 
            onClick={() => setLang('ko')}
            className={`px-2 py-1 text-xs rounded transition-all ${lang === 'ko' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'}`}
          >KO</button>
          <button 
            onClick={() => setLang('en')}
            className={`px-2 py-1 text-xs rounded transition-all ${lang === 'en' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'}`}
          >EN</button>
        </div>
      </div>

      {/* Content Area */}
      <main className="flex-1 glass-card rounded-2xl p-6 md:p-8 relative overflow-hidden flex flex-col">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none" />
        <div className="relative z-10 w-full h-full">
            {activeTab === 'society' && <SocietyTab data={tabs.society} />}
            {activeTab === 'government' && <GovernmentTab data={tabs.government} />}
            {activeTab === 'market' && <MarketTab data={tabs.market} />}
            {activeTab === 'finance' && <FinanceTab data={tabs.finance} />}
        </div>
      </main>
    </div>
  )
}

export default App
