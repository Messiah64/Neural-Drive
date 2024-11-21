'use client'

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Activity, AlertCircle, CheckCircle, XCircle, Loader2, Brain, Waves } from 'lucide-react';
import { startRecording, stopRecording, startInference, stopInference, getStatus, trainModel } from '../api';

// Custom Button component using theme variables
const MotionButton = ({ 
  children, 
  isRecording, 
  disabled, 
  onClick, 
  className = "",
  isCalibrated = false
}: {
  children: React.ReactNode;
  isRecording?: boolean;
  disabled?: boolean;
  onClick: () => void;
  className?: string;
  isCalibrated?: boolean;
}) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={`
      w-full
      ${isRecording ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90' : 
        isCalibrated ? 'bg-green-600 text-white hover:bg-green-700' :
        'bg-primary text-primary-foreground hover:bg-primary/90'}
      rounded-md
      transition-colors
      disabled:cursor-not-allowed
      disabled:opacity-50
      p-4
      ${className}
    `}
  >
    {children}
  </button>
);

export default function Home() {
  const [recordingMotion, setRecordingMotion] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState(15);
  const [prediction, setPrediction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isInferring, setIsInferring] = useState(false);
  const [calibratedMotions, setCalibratedMotions] = useState<Set<string>>(new Set());
  const [isTraining, setIsTraining] = useState(false);
  const [modelTrained, setModelTrained] = useState(false);

  const motions = ['GO', 'STOP'];
  const isCalibrated = calibratedMotions.size === motions.length;

  // Poll for status updates
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    const pollStatus = async () => {
      try {
        const status = await getStatus();
        
        if (status.status === 'error') {
          setError(status.message);
          if (recordingMotion) {
            setRecordingMotion(null);
            setTimeLeft(15);
          }
        } else if (status.status === 'success') {
          if (recordingMotion) {
            setCalibratedMotions(prev => new Set([...prev, recordingMotion]));
          }
        } else if (status.status === 'prediction') {
          setPrediction(status.prediction);
        }
      } catch (err) {
        console.error('Status polling error:', err);
      }
    };

    if (recordingMotion || isInferring) {
      intervalId = setInterval(pollStatus, 1000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [recordingMotion, isInferring]);

  // Timer effect
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (recordingMotion && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
    } else if (timeLeft === 0 && recordingMotion) {
      handleStopRecording();
    }
    return () => clearInterval(timer);
  }, [recordingMotion, timeLeft]);

  // Start recording handler
  const handleStartRecording = async (motion: string) => {
    try {
      setError(null);
      const response = await startRecording(motion);
      if (response.status === 'success') {
        setRecordingMotion(motion);
        setTimeLeft(15);
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError('Failed to start recording');
      console.error(err);
    }
  };

  // Stop recording handler
  const handleStopRecording = async () => {
    try {
      if (recordingMotion) {
        await stopRecording();
        setRecordingMotion(null);
        setTimeLeft(15);
      }
    } catch (err) {
      setError('Failed to stop recording');
      console.error(err);
    }
  };

  // Training handler
  const handleTraining = async () => {
    try {
      setIsTraining(true);
      setError(null);
      const response = await trainModel();
      if (response.status === 'success') {
        setModelTrained(true);
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError('Failed to train model');
      console.error(err);
    } finally {
      setIsTraining(false);
    }
  };

  // Toggle inference handler
  const toggleInference = async () => {
    try {
      setError(null);
      if (isInferring) {
        await stopInference();
        setIsInferring(false);
        setPrediction(null);
      } else {
        const response = await startInference();
        if (response.status === 'success') {
          setIsInferring(true);
        } else {
          setError(response.message);
        }
      }
    } catch (err) {
      setError('Failed to toggle inference');
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold tracking-tight flex items-center justify-center gap-2">
            <Brain className="w-8 h-8 text-primary" />
            Neural Drive Calibration
          </h1>
          <p className="text-muted-foreground">One time calibration for new users only</p>
        </div>

        {/* Main Content */}
        <div className="grid gap-8">
          {/* Calibration Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary" />
                System Calibration
              </CardTitle>
              <CardDescription>
                Record sample controls to train the processing system
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Motion Recording Buttons */}
                {motions.map((motion) => (
                  <Card key={motion} className="border-2 border-dashed hover:border-primary/20 transition-colors">
                    <CardContent className="pt-6">
                      <MotionButton
                        isRecording={recordingMotion === motion}
                        disabled={recordingMotion !== null && recordingMotion !== motion}
                        onClick={() => handleStartRecording(motion)}
                        className="h-32 text-lg"
                        isCalibrated={calibratedMotions.has(motion)}
                      >
                        <div className="flex flex-col items-center gap-3">
                          {calibratedMotions.has(motion) ? (
                            <CheckCircle className="w-8 h-8" />
                          ) : (
                            <Activity className={`w-8 h-8 ${recordingMotion === motion ? 'animate-pulse' : ''}`} />
                          )}
                          <div className="space-y-1">
                            <div>"{motion}" Control</div>
                            {recordingMotion === motion && (
                              <div className="text-sm font-normal">{timeLeft}s remaining</div>
                            )}
                          </div>
                        </div>
                      </MotionButton>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Recording Status */}
              {recordingMotion && (
                <Alert className="bg-primary/10 border-primary/20">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  <AlertTitle className="text-primary">Recording in Progress</AlertTitle>
                  <AlertDescription className="text-primary/80">
                    Think about "{recordingMotion}" for {timeLeft} seconds.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Training Card */}
          {isCalibrated && !modelTrained && (
            <Card>
              <CardHeader>
                <CardTitle className="text-xl flex items-center gap-2">
                  <Brain className="w-5 h-5 text-primary" />
                  Model Training
                </CardTitle>
                <CardDescription>
                  Train the model with recorded data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <MotionButton
                  isRecording={isTraining}
                  onClick={handleTraining}
                  className="h-16 text-lg"
                >
                  {isTraining ? (
                    <span className="flex items-center gap-2 justify-center">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Training Model...
                    </span>
                  ) : (
                    'Train Model'
                  )}
                </MotionButton>
              </CardContent>
            </Card>
          )}

          {/* Real-time Classification Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <Waves className="w-5 h-5 text-primary" />
                Real-time Processing
              </CardTitle>
              <CardDescription>
                Start real-time control processing
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <MotionButton
                isRecording={isInferring}
                disabled={!isCalibrated || !modelTrained}
                onClick={toggleInference}
                className="h-16 text-lg"
              >
                {isInferring ? (
                  <span className="flex items-center gap-2 justify-center">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Stop Processing
                  </span>
                ) : (
                  'Start Real-time Processing'
                )}
              </MotionButton>

              {/* Prediction Display */}
              {isInferring && (
                <Card className="bg-muted border-2">
                  <CardContent className="pt-6">
                    <div className="text-center space-y-2">
                      <p className="text-sm text-muted-foreground">Current Prediction</p>
                      <div className="text-4xl font-bold text-primary">
                        {prediction ? prediction : 'Waiting...'}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Status Footer */}
        <div className="text-center text-sm text-muted-foreground">
          {modelTrained ? (
            <div className="flex items-center justify-center gap-2 text-primary">
              <CheckCircle className="w-4 h-4" />
              System calibrated and model trained
            </div>
          ) : isCalibrated ? (
            <div className="flex items-center justify-center gap-2 text-primary">
              <CheckCircle className="w-4 h-4" />
              Calibration complete - Ready for training
            </div>
          ) : (
            <div className="flex items-center justify-center gap-2">
              <AlertCircle className="w-4 h-4" />
              Please complete calibration for both controls
            </div>
          )}
        </div>
      </div>
    </div>
  );
}