import { useState, useMemo } from 'react';
import { motion } from 'motion/react';
import { Upload, BarChart3, Users, TrendingUp, Calendar, Clock, Target, Award, Search, Filter, Video, Activity } from 'lucide-react';
import { Button } from './ui/button';
import logoImg from '../../imports/Logo.png';

interface MatchReport {
  id: string;
  fileName: string;
  date: string;
  duration: string;
  playersDetected: number;
  totalShots: number;
  successRate: number;
  thumbnail: string;
  teams: {
    teamA: string;
    teamB: string;
    score: string;
  };
}

interface DashboardProps {
  onNewUpload: () => void;
  onViewMatch: (matchId: string, data: any, fileName: string) => void;
}

const mockMatches: MatchReport[] = [
  {
    id: '1',
    fileName: 'Heimspiel_vs_TSV_Mannheim.mp4',
    date: '2026-04-15',
    duration: '54:07',
    playersDetected: 14,
    totalShots: 42,
    successRate: 67,
    thumbnail: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=225&fit=crop',
    teams: {
      teamA: 'Rot',
      teamB: 'Blau',
      score: '28:24'
    }
  },
  {
    id: '2',
    fileName: 'Auswärtsspiel_Rhein_Neckar.mp4',
    date: '2026-04-12',
    duration: '51:34',
    playersDetected: 14,
    totalShots: 38,
    successRate: 63,
    thumbnail: 'https://images.unsplash.com/photo-1612872087720-bb876e2e67d1?w=400&h=225&fit=crop',
    teams: {
      teamA: 'Grün',
      teamB: 'Weiß',
      score: '25:27'
    }
  },
  {
    id: '3',
    fileName: 'Training_Taktik_Session.mp4',
    date: '2026-04-10',
    duration: '48:22',
    playersDetected: 12,
    totalShots: 31,
    successRate: 71,
    thumbnail: 'https://images.unsplash.com/photo-1606925797300-0b35e9d1794e?w=400&h=225&fit=crop',
    teams: {
      teamA: 'Rot',
      teamB: 'Gelb',
      score: '22:19'
    }
  },
  {
    id: '4',
    fileName: 'Pokalspiel_Viertelfinale.mp4',
    date: '2026-04-08',
    duration: '56:45',
    playersDetected: 14,
    totalShots: 47,
    successRate: 64,
    thumbnail: 'https://images.unsplash.com/photo-1551958219-acbc608c6377?w=400&h=225&fit=crop',
    teams: {
      teamA: 'Blau',
      teamB: 'Schwarz',
      score: '30:29'
    }
  },
  {
    id: '5',
    fileName: 'Ligaspiel_HC_Stuttgart.mp4',
    date: '2026-04-05',
    duration: '52:18',
    playersDetected: 14,
    totalShots: 40,
    successRate: 70,
    thumbnail: 'https://images.unsplash.com/photo-1589487391730-58f20eb2c308?w=400&h=225&fit=crop',
    teams: {
      teamA: 'Rot',
      teamB: 'Grün',
      score: '28:25'
    }
  },
  {
    id: '6',
    fileName: 'Derby_Lokalrivale.mp4',
    date: '2026-04-01',
    duration: '55:12',
    playersDetected: 14,
    totalShots: 44,
    successRate: 66,
    thumbnail: 'https://images.unsplash.com/photo-1551958219-acbc608c6377?w=400&h=225&fit=crop',
    teams: {
      teamA: 'Weiß',
      teamB: 'Rot',
      score: '29:28'
    }
  }
];

function generateMockAnalysis(): any {
  return {
    duration: 3247,
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
      playerDetectionRate: 82,
      teamClassificationAccuracy: 87,
      formationAccuracy: 76,
      fieldDetectionConfidence: 90,
    },
  };
}

const getTeamColor = (color: string): string => {
  const colorMap: { [key: string]: string } = {
    'Rot': 'bg-red-500',
    'Blau': 'bg-blue-500',
    'Grün': 'bg-green-500',
    'Gelb': 'bg-yellow-500',
    'Weiß': 'bg-gray-300',
    'Schwarz': 'bg-gray-900'
  };
  return colorMap[color] || 'bg-gray-500';
};

export function Dashboard({ onNewUpload, onViewMatch }: DashboardProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'name'>('date');

  const totalAnalyses = mockMatches.length;
  const totalVideoMinutes = mockMatches.reduce((acc, m) => {
    const [min, sec] = m.duration.split(':').map(Number);
    return acc + min + (sec / 60);
  }, 0);
  const lastAnalysisDate = mockMatches.length > 0 ? mockMatches[0].date : '';

  const filteredMatches = useMemo(() => {
    let filtered = mockMatches.filter(match =>
      match.fileName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      match.teams.teamA.toLowerCase().includes(searchQuery.toLowerCase()) ||
      match.teams.teamB.toLowerCase().includes(searchQuery.toLowerCase())
    );

    filtered.sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.date).getTime() - new Date(a.date).getTime();
      } else {
        return a.fileName.localeCompare(b.fileName);
      }
    });

    return filtered;
  }, [searchQuery, sortBy]);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <img src={logoImg} alt="SportsVision Logo" className="h-16" />
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-900 via-sky-600 to-orange-500 bg-clip-text text-transparent">
                SportsVision Analytics
              </h1>
              <p className="text-gray-600">Handball Video Intelligence Platform</p>
            </div>
          </div>
          <Button
            onClick={onNewUpload}
            className="bg-gradient-to-r from-blue-900 to-sky-600 hover:from-blue-800 hover:to-sky-500 shadow-lg hover:shadow-xl transition-all"
            size="lg"
          >
            <Upload className="w-5 h-5 mr-2" />
            Neues Video hochladen
          </Button>
        </div>
      </motion.div>

      {/* Quick Stats */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-900">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Analysen gesamt</p>
              <p className="text-3xl font-bold text-gray-900">{totalAnalyses}</p>
            </div>
            <BarChart3 className="w-12 h-12 text-blue-900 opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-sky-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Gesamte Videozeit</p>
              <p className="text-3xl font-bold text-gray-900">{Math.round(totalVideoMinutes)}<span className="text-lg text-gray-600">min</span></p>
            </div>
            <Video className="w-12 h-12 text-sky-600 opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Letzte Analyse</p>
              <p className="text-lg font-bold text-gray-900">{new Date(lastAnalysisDate).toLocaleDateString('de-DE', { day: '2-digit', month: 'short' })}</p>
            </div>
            <Calendar className="w-12 h-12 text-orange-500 opacity-20" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">System-Status</p>
              <p className="text-lg font-bold text-green-600">Aktiv</p>
            </div>
            <Activity className="w-12 h-12 text-green-600 opacity-20" />
          </div>
        </div>
      </motion.div>

      {/* Recent Matches */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Match-Historie</h2>
        </div>

        {/* Search and Filter Bar */}
        <div className="bg-white rounded-xl shadow-lg p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Suche nach Dateiname oder Team..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-600" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'date' | 'name')}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent bg-white"
              >
                <option value="date">Sortieren: Neueste zuerst</option>
                <option value="name">Sortieren: Name A-Z</option>
              </select>
            </div>
          </div>
        </div>

        {filteredMatches.length === 0 ? (
          <div className="text-center py-12">
            <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">Keine Matches gefunden</p>
            <p className="text-gray-400 text-sm mt-2">Versuchen Sie eine andere Suche</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredMatches.map((match, index) => (
            <motion.div
              key={match.id}
              className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-all cursor-pointer group"
              onClick={() => onViewMatch(match.id, generateMockAnalysis(), match.fileName)}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
              whileHover={{ scale: 1.02 }}
            >
              {/* Thumbnail */}
              <div className="relative h-40 overflow-hidden bg-gradient-to-br from-blue-900 to-sky-600">
                <img
                  src={match.thumbnail}
                  alt={match.fileName}
                  className="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-110 transition-all duration-300"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                <div className="absolute bottom-3 left-3 right-3">
                  <p className="text-white font-semibold text-sm truncate">{match.fileName}</p>
                  <div className="flex items-center gap-3 mt-1 text-white/90 text-xs">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {match.duration}
                    </span>
                    <span className="font-bold">{match.teams.score}</span>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${getTeamColor(match.teams.teamA)}`}></div>
                    <span className="text-sm text-gray-700">{match.teams.teamA}</span>
                    <span className="text-xs text-gray-400">vs</span>
                    <div className={`w-3 h-3 rounded-full ${getTeamColor(match.teams.teamB)}`}></div>
                    <span className="text-sm text-gray-700">{match.teams.teamB}</span>
                  </div>
                  <span className="text-xs text-gray-500">{new Date(match.date).toLocaleDateString('de-DE')}</span>
                </div>

                <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-gray-100">
                  <div className="text-center">
                    <p className="text-xs text-gray-500">Spieler</p>
                    <p className="text-sm font-semibold text-gray-900">{match.playersDetected}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500">Würfe</p>
                    <p className="text-sm font-semibold text-gray-900">{match.totalShots}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500">Quote</p>
                    <p className="text-sm font-semibold text-green-600">{match.successRate}%</p>
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-center text-sm text-sky-600 group-hover:text-sky-700 font-medium">
                  Analyse öffnen →
                </div>
              </div>
            </motion.div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Technology Footer */}
      <motion.div
        className="text-center mt-12 text-sm text-gray-500"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.8 }}
      >
        <p>Powered by OpenCV, K-Means Clustering & Deep Learning</p>
      </motion.div>
    </div>
  );
}
