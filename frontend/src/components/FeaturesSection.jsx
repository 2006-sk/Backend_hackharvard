import React, { useEffect, useRef } from 'react';
import { Timeline } from './ui/timeline';
import WaveSurfer from 'wavesurfer.js';
import SpectrogramPlugin from 'wavesurfer.js/dist/plugins/spectrogram.esm.js';
import colormap from 'colormap';
import { Card, CardContent } from './ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from './ui/chart';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

const FeaturesSection = () => {
  const waveformRef = useRef(null);
  const spectrogramRef = useRef(null);

  useEffect(() => {
    // Generate a viridis colormap
    const viridisColormap = colormap({
      colormap: 'viridis',
      nshades: 256,
      format: 'float'
    });

    // Create a mock audio URL for demonstration
    const createMockAudioUrl = () => {
      // Use a simple data URL with a short audio tone
      // This creates a 2-second 440Hz sine wave
      const sampleRate = 44100;
      const duration = 2;
      const length = sampleRate * duration;
      const buffer = new ArrayBuffer(44 + length * 2);
      const view = new DataView(buffer);
      
      // WAV header
      const writeString = (offset, string) => {
        for (let i = 0; i < string.length; i++) {
          view.setUint8(offset + i, string.charCodeAt(i));
        }
      };
      
      writeString(0, 'RIFF');
      view.setUint32(4, 36 + length * 2, true);
      writeString(8, 'WAVE');
      writeString(12, 'fmt ');
      view.setUint32(16, 16, true);
      view.setUint16(20, 1, true);
      view.setUint16(22, 1, true);
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * 2, true);
      view.setUint16(32, 2, true);
      view.setUint16(34, 16, true);
      writeString(36, 'data');
      view.setUint32(40, length * 2, true);
      
      // Generate more complex audio data with multiple frequencies
      for (let i = 0; i < length; i++) {
        const t = i / sampleRate;
        const sample = 
          Math.sin(2 * Math.PI * 440 * t) * 0.3 + // A4 note
          Math.sin(2 * Math.PI * 880 * t) * 0.2 + // A5 note
          Math.sin(2 * Math.PI * 1320 * t) * 0.15 + // E6 note
          Math.sin(2 * Math.PI * 220 * t) * 0.1 + // A3 note
          (Math.random() - 0.5) * 0.05; // Some noise
        view.setInt16(44 + i * 2, sample * 32767, true);
      }
      
      const blob = new Blob([buffer], { type: 'audio/wav' });
      return URL.createObjectURL(blob);
    };

    if (waveformRef.current && spectrogramRef.current) {
      // Initialize WaveSurfer with spectrogram
      const wavesurfer = WaveSurfer.create({
        container: waveformRef.current,
        waveColor: '#3b82f6',
        progressColor: '#1d4ed8',
        height: 80,
        normalize: true,
        backend: 'WebAudio',
        mediaControls: false,
        backgroundColor: '#000000'
      });

      // Add spectrogram plugin with generated colormap
      wavesurfer.registerPlugin(
        SpectrogramPlugin.create({
          container: spectrogramRef.current,
          labels: true,
          height: 120,
          colorMap: viridisColormap,
          backgroundColor: '#000000'
        })
      );

      // Load mock audio
      const audioUrl = createMockAudioUrl();
      wavesurfer.load(audioUrl);

      return () => {
        wavesurfer.destroy();
      };
    }
  }, []);

  const timelineData = [
    {
      title: "Voice Analysis",
      content: (
        <div className="bg-black rounded-2xl p-6 border border-gray-700">
          <div className="flex items-center space-x-4 mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xl">🎤</span>
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Live Voice Analysis</h3>
              <p className="text-gray-400">Real-time waveform processing</p>
            </div>
          </div>
          
          {/* Real WaveSurfer Waveform */}
          <div className="mb-4">
            <div className="bg-black rounded-lg p-4 border border-gray-600">
              <div ref={waveformRef} className="w-full"></div>
            </div>
          </div>

          {/* Real Spectrogram */}
          <div className="mb-4">
            <div className="bg-black rounded-lg p-4 border border-gray-600">
              <div ref={spectrogramRef} className="w-full"></div>
            </div>
          </div>

          <p className="text-gray-300 text-sm">
            Advanced audio processing with real-time frequency analysis
          </p>
        </div>
      ),
    },
    {
      title: "Risk Assessment",
      content: (
        <div className="bg-black rounded-2xl p-6 border border-gray-700">
          <div className="flex items-center space-x-4 mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-pink-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xl">⚠️</span>
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Dynamic Risk Scoring</h3>
              <p className="text-gray-400">Instant threat level assessment</p>
            </div>
          </div>
          {/* Risk Score Chart */}
          <div className="mb-4">
            <Card className="bg-black border-gray-600">
              <CardContent className="p-4">
                <div className="text-center mb-3">
                  <h4 className="text-sm font-medium text-gray-400">Current Risk Distribution</h4>
                </div>
                <ChartContainer config={{}}>
                  <ResponsiveContainer width="100%" height={120}>
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Safe', value: 65, color: '#10b981' },
                          { name: 'Medium', value: 25, color: '#f59e0b' },
                          { name: 'High', value: 10, color: '#ef4444' }
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={25}
                        outerRadius={45}
                        dataKey="value"
                      >
                        {[
                          { name: 'Safe', value: 65, color: '#10b981' },
                          { name: 'Medium', value: 25, color: '#f59e0b' },
                          { name: 'High', value: 10, color: '#ef4444' }
                        ].map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <ChartTooltip content={<ChartTooltipContent />} />
                    </PieChart>
                  </ResponsiveContainer>
                </ChartContainer>
                <div className="flex justify-center space-x-4 mt-2 text-xs">
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-400">Safe: 65%</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <span className="text-gray-400">Medium: 25%</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span className="text-gray-400">High: 10%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Risk Factors Bar Chart */}
          <div className="mb-4">
            <Card className="bg-black border-gray-600">
              <CardContent className="p-4">
                <div className="text-center mb-3">
                  <h4 className="text-sm font-medium text-gray-400">Risk Factor Analysis</h4>
                </div>
                <ChartContainer config={{}}>
                  <ResponsiveContainer width="100%" height={100}>
                    <BarChart data={[
                      { factor: 'Voice Pattern', risk: 85 },
                      { factor: 'Language', risk: 70 },
                      { factor: 'Caller ID', risk: 45 },
                      { factor: 'Duration', risk: 30 }
                    ]}>
                      <XAxis dataKey="factor" stroke="#9ca3af" fontSize={10} />
                      <YAxis stroke="#9ca3af" fontSize={10} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Bar dataKey="risk" fill="#ef4444" radius={[2, 2, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>
          </div>

          <p className="text-gray-300 text-sm">
            Multi-factor risk analysis with real-time scoring and pattern recognition
          </p>
        </div>
      ),
    },
    {
      title: "Live Protection",
      content: (
        <div className="bg-black rounded-2xl p-6 border border-gray-700">
          <div className="flex items-center space-x-4 mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xl">🛡️</span>
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Real-time Protection</h3>
              <p className="text-gray-400">24/7 scam call monitoring</p>
            </div>
          </div>
          {/* Protection Stats */}
          <div className="mb-4">
            <Card className="bg-black border-gray-600">
              <CardContent className="p-4">
                <div className="text-center mb-3">
                  <h4 className="text-sm font-medium text-gray-400">24/7 Protection Metrics</h4>
                </div>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-400">99.7%</div>
                    <div className="text-xs text-gray-400">Block Rate</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-400">2.3ms</div>
                    <div className="text-xs text-gray-400">Response Time</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-400">1.2M</div>
                    <div className="text-xs text-gray-400">Calls Monitored</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-orange-400">847</div>
                    <div className="text-xs text-gray-400">Threats Blocked</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Real-time Monitoring Chart */}
          <div className="mb-4">
            <Card className="bg-black border-gray-600">
              <CardContent className="p-4">
                <div className="text-center mb-3">
                  <h4 className="text-sm font-medium text-gray-400">Live Threat Detection</h4>
                </div>
                <ChartContainer config={{}}>
                  <ResponsiveContainer width="100%" height={100}>
                    <LineChart data={[
                      { time: '00:00', threats: 2 },
                      { time: '04:00', threats: 1 },
                      { time: '08:00', threats: 8 },
                      { time: '12:00', threats: 15 },
                      { time: '16:00', threats: 12 },
                      { time: '20:00', threats: 6 },
                      { time: '24:00', threats: 3 }
                    ]}>
                      <XAxis dataKey="time" stroke="#9ca3af" fontSize={10} />
                      <YAxis stroke="#9ca3af" fontSize={10} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Line 
                        type="monotone" 
                        dataKey="threats" 
                        stroke="#ef4444" 
                        strokeWidth={2}
                        dot={{ fill: '#ef4444', strokeWidth: 2, r: 3 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>
          </div>

          {/* Protection Status Indicators */}
          <div className="mb-4">
            <Card className="bg-black border-gray-600">
              <CardContent className="p-4">
                <div className="text-center mb-3">
                  <h4 className="text-sm font-medium text-gray-400">System Status</h4>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">AI Engine</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-green-400">Active</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Database</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-green-400">Synced</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Network</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-green-400">Connected</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <p className="text-gray-300 text-sm">
            Advanced threat detection with real-time monitoring and instant response capabilities
          </p>
        </div>
      ),
    },
  ];

  return (
    <section id="features" className="py-20 bg-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            AI Voice Analysis <span className="text-blue-500">Technology</span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Experience the future of call protection with our advanced AI-powered voice analysis system
          </p>
        </div>

        {/* Timeline */}
        <Timeline data={timelineData} />
      </div>
    </section>
  );
};

export default FeaturesSection;