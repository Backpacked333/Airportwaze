/**
 * User Profile Component for AirportWaze Gamification
 * Displays user stats, level, XP progress, achievements, and badges
 */

import React, { useEffect, useState } from 'react';
import {
  Trophy,
  Star,
  TrendingUp,
  MapPin,
  Plane,
  Clock,
  Award,
  Settings,
  Edit3,
  ChevronRight,
  Zap
} from 'lucide-react';

// Types
interface UserStats {
  total_trips: number;
  total_distance_km: number;
  total_checkpoints_visited: number;
  total_airports_visited: number;
  total_time_saved_minutes: number;
}

interface UserProfileData {
  id: number;
  user_id: number;
  level: number;
  total_xp: number;
  current_level_xp: number;
  xp_to_next_level: number;
  level_progress: number;
  avatar_url?: string;
  avatar_frame: string;
  title: string;
  stats: UserStats;
  badges_unlocked: string[];
  badge_showcase: string[];
  created_at: string;
  last_active_at: string;
}

interface Achievement {
  id: number;
  name: string;
  description: string;
  icon: string;
  category: string;
  xp_reward: number;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  unlocked_at?: string;
}

interface UserProfileProps {
  userId: number;
  onEditProfile?: () => void;
  onViewAchievements?: () => void;
}

// Badge data (would normally come from API)
const BADGE_ICONS: Record<string, string> = {
  frequent_flyer: '✈️',
  speed_demon: '⚡',
  explorer: '🗺️',
  navigator: '🧭',
  time_saver: '⏱️',
  social_butterfly: '🦋',
  early_bird: '🐦',
  night_owl: '🦉'
};

const UserProfile: React.FC<UserProfileProps> = ({
  userId,
  onEditProfile,
  onViewAchievements
}) => {
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [recentAchievements, setRecentAchievements] = useState<Achievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchUserProfile();
  }, [userId]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      // In production, this would be an actual API call
      const response = await fetch(`/api/gamification/profile?user_id=${userId}`);
      if (!response.ok) throw new Error('Failed to fetch profile');

      const data = await response.json();
      setProfile(data);

      // Fetch recent achievements
      const achievementsResponse = await fetch(`/api/gamification/achievements?user_id=${userId}&recent=3`);
      if (achievementsResponse.ok) {
        const achievementsData = await achievementsResponse.json();
        setRecentAchievements(achievementsData);
      }
    } catch (err) {
      console.error('Error fetching profile:', err);
      setError('Failed to load profile');
      // Mock data for development
      setProfile({
        id: 1,
        user_id: userId,
        level: 12,
        total_xp: 8750,
        current_level_xp: 350,
        xp_to_next_level: 1000,
        level_progress: 35,
        avatar_url: undefined,
        avatar_frame: 'gold',
        title: 'Airport Navigator',
        stats: {
          total_trips: 47,
          total_distance_km: 125.3,
          total_checkpoints_visited: 284,
          total_airports_visited: 12,
          total_time_saved_minutes: 312
        },
        badges_unlocked: ['frequent_flyer', 'speed_demon', 'explorer', 'navigator'],
        badge_showcase: ['frequent_flyer', 'speed_demon', 'navigator'],
        created_at: new Date().toISOString(),
        last_active_at: new Date().toISOString()
      });
    } finally {
      setLoading(false);
    }
  };

  const getRarityColor = (rarity: string): string => {
    switch (rarity) {
      case 'legendary': return 'from-yellow-400 to-orange-500';
      case 'epic': return 'from-purple-400 to-pink-500';
      case 'rare': return 'from-blue-400 to-cyan-500';
      default: return 'from-gray-400 to-gray-500';
    }
  };

  const getFrameColor = (frame: string): string => {
    switch (frame) {
      case 'gold': return 'border-yellow-400 shadow-yellow-400/50';
      case 'silver': return 'border-gray-300 shadow-gray-300/50';
      case 'bronze': return 'border-orange-400 shadow-orange-400/50';
      default: return 'border-blue-400 shadow-blue-400/50';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <Trophy className="mx-auto mb-4 text-gray-400" size={48} />
          <p className="text-gray-600">{error || 'Profile not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex justify-end mb-4">
            <button
              onClick={onEditProfile}
              className="flex items-center gap-2 bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg backdrop-blur-sm transition"
            >
              <Settings size={18} />
              Settings
            </button>
          </div>

          {/* Avatar and Level */}
          <div className="flex flex-col items-center mb-6">
            <div className={`relative mb-4 border-4 rounded-full ${getFrameColor(profile.avatar_frame)} shadow-lg`}>
              {profile.avatar_url ? (
                <img
                  src={profile.avatar_url}
                  alt="Avatar"
                  className="w-32 h-32 rounded-full object-cover"
                />
              ) : (
                <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-4xl font-bold">
                  {profile.user_id.toString().slice(0, 2)}
                </div>
              )}
              <button
                onClick={onEditProfile}
                className="absolute bottom-0 right-0 bg-blue-600 hover:bg-blue-700 p-2 rounded-full shadow-lg"
              >
                <Edit3 size={16} />
              </button>
            </div>

            <h1 className="text-3xl font-bold mb-1">Level {profile.level}</h1>
            <p className="text-blue-100 text-lg mb-4">{profile.title}</p>

            {/* Badge Showcase */}
            {profile.badge_showcase && profile.badge_showcase.length > 0 && (
              <div className="flex gap-2 mb-4">
                {profile.badge_showcase.map((badgeId) => (
                  <div
                    key={badgeId}
                    className="bg-white/20 backdrop-blur-sm rounded-lg p-2 text-2xl"
                    title={badgeId.replace('_', ' ')}
                  >
                    {BADGE_ICONS[badgeId] || '🏆'}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* XP Progress Bar */}
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Level Progress</span>
              <span className="text-sm font-bold">{profile.current_level_xp} / {profile.xp_to_next_level} XP</span>
            </div>
            <div className="relative h-4 bg-white/20 rounded-full overflow-hidden">
              <div
                className="absolute inset-y-0 left-0 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${profile.level_progress}%` }}
              >
                <div className="absolute inset-0 bg-white/30 animate-pulse"></div>
              </div>
            </div>
            <p className="text-xs text-blue-100 mt-2 text-center">
              {Math.round(profile.level_progress)}% to Level {profile.level + 1}
            </p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <TrendingUp size={24} className="text-blue-600" />
          Your Stats
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
          <StatCard
            icon={<Plane className="text-blue-600" />}
            label="Total Trips"
            value={profile.stats.total_trips.toLocaleString()}
            color="bg-blue-50"
          />
          <StatCard
            icon={<MapPin className="text-green-600" />}
            label="Checkpoints"
            value={profile.stats.total_checkpoints_visited.toLocaleString()}
            color="bg-green-50"
          />
          <StatCard
            icon={<TrendingUp className="text-purple-600" />}
            label="Distance"
            value={`${profile.stats.total_distance_km.toFixed(1)} km`}
            color="bg-purple-50"
          />
          <StatCard
            icon={<MapPin className="text-orange-600" />}
            label="Airports"
            value={profile.stats.total_airports_visited.toLocaleString()}
            color="bg-orange-50"
          />
          <StatCard
            icon={<Clock className="text-red-600" />}
            label="Time Saved"
            value={`${Math.floor(profile.stats.total_time_saved_minutes / 60)}h ${profile.stats.total_time_saved_minutes % 60}m`}
            color="bg-red-50"
          />
          <StatCard
            icon={<Star className="text-yellow-600" />}
            label="Total XP"
            value={profile.total_xp.toLocaleString()}
            color="bg-yellow-50"
          />
        </div>

        {/* Recent Achievements */}
        {recentAchievements.length > 0 && (
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                <Trophy size={24} className="text-yellow-600" />
                Recent Achievements
              </h2>
              <button
                onClick={onViewAchievements}
                className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
              >
                View All
                <ChevronRight size={18} />
              </button>
            </div>

            <div className="space-y-3">
              {recentAchievements.map((achievement) => (
                <div
                  key={achievement.id}
                  className="bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition flex items-center gap-4"
                >
                  <div className={`w-16 h-16 rounded-lg bg-gradient-to-br ${getRarityColor(achievement.rarity)} flex items-center justify-center text-3xl`}>
                    {achievement.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-800">{achievement.name}</h3>
                    <p className="text-sm text-gray-600">{achievement.description}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
                        +{achievement.xp_reward} XP
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full font-medium capitalize ${
                        achievement.rarity === 'legendary' ? 'bg-yellow-100 text-yellow-700' :
                        achievement.rarity === 'epic' ? 'bg-purple-100 text-purple-700' :
                        achievement.rarity === 'rare' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {achievement.rarity}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Badges Collection */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <Award size={24} className="text-purple-600" />
              Badge Collection
            </h2>
            <span className="text-sm text-gray-600">
              {profile.badges_unlocked.length} badges earned
            </span>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="grid grid-cols-4 md:grid-cols-6 gap-4">
              {profile.badges_unlocked.map((badgeId) => (
                <div
                  key={badgeId}
                  className="aspect-square bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg flex items-center justify-center text-4xl hover:scale-110 transition cursor-pointer"
                  title={badgeId.replace('_', ' ')}
                >
                  {BADGE_ICONS[badgeId] || '🏆'}
                </div>
              ))}
              {/* Locked badges preview */}
              {[...Array(Math.max(0, 6 - profile.badges_unlocked.length))].map((_, i) => (
                <div
                  key={`locked-${i}`}
                  className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center text-2xl opacity-30"
                >
                  🔒
                </div>
              ))}
            </div>

            <button
              onClick={onViewAchievements}
              className="w-full mt-6 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 rounded-lg flex items-center justify-center gap-2 transition"
            >
              <Zap size={20} />
              Unlock More Badges
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Stat Card Component
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ icon, label, value, color }) => {
  return (
    <div className={`${color} rounded-xl p-4 shadow-sm hover:shadow-md transition`}>
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 bg-white rounded-lg">
          {icon}
        </div>
      </div>
      <p className="text-2xl font-bold text-gray-800">{value}</p>
      <p className="text-sm text-gray-600">{label}</p>
    </div>
  );
};

export default UserProfile;
