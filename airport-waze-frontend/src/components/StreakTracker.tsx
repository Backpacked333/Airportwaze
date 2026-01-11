/**
 * Streak Tracker Component for AirportWaze
 * Displays daily travel streak with fire icon animation and milestones
 */

import React, { useEffect, useState } from 'react';
import { Flame, Calendar, Award, TrendingUp, Clock, Star, Zap } from 'lucide-react';

// Types
interface StreakData {
  id: number;
  current_streak: number;
  longest_streak: number;
  last_activity_date: string | null;
  streak_start_date: string | null;
  total_active_days: number;
  is_active: boolean;
}

interface StreakMilestone {
  days: number;
  title: string;
  description: string;
  icon: string;
  xp_reward: number;
  unlocked: boolean;
}

interface StreakTrackerProps {
  userId: number;
  compact?: boolean;
  onStreakMilestone?: (milestone: StreakMilestone) => void;
}

const STREAK_MILESTONES: Omit<StreakMilestone, 'unlocked'>[] = [
  {
    days: 3,
    title: 'Getting Started',
    description: '3-day streak',
    icon: '🔥',
    xp_reward: 50
  },
  {
    days: 7,
    title: 'Week Warrior',
    description: '7-day streak',
    icon: '⚡',
    xp_reward: 150
  },
  {
    days: 14,
    title: 'Fortnight Flyer',
    description: '14-day streak',
    icon: '✨',
    xp_reward: 300
  },
  {
    days: 30,
    title: 'Monthly Master',
    description: '30-day streak',
    icon: '🌟',
    xp_reward: 500
  },
  {
    days: 100,
    title: 'Century Traveler',
    description: '100-day streak',
    icon: '💯',
    xp_reward: 1000
  },
  {
    days: 365,
    title: 'Year-Round Navigator',
    description: '365-day streak',
    icon: '👑',
    xp_reward: 5000
  }
];

const StreakTracker: React.FC<StreakTrackerProps> = ({
  userId,
  compact = false,
  onStreakMilestone
}) => {
  const [streakData, setStreakData] = useState<StreakData | null>(null);
  const [milestones, setMilestones] = useState<StreakMilestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [animateFlame, setAnimateFlame] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);

  useEffect(() => {
    fetchStreakData();
  }, [userId]);

  useEffect(() => {
    if (streakData) {
      updateMilestones();
      // Animate flame for active streaks
      if (streakData.is_active && streakData.current_streak > 0) {
        setAnimateFlame(true);
      }
    }
  }, [streakData]);

  const fetchStreakData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/gamification/streak?user_id=${userId}`);
      if (!response.ok) throw new Error('Failed to fetch streak');

      const data = await response.json();
      setStreakData(data);
    } catch (err) {
      console.error('Error fetching streak:', err);
      // Mock data for development
      setStreakData({
        id: 1,
        current_streak: 7,
        longest_streak: 15,
        last_activity_date: new Date().toISOString(),
        streak_start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        total_active_days: 42,
        is_active: true
      });
    } finally {
      setLoading(false);
    }
  };

  const updateMilestones = () => {
    if (!streakData) return;

    const updatedMilestones = STREAK_MILESTONES.map(m => ({
      ...m,
      unlocked: streakData.current_streak >= m.days
    }));

    setMilestones(updatedMilestones);

    // Check if we just hit a milestone
    const justUnlocked = updatedMilestones.find(
      m => m.unlocked && m.days === streakData.current_streak
    );
    if (justUnlocked && onStreakMilestone) {
      onStreakMilestone(justUnlocked);
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 3000);
    }
  };

  const getFlameSize = (streak: number): number => {
    if (streak < 3) return 1;
    if (streak < 7) return 1.2;
    if (streak < 14) return 1.4;
    if (streak < 30) return 1.6;
    if (streak < 100) return 1.8;
    return 2;
  };

  const getFlameColor = (streak: number): string => {
    if (streak < 3) return 'text-orange-400';
    if (streak < 7) return 'text-orange-500';
    if (streak < 14) return 'text-red-500';
    if (streak < 30) return 'text-red-600';
    if (streak < 100) return 'text-purple-500';
    return 'text-yellow-400';
  };

  const getDaysUntilNextMilestone = (): { days: number; milestone: StreakMilestone } | null => {
    if (!streakData) return null;

    const nextMilestone = milestones.find(m => !m.unlocked);
    if (!nextMilestone) return null;

    return {
      days: nextMilestone.days - streakData.current_streak,
      milestone: nextMilestone
    };
  };

  const getStreakWeek = (): boolean[] => {
    if (!streakData) return Array(7).fill(false);

    const today = new Date();
    const weekDays = Array(7).fill(false);

    if (!streakData.last_activity_date) return weekDays;

    const lastActivity = new Date(streakData.last_activity_date);

    for (let i = 0; i < Math.min(streakData.current_streak, 7); i++) {
      weekDays[6 - i] = true;
    }

    return weekDays;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  if (!streakData) {
    return (
      <div className="text-center p-8 text-gray-600">
        <p>Start your streak by using AirportWaze daily!</p>
      </div>
    );
  }

  // Compact view for dashboard/header
  if (compact) {
    return (
      <div className="flex items-center gap-3 bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-3 border border-orange-200">
        <div className={`relative ${animateFlame ? 'animate-bounce' : ''}`}>
          <Flame
            size={32 * getFlameSize(streakData.current_streak)}
            className={`${getFlameColor(streakData.current_streak)} drop-shadow-lg`}
          />
          {streakData.current_streak > 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-white font-bold text-sm drop-shadow-md">
                {streakData.current_streak}
              </span>
            </div>
          )}
        </div>
        <div>
          <p className="font-bold text-gray-800">{streakData.current_streak} Day Streak</p>
          <p className="text-xs text-gray-600">Keep it going!</p>
        </div>
      </div>
    );
  }

  // Full view
  const nextMilestone = getDaysUntilNextMilestone();
  const weekDays = getStreakWeek();

  return (
    <div className="max-w-2xl mx-auto">
      {/* Celebration Banner */}
      {showCelebration && (
        <div className="mb-4 bg-gradient-to-r from-yellow-400 to-orange-500 text-white rounded-xl p-4 shadow-lg animate-pulse">
          <div className="flex items-center justify-center gap-3">
            <Award size={32} />
            <div className="text-center">
              <p className="font-bold text-lg">Streak Milestone Reached!</p>
              <p className="text-sm">Keep up the amazing work!</p>
            </div>
            <Award size={32} />
          </div>
        </div>
      )}

      {/* Main Streak Display */}
      <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl p-8 shadow-lg border-2 border-orange-200">
        <div className="text-center mb-6">
          <div className={`inline-block relative ${animateFlame ? 'animate-bounce' : ''}`}>
            <Flame
              size={80 * getFlameSize(streakData.current_streak)}
              className={`${getFlameColor(streakData.current_streak)} drop-shadow-2xl`}
            />
            {streakData.current_streak > 0 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-white font-bold text-3xl drop-shadow-lg">
                  {streakData.current_streak}
                </span>
              </div>
            )}
          </div>

          <h2 className="text-4xl font-bold text-gray-800 mt-4">
            {streakData.current_streak} Day Streak
          </h2>
          <p className="text-gray-600 mt-2">
            {streakData.is_active ? 'Keep it going!' : 'Start traveling to build your streak'}
          </p>
        </div>

        {/* Week Calendar */}
        <div className="flex justify-center gap-2 mb-6">
          {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, index) => (
            <div
              key={index}
              className={`w-12 h-12 rounded-lg flex flex-col items-center justify-center transition ${
                weekDays[index]
                  ? 'bg-gradient-to-br from-orange-400 to-red-500 text-white shadow-md'
                  : 'bg-white text-gray-400 border border-gray-200'
              }`}
            >
              <span className="text-xs font-medium">{day}</span>
              {weekDays[index] && <Flame size={12} className="mt-0.5" />}
            </div>
          ))}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-white rounded-lg p-4 text-center">
            <TrendingUp className="mx-auto mb-2 text-blue-600" size={24} />
            <p className="text-2xl font-bold text-gray-800">{streakData.longest_streak}</p>
            <p className="text-sm text-gray-600">Longest Streak</p>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <Calendar className="mx-auto mb-2 text-green-600" size={24} />
            <p className="text-2xl font-bold text-gray-800">{streakData.total_active_days}</p>
            <p className="text-sm text-gray-600">Total Active Days</p>
          </div>
        </div>

        {/* Next Milestone */}
        {nextMilestone && (
          <div className="bg-white rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Star className="text-yellow-500" size={20} />
                <span className="font-semibold text-gray-800">Next Milestone</span>
              </div>
              <span className="text-sm text-gray-600">
                {nextMilestone.days} days to go
              </span>
            </div>

            <div className="mb-2">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-700">
                  {nextMilestone.milestone.title}
                </span>
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                  +{nextMilestone.milestone.xp_reward} XP
                </span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-orange-400 to-red-500 transition-all duration-500"
                  style={{
                    width: `${(streakData.current_streak / nextMilestone.milestone.days) * 100}%`
                  }}
                />
              </div>
            </div>
            <p className="text-xs text-gray-500">{nextMilestone.milestone.description}</p>
          </div>
        )}

        {/* Last Activity */}
        {streakData.last_activity_date && (
          <div className="text-center text-sm text-gray-600">
            <Clock size={14} className="inline mr-1" />
            Last activity: {new Date(streakData.last_activity_date).toLocaleDateString()}
          </div>
        )}
      </div>

      {/* Milestones Section */}
      <div className="mt-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <Award size={24} className="text-purple-600" />
          Streak Milestones
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {milestones.map((milestone) => (
            <div
              key={milestone.days}
              className={`rounded-xl p-4 border-2 transition ${
                milestone.unlocked
                  ? 'bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-400 shadow-md'
                  : 'bg-white border-gray-200 opacity-60'
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <div className={`text-3xl ${milestone.unlocked ? 'animate-pulse' : 'grayscale'}`}>
                  {milestone.icon}
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-gray-800">{milestone.title}</h4>
                  <p className="text-sm text-gray-600">{milestone.description}</p>
                </div>
                {milestone.unlocked && (
                  <div className="bg-green-500 rounded-full p-1">
                    <Zap className="text-white" size={16} />
                  </div>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
                  +{milestone.xp_reward} XP
                </span>
                <span className="text-sm font-semibold text-gray-700">
                  {milestone.days} days
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tips Section */}
      <div className="mt-6 bg-blue-50 rounded-xl p-6 border border-blue-200">
        <h4 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
          <Zap className="text-blue-600" size={20} />
          Streak Tips
        </h4>
        <ul className="space-y-2 text-sm text-gray-700">
          <li className="flex items-start gap-2">
            <span className="text-blue-600">•</span>
            <span>Use AirportWaze at least once a day to maintain your streak</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600">•</span>
            <span>Complete checkpoints or navigate to any location to count as activity</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600">•</span>
            <span>Streaks reset if you miss a day, so stay consistent!</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600">•</span>
            <span>Unlock special rewards and badges by reaching milestone streaks</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default StreakTracker;
