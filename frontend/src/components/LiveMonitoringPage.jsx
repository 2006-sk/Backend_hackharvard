import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { 
  Phone, 
  PhoneOff, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  X,
  Activity,
  Shield,
  MessageSquare,
  TrendingUp,
  Timer
} from 'lucide-react';
import useWebSocket from '../hooks/useWebSocket';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';

const LiveMonitoringPage = ({ onClose }) => {
  const [callData, setCallData] = useState(null);
  const [callHistory, setCallHistory] = useState([]);
  const [updates, setUpdates] = useState([]);
  const [isEndingCall, setIsEndingCall] = useState(false);
  const [showIPhone, setShowIPhone] = useState(true);
  const [showScamAlert, setShowScamAlert] = useState(false);
  const [alertShown, setAlertShown] = useState(false);

  // Handle WebSocket messages
  const handleMessage = useCallback((data) => {
    console.log('📨 Processing WebSocket message:', data);
    
    // Handle connection established message
    if (data.type === 'connection_established') {
      console.log('✅ WebSocket connection established:', data.message);
      return;
    }
    
    // Handle call events (using event field)
    switch (data.event) {
      case 'call_start':
        console.log('📞 Call started:', data.streamSid);
        setCallData({
          streamSid: data.streamSid,
          startTime: new Date(data.timestamp),
          status: 'active',
          transcript: '',
          cleanTranscript: '',
          riskScore: 0,
          riskBand: 'SAFE',
          updates: [],
          duration: 0,
          finalScore: null,
          endTime: null
        });
        setUpdates([]);
        break;

      case 'update':
        console.log('📝 Call update received:', data);
        setCallData(prev => {
          // If no call data exists, create it from the first update
          if (!prev) {
            console.log('📞 Creating call data from first update:', data.streamSid);
            const callInfo = {
              streamSid: data.streamSid,
              startTime: new Date(data.timestamp),
              status: 'active',
              transcript: data.text,
              cleanTranscript: data.clean_text,
              riskScore: data.risk,
              riskBand: data.band,
              updates: [],
              duration: 0,
              finalScore: null,
              endTime: null
            };
            
            const update = {
              text: data.text,
              cleanText: data.clean_text,
              risk: data.risk,
              riskBand: data.band,
              timestamp: new Date(data.timestamp)
            };
            
            setUpdates([update]);
            
            // Check if initial risk score crosses 85% and show scam alert
            if (data.risk > 0.85 && !alertShown) {
              console.log('🚨 High risk detected on call start! Risk score:', (data.risk * 100).toFixed(1) + '%');
              setShowScamAlert(true);
              setAlertShown(true);
            }
            
            return {
              ...callInfo,
              updates: [update]
            };
          }
          
          // If streamSid doesn't match, ignore
          if (prev.streamSid !== data.streamSid) {
            console.log('⚠️ StreamSid mismatch, ignoring update');
            return prev;
          }
          
          const update = {
            text: data.text,
            cleanText: data.clean_text,
            risk: data.risk,
            riskBand: data.band,
            timestamp: new Date(data.timestamp)
          };
          
          setUpdates(prevUpdates => [...prevUpdates, update]);
          
          // Check if risk score crosses 85% and show scam alert
          if (data.risk > 0.85 && !alertShown) {
            console.log('🚨 High risk detected! Risk score:', (data.risk * 100).toFixed(1) + '%');
            setShowScamAlert(true);
            setAlertShown(true);
          }
          
          return {
            ...prev,
            transcript: data.text,
            cleanTranscript: data.clean_text,
            riskScore: data.risk,
            riskBand: data.band,
            updates: [...(prev.updates || []), update],
            duration: Math.floor((new Date() - prev.startTime) / 1000)
          };
        });
        break;

      case 'call_end':
        console.log('🏁 Call ended:', data);
        setCallData(prev => {
          if (!prev || prev.streamSid !== data.streamSid) return prev;
          
          const finalCall = {
            ...prev,
            status: 'ended',
            finalScore: data.final_score,
            duration: data.duration,
            endTime: new Date(data.timestamp)
          };
          
          setCallHistory(prevHistory => [finalCall, ...prevHistory.slice(0, 9)]);
          return finalCall;
        });
        break;

      default:
        console.log('❓ Unknown message type:', data.type || data.event);
    }
  }, []);

  const { isConnected, isConnecting, error, disconnect } = useWebSocket('wss://submammary-correlatively-irma.ngrok-free.dev/notify', handleMessage);


  // Update call duration every second
  useEffect(() => {
    if (!callData || callData.status !== 'active') return;

    const interval = setInterval(() => {
      setCallData(prev => ({
        ...prev,
        duration: Math.floor((new Date() - prev.startTime) / 1000)
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, [callData]);

  const getRiskColor = (risk) => {
    if (risk >= 0.7) return 'text-red-400 bg-red-900/20';
    if (risk >= 0.4) return 'text-yellow-400 bg-yellow-900/20';
    return 'text-green-400 bg-green-900/20';
  };

  const getRiskBandColor = (band) => {
    switch (band) {
      case 'HIGH': return 'bg-red-500';
      case 'MEDIUM': return 'bg-yellow-500';
      case 'LOW': return 'bg-blue-500';
      case 'SAFE': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleEndCall = async () => {
    if (!callData?.streamSid) {
      console.log('No active call to end');
      disconnect();
      onClose();
      return;
    }

    setIsEndingCall(true);
    
    try {
      console.log('📞 Sending end call request to backend...');
      const response = await fetch(`https://submammary-correlatively-irma.ngrok-free.dev/api/calls/${callData.streamSid}/disconnect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        }
      });

      if (response.ok) {
        console.log('✅ Call ended successfully via API');
        // Update call data to show ended status
        setCallData(prev => ({
          ...prev,
          status: 'ended',
          endTime: new Date()
        }));
      } else {
        console.error('❌ Failed to end call via API:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('❌ Error ending call via API:', error);
    } finally {
      setIsEndingCall(false);
      // Hide iPhone UI with smooth transition
      setShowIPhone(false);
      // Don't automatically close the page - let user stay on monitoring page
      console.log('📞 Call ended, iPhone UI hidden, staying on monitoring page');
    }
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div 
        className="border-b border-gray-600/40 px-6 py-4"
        style={{
          background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(0, 0, 0, 0.7) 50%, rgba(31, 41, 55, 0.8) 100%)',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
        }}
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold flex items-center space-x-2">
              <Phone className="w-6 h-6" />
              <span>ScamShield - Live Call Monitoring</span>
            </h1>
            {isConnected && (
              <div className="flex items-center space-x-2 text-green-400">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span className="text-xs">Connected</span>
              </div>
            )}
            {isConnecting && (
              <div className="flex items-center space-x-2 text-yellow-400">
                <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                <span className="text-xs">Connecting...</span>
              </div>
            )}
            {error && (
              <div className="flex items-center space-x-2 text-red-400">
                <div className="w-2 h-2 bg-red-400 rounded-full" />
                <span className="text-xs">Error</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={handleEndCall}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
            >
              <PhoneOff className="w-4 h-4" />
              <span>Exit</span>
            </button>
            <button
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-700 text-white p-2 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-8" style={{ minHeight: '100vh' }}>
        {callData ? (
          <div className={`grid grid-cols-1 gap-8 transition-all duration-1000 ${
            showIPhone ? 'lg:grid-cols-4' : 'lg:grid-cols-1'
          }`}>
            {/* Current Call Details */}
            <div className={`transition-all duration-1000 ${
              showIPhone ? 'lg:col-span-2 space-y-8' : 'lg:col-span-1'
            }`}>
              {/* When iPhone is visible - stacked layout */}
              {showIPhone ? (
                <>
                  {/* Call Status Card */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-2xl p-6 border border-gray-600/40 shadow-2xl"
                    style={{
                      background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(0, 0, 0, 0.7) 50%, rgba(31, 41, 55, 0.8) 100%)',
                      backdropFilter: 'blur(20px)',
                      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(75, 85, 99, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15)'
                    }}
                  >
                <h2 className="text-2xl font-bold flex items-center space-x-2 mb-4">
                  <Activity className="w-6 h-6" />
                  <span>Live Call Status</span>
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-400">Stream SID</label>
                    <p className="text-white font-mono text-sm">{callData.streamSid}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">Status</label>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${callData.status === 'active' ? 'bg-green-400' : 'bg-gray-400'}`} />
                      <span className="text-white capitalize">{callData.status}</span>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">Start Time</label>
                    <p className="text-white">{callData.startTime.toLocaleTimeString()}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">Duration</label>
                    <p className="text-white flex items-center space-x-1">
                      <Timer className="w-4 h-4" />
                      <span>{formatDuration(callData.duration)}</span>
                    </p>
                  </div>
                </div>
              </motion.div>

              {/* Risk Analysis */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="rounded-2xl p-6 border border-gray-600/40 shadow-2xl"
                style={{
                  background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(0, 0, 0, 0.7) 50%, rgba(31, 41, 55, 0.8) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(75, 85, 99, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15)'
                }}
              >
                <h2 className="text-2xl font-bold mb-4 flex items-center space-x-2">
                  <Shield className="w-6 h-6" />
                  <span>Risk Analysis</span>
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-400">Current Risk Score</label>
                    <div className={`text-3xl font-bold ${getRiskColor(callData.riskScore)}`}>
                      {(callData.riskScore * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">Risk Band</label>
                    <div className="flex items-center space-x-2">
                      <div className={`w-3 h-3 rounded-full ${getRiskBandColor(callData.riskBand)}`} />
                      <span className="text-white font-semibold">{callData.riskBand}</span>
                    </div>
                  </div>
                  {callData.finalScore !== null && (
                    <div className="md:col-span-2">
                      <label className="text-sm text-gray-400">Final Score</label>
                      <div className={`text-2xl font-bold ${getRiskColor(callData.finalScore)}`}>
                        {(callData.finalScore * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
                </>
              ) : (
                /* When iPhone is hidden - side by side layout */
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Call Status Card */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-2xl p-6 border border-gray-600/40 shadow-2xl"
                    style={{
                      background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(0, 0, 0, 0.7) 50%, rgba(31, 41, 55, 0.8) 100%)',
                      backdropFilter: 'blur(20px)',
                      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(75, 85, 99, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15)'
                    }}
                  >
                    <h2 className="text-2xl font-bold flex items-center space-x-2 mb-4">
                      <Activity className="w-6 h-6 text-blue-400" />
                      <span>Live Call Status</span>
                    </h2>
                    <div className="grid grid-cols-1 gap-4">
                      <div>
                        <label className="text-sm text-gray-400">Stream SID</label>
                        <p className="text-white font-mono text-sm">{callData.streamSid}</p>
                      </div>
                      <div>
                        <label className="text-sm text-gray-400">Status</label>
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${callData.status === 'active' ? 'bg-green-400' : 'bg-gray-400'}`} />
                          <span className="text-white capitalize">{callData.status}</span>
                        </div>
                      </div>
                      <div>
                        <label className="text-sm text-gray-400">Start Time</label>
                        <p className="text-white">{callData.startTime.toLocaleTimeString()}</p>
                      </div>
                      <div>
                        <label className="text-sm text-gray-400">Duration</label>
                        <p className="text-white flex items-center space-x-1">
                          <Timer className="w-4 h-4" />
                          <span>{formatDuration(callData.duration)}</span>
                        </p>
                      </div>
                    </div>
                  </motion.div>

                  {/* Risk Analysis */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="rounded-2xl p-6 border border-gray-600/40 shadow-2xl"
                    style={{
                      background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(0, 0, 0, 0.7) 50%, rgba(31, 41, 55, 0.8) 100%)',
                      backdropFilter: 'blur(20px)',
                      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(75, 85, 99, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15)'
                    }}
                  >
                    <h2 className="text-2xl font-bold mb-4 flex items-center space-x-2">
                      <Shield className="w-6 h-6 text-orange-400" />
                      <span>Risk Analysis</span>
                    </h2>
                    <div className="grid grid-cols-1 gap-4">
                      <div>
                        <label className="text-sm text-gray-400">Current Risk Score</label>
                        <p className={`text-3xl font-bold ${getRiskColor(callData.riskScore)}`}>
                          {(callData.riskScore * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div>
                        <label className="text-sm text-gray-400">Risk Band</label>
                        <p className={`text-3xl font-bold ${getRiskColor(callData.riskScore)}`}>
                          {callData.riskBand}
                        </p>
                      </div>
                      {callData.finalScore !== null && (
                        <div>
                          <label className="text-sm text-gray-400">Final Risk Score</label>
                          <p className={`text-3xl font-bold ${getRiskColor(callData.finalScore)}`}>
                            {(callData.finalScore * 100).toFixed(1)}%
                          </p>
                        </div>
                      )}
                    </div>
                  </motion.div>
                </div>
              )}

              {/* Transcript */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="rounded-2xl p-6 border border-gray-600/40 shadow-2xl mt-8"
                style={{
                  background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(0, 0, 0, 0.7) 50%, rgba(31, 41, 55, 0.8) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(75, 85, 99, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15)'
                }}
              >
                <h2 className="text-2xl font-bold mb-4 flex items-center space-x-2">
                  <MessageSquare className="w-6 h-6 text-purple-400" />
                  <span>{showIPhone ? 'Live Transcript' : 'Complete Conversation Log'}</span>
                </h2>
                <div className="space-y-4">
                  {showIPhone ? (
                    /* Live transcript view */
                    <>
                      <div>
                        <label className="text-sm text-gray-400">Current Statement</label>
                        <div className="bg-black/60 rounded-lg p-4 font-mono text-sm min-h-[60px] flex items-center">
                          {callData.transcript || 'Waiting for transcript...'}
                        </div>
                      </div>
                      <div>
                        <label className="text-sm text-gray-400">Processed Text</label>
                        <div className="bg-black/60 rounded-lg p-4 font-mono text-sm min-h-[60px] flex items-center">
                          {callData.cleanTranscript || 'Waiting for clean transcript...'}
                        </div>
                      </div>
                    </>
                  ) : (
                    /* Combined conversation log */
                    <div>
                      <label className="text-sm text-gray-400 mb-3 block">Full Conversation History</label>
                      <div className="bg-black/60 rounded-lg p-6">
                        {updates.length > 0 ? (
                          <p className="text-white text-base leading-relaxed">
                            {updates.map((update, index) => (
                              <span key={index}>
                                {update.cleanText}
                                {index < updates.length - 1 && ' '}
                              </span>
                            ))}
                          </p>
                        ) : (
                          <div className="text-center py-8">
                            <p className="text-gray-400 mb-4">No conversation data available</p>
                            <p className="text-gray-500 text-sm">Conversation will appear here as the call progresses</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            </div>

            {/* Updates Timeline */}
            <div className={`space-y-8 transition-all duration-1000 ${
              showIPhone ? 'lg:col-span-1' : 'lg:col-span-1'
            }`}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="rounded-2xl p-6 border border-gray-600/40 shadow-2xl"
                style={{
                  background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(0, 0, 0, 0.7) 50%, rgba(31, 41, 55, 0.8) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(75, 85, 99, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15)'
                }}
              >
                <h2 className="text-2xl font-bold mb-6 flex items-center space-x-2">
                  <TrendingUp className="w-6 h-6 text-blue-400" />
                  <span>Live Updates</span>
                </h2>
                <div 
                  className="space-y-6 custom-scrollbar"
                  style={{
                    height: '600px',
                    overflowY: 'scroll',
                    overflowX: 'hidden',
                    position: 'relative'
                  }}
                >
                  {/* Scroll indicator gradient */}
                  <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-black/40 to-transparent pointer-events-none z-10"></div>
                  {updates.length > 0 ? (
                    <div className="pr-2">
                      {updates.map((update, index) => (
                      <motion.div 
                        key={index} 
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="group p-5 rounded-xl border border-gray-600/40 transition-all duration-300"
                        style={{
                          background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(0, 0, 0, 0.4) 50%, rgba(31, 41, 55, 0.5) 100%)',
                          backdropFilter: 'blur(10px)',
                          boxShadow: '0 8px 25px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
                        }}
                        onMouseEnter={(e) => {
                          e.target.style.background = 'linear-gradient(135deg, rgba(17, 24, 39, 0.8) 0%, rgba(0, 0, 0, 0.6) 50%, rgba(31, 41, 55, 0.7) 100%)';
                          e.target.style.borderColor = 'rgba(75, 85, 99, 0.6)';
                        }}
                        onMouseLeave={(e) => {
                          e.target.style.background = 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(0, 0, 0, 0.4) 50%, rgba(31, 41, 55, 0.5) 100%)';
                          e.target.style.borderColor = 'rgba(75, 85, 99, 0.4)';
                        }}
                      >
                        <div className="flex items-start space-x-4">
                          {/* Risk Indicator */}
                          <div className="flex-shrink-0">
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center shadow-lg ${
                              update.riskBand === 'HIGH' ? 'bg-red-500' :
                              update.riskBand === 'MEDIUM' ? 'bg-yellow-500' :
                              'bg-green-500'
                            }`}>
                              <Shield className="w-6 h-6 text-white" />
                            </div>
                          </div>
                          
                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            {/* Header with Risk and Timestamp */}
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center space-x-3">
                                <span className="text-lg font-bold text-white">
                                  {(update.risk * 100).toFixed(1)}%
                                </span>
                                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                                  update.riskBand === 'HIGH' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                                  update.riskBand === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                                  'bg-green-500/20 text-green-400 border border-green-500/30'
                                }`}>
                                  {update.riskBand}
                                </span>
                              </div>
                              <div className="flex items-center space-x-2 text-gray-400">
                                <Clock className="w-4 h-4" />
                                <span className="text-sm font-medium">
                                  {update.timestamp.toLocaleTimeString()}
                                </span>
                              </div>
                            </div>
                            
                            {/* Processed Text */}
                            <div className="bg-black/60 rounded-lg p-4 border border-gray-700/30">
                              <div className="flex items-center space-x-2 mb-2">
                                <MessageSquare className="w-4 h-4 text-blue-400" />
                                <span className="text-sm font-medium text-gray-300">Processed Text</span>
                              </div>
                              <p className="text-white font-medium leading-relaxed">
                                "{update.cleanText}"
                              </p>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="w-16 h-16 bg-black/40 backdrop-blur-sm rounded-full flex items-center justify-center mx-auto mb-4">
                        <TrendingUp className="w-8 h-8 text-gray-400" />
                      </div>
                      <p className="text-gray-400 text-lg">Waiting for live updates...</p>
                      <p className="text-gray-500 text-sm mt-2">Updates will appear here as the call progresses</p>
                      <p className="text-gray-600 text-xs mt-2">Scroll will appear when content exceeds container height</p>
                    </div>
                  )}
                </div>
              </motion.div>

              {/* Call History */}
              {callHistory.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="rounded-2xl p-6 border border-gray-600/40 shadow-2xl"
                  style={{
                    background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(0, 0, 0, 0.7) 50%, rgba(31, 41, 55, 0.8) 100%)',
                    backdropFilter: 'blur(20px)',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(75, 85, 99, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15)'
                  }}
                >
                  <h2 className="text-2xl font-bold mb-4 flex items-center space-x-2">
                    <Clock className="w-6 h-6" />
                    <span>Recent Calls</span>
                  </h2>
                  <div className="space-y-4">
                    {callHistory.slice(0, 5).map((call, index) => (
                      <div 
                        key={index} 
                        className="p-3 rounded-lg border border-gray-600/40"
                        style={{
                          background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(0, 0, 0, 0.4) 50%, rgba(31, 41, 55, 0.5) 100%)',
                          backdropFilter: 'blur(10px)',
                          boxShadow: '0 4px 15px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
                        }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-mono text-gray-300">
                            {call.streamSid.slice(-8)}
                          </span>
                          <span className="text-xs text-gray-400">
                            {call.endTime?.toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${getRiskBandColor(call.riskBand)}`} />
                          <span className="text-sm text-white">
                            {(call.finalScore * 100).toFixed(1)}% - {call.riskBand}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </div>

            {/* iPhone 15 Mock Screen */}
            {showIPhone && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20, scale: 0.9 }}
                transition={{ delay: 0.5, duration: 0.5 }}
                className="lg:col-span-1 sticky top-6"
              >
                <div className="bg-gray-800 rounded-[3rem] p-2 border-2 border-gray-600 shadow-2xl transform perspective-1000">
                  <div className="bg-black rounded-[2.5rem] overflow-hidden shadow-inner relative">
                    {/* iPhone 15 Screen */}
                    <div className="relative bg-gray-900 h-[600px] w-[300px] mx-auto rounded-[2rem] overflow-hidden">
                      {/* Status Bar */}
                      <div className="flex justify-between items-center px-8 pt-4 pb-3">
                        <span className="text-white text-sm font-semibold">6:11</span>
                        <div className="flex items-center space-x-2">
                          {/* Signal bars */}
                          <div className="flex space-x-0.5">
                            <div className="w-1 h-2 bg-white rounded-full"></div>
                            <div className="w-1 h-3 bg-white rounded-full"></div>
                            <div className="w-1 h-4 bg-white rounded-full"></div>
                          </div>
                          {/* WiFi icon */}
                          <div className="w-4 h-3 relative">
                            <div className="absolute bottom-0 left-0 w-3 h-1 bg-white rounded-full"></div>
                            <div className="absolute bottom-0.5 left-0.5 w-2 h-1 bg-white rounded-full"></div>
                            <div className="absolute bottom-1 left-1 w-1 h-1 bg-white rounded-full"></div>
                          </div>
                          {/* Battery */}
                          <div className="flex items-center space-x-1">
                            <div className="w-6 h-3 border border-white rounded-sm relative">
                              <div className="w-4 h-2 bg-white rounded-sm ml-0.5 mt-0.5"></div>
                            </div>
                            <div className="w-0.5 h-2 bg-white rounded-r-sm"></div>
                            <span className="text-white text-xs font-medium">76</span>
                          </div>
                        </div>
                      </div>

                      {/* Dynamic Island */}
                      <div className="absolute top-3 left-1/2 transform -translate-x-1/2 w-32 h-8 bg-black rounded-full flex items-center justify-center shadow-lg">
                        <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                      </div>

                      {/* Call Info */}
                      <div className="flex flex-col items-center justify-center h-full -mt-20 px-8">
                        <div className="text-center mb-12">
                          <div className="text-gray-400 text-lg mb-3 font-medium">Calling...</div>
                          <div className="text-white text-3xl font-bold">
                            {callData?.streamSid ? 'Scam Call' : 'Unknown Caller'}
                          </div>
                        </div>

                        {/* Call Duration */}
                        <div className="text-white text-3xl font-mono mb-12 font-light">
                          {formatDuration(callData?.duration || 0)}
                        </div>

                        {/* Risk Indicator */}
                        <div className="mb-12">
                          <div className={`w-20 h-20 rounded-full flex items-center justify-center shadow-lg ${
                            callData?.riskBand === 'HIGH' ? 'bg-red-500' :
                            callData?.riskBand === 'MEDIUM' ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`}>
                            <Shield className="w-10 h-10 text-white" />
                          </div>
                          <div className="text-center mt-3">
                            <div className="text-white text-base font-semibold">
                              {callData?.riskBand || 'SAFE'}
                            </div>
                            <div className="text-gray-400 text-sm">
                              {(callData?.riskScore * 100 || 0).toFixed(1)}% Risk
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Call Controls */}
                      <div className="absolute bottom-12 left-0 right-0 px-12">
                        <div className="grid grid-cols-3 gap-6">
                          {/* Audio */}
                          <div className="flex flex-col items-center">
                            <div className="w-14 h-14 bg-gray-700/80 rounded-full flex items-center justify-center mb-3 shadow-lg backdrop-blur-sm">
                              <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12 2C13.1 2 14 2.9 14 4V12C14 13.1 13.1 14 12 14S10 13.1 10 12V4C10 2.9 10.9 2 12 2M19 10V12C19 15.9 15.9 19 12 19S5 15.9 5 12V10H7V12C7 14.8 9.2 17 12 17S17 14.8 17 12V10H19M12 6C10.9 6 10 6.9 10 8V12C10 13.1 10.9 14 12 14S14 13.1 14 12V8C14 6.9 13.1 6 12 6Z"/>
                              </svg>
                            </div>
                            <span className="text-white text-xs font-medium">Audio</span>
                          </div>

                          {/* FaceTime */}
                          <div className="flex flex-col items-center">
                            <div className="w-14 h-14 bg-gray-700/80 rounded-full flex items-center justify-center mb-3 shadow-lg backdrop-blur-sm">
                              <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M17 10.5V7C17 6.45 16.55 6 16 6H4C3.45 6 3 6.45 3 7V17C3 17.55 3.45 18 4 18H16C16.55 18 17 17.55 17 17V13.5L21 17.5V6.5L17 10.5Z"/>
                              </svg>
                            </div>
                            <span className="text-white text-xs font-medium">FaceTime</span>
                          </div>

                          {/* Mute */}
                          <div className="flex flex-col items-center">
                            <div className="w-14 h-14 bg-gray-700/80 rounded-full flex items-center justify-center mb-3 shadow-lg backdrop-blur-sm">
                              <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12 14C13.1 14 14 13.1 14 12V5C14 3.9 13.1 3 12 3S10 3.9 10 5V12C10 13.1 10.9 14 12 14M16.5 12C16.5 10.2 15.7 8.7 14.5 7.8L13.5 8.8C14.3 9.4 14.8 10.2 14.8 11.1H16.5M19 12C19 9.1 17.2 6.6 14.5 5.7L13.5 6.7C15.4 7.3 16.8 9.4 16.8 11.1H19M9 12C9 9.1 7.2 6.6 4.5 5.7L3.5 6.7C5.4 7.3 6.8 9.4 6.8 11.1H9M12 16C14.2 16 16 14.2 16 12H14C14 13.1 13.1 14 12 14S10 13.1 10 12H8C8 14.2 9.8 16 12 16Z"/>
                              </svg>
                            </div>
                            <span className="text-white text-xs font-medium">Mute</span>
                          </div>

                          {/* Add Call */}
                          <div className="flex flex-col items-center">
                            <div className="w-14 h-14 bg-gray-700/80 rounded-full flex items-center justify-center mb-3 shadow-lg backdrop-blur-sm">
                              <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M15 12C17.21 12 19 10.21 19 8S17.21 4 15 4 11 5.79 11 8 12.79 12 15 12M15 6C16.1 6 17 6.9 17 8S16.1 10 15 10 13 9.1 13 8 13.9 6 15 6M15 14C12.33 14 7 15.34 7 18V20H23V18C23 15.34 17.67 14 15 14M9 18C9.22 17.28 12.31 16 15 16S20.78 17.28 21 18H9M15 16C12.79 16 11 14.21 11 12S12.79 8 15 8 19 9.79 19 12 17.21 16 15 16M15 10C13.9 10 13 10.9 13 12S13.9 14 15 14 17 13.1 17 12 16.1 10 15 10Z"/>
                              </svg>
                            </div>
                            <span className="text-white text-xs font-medium">Add</span>
                          </div>

                          {/* End Call */}
                          <div className="flex flex-col items-center">
                            <button
                              onClick={handleEndCall}
                              disabled={isEndingCall || !callData?.streamSid}
                              className={`w-14 h-14 rounded-full flex items-center justify-center mb-3 shadow-lg transition-all ${
                                isEndingCall || !callData?.streamSid
                                  ? 'bg-gray-600/80 cursor-not-allowed'
                                  : 'bg-red-600 hover:bg-red-700 active:scale-95 shadow-red-500/50'
                              }`}
                            >
                              {isEndingCall ? (
                                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              ) : (
                                <PhoneOff className="w-7 h-7 text-white" />
                              )}
                            </button>
                            <span className="text-white text-xs font-medium">
                              {isEndingCall ? 'Ending...' : 'End'}
                            </span>
                          </div>

                          {/* Keypad */}
                          <div className="flex flex-col items-center">
                            <div className="w-14 h-14 bg-gray-700/80 rounded-full flex items-center justify-center mb-3 shadow-lg backdrop-blur-sm">
                              <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M2 3H22C23.1 3 24 3.9 24 5V19C24 20.1 23.1 21 22 21H2C0.9 21 0 20.1 0 19V5C0 3.9 0.9 3 2 3M2 5V19H22V5H2M4 7H6V9H4V7M8 7H10V9H8V7M12 7H14V9H12V7M16 7H18V9H16V7M20 7H22V9H20V7M4 11H6V13H4V11M8 11H10V13H8V11M12 11H14V13H12V11M16 11H18V13H16V11M20 11H22V13H20V11M4 15H6V17H4V15M8 15H10V17H8V15M12 15H14V17H12V15M16 15H18V17H16V15M20 15H22V17H20V15Z"/>
                              </svg>
                            </div>
                            <span className="text-white text-xs font-medium">Keypad</span>
                          </div>
                        </div>
                      </div>

                      {/* Home Indicator */}
                      <div className="absolute bottom-3 left-1/2 transform -translate-x-1/2 w-32 h-1 bg-white/80 rounded-full"></div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="w-16 h-16 bg-black/40 backdrop-blur-sm rounded-full flex items-center justify-center mx-auto mb-4">
                <Phone className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold mb-2">No Active Calls</h3>
              <p className="text-gray-400">Waiting for call data...</p>
              <div className="mt-4 text-sm text-gray-500">
                <p>Connection Status: {isConnected ? '✅ Connected' : '❌ Disconnected'}</p>
                {error && <p className="text-red-400">Error: {error}</p>}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Scam Alert Dialog */}
      <AlertDialog open={showScamAlert} onOpenChange={setShowScamAlert}>
        <AlertDialogContent className="max-w-md bg-black border-gray-700">
          {/* Close Button */}
          <button
            onClick={() => setShowScamAlert(false)}
            className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          
          <AlertDialogHeader>
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-white" />
              </div>
              <div>
                <AlertDialogTitle className="text-2xl font-bold text-red-400">
                  🚨 SCAM ALERT
                </AlertDialogTitle>
              </div>
            </div>
            <AlertDialogDescription className="text-base text-gray-300 space-y-3">
              <p className="font-semibold text-lg text-white">
                This call appears to be a potential scam!
              </p>
              <p>
                Our AI has detected suspicious patterns in this conversation with a risk score of{' '}
                <span className="font-bold text-red-400">
                  {callData ? (callData.riskScore * 100).toFixed(1) : '0'}%
                </span>
              </p>
              <div className="bg-gray-800 border border-gray-600 rounded-lg p-4 mt-4">
                <p className="text-sm text-gray-200 font-medium">
                  ⚠️ <strong>Recommended Actions:</strong>
                </p>
                <ul className="text-sm text-gray-300 mt-2 space-y-1">
                  <li>• Do not provide personal information</li>
                  <li>• Do not make any payments</li>
                  <li>• Hang up immediately if requested</li>
                  <li>• Report to authorities if needed</li>
                </ul>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex-col sm:flex-row gap-3">
            <AlertDialogCancel 
              onClick={() => setShowScamAlert(false)}
              className="w-full sm:w-auto bg-gray-700 hover:bg-gray-600 text-white border-gray-600"
            >
              Continue Monitoring
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={() => {
                setShowScamAlert(false);
                handleEndCall();
              }}
              className="w-full sm:w-auto bg-red-600 hover:bg-red-700 text-white"
            >
              End Call Now
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default LiveMonitoringPage;
