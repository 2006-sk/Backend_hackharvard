import LandingNavbar from './components/LandingNavbar'
import HeroSection from './components/HeroSection'
import DataVisualizationSection from './components/DataVisualizationSection'
import FeaturesSection from './components/FeaturesSection'
import AboutSection from './components/AboutSection'
import Footer from './components/Footer'
import LiveMonitoringPage from './components/LiveMonitoringPage'
import LenisProvider from './components/LenisProvider'
import { useState } from 'react'

function App() {
  const [showLiveMonitoring, setShowLiveMonitoring] = useState(false)

  if (showLiveMonitoring) {
    return (
      <LenisProvider>
        <LiveMonitoringPage onClose={() => setShowLiveMonitoring(false)} />
      </LenisProvider>
    )
  }

  const handleStartLiveCall = () => {
    console.log('🚀 Starting Live Call Monitoring...');
    setShowLiveMonitoring(true);
  };

  return (
    <LenisProvider>
      <LandingNavbar onStartLiveCall={handleStartLiveCall} />
      <HeroSection />
      <DataVisualizationSection />
      <FeaturesSection />
      <AboutSection />
      <Footer />
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={handleStartLiveCall}
          className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg shadow-lg transition-colors flex items-center space-x-2"
        >
          <span>📞</span>
          <span>Start Live Call</span>
        </button>
      </div>
    </LenisProvider>
  )
}

export default App
