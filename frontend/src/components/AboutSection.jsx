import React from 'react';
import { motion } from 'framer-motion';

const AboutSection = () => {
  const stats = [
    { number: '1M+', label: 'Calls Analyzed' },
    { number: '99.7%', label: 'Accuracy Rate' },
    { number: '50K+', label: 'Scams Prevented' },
    { number: '24/7', label: 'AI Monitoring' }
  ];

  return (
    <section id="about" className="py-20 bg-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left side - Content */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="space-y-8"
          >
            <h2 className="text-4xl lg:text-5xl font-bold text-white">
              About Our AI Platform
            </h2>
            <p className="text-xl text-gray-300 leading-relaxed">
              We're revolutionizing call security with cutting-edge AI technology that 
              protects users from fraudulent calls in real-time. Our advanced voice 
              analysis system combines machine learning with behavioral pattern recognition.
            </p>
            <p className="text-lg text-gray-400 leading-relaxed">
              From individual users to enterprise organizations, we've prevented thousands 
              of scam attempts and saved millions in potential losses with our comprehensive 
              fraud detection platform.
            </p>
            
            {/* Stats */}
            <div className="grid grid-cols-2 gap-8 pt-8">
              {stats.map((stat, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="text-center"
                >
                  <div className="text-3xl lg:text-4xl font-bold text-blue-400 mb-2">
                    {stat.number}
                  </div>
                  <div className="text-gray-300 font-medium">
                    {stat.label}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Right side - Visual */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            viewport={{ once: true }}
            className="relative"
          >
            <div className="relative">
              {/* Background elements */}
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="absolute -top-10 -right-10 w-32 h-32 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full opacity-20 blur-xl"
              />
              <motion.div
                animate={{ rotate: -360 }}
                transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                className="absolute -bottom-10 -left-10 w-24 h-24 bg-gradient-to-r from-pink-400 to-rose-400 rounded-full opacity-20 blur-xl"
              />
              
              {/* Main content card */}
              <div className="relative bg-gray-800 rounded-3xl p-8 shadow-2xl border border-gray-700">
                <div className="space-y-6">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-xl">🤖</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-white">AI-Powered Analysis</h3>
                      <p className="text-gray-300">Advanced machine learning algorithms</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-xl">🛡️</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-white">Real-time Protection</h3>
                      <p className="text-gray-300">Instant scam detection and blocking</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-xl">📊</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-white">Advanced Analytics</h3>
                      <p className="text-gray-300">Comprehensive risk assessment and reporting</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
