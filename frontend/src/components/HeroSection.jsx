import Spline from '@splinetool/react-spline';
import { useState } from 'react';

const HeroSection = () => {
  const [splineKey, setSplineKey] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const handleRefresh = () => {
    setSplineKey(prev => prev + 1);
    setIsLoading(true);
    setHasError(false);
  };

  return (
    <div className="h-screen w-full overflow-hidden relative">
      {isLoading && (
        <div className="absolute inset-0 bg-black flex items-center justify-center z-10">
          <div className="text-white text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p>Loading 3D Scene...</p>
          </div>
        </div>
      )}
      
      {hasError && (
        <div className="absolute inset-0 bg-black flex items-center justify-center z-10">
          <div className="text-white text-center">
            <p className="mb-4">Failed to load 3D scene</p>
            <button 
              onClick={handleRefresh}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      <Spline 
        key={splineKey}
        scene="https://prod.spline.design/cGkRsbV7cqwAK7Zd/scene.splinecode" 
        style={{ width: '100%', height: '100%' }}
        onLoad={() => {
          console.log('✅ Spline scene loaded successfully');
          setIsLoading(false);
          setHasError(false);
        }}
        onError={(error) => {
          console.error('❌ Spline scene error:', error);
          setIsLoading(false);
          setHasError(true);
        }}
      />
    </div>
  );
};

export default HeroSection;
