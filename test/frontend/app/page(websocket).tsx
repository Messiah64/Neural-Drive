// ========================================================================================================================================
// Websocket enabled 
// ========================================================================================================================================

// 'use client'

// import React, { useState, useEffect } from 'react';
// import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
// import { Button } from '@/components/ui/button';
// import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
// import { Activity, AlertCircle, CheckCircle, XCircle, Loader2, Brain, Waves } from 'lucide-react';
// import { useWebSocket } from './hooks/useWebSocket';

// const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_BASE_URL || 'ws://localhost:8000/ws';

// export default function Home() {
//   const [status, setStatus] = useState('idle');
//   const [timeLeft, setTimeLeft] = useState(15);
//   const [prediction, setPrediction] = useState<string | null>(null);
//   const [error, setError] = useState<string | null>(null);
//   const [isCalibrated, setIsCalibrated] = useState(false);
//   const [confidence, setConfidence] = useState<number>(0);
//   const { connect, disconnect, error: wsError } = useWebSocket(WS_BASE_URL);

//   useEffect(() => {
//     if (wsError) {
//       setError(wsError);
//     }
//   }, [wsError]);

//   useEffect(() => {
//     let timer;
//     if ((status === 'recording-yes' || status === 'recording-no') && timeLeft > 0) {
//       timer = setInterval(() => {
//         setTimeLeft(prev => prev - 1);
//       }, 1000);
//     } else if (timeLeft === 0) {
//       if (status === 'recording-yes' || status === 'recording-no') {
//         disconnect();
//         setStatus('idle');
//         setTimeLeft(15);
//         setIsCalibrated(true);
//       }
//     }
//     return () => clearInterval(timer);
//   }, [status, timeLeft, disconnect]);

//   const startRecording = async (label: 'yes' | 'no') => {
//     setError(null);
//     setStatus(`recording-${label}`);
//     setTimeLeft(15);

//     const ws = connect(`/record/${label}`);
//     if (ws) {
//       ws.onmessage = (event) => {
//         const data = JSON.parse(event.data);
        
//         if (data.status === 'error') {
//           setError(data.message);
//           setStatus('idle');
//           disconnect();
//         }
//       };
//     }
//   };

//   const startInference = () => {
//     setError(null);
//     setStatus('inferring');
//     setPrediction(null);

//     const ws = connect('/inference');
//     if (ws) {
//       ws.onmessage = (event) => {
//         const data = JSON.parse(event.data);
        
//         if (data.status === 'prediction') {
//           setPrediction(data.result);
//           setConfidence(data.confidence || 0);
//         } else if (data.status === 'error') {
//           setError(data.message);
//           setStatus('idle');
//           disconnect();
//         }
//       };
//     }
//   };

//   const stopInference = () => {
//     disconnect();
//     setStatus('idle');
//     setPrediction(null);
//     setConfidence(0);
//   };

//   return (
//     <div className="min-h-screen bg-gray-50 p-8">
//       <div className="max-w-5xl mx-auto space-y-8">
//         {/* Header */}
//         <div className="text-center space-y-2">
//           <h1 className="text-3xl font-bold tracking-tight flex items-center justify-center gap-2">
//             <Brain className="w-8 h-8 text-blue-600" />
//             EMG Classification System
//           </h1>
//           <p className="text-gray-500">Neural Interface Motion Detection</p>
//         </div>

//         {/* Main Content */}
//         <div className="grid gap-8 md:grid-cols-2">
//           {/* Calibration Card */}
//           <Card className="md:col-span-2">
//             <CardHeader>
//               <CardTitle className="text-xl flex items-center gap-2">
//                 <Activity className="w-5 h-5 text-blue-600" />
//                 System Calibration
//               </CardTitle>
//               <CardDescription>
//                 Record sample motions to train the classification system
//               </CardDescription>
//             </CardHeader>
//             <CardContent className="space-y-6">
//               <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
//                 {/* YES Recording Button */}
//                 <Card className="border-2 border-dashed hover:border-blue-400 transition-colors">
//                   <CardContent className="pt-6">
//                     <Button 
//                       onClick={() => startRecording('yes')}
//                       disabled={status !== 'idle'}
//                       className="w-full h-32 text-lg"
//                       variant={status === 'recording-yes' ? "destructive" : "default"}
//                     >
//                       <div className="flex flex-col items-center gap-3">
//                         <CheckCircle className={`w-8 h-8 ${status === 'recording-yes' ? 'animate-pulse' : ''}`} />
//                         <div className="space-y-1">
//                           <div>Record "YES" Motion</div>
//                           {status === 'recording-yes' && (
//                             <div className="text-sm font-normal">{timeLeft}s remaining</div>
//                           )}
//                         </div>
//                       </div>
//                     </Button>
//                   </CardContent>
//                 </Card>

//                 {/* NO Recording Button */}
//                 <Card className="border-2 border-dashed hover:border-blue-400 transition-colors">
//                   <CardContent className="pt-6">
//                     <Button 
//                       onClick={() => startRecording('no')}
//                       disabled={status !== 'idle'}
//                       className="w-full h-32 text-lg"
//                       variant={status === 'recording-no' ? "destructive" : "default"}
//                     >
//                       <div className="flex flex-col items-center gap-3">
//                         <XCircle className={`w-8 h-8 ${status === 'recording-no' ? 'animate-pulse' : ''}`} />
//                         <div className="space-y-1">
//                           <div>Record "NO" Motion</div>
//                           {status === 'recording-no' && (
//                             <div className="text-sm font-normal">{timeLeft}s remaining</div>
//                           )}
//                         </div>
//                       </div>
//                     </Button>
//                   </CardContent>
//                 </Card>
//               </div>

//               {/* Recording Status */}
//               {status.startsWith('recording') && (
//                 <Alert className="bg-blue-50 border-blue-200">
//                   <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
//                   <AlertTitle className="text-blue-800">Recording in Progress</AlertTitle>
//                   <AlertDescription className="text-blue-600">
//                     Please perform the {status === 'recording-yes' ? '"YES"' : '"NO"'} motion repeatedly for {timeLeft} seconds.
//                   </AlertDescription>
//                 </Alert>
//               )}
//             </CardContent>
//           </Card>

//           {/* Real-time Classification Card */}
//           <Card className="md:col-span-2">
//             <CardHeader>
//               <CardTitle className="text-xl flex items-center gap-2">
//                 <Waves className="w-5 h-5 text-blue-600" />
//                 Real-time Classification
//               </CardTitle>
//               <CardDescription>
//                 Start real-time motion classification
//               </CardDescription>
//             </CardHeader>
//             <CardContent className="space-y-6">
//               <Button 
//                 onClick={status === 'inferring' ? stopInference : startInference}
//                 disabled={!isCalibrated}
//                 className="w-full h-16 text-lg"
//                 variant={status === 'inferring' ? "destructive" : "default"}
//               >
//                 {status === 'inferring' ? (
//                   <span className="flex items-center gap-2">
//                     <Loader2 className="w-4 h-4 animate-spin" />
//                     Stop Classification
//                   </span>
//                 ) : (
//                   'Start Real-time Classification'
//                 )}
//               </Button>

//               {/* Prediction Display */}
//               {status === 'inferring' && (
//                 <Card className="bg-gray-50 border-2">
//                   <CardContent className="pt-6">
//                     <div className="text-center space-y-2">
//                       <p className="text-sm text-gray-500">Current Prediction</p>
//                       <div className="text-4xl font-bold text-blue-600">
//                         {prediction ? prediction : 'Waiting...'}
//                       </div>
//                       {prediction && (
//                         <div className="text-sm text-gray-500">
//                           Confidence: {(confidence * 100).toFixed(1)}%
//                         </div>
//                       )}
//                     </div>
//                   </CardContent>
//                 </Card>
//               )}
//             </CardContent>
//           </Card>
//         </div>

//         {/* Error Display */}
//         {error && (
//           <Alert variant="destructive" className="md:col-span-2">
//             <AlertCircle className="h-4 w-4" />
//             <AlertTitle>Error</AlertTitle>
//             <AlertDescription>{error}</AlertDescription>
//           </Alert>
//         )}

//         {/* Status Footer */}
//         <div className="text-center text-sm text-gray-500">
//           {isCalibrated ? (
//             <div className="flex items-center justify-center gap-2 text-green-600">
//               <CheckCircle className="w-4 h-4" />
//               System calibrated and ready
//             </div>
//           ) : (
//             <div className="flex items-center justify-center gap-2">
//               <AlertCircle className="w-4 h-4" />
//               Please complete calibration to begin
//             </div>
//           )}
//         </div>
//       </div>
//     </div>
//   );
// }
