import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from './ui/chart';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Legend } from 'recharts';

const DataVisualizationSection = () => {
  // Growth over time data
  const growthData = [
    { year: '2019', peopleAffected: 3.2, moneyLost: 8.5 },
    { year: '2020', peopleAffected: 4.1, moneyLost: 12.3 },
    { year: '2021', peopleAffected: 5.8, moneyLost: 18.7 },
    { year: '2022', peopleAffected: 7.9, moneyLost: 24.1 },
    { year: '2023', peopleAffected: 11.2, moneyLost: 32.8 },
    { year: '2024', peopleAffected: 15.6, moneyLost: 45.2 }
  ];

  const chartConfig = {
    peopleAffected: {
      label: "People Affected",
      color: "#3b82f6",
    },
    moneyLost: {
      label: "Money Lost (Billions)",
      color: "#ef4444",
    },
  };

  return (
    <section id="data" className="py-20 bg-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Growth Over <span className="text-red-500">Time</span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Showing people affected and money lost to scam calls for the last 6 years
          </p>
        </div>

        {/* Key Statistics */}
        <div className="flex justify-center gap-16 mb-8">
          <div className="text-center">
            <div className="text-3xl font-bold text-white">15.6M</div>
            <div className="text-gray-400 text-sm">People Affected</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-white">$45.2B</div>
            <div className="text-gray-400 text-sm">Money Lost</div>
          </div>
        </div>

        {/* Chart and Insights Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-12">
          {/* Chart - Left Side */}
          <div className="lg:col-span-3">
            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="p-6">
                <ChartContainer config={chartConfig}>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={growthData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis 
                        dataKey="year" 
                        stroke="#9ca3af"
                        fontSize={12}
                      />
                      <YAxis 
                        stroke="#9ca3af"
                        fontSize={12}
                      />
                      <ChartTooltip 
                        content={<ChartTooltipContent />}
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                          color: '#ffffff'
                        }}
                      />
                      <Legend />
                      <Bar dataKey="peopleAffected" fill="#3b82f6" name="People Affected (Millions)" />
                      <Bar dataKey="moneyLost" fill="#ef4444" name="Money Lost (Billions)" />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>
          </div>

          {/* Insights Card - Right Side */}
          <div className="lg:col-span-2">
            <Card className="bg-gradient-to-br from-gray-900/80 to-black/80 backdrop-blur-xl border border-gray-700/30 shadow-2xl">
              <CardHeader>
                <CardTitle className="text-xl font-bold text-white">
                  Concerning Trends
                </CardTitle>
                <CardDescription className="text-gray-300">
                  Key insights from the data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                  <div>
                    <p className="text-white font-medium">Exponential Growth</p>
                    <p className="text-gray-400 text-sm">387% increase in people affected since 2019</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                  <div>
                    <p className="text-white font-medium">Financial Impact</p>
                    <p className="text-gray-400 text-sm">$45.2B lost in 2024 alone - equivalent to GDP of small countries</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 flex-shrink-0"></div>
                  <div>
                    <p className="text-white font-medium">Accelerating Rate</p>
                    <p className="text-gray-400 text-sm">Growth rate increasing by 25% year-over-year</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                  <div>
                    <p className="text-white font-medium">Underreported Crisis</p>
                    <p className="text-gray-400 text-sm">Only 15% of scam calls are actually reported to authorities</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                  <div>
                    <p className="text-white font-medium">Global Reach</p>
                    <p className="text-gray-400 text-sm">Affecting 1 in 3 people worldwide by 2025</p>
                  </div>
                </div>
                
                <div className="pt-4 border-t border-gray-700/50">
                  <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-3">
                    <p className="text-red-400 font-medium text-sm">
                      ⚠️ Without intervention, losses could reach $100B+ by 2026
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};

export default DataVisualizationSection;
