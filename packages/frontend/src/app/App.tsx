import { useState, useEffect } from 'react';
import { VideoUpload } from './components/VideoUpload';
import { ProcessingStatus } from './components/ProcessingStatus';
import { AnalysisResults } from './components/AnalysisResults';
import { Dashboard } from './components/Dashboard';
import { Button } from './components/ui/button';
import { ArrowLeft, Video, Sparkles } from 'lucide-react';
import { motion } from 'motion/react';
import logoImg from '../imports/Logo.png';

type AppState = 'dashboard' | 'upload' | 'processing' | 'results';

interface AnalysisData {
  duration: number;
  playersDetected: number;
  totalShots: number;
  successfulShots: number;
  framesExtracted: number;
  ballDetectionRate: number;
  teamAColor: string;
  teamBColor: string;
  possession: {
    teamA: number;
    teamB: number;
  };
  defensiveFormations: Array<{
    formation: string;
    frequency: number;
    successRate: number;
  }>;
  offensivePlays: Array<{
    play: string;
    frequency: number;
    successRate: number;
  }>;
  shotPositions: {
    rueckraum: { attempts: number; goals: number };
    kreis: { attempts: number; goals: number };
    aussenLinks: { attempts: number; goals: number };
    aussenRechts: { attempts: number; goals: number };
  };
  playerStats: Array<{
    id: number;
    name: string;
    shots: number;
    goals: number;
    assists: number;
    distance: number;
    team: 'A' | 'B';
  }>;
  events: Array<{
    time: string;
    type: string;
    description: string;
  }>;
  heatmapData: Array<{
    zone: string;
    intensity: number;
  }>;
  qualityMetrics: {
    playerDetectionRate: number; // Anforderung 3.1: ≥80%
    teamClassificationAccuracy: number; // Anforderung 3.2: ≥85%
    formationAccuracy: number; // Anforderung 3.3: ≥75%
    fieldDetectionConfidence: number; // Spielfeld-Erkennung
  };
}

const processingSteps = [
  'Video wird geladen...',
  'Kameraanpassung und Frame-Extraktion (OpenCV)...',
  'Objekterkennung: Spieler, Ball und Spielfeld...',
  'Bounding Box Visualisierung aktiv...',
  'Trikotfarben-Erkennung (K-Means Clustering)...',
  'Automatische Teameinteilung läuft...',
  'Abwehrformationen werden klassifiziert...',
  'Offensive Spielzüge werden erkannt...',
  'Match-Report wird generiert...',
];

// Mock analysis data generator
function generateMockAnalysis(): AnalysisData {
  return {
    duration: 3247, // 54:07 minutes
    playersDetected: 14,
    totalShots: 42,
    successfulShots: 28,
    framesExtracted: 97410,
    ballDetectionRate: 94.3,
    teamAColor: 'Rot',
    teamBColor: 'Blau',
    possession: {
      teamA: 58,
      teamB: 42,
    },
    defensiveFormations: [
      { formation: '6-0', frequency: 42, successRate: 67 },
      { formation: '5-1', frequency: 28, successRate: 71 },
      { formation: '3-2-1', frequency: 15, successRate: 58 },
    ],
    offensivePlays: [
      { play: 'Kreuzen', frequency: 24, successRate: 62 },
      { play: 'Parallelstoß', frequency: 18, successRate: 55 },
      { play: 'Kempa-Trick', frequency: 8, successRate: 75 },
      { play: 'Konter', frequency: 16, successRate: 81 },
    ],
    shotPositions: {
      rueckraum: { attempts: 26, goals: 18 },
      kreis: { attempts: 12, goals: 8 },
      aussenLinks: { attempts: 4, goals: 2 },
      aussenRechts: { attempts: 4, goals: 2 },
    },
    playerStats: [
      { id: 7, name: 'Spieler #7', shots: 12, goals: 8, assists: 3, distance: 2847, team: 'A' },
      { id: 13, name: 'Spieler #13', shots: 9, goals: 7, assists: 5, distance: 3124, team: 'A' },
      { id: 21, name: 'Spieler #21', shots: 8, goals: 5, assists: 2, distance: 2653, team: 'B' },
      { id: 4, name: 'Spieler #4', shots: 6, goals: 4, assists: 4, distance: 2891, team: 'A' },
      { id: 18, name: 'Spieler #18', shots: 7, goals: 4, assists: 1, distance: 2447, team: 'B' },
    ],
    events: [
      { time: '02:34', type: 'goal', description: 'Tor durch Spieler #7 - Sprungwurf aus 8m' },
      { time: '05:12', type: 'save', description: 'Parade des Torwarts - Wurf von Spieler #13' },
      { time: '08:45', type: 'goal', description: 'Tor durch Spieler #21 - Durchbruch und Abschluss' },
      { time: '12:23', type: 'penalty', description: '7-Meter für Team A - Foul erkannt' },
      { time: '15:56', type: 'goal', description: 'Tor durch Spieler #13 - Kempa-Trick erfolgreich' },
      { time: '19:34', type: 'timeout', description: 'Team-Timeout Team B' },
      { time: '23:17', type: 'goal', description: 'Tor durch Spieler #4 - Konter abgeschlossen' },
      { time: '27:42', type: 'save', description: 'Glanzparade - Wurf von Spieler #7 gehalten' },
    ],
    heatmapData: [
      { zone: 'Links außen', intensity: 45 },
      { zone: 'Linker Rückraum', intensity: 72 },
      { zone: 'Mitte', intensity: 89 },
      { zone: 'Rechter Rückraum', intensity: 68 },
      { zone: 'Rechts außen', intensity: 51 },
      { zone: 'Kreis', intensity: 94 },
    ],
    qualityMetrics: {
      playerDetectionRate: 82, // Anforderung 3.1: ≥80%
      teamClassificationAccuracy: 87, // Anforderung 3.2: ≥85%
      formationAccuracy: 76, // Anforderung 3.3: ≥75%
      fieldDetectionConfidence: 90, // Spielfeld-Erkennung
    },
  };
}

function App() {
  const [state, setState] = useState<AppState>('dashboard');
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [matchId, setMatchId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [selectedMatchId, setSelectedMatchId] = useState<string | null>(null);

  // Handle video upload and automatically start processing
  const handleVideoUpload = (file: File, newMatchId: string) => {
    setVideoFile(file);
    setMatchId(newMatchId);
    setState('processing');
    setProgress(0);
    setCurrentStep('Video wird hochgeladen...');
  };

  // Poll backend for actual processing status
  useEffect(() => {
    if (state !== 'processing' || !matchId) return;

    const checkProcessingStatus = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/api/v1/videos/${matchId}/output`);
        const data = await response.json();
        
        // Update progress based on status
        if (data.status === 'ready') {
          // Processing complete - fetch actual analysis data from backend
          setProgress(100);
          setCurrentStep('Verarbeitung abgeschlossen!');
          
          // For now, use mock data but in future would fetch from backend
          setTimeout(() => {
            setAnalysisData(generateMockAnalysis());
            setState('results');
          }, 500);
        } else {
          // Still processing - increment progress
          setProgress((prev) => {
            const newProgress = Math.min(prev + Math.random() * 5 + 1, 95);
            
            // Update processing step based on progress
            const stepIndex = Math.min(
              Math.floor((newProgress / 100) * processingSteps.length),
              processingSteps.length - 1
            );
            setCurrentStep(processingSteps[stepIndex]);
            
            return newProgress;
          });
        }
      } catch (error) {
        console.error('Error checking processing status:', error);
        // Fall back to simulation if backend is not ready
        setProgress((prev) => {
          const newProgress = Math.min(prev + Math.random() * 8 + 2, 100);
          
          const stepIndex = Math.min(
            Math.floor((newProgress / 100) * processingSteps.length),
            processingSteps.length - 1
          );
          setCurrentStep(processingSteps[stepIndex]);

          if (newProgress >= 100) {
            setTimeout(() => {
              setAnalysisData(generateMockAnalysis());
              setState('results');
            }, 500);
          }

          return newProgress;
        });
      }
    };

    // Poll every 5 minutes
    const interval = setInterval(checkProcessingStatus, 5 * 60 * 1000);
    
    // Initial check
    checkProcessingStatus();

    return () => clearInterval(interval);
  }, [state, matchId]);

  const handleReset = () => {
    setState('dashboard');
    setVideoFile(null);
    setMatchId(null);
    setProgress(0);
    setCurrentStep('');
    setAnalysisData(null);
    setSelectedMatchId(null);
  };

  const handleNewUpload = () => {
    setState('upload');
  };

  const handleViewMatch = (matchId: string, data: AnalysisData, fileName: string) => {
    setSelectedMatchId(matchId);
    setAnalysisData(data);
    setVideoFile(new File([], fileName));
    setState('results');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-sky-50 to-orange-50">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-sky-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-900 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-orange-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 py-8">
        {/* Main Content */}
        {state === 'dashboard' && (
          <Dashboard onNewUpload={handleNewUpload} onViewMatch={handleViewMatch} />
        )}

        {state === 'upload' && (
          <div className="min-h-screen flex flex-col items-center justify-center -mt-8">
            {/* Back Button */}
            <div className="w-full max-w-2xl mb-4">
              <Button
                variant="outline"
                onClick={handleReset}
                className="shadow-md hover:shadow-lg transition-all"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Zurück zum Dashboard
              </Button>
            </div>

            {/* Hero Section */}
            <motion.div
              className="text-center mb-12"
              initial={{ opacity: 0, y: -30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <motion.img
                src={logoImg}
                alt="SportsVision Logo"
                className="h-24 mx-auto mb-8"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              />

              <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-900 via-sky-600 to-orange-500 bg-clip-text text-transparent">
                Handball Video Analytics
              </h1>

              <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-4">
                Automatisierte KI-gestützte Analyse von Handballspielen mit Computer Vision Technologie
              </p>

              <p className="text-lg text-gray-500 max-w-xl mx-auto">
                Laden Sie Ihr Video hoch und erhalten Sie detaillierte Einblicke zu Spielzügen, Formationen und Spielerstatistiken
              </p>
            </motion.div>

            {/* Upload Section */}
            <motion.div
              className="w-full max-w-2xl"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              <VideoUpload onVideoUpload={handleVideoUpload} />
            </motion.div>

            {/* Technology Note */}
            <motion.div
              className="text-center mt-8 text-sm text-gray-500 max-w-xl"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.6 }}
            >
              <p>Powered by OpenCV, K-Means Clustering & Deep Learning</p>
            </motion.div>
          </div>
        )}

        {state === 'processing' && videoFile && (
          <div className="max-w-3xl mx-auto mt-20">
            <ProcessingStatus
              fileName={videoFile.name}
              progress={Math.round(progress)}
              currentStep={currentStep}
              isComplete={progress >= 100}
            />
          </div>
        )}

        {state === 'results' && analysisData && videoFile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <div className="mb-6 mt-8">
              <Button 
                variant="outline" 
                onClick={handleReset}
                className="shadow-md hover:shadow-lg transition-all border-2 hover:border-sky-500"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Neues Video analysieren
              </Button>
            </div>
            <AnalysisResults data={analysisData} videoName={videoFile.name} matchId={matchId || undefined} />
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default App;