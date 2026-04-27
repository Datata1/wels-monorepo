import { Users, Activity, Target, TrendingUp, MapPin, Clock, Award, Zap, Camera, Shield, Play, BarChart3, CheckCircle2, FileText, Video, Loader2 } from 'lucide-react';
import { Card } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { motion } from 'motion/react';
import { useState, useEffect } from 'react';

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
    playerDetectionRate: number;
    teamClassificationAccuracy: number;
    formationAccuracy: number;
    fieldDetectionConfidence: number;
  };
}

interface AnalysisResultsProps {
  data: AnalysisData;
  videoName: string;
  matchId?: string;
}

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

function OutputVideoTab({ matchId }: { matchId?: string }) {
  const [videoPath, setVideoPath] = useState<string | null>(null);
  const [status, setStatus] = useState<'loading' | 'processing' | 'ready' | 'error'>('loading');

  useEffect(() => {
    if (!matchId) {
      setStatus('loading');
      return;
    }

    const checkVideo = async () => {
      setStatus('loading');
      try {
        const response = await fetch(`${BACKEND_URL}/api/v1/videos/${matchId}/output`);
        const result = await response.json();
        
        if (result.status === 'ready') {
          // Use the streaming endpoint URL instead of local file path
          setVideoPath(`${BACKEND_URL}/api/v1/videos/${matchId}/output/video`);
          setStatus('ready');
        } else {
          setStatus('processing');
          // Poll every 5 seconds
          setTimeout(checkVideo, 5000);
        }
      } catch {
        setStatus('error');
      }
    };

    checkVideo();
  }, [matchId]);

  if (status === 'loading' || status === 'processing') {
    return (
      <Card className="p-8 shadow-xl border-2 border-sky-200">
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-12 h-12 animate-spin text-sky-600 mb-4" />
          <p className="text-lg text-gray-600">
            {status === 'loading' ? 'Lade Video...' : 'Warte auf verarbeitetes Video...'}
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Das Video wird nach der Pipeline-Verarbeitung verfügbar sein.
          </p>
        </div>
      </Card>
    );
  }

  if (status === 'error' || !videoPath) {
    return (
      <Card className="p-8 shadow-xl border-2 border-red-200">
        <div className="flex flex-col items-center justify-center py-12">
          <Video className="w-12 h-12 text-red-400 mb-4" />
          <p className="text-lg text-gray-600">Video nicht verfügbar</p>
          <p className="text-sm text-gray-500 mt-2">
            Das Output-Video wurde noch nicht generiert.
          </p>
        </div>
      </Card>
    );
  }

  // Convert file path to URL for video player
  const videoUrl = `http://localhost:8000/api/v1/videos/${matchId}/output/video`;

  return (
    <Card className="p-8 shadow-xl border-2 border-sky-200">
      <h3 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <Video className="w-6 h-6 text-sky-600" />
        Output Video
      </h3>
      <p className="text-gray-600 mb-6">
        Das annotierte Video mit Bounding Boxes und Spieler-Tracking.
      </p>
      <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
        <video
          controls
          className="w-full h-full"
          src={videoPath}
        >
          Ihr Browser unterstützt das Video-Element nicht.
        </video>
      </div>
    </Card>
  );
}

export function AnalysisResults({ data, videoName, matchId }: AnalysisResultsProps) {
  const shotAccuracy = ((data.successfulShots / data.totalShots) * 100).toFixed(1);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <motion.div 
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <motion.div 
        className="flex items-center justify-between bg-gradient-to-r from-blue-900 via-sky-600 to-orange-500 p-6 rounded-2xl shadow-2xl text-white"
        variants={itemVariants}
      >
        <div>
          <h2 className="text-3xl font-bold flex items-center gap-3">
            <Award className="w-8 h-8" />
            Match-Report Overview
          </h2>
          <p className="text-blue-100 mt-1">{videoName}</p>
        </div>
        <Badge variant="outline" className="text-lg bg-white text-blue-900 border-0 px-4 py-2">
          <Clock className="w-4 h-4 mr-2" />
          {Math.floor(data.duration / 60)}:{(data.duration % 60).toString().padStart(2, '0')} Min
        </Badge>
      </motion.div>

      {/* Key Metrics */}
      <motion.div 
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
        variants={containerVariants}
      >
        <motion.div variants={itemVariants}>
          <Card className="p-6 hover:shadow-xl transition-all border-2 border-transparent hover:border-sky-400 bg-gradient-to-br from-sky-50 to-white">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-sky-500 to-blue-700 rounded-xl shadow-lg">
                <Camera className="w-7 h-7 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600 font-medium">Frames extrahiert</p>
                <p className="text-3xl font-bold text-sky-600">{data.framesExtracted.toLocaleString()}</p>
              </div>
            </div>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card className="p-6 hover:shadow-xl transition-all border-2 border-transparent hover:border-blue-400 bg-gradient-to-br from-blue-50 to-white">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-blue-600 to-blue-900 rounded-xl shadow-lg">
                <Users className="w-7 h-7 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600 font-medium">Spieler erkannt</p>
                <p className="text-3xl font-bold text-blue-700">{data.playersDetected}</p>
              </div>
            </div>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card className="p-6 hover:shadow-xl transition-all border-2 border-transparent hover:border-orange-400 bg-gradient-to-br from-orange-50 to-white">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-orange-500 to-orange-700 rounded-xl shadow-lg">
                <Target className="w-7 h-7 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600 font-medium">Ball-Detektion</p>
                <p className="text-3xl font-bold text-orange-600">{data.ballDetectionRate}%</p>
              </div>
            </div>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card className="p-6 hover:shadow-xl transition-all border-2 border-transparent hover:border-green-400 bg-gradient-to-br from-green-50 to-white">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-green-500 to-green-700 rounded-xl shadow-lg">
                <TrendingUp className="w-7 h-7 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600 font-medium">Trefferquote</p>
                <p className="text-3xl font-bold text-green-600">{shotAccuracy}%</p>
              </div>
            </div>
          </Card>
        </motion.div>
      </motion.div>

      {/* Team Colors and Possession */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-6 border-2 border-sky-200 shadow-lg">
          <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-sky-600" />
            Teameinteilung (K-Means Clustering)
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg border-2 border-red-200">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-red-500 rounded-full border-2 border-red-700"></div>
                <span className="font-semibold">Team A</span>
              </div>
              <Badge className="bg-red-500">Trikot: {data.teamAColor}</Badge>
            </div>
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border-2 border-blue-200">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full border-2 border-blue-700"></div>
                <span className="font-semibold">Team B</span>
              </div>
              <Badge className="bg-blue-500">Trikot: {data.teamBColor}</Badge>
            </div>
          </div>
        </Card>

        <Card className="p-6 border-2 border-sky-200 shadow-lg">
          <h3 className="font-bold text-lg mb-4">Ballbesitz-Verteilung</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="font-semibold text-red-600">Team A</span>
                <span className="font-bold text-red-600">{data.possession.teamA}%</span>
              </div>
              <div className="h-6 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-red-500 to-red-600 rounded-full"
                  style={{ width: `${data.possession.teamA}%` }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="font-semibold text-blue-600">Team B</span>
                <span className="font-bold text-blue-600">{data.possession.teamB}%</span>
              </div>
              <div className="h-6 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full"
                  style={{ width: `${data.possession.teamB}%` }}
                ></div>
              </div>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Detailed Analysis Tabs */}
      <motion.div variants={itemVariants}>
        <Tabs defaultValue="quality" className="w-full">
          <TabsList className="grid w-full grid-cols-7 bg-gradient-to-r from-blue-100 to-orange-100 p-1 rounded-xl">
            <TabsTrigger value="quality" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-md">
              <CheckCircle2 className="w-4 h-4 mr-2" />
              Qualität
            </TabsTrigger>
            <TabsTrigger value="formations" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-md">
              <Shield className="w-4 h-4 mr-2" />
              Abwehr
            </TabsTrigger>
            <TabsTrigger value="offense" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-md">
              <Play className="w-4 h-4 mr-2" />
              Angriff
            </TabsTrigger>
            <TabsTrigger value="shots" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-md">
              <BarChart3 className="w-4 h-4 mr-2" />
              Würfe
            </TabsTrigger>
            <TabsTrigger value="players" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-md">
              <Zap className="w-4 h-4 mr-2" />
              Spieler
            </TabsTrigger>
            <TabsTrigger value="heatmap" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-md">
              <MapPin className="w-4 h-4 mr-2" />
              Heatmap
            </TabsTrigger>
            <TabsTrigger value="output" className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-md">
              <Video className="w-4 h-4 mr-2" />
              Output Video
            </TabsTrigger>
          </TabsList>

          <TabsContent value="quality" className="mt-6">
            <Card className="shadow-xl border-2 border-green-200">
              <div className="p-8">
                <h3 className="text-2xl font-bold mb-2 flex items-center gap-2">
                  <CheckCircle2 className="w-6 h-6 text-green-600" />
                  Qualitätsmetriken (Abnahmekriterien)
                </h3>
                <p className="text-gray-600 mb-6">Erfüllung der definierten Mindestanforderungen gemäß Abnahmekatalog</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* 3.1 Spielererkennung */}
                  <motion.div
                    className="p-6 rounded-xl border-2 bg-gradient-to-br from-green-50 to-white"
                    style={{
                      borderColor: data.qualityMetrics.playerDetectionRate >= 80 ? 'rgb(34 197 94)' : 'rgb(239 68 68)'
                    }}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="font-bold text-lg mb-1">Spielererkennung</h4>
                        <p className="text-sm text-gray-600">Anforderung 3.1: ≥ 80%</p>
                      </div>
                      {data.qualityMetrics.playerDetectionRate >= 80 ? (
                        <CheckCircle2 className="w-8 h-8 text-green-600" />
                      ) : (
                        <div className="w-8 h-8 text-red-600 font-bold text-2xl">⚠</div>
                      )}
                    </div>
                    <div className="mb-3">
                      <div className="flex justify-between mb-1">
                        <span className="text-sm font-medium">Erkennungsrate:</span>
                        <span className="font-bold">{data.qualityMetrics.playerDetectionRate}%</span>
                      </div>
                      <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${data.qualityMetrics.playerDetectionRate}%`,
                            background: data.qualityMetrics.playerDetectionRate >= 80
                              ? 'linear-gradient(to right, rgb(34 197 94), rgb(22 163 74))'
                              : 'linear-gradient(to right, rgb(239 68 68), rgb(220 38 38))'
                          }}
                        ></div>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      Anteil der erkannten Spieler mit stabiler Bounding-Box über die gesamte Sequenz
                    </p>
                    <Badge className={data.qualityMetrics.playerDetectionRate >= 80 ? 'bg-green-600 mt-3' : 'bg-red-600 mt-3'}>
                      {data.qualityMetrics.playerDetectionRate >= 80 ? '✓ Erfüllt' : '✗ Nicht erfüllt'}
                    </Badge>
                  </motion.div>

                  {/* 3.2 Teameinteilung */}
                  <motion.div
                    className="p-6 rounded-xl border-2 bg-gradient-to-br from-blue-50 to-white"
                    style={{
                      borderColor: data.qualityMetrics.teamClassificationAccuracy >= 85 ? 'rgb(34 197 94)' : 'rgb(239 68 68)'
                    }}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.2 }}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="font-bold text-lg mb-1">Teameinteilung</h4>
                        <p className="text-sm text-gray-600">Anforderung 3.2: ≥ 85%</p>
                      </div>
                      {data.qualityMetrics.teamClassificationAccuracy >= 85 ? (
                        <CheckCircle2 className="w-8 h-8 text-green-600" />
                      ) : (
                        <div className="w-8 h-8 text-red-600 font-bold text-2xl">⚠</div>
                      )}
                    </div>
                    <div className="mb-3">
                      <div className="flex justify-between mb-1">
                        <span className="text-sm font-medium">Klassifizierungsgenauigkeit:</span>
                        <span className="font-bold">{data.qualityMetrics.teamClassificationAccuracy}%</span>
                      </div>
                      <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${data.qualityMetrics.teamClassificationAccuracy}%`,
                            background: data.qualityMetrics.teamClassificationAccuracy >= 85
                              ? 'linear-gradient(to right, rgb(34 197 94), rgb(22 163 74))'
                              : 'linear-gradient(to right, rgb(239 68 68), rgb(220 38 38))'
                          }}
                        ></div>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      K-Means Clustering Genauigkeit bei der automatischen Teamzuordnung anhand Trikotfarben
                    </p>
                    <Badge className={data.qualityMetrics.teamClassificationAccuracy >= 85 ? 'bg-green-600 mt-3' : 'bg-red-600 mt-3'}>
                      {data.qualityMetrics.teamClassificationAccuracy >= 85 ? '✓ Erfüllt' : '✗ Nicht erfüllt'}
                    </Badge>
                  </motion.div>

                  {/* 3.3 Formationsklassifizierung */}
                  <motion.div
                    className="p-6 rounded-xl border-2 bg-gradient-to-br from-sky-50 to-white"
                    style={{
                      borderColor: data.qualityMetrics.formationAccuracy >= 75 ? 'rgb(34 197 94)' : 'rgb(239 68 68)'
                    }}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.3 }}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="font-bold text-lg mb-1">Formationsklassifizierung</h4>
                        <p className="text-sm text-gray-600">Anforderung 3.3: ≥ 75%</p>
                      </div>
                      {data.qualityMetrics.formationAccuracy >= 75 ? (
                        <CheckCircle2 className="w-8 h-8 text-green-600" />
                      ) : (
                        <div className="w-8 h-8 text-red-600 font-bold text-2xl">⚠</div>
                      )}
                    </div>
                    <div className="mb-3">
                      <div className="flex justify-between mb-1">
                        <span className="text-sm font-medium">Trefferquote:</span>
                        <span className="font-bold">{data.qualityMetrics.formationAccuracy}%</span>
                      </div>
                      <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${data.qualityMetrics.formationAccuracy}%`,
                            background: data.qualityMetrics.formationAccuracy >= 75
                              ? 'linear-gradient(to right, rgb(34 197 94), rgb(22 163 74))'
                              : 'linear-gradient(to right, rgb(239 68 68), rgb(220 38 38))'
                          }}
                        ></div>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      Genauigkeit bei der Erkennung von Abwehrformationen (6:0, 5:1, 3:2:1) in statischen Phasen
                    </p>
                    <Badge className={data.qualityMetrics.formationAccuracy >= 75 ? 'bg-green-600 mt-3' : 'bg-red-600 mt-3'}>
                      {data.qualityMetrics.formationAccuracy >= 75 ? '✓ Erfüllt' : '✗ Nicht erfüllt'}
                    </Badge>
                  </motion.div>

                  {/* Spielfeld-Erkennung (Bonus) */}
                  <motion.div
                    className="p-6 rounded-xl border-2 border-orange-200 bg-gradient-to-br from-orange-50 to-white"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.4 }}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="font-bold text-lg mb-1">Spielfeld-Erkennung</h4>
                        <p className="text-sm text-gray-600">Zusätzliche Metrik (Anforderung 2.1)</p>
                      </div>
                      <CheckCircle2 className="w-8 h-8 text-green-600" />
                    </div>
                    <div className="mb-3">
                      <div className="flex justify-between mb-1">
                        <span className="text-sm font-medium">Erkennungskonf idenz:</span>
                        <span className="font-bold">{data.qualityMetrics.fieldDetectionConfidence}%</span>
                      </div>
                      <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-orange-500 to-orange-600 rounded-full"
                          style={{ width: `${data.qualityMetrics.fieldDetectionConfidence}%` }}
                        ></div>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      Konfidenz der automatischen Spielfeld-Erkennung zur Kontextualisierung der Spielerdaten
                    </p>
                    <Badge className="bg-orange-600 mt-3">
                      ✓ Erfolgreich
                    </Badge>
                  </motion.div>
                </div>

                {/* Gesamtstatus */}
                <motion.div
                  className="mt-8 p-6 rounded-xl border-2 bg-gradient-to-r from-green-50 to-blue-50"
                  style={{
                    borderColor: data.qualityMetrics.playerDetectionRate >= 80 &&
                                 data.qualityMetrics.teamClassificationAccuracy >= 85 &&
                                 data.qualityMetrics.formationAccuracy >= 75
                      ? 'rgb(34 197 94)'
                      : 'rgb(234 179 8)'
                  }}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xl font-bold mb-2">Gesamtbewertung</h4>
                      <p className="text-gray-600">
                        {data.qualityMetrics.playerDetectionRate >= 80 &&
                         data.qualityMetrics.teamClassificationAccuracy >= 85 &&
                         data.qualityMetrics.formationAccuracy >= 75
                          ? 'Alle Mindestanforderungen aus dem Abnahmekatalog erfüllt'
                          : 'Einige Anforderungen unterschreiten die Mindestwerte'}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-4xl font-bold text-green-600 mb-1">
                        {data.qualityMetrics.playerDetectionRate >= 80 &&
                         data.qualityMetrics.teamClassificationAccuracy >= 85 &&
                         data.qualityMetrics.formationAccuracy >= 75
                          ? '✓'
                          : '⚠'}
                      </div>
                      <Badge className={
                        data.qualityMetrics.playerDetectionRate >= 80 &&
                        data.qualityMetrics.teamClassificationAccuracy >= 85 &&
                        data.qualityMetrics.formationAccuracy >= 75
                          ? 'bg-green-600'
                          : 'bg-yellow-600'
                      }>
                        {data.qualityMetrics.playerDetectionRate >= 80 &&
                         data.qualityMetrics.teamClassificationAccuracy >= 85 &&
                         data.qualityMetrics.formationAccuracy >= 75
                          ? 'Abnahmebereit'
                          : 'Verbesserung empfohlen'}
                      </Badge>
                    </div>
                  </div>
                </motion.div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="formations" className="mt-6">
            <Card className="shadow-xl border-2 border-sky-200">
              <div className="p-8">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  <Shield className="w-6 h-6 text-sky-600" />
                  Klassifizierte Abwehrformationen
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {data.defensiveFormations.map((formation, index) => (
                    <motion.div
                      key={index}
                      className="p-6 rounded-xl border-2 border-sky-200 bg-gradient-to-br from-sky-50 to-white hover:shadow-lg transition-all"
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <div className="text-center">
                        <div className="text-4xl font-bold text-sky-700 mb-2">{formation.formation}</div>
                        <div className="text-gray-600 mb-4">Formation</div>
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Häufigkeit:</span>
                            <Badge className="bg-sky-600">{formation.frequency}x</Badge>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Erfolgsquote:</span>
                            <Badge className="bg-green-600">{formation.successRate}%</Badge>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="offense" className="mt-6">
            <Card className="shadow-xl border-2 border-orange-200">
              <div className="p-8">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  <Play className="w-6 h-6 text-orange-600" />
                  Offensive Spielzüge (Regelbasierte Erkennung)
                </h3>
                <div className="space-y-4">
                  {data.offensivePlays.map((play, index) => (
                    <motion.div
                      key={index}
                      className="p-5 rounded-xl border-2 border-orange-200 bg-gradient-to-r from-orange-50 to-white hover:shadow-lg transition-all"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="text-xl font-bold text-orange-700 mb-2">{play.play}</h4>
                          <div className="flex gap-4">
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-600">Häufigkeit:</span>
                              <Badge className="bg-orange-600">{play.frequency}x</Badge>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-600">Erfolgsquote:</span>
                              <Badge className="bg-green-600">{play.successRate}%</Badge>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-4xl font-bold text-orange-600">{play.frequency}</div>
                          <div className="text-sm text-gray-500">Gesamt</div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="shots" className="mt-6">
            <Card className="shadow-xl border-2 border-blue-200">
              <div className="p-8">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  <Target className="w-6 h-6 text-blue-600" />
                  Abschlussaktionen nach Position
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="p-6 rounded-xl border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-white">
                    <h4 className="text-lg font-bold mb-4 text-blue-700">Rückraum</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Versuche:</span>
                        <span className="font-bold">{data.shotPositions.rueckraum.attempts}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Tore:</span>
                        <span className="font-bold text-green-600">{data.shotPositions.rueckraum.goals}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Quote:</span>
                        <Badge className="bg-green-600">
                          {((data.shotPositions.rueckraum.goals / data.shotPositions.rueckraum.attempts) * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="p-6 rounded-xl border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-white">
                    <h4 className="text-lg font-bold mb-4 text-blue-700">Kreis</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Versuche:</span>
                        <span className="font-bold">{data.shotPositions.kreis.attempts}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Tore:</span>
                        <span className="font-bold text-green-600">{data.shotPositions.kreis.goals}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Quote:</span>
                        <Badge className="bg-green-600">
                          {((data.shotPositions.kreis.goals / data.shotPositions.kreis.attempts) * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="p-6 rounded-xl border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-white">
                    <h4 className="text-lg font-bold mb-4 text-blue-700">Außen Links</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Versuche:</span>
                        <span className="font-bold">{data.shotPositions.aussenLinks.attempts}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Tore:</span>
                        <span className="font-bold text-green-600">{data.shotPositions.aussenLinks.goals}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Quote:</span>
                        <Badge className="bg-green-600">
                          {((data.shotPositions.aussenLinks.goals / data.shotPositions.aussenLinks.attempts) * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="p-6 rounded-xl border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-white">
                    <h4 className="text-lg font-bold mb-4 text-blue-700">Außen Rechts</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Versuche:</span>
                        <span className="font-bold">{data.shotPositions.aussenRechts.attempts}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Tore:</span>
                        <span className="font-bold text-green-600">{data.shotPositions.aussenRechts.goals}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Quote:</span>
                        <Badge className="bg-green-600">
                          {((data.shotPositions.aussenRechts.goals / data.shotPositions.aussenRechts.attempts) * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="players" className="mt-6">
            <Card className="shadow-xl border-2 border-sky-200">
              <div className="p-8">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                  <Zap className="w-6 h-6 text-sky-600" />
                  Top Spieler
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b-2 border-sky-200 bg-sky-50">
                        <th className="text-left py-4 px-4 font-bold">Spieler</th>
                        <th className="text-center py-4 px-4 font-bold">Team</th>
                        <th className="text-center py-4 px-4 font-bold">Würfe</th>
                        <th className="text-center py-4 px-4 font-bold">Tore</th>
                        <th className="text-center py-4 px-4 font-bold">Assists</th>
                        <th className="text-center py-4 px-4 font-bold">Distanz (m)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.playerStats.map((player, index) => (
                        <motion.tr 
                          key={player.id} 
                          className="border-b hover:bg-sky-50 transition-colors"
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 }}
                        >
                          <td className="py-4 px-4 font-semibold">{player.name}</td>
                          <td className="text-center py-4 px-4">
                            <Badge className={player.team === 'A' ? 'bg-red-500' : 'bg-blue-500'}>
                              Team {player.team}
                            </Badge>
                          </td>
                          <td className="text-center py-4 px-4">{player.shots}</td>
                          <td className="text-center py-4 px-4">
                            <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium">
                              {player.goals}
                            </span>
                          </td>
                          <td className="text-center py-4 px-4">{player.assists}</td>
                          <td className="text-center py-4 px-4">{player.distance.toFixed(0)}</td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="heatmap" className="mt-6">
            <Card className="shadow-xl border-2 border-orange-200">
              <div className="p-8">
                <h3 className="text-2xl font-bold mb-6">Aktivitäts-Heatmap</h3>
                <div className="grid grid-cols-3 gap-6">
                  {data.heatmapData.map((zone, index) => (
                    <motion.div
                      key={index}
                      className="p-8 rounded-2xl border-2 flex flex-col items-center justify-center gap-3 shadow-lg hover:shadow-2xl transition-all"
                      style={{
                        backgroundColor: `rgba(14, 116, 144, ${zone.intensity / 100})`,
                        borderColor: `rgba(14, 116, 144, ${Math.min(1, zone.intensity / 50)})`,
                        color: zone.intensity > 50 ? 'white' : '#1e3a5f'
                      }}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.1 }}
                      whileHover={{ scale: 1.05 }}
                    >
                      <MapPin className="w-8 h-8" />
                      <p className="font-bold text-lg text-center">{zone.zone}</p>
                      <p className="text-2xl font-bold">{zone.intensity}%</p>
                      <p className="text-sm">Aktivität</p>
                    </motion.div>
                  ))}
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="output" className="mt-6">
            <OutputVideoTab matchId={matchId} />
          </TabsContent>
        </Tabs>
      </motion.div>
    </motion.div>
  );
}