/**
 * Leaderboard Component for AirportWaze
 * Displays user rankings with different time periods and filtering options
 */

import React, { useEffect, useState } from 'react';
import {
  Trophy,
  Medal,
  TrendingUp,
  Clock,
  Users,
  Crown,
  Award,
  ChevronUp,
  ChevronDown,
  RefreshCw
} from 'lucide-react';

// Types
type LeaderboardPeriod = 'daily' | 'weekly' | 'monthly' | 'all_time';
type LeaderboardMetric = 'xp' | 'distance' | 'checkpoints' | 'airports';

interface LeaderboardUser {
  rank: number;
  user_id: number;
  username?: string;
  level: number;
  title: string;
  avatar_url?: string;
  avatar_frame: string;
  score: number;
  previous_rank?: number;
}

interface LeaderboardProps {
  currentUserId: number;
  initialPeriod?: LeaderboardPeriod;
  initialMetric?: LeaderboardMetric;
}

const Leaderboard: React.FC<LeaderboardProps> = ({
  currentUserId,
  initialPeriod = 'weekly',
  initialMetric = 'xp'
}) => {
  const [leaderboardData, setLeaderboardData] = useState<LeaderboardUser[]>([]);
  const [currentUserRank, setCurrentUserRank] = useState<LeaderboardUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<LeaderboardPeriod>(initialPeriod);
  const [metric, setMetric] = useState<LeaderboardMetric>(initialMetric);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    fetchLeaderboard();
  }, [period, metric]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/gamification/leaderboard?period=${period}&metric=${metric}&limit=100`
      );

      if (!response.ok) throw new Error('Failed to fetch leaderboard');

      const data = await response.json();
      setLeaderboardData(data.rankings);
      setCurrentUserRank(data.current_user);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching leaderboard:', err);
      // Mock data for development
      setLeaderboardData(getMockLeaderboard());
      setCurrentUserRank(getMockCurrentUser(currentUserId));
    } finally {
      setLoading(false);
    }
  };

  const getPeriodLabel = (p: LeaderboardPeriod): string => {
    switch (p) {
      case 'daily': return 'Today';
      case 'weekly': return 'This Week';
      case 'monthly': return 'This Month';
      case 'all_time': return 'All Time';
    }
  };

  const getMetricLabel = (m: LeaderboardMetric): string => {
    switch (m) {
      case 'xp': return 'XP';
      case 'distance': return 'Distance (km)';
      case 'checkpoints': return 'Checkpoints';
      case 'airports': return 'Airports';
    }
  };

  const formatScore = (score: number, m: LeaderboardMetric): string => {
    if (m === 'distance') {
      return `${score.toFixed(1)} km`;
    }
    return score.toLocaleString();
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Crown className="text-yellow-400" size={28} />;
      case 2:
        return <Medal className="text-gray-400" size={28} />;
      case 3:
        return <Medal className="text-orange-400" size={28} />;
      default:
        return <span className="text-lg font-bold text-gray-600">#{rank}</span>;
    }
  };

  const getRankChange = (user: LeaderboardUser) => {
    if (!user.previous_rank) return null;

    const change = user.previous_rank - user.rank;
    if (change > 0) {
      return (
        <div className="flex items-center gap-1 text-green-600 text-sm font-medium">
          <ChevronUp size={16} />
          <span>+{change}</span>
        </div>
      );
    } else if (change < 0) {
      return (
        <div className="flex items-center gap-1 text-red-600 text-sm font-medium">
          <ChevronDown size={16} />
          <span>{change}</span>
        </div>
      );
    }
    return <span className="text-gray-400 text-sm">-</span>;
  };

  const getFrameColor = (frame: string): string => {
    switch (frame) {
      case 'gold': return 'border-yellow-400';
      case 'silver': return 'border-gray-300';
      case 'bronze': return 'border-orange-400';
      default: return 'border-blue-400';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading leaderboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
                <Trophy size={36} />
                Leaderboard
              </h1>
              <p className="text-blue-100">Compete with travelers worldwide</p>
            </div>
            <button
              onClick={fetchLeaderboard}
              className="bg-white/20 hover:bg-white/30 backdrop-blur-sm px-4 py-2 rounded-lg flex items-center gap-2 transition"
            >
              <RefreshCw size={18} />
              Refresh
            </button>
          </div>

          {/* Current User Rank */}
          {currentUserRank && (
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 mb-4">
              <p className="text-sm text-blue-100 mb-2">Your Rank</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="text-2xl font-bold">#{currentUserRank.rank}</div>
                  <div>
                    <p className="font-semibold">Level {currentUserRank.level}</p>
                    <p className="text-sm text-blue-100">{currentUserRank.title}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold">{formatScore(currentUserRank.score, metric)}</p>
                  {getRankChange(currentUserRank)}
                </div>
              </div>
            </div>
          )}

          {/* Period Selector */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            <PeriodButton
              active={period === 'daily'}
              onClick={() => setPeriod('daily')}
              icon={<Clock size={16} />}
              label="Daily"
            />
            <PeriodButton
              active={period === 'weekly'}
              onClick={() => setPeriod('weekly')}
              icon={<Clock size={16} />}
              label="Weekly"
            />
            <PeriodButton
              active={period === 'monthly'}
              onClick={() => setPeriod('monthly')}
              icon={<Clock size={16} />}
              label="Monthly"
            />
            <PeriodButton
              active={period === 'all_time'}
              onClick={() => setPeriod('all_time')}
              icon={<Trophy size={16} />}
              label="All Time"
            />
          </div>
        </div>
      </div>

      {/* Metric Selector */}
      <div className="bg-white border-b sticky top-0 z-10 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex gap-2 overflow-x-auto">
            <MetricButton
              active={metric === 'xp'}
              onClick={() => setMetric('xp')}
              label="Total XP"
              icon="⭐"
            />
            <MetricButton
              active={metric === 'distance'}
              onClick={() => setMetric('distance')}
              label="Distance"
              icon="📏"
            />
            <MetricButton
              active={metric === 'checkpoints'}
              onClick={() => setMetric('checkpoints')}
              label="Checkpoints"
              icon="📍"
            />
            <MetricButton
              active={metric === 'airports'}
              onClick={() => setMetric('airports')}
              label="Airports"
              icon="✈️"
            />
          </div>
        </div>
      </div>

      {/* Leaderboard List */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Top 3 Podium */}
        {leaderboardData.length >= 3 && (
          <div className="mb-8">
            <div className="flex items-end justify-center gap-4 mb-6">
              {/* 2nd Place */}
              <PodiumCard user={leaderboardData[1]} rank={2} metric={metric} />

              {/* 1st Place */}
              <PodiumCard user={leaderboardData[0]} rank={1} metric={metric} isFirst />

              {/* 3rd Place */}
              <PodiumCard user={leaderboardData[2]} rank={3} metric={metric} />
            </div>
          </div>
        )}

        {/* Rankings List */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 bg-gray-50 border-b">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-800 flex items-center gap-2">
                <Users size={20} />
                {getPeriodLabel(period)} Rankings
              </h2>
              <p className="text-sm text-gray-600">
                Updated {lastUpdated.toLocaleTimeString()}
              </p>
            </div>
          </div>

          <div className="divide-y">
            {leaderboardData.slice(3).map((user) => (
              <LeaderboardRow
                key={user.user_id}
                user={user}
                metric={metric}
                isCurrentUser={user.user_id === currentUserId}
              />
            ))}

            {leaderboardData.length === 0 && (
              <div className="text-center py-12">
                <Trophy className="mx-auto mb-4 text-gray-300" size={64} />
                <p className="text-gray-600">No rankings available yet</p>
                <p className="text-gray-400 text-sm">Be the first to compete!</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-6 text-center text-sm text-gray-600">
          <p>Rankings update every hour</p>
          <p className="mt-1">Keep traveling to climb the leaderboard!</p>
        </div>
      </div>
    </div>
  );
};

// Period Button Component
interface PeriodButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}

const PeriodButton: React.FC<PeriodButtonProps> = ({ active, onClick, icon, label }) => {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition whitespace-nowrap ${
        active
          ? 'bg-white text-blue-600 shadow-md'
          : 'bg-white/20 text-white hover:bg-white/30'
      }`}
    >
      {icon}
      {label}
    </button>
  );
};

// Metric Button Component
interface MetricButtonProps {
  active: boolean;
  onClick: () => void;
  label: string;
  icon: string;
}

const MetricButton: React.FC<MetricButtonProps> = ({ active, onClick, label, icon }) => {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition whitespace-nowrap ${
        active
          ? 'bg-blue-600 text-white shadow-md'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      <span>{icon}</span>
      {label}
    </button>
  );
};

// Podium Card Component
interface PodiumCardProps {
  user: LeaderboardUser;
  rank: number;
  metric: LeaderboardMetric;
  isFirst?: boolean;
}

const PodiumCard: React.FC<PodiumCardProps> = ({ user, rank, metric, isFirst = false }) => {
  const formatScore = (score: number, m: LeaderboardMetric): string => {
    if (m === 'distance') {
      return `${score.toFixed(1)} km`;
    }
    return score.toLocaleString();
  };

  const getFrameColor = (frame: string): string => {
    switch (frame) {
      case 'gold': return 'border-yellow-400';
      case 'silver': return 'border-gray-300';
      case 'bronze': return 'border-orange-400';
      default: return 'border-blue-400';
    }
  };

  const getPodiumColor = (r: number): string => {
    switch (r) {
      case 1: return 'from-yellow-400 to-orange-500';
      case 2: return 'from-gray-300 to-gray-400';
      case 3: return 'from-orange-400 to-orange-500';
      default: return 'from-gray-200 to-gray-300';
    }
  };

  return (
    <div className={`flex flex-col items-center ${isFirst ? 'scale-110' : ''}`}>
      <div className="relative mb-3">
        <div className={`w-20 h-20 rounded-full border-4 ${getFrameColor(user.avatar_frame)} overflow-hidden bg-gradient-to-br ${getPodiumColor(rank)}`}>
          {user.avatar_url ? (
            <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-2xl font-bold text-white">
              {user.user_id.toString().slice(0, 2)}
            </div>
          )}
        </div>
        <div className={`absolute -top-2 -right-2 w-8 h-8 rounded-full bg-gradient-to-br ${getPodiumColor(rank)} flex items-center justify-center shadow-lg`}>
          {rank === 1 && <Crown className="text-white" size={18} />}
          {rank === 2 && <Medal className="text-white" size={18} />}
          {rank === 3 && <Medal className="text-white" size={18} />}
        </div>
      </div>
      <div className="text-center">
        <p className="font-semibold text-gray-800 text-sm mb-1">Level {user.level}</p>
        <p className="text-xs text-gray-600 mb-2">{user.title}</p>
        <div className={`bg-gradient-to-r ${getPodiumColor(rank)} text-white px-3 py-1 rounded-full font-bold text-sm`}>
          {formatScore(user.score, metric)}
        </div>
      </div>
    </div>
  );
};

// Leaderboard Row Component
interface LeaderboardRowProps {
  user: LeaderboardUser;
  metric: LeaderboardMetric;
  isCurrentUser: boolean;
}

const LeaderboardRow: React.FC<LeaderboardRowProps> = ({ user, metric, isCurrentUser }) => {
  const formatScore = (score: number, m: LeaderboardMetric): string => {
    if (m === 'distance') {
      return `${score.toFixed(1)} km`;
    }
    return score.toLocaleString();
  };

  const getFrameColor = (frame: string): string => {
    switch (frame) {
      case 'gold': return 'border-yellow-400';
      case 'silver': return 'border-gray-300';
      case 'bronze': return 'border-orange-400';
      default: return 'border-blue-400';
    }
  };

  const getRankChange = (user: LeaderboardUser) => {
    if (!user.previous_rank) return null;

    const change = user.previous_rank - user.rank;
    if (change > 0) {
      return (
        <div className="flex items-center gap-1 text-green-600 text-xs font-medium">
          <ChevronUp size={14} />
          <span>{change}</span>
        </div>
      );
    } else if (change < 0) {
      return (
        <div className="flex items-center gap-1 text-red-600 text-xs font-medium">
          <ChevronDown size={14} />
          <span>{Math.abs(change)}</span>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`p-4 hover:bg-gray-50 transition ${isCurrentUser ? 'bg-blue-50' : ''}`}>
      <div className="flex items-center gap-4">
        {/* Rank */}
        <div className="w-12 text-center">
          <div className="text-lg font-bold text-gray-700">#{user.rank}</div>
          {getRankChange(user)}
        </div>

        {/* Avatar */}
        <div className={`w-12 h-12 rounded-full border-2 ${getFrameColor(user.avatar_frame)} overflow-hidden bg-gradient-to-br from-blue-400 to-purple-500`}>
          {user.avatar_url ? (
            <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-lg font-bold text-white">
              {user.user_id.toString().slice(0, 2)}
            </div>
          )}
        </div>

        {/* User Info */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <p className="font-semibold text-gray-800">
              Level {user.level}
              {isCurrentUser && <span className="ml-2 text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full">You</span>}
            </p>
          </div>
          <p className="text-sm text-gray-600">{user.title}</p>
        </div>

        {/* Score */}
        <div className="text-right">
          <p className="text-lg font-bold text-gray-800">{formatScore(user.score, metric)}</p>
        </div>
      </div>
    </div>
  );
};

// Mock data generator
const getMockLeaderboard = (): LeaderboardUser[] => {
  const titles = ['Airport Master', 'Sky Navigator', 'Travel Expert', 'Journey Guru', 'Airport Explorer'];
  const frames = ['gold', 'silver', 'bronze', 'default', 'default'];

  return Array.from({ length: 20 }, (_, i) => ({
    rank: i + 1,
    user_id: 1000 + i,
    level: Math.floor(Math.random() * 30) + 1,
    title: titles[Math.floor(Math.random() * titles.length)],
    avatar_frame: i < 3 ? frames[i] : 'default',
    score: Math.floor(Math.random() * 10000) + (20 - i) * 500,
    previous_rank: i > 0 ? i + Math.floor(Math.random() * 5) - 2 : undefined
  }));
};

const getMockCurrentUser = (userId: number): LeaderboardUser => {
  return {
    rank: 42,
    user_id: userId,
    level: 12,
    title: 'Airport Navigator',
    avatar_frame: 'gold',
    score: 3450,
    previous_rank: 45
  };
};

export default Leaderboard;
