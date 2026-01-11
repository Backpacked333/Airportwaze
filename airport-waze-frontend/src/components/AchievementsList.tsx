/**
 * Achievements List Component for AirportWaze
 * Displays unlocked badges, progress tracking, and achievement categories
 */

import React, { useEffect, useState } from 'react';
import {
  Trophy,
  Star,
  Lock,
  CheckCircle,
  TrendingUp,
  Zap,
  Search,
  Filter,
  Award,
  Target
} from 'lucide-react';

// Types
interface Achievement {
  id: number;
  name: string;
  description: string;
  icon: string;
  category: string;
  xp_reward: number;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  requirement_type: string;
  requirement_value: number;
  badge_id?: string;
  is_hidden: boolean;
}

interface UserAchievement {
  id: number;
  achievement: Achievement;
  progress: number;
  is_unlocked: boolean;
  unlocked_at?: string;
  progress_percentage: number;
}

interface AchievementsListProps {
  userId: number;
  onAchievementClick?: (achievement: UserAchievement) => void;
}

type FilterType = 'all' | 'unlocked' | 'locked' | 'in_progress';
type CategoryType = 'all' | 'travel' | 'speed' | 'social' | 'exploration' | 'special';

const AchievementsList: React.FC<AchievementsListProps> = ({
  userId,
  onAchievementClick
}) => {
  const [achievements, setAchievements] = useState<UserAchievement[]>([]);
  const [filteredAchievements, setFilteredAchievements] = useState<UserAchievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<FilterType>('all');
  const [category, setCategory] = useState<CategoryType>('all');
  const [sortBy, setSortBy] = useState<'recent' | 'rarity' | 'progress'>('recent');

  useEffect(() => {
    fetchAchievements();
  }, [userId]);

  useEffect(() => {
    filterAndSortAchievements();
  }, [achievements, searchQuery, filter, category, sortBy]);

  const fetchAchievements = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/gamification/achievements?user_id=${userId}`);
      if (!response.ok) throw new Error('Failed to fetch achievements');

      const data = await response.json();
      setAchievements(data);
    } catch (err) {
      console.error('Error fetching achievements:', err);
      // Mock data for development
      setAchievements(getMockAchievements());
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortAchievements = () => {
    let filtered = [...achievements];

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(ua =>
        !ua.achievement.is_hidden &&
        (ua.achievement.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
         ua.achievement.description.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    // Apply status filter
    if (filter === 'unlocked') {
      filtered = filtered.filter(ua => ua.is_unlocked);
    } else if (filter === 'locked') {
      filtered = filtered.filter(ua => !ua.is_unlocked);
    } else if (filter === 'in_progress') {
      filtered = filtered.filter(ua => !ua.is_unlocked && ua.progress > 0);
    }

    // Apply category filter
    if (category !== 'all') {
      filtered = filtered.filter(ua => ua.achievement.category === category);
    }

    // Sort achievements
    filtered.sort((a, b) => {
      if (sortBy === 'recent') {
        if (a.is_unlocked && b.is_unlocked) {
          return (b.unlocked_at || '').localeCompare(a.unlocked_at || '');
        }
        return a.is_unlocked ? -1 : b.is_unlocked ? 1 : 0;
      } else if (sortBy === 'rarity') {
        const rarityOrder = { legendary: 4, epic: 3, rare: 2, common: 1 };
        return rarityOrder[b.achievement.rarity] - rarityOrder[a.achievement.rarity];
      } else if (sortBy === 'progress') {
        return b.progress_percentage - a.progress_percentage;
      }
      return 0;
    });

    setFilteredAchievements(filtered);
  };

  const getRarityColor = (rarity: string): string => {
    switch (rarity) {
      case 'legendary': return 'from-yellow-400 to-orange-500';
      case 'epic': return 'from-purple-400 to-pink-500';
      case 'rare': return 'from-blue-400 to-cyan-500';
      default: return 'from-gray-400 to-gray-500';
    }
  };

  const getRarityBorderColor = (rarity: string): string => {
    switch (rarity) {
      case 'legendary': return 'border-yellow-400';
      case 'epic': return 'border-purple-400';
      case 'rare': return 'border-blue-400';
      default: return 'border-gray-300';
    }
  };

  const getStats = () => {
    const unlocked = achievements.filter(ua => ua.is_unlocked).length;
    const total = achievements.filter(ua => !ua.achievement.is_hidden).length;
    const inProgress = achievements.filter(ua => !ua.is_unlocked && ua.progress > 0).length;
    const totalXP = achievements
      .filter(ua => ua.is_unlocked)
      .reduce((sum, ua) => sum + ua.achievement.xp_reward, 0);

    return { unlocked, total, inProgress, totalXP };
  };

  const stats = getStats();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading achievements...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
            <Trophy size={36} />
            Achievements
          </h1>
          <p className="text-blue-100 mb-6">Track your progress and unlock rewards</p>

          {/* Stats Overview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <CheckCircle size={20} className="text-green-300" />
                <span className="text-sm font-medium">Unlocked</span>
              </div>
              <p className="text-2xl font-bold">{stats.unlocked} / {stats.total}</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp size={20} className="text-yellow-300" />
                <span className="text-sm font-medium">In Progress</span>
              </div>
              <p className="text-2xl font-bold">{stats.inProgress}</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <Star size={20} className="text-orange-300" />
                <span className="text-sm font-medium">Total XP</span>
              </div>
              <p className="text-2xl font-bold">{stats.totalXP.toLocaleString()}</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1">
                <Award size={20} className="text-purple-300" />
                <span className="text-sm font-medium">Completion</span>
              </div>
              <p className="text-2xl font-bold">{Math.round((stats.unlocked / stats.total) * 100)}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white border-b sticky top-0 z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4">
          {/* Search */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search achievements..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Filter Buttons */}
          <div className="flex flex-wrap gap-2 mb-4">
            <FilterButton
              active={filter === 'all'}
              onClick={() => setFilter('all')}
              icon={<Target size={16} />}
              label="All"
            />
            <FilterButton
              active={filter === 'unlocked'}
              onClick={() => setFilter('unlocked')}
              icon={<CheckCircle size={16} />}
              label="Unlocked"
            />
            <FilterButton
              active={filter === 'in_progress'}
              onClick={() => setFilter('in_progress')}
              icon={<TrendingUp size={16} />}
              label="In Progress"
            />
            <FilterButton
              active={filter === 'locked'}
              onClick={() => setFilter('locked')}
              icon={<Lock size={16} />}
              label="Locked"
            />
          </div>

          {/* Category Filters */}
          <div className="flex flex-wrap gap-2">
            <CategoryButton active={category === 'all'} onClick={() => setCategory('all')} label="All" />
            <CategoryButton active={category === 'travel'} onClick={() => setCategory('travel')} label="Travel" emoji="✈️" />
            <CategoryButton active={category === 'speed'} onClick={() => setCategory('speed')} label="Speed" emoji="⚡" />
            <CategoryButton active={category === 'social'} onClick={() => setCategory('social')} label="Social" emoji="👥" />
            <CategoryButton active={category === 'exploration'} onClick={() => setCategory('exploration')} label="Exploration" emoji="🗺️" />
            <CategoryButton active={category === 'special'} onClick={() => setCategory('special')} label="Special" emoji="⭐" />
          </div>
        </div>
      </div>

      {/* Achievements Grid */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        {filteredAchievements.length === 0 ? (
          <div className="text-center py-12">
            <Trophy className="mx-auto mb-4 text-gray-300" size={64} />
            <p className="text-gray-600 text-lg">No achievements found</p>
            <p className="text-gray-400">Try adjusting your filters</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAchievements.map((userAchievement) => (
              <AchievementCard
                key={userAchievement.id}
                userAchievement={userAchievement}
                onClick={() => onAchievementClick?.(userAchievement)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Filter Button Component
interface FilterButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}

const FilterButton: React.FC<FilterButtonProps> = ({ active, onClick, icon, label }) => {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
        active
          ? 'bg-blue-600 text-white shadow-md'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {icon}
      {label}
    </button>
  );
};

// Category Button Component
interface CategoryButtonProps {
  active: boolean;
  onClick: () => void;
  label: string;
  emoji?: string;
}

const CategoryButton: React.FC<CategoryButtonProps> = ({ active, onClick, label, emoji }) => {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-full text-sm font-medium transition ${
        active
          ? 'bg-purple-600 text-white shadow-md'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {emoji && <span className="mr-1">{emoji}</span>}
      {label}
    </button>
  );
};

// Achievement Card Component
interface AchievementCardProps {
  userAchievement: UserAchievement;
  onClick: () => void;
}

const AchievementCard: React.FC<AchievementCardProps> = ({ userAchievement, onClick }) => {
  const { achievement, progress, is_unlocked, progress_percentage } = userAchievement;

  const getRarityColor = (rarity: string): string => {
    switch (rarity) {
      case 'legendary': return 'from-yellow-400 to-orange-500';
      case 'epic': return 'from-purple-400 to-pink-500';
      case 'rare': return 'from-blue-400 to-cyan-500';
      default: return 'from-gray-400 to-gray-500';
    }
  };

  const getRarityBorderColor = (rarity: string): string => {
    switch (rarity) {
      case 'legendary': return 'border-yellow-400';
      case 'epic': return 'border-purple-400';
      case 'rare': return 'border-blue-400';
      default: return 'border-gray-300';
    }
  };

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl p-5 shadow-sm hover:shadow-lg transition cursor-pointer border-2 ${
        is_unlocked ? getRarityBorderColor(achievement.rarity) : 'border-gray-200'
      } ${!is_unlocked && 'opacity-75'}`}
    >
      {/* Icon and Status */}
      <div className="flex items-start justify-between mb-4">
        <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${
          is_unlocked ? getRarityColor(achievement.rarity) : 'from-gray-300 to-gray-400'
        } flex items-center justify-center text-3xl relative`}>
          {is_unlocked ? achievement.icon : '🔒'}
          {is_unlocked && (
            <div className="absolute -top-2 -right-2 bg-green-500 rounded-full p-1">
              <CheckCircle size={16} className="text-white" />
            </div>
          )}
        </div>

        {/* Rarity Badge */}
        <span className={`text-xs px-2 py-1 rounded-full font-medium capitalize ${
          achievement.rarity === 'legendary' ? 'bg-yellow-100 text-yellow-700' :
          achievement.rarity === 'epic' ? 'bg-purple-100 text-purple-700' :
          achievement.rarity === 'rare' ? 'bg-blue-100 text-blue-700' :
          'bg-gray-100 text-gray-700'
        }`}>
          {achievement.rarity}
        </span>
      </div>

      {/* Achievement Info */}
      <h3 className="font-bold text-gray-800 mb-1">
        {achievement.is_hidden && !is_unlocked ? '???' : achievement.name}
      </h3>
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
        {achievement.is_hidden && !is_unlocked ? 'Hidden achievement' : achievement.description}
      </p>

      {/* Progress Bar */}
      {!is_unlocked && !achievement.is_hidden && (
        <div className="mb-3">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-gray-600">Progress</span>
            <span className="text-xs font-semibold text-gray-700">
              {progress} / {achievement.requirement_value}
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r ${getRarityColor(achievement.rarity)} transition-all duration-500`}
              style={{ width: `${Math.min(progress_percentage, 100)}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{Math.round(progress_percentage)}% complete</p>
        </div>
      )}

      {/* Rewards */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="flex items-center gap-2">
          <Zap size={16} className="text-yellow-500" />
          <span className="text-sm font-semibold text-gray-700">+{achievement.xp_reward} XP</span>
        </div>
        {is_unlocked && userAchievement.unlocked_at && (
          <span className="text-xs text-gray-500">
            {new Date(userAchievement.unlocked_at).toLocaleDateString()}
          </span>
        )}
      </div>
    </div>
  );
};

// Mock data generator
const getMockAchievements = (): UserAchievement[] => {
  return [
    {
      id: 1,
      achievement: {
        id: 1,
        name: 'First Flight',
        description: 'Complete your first airport journey',
        icon: '✈️',
        category: 'travel',
        xp_reward: 100,
        rarity: 'common',
        requirement_type: 'trips',
        requirement_value: 1,
        is_hidden: false
      },
      progress: 1,
      is_unlocked: true,
      unlocked_at: new Date().toISOString(),
      progress_percentage: 100
    },
    {
      id: 2,
      achievement: {
        id: 2,
        name: 'Speed Demon',
        description: 'Save 1 hour total using optimal routes',
        icon: '⚡',
        category: 'speed',
        xp_reward: 250,
        rarity: 'rare',
        requirement_type: 'time_saved',
        requirement_value: 60,
        is_hidden: false
      },
      progress: 45,
      is_unlocked: false,
      progress_percentage: 75
    },
    {
      id: 3,
      achievement: {
        id: 3,
        name: 'Globe Trotter',
        description: 'Visit 10 different airports',
        icon: '🌍',
        category: 'exploration',
        xp_reward: 500,
        rarity: 'epic',
        requirement_type: 'airports',
        requirement_value: 10,
        is_hidden: false
      },
      progress: 7,
      is_unlocked: false,
      progress_percentage: 70
    }
  ];
};

export default AchievementsList;
