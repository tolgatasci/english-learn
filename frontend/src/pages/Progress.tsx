import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ProgressCircle } from '@/components/ui/progress-circle';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getLearningProgress, getWeeklyStats } from '@/services/api';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';

const Progress: React.FC = () => {
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
    refetch: refetchStats
  } = useQuery({
    queryKey: ['progressStats'],
    queryFn: getLearningProgress,
    retry: 2,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const {
    data: weeklyStats,
    isLoading: weeklyLoading,
    error: weeklyError,
    refetch: refetchWeekly
  } = useQuery({
    queryKey: ['weeklyStats'],
    queryFn: getWeeklyStats,
    retry: 2,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const handleRefresh = async () => {
    try {
      await Promise.all([refetchStats(), refetchWeekly()]);
    } catch (error) {
      console.error('Refresh error:', error);
    }
  };

  if (statsLoading || weeklyLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (statsError || weeklyError) {
    return (
      <div className="space-y-4">
        <Alert variant="destructive">
          <AlertDescription>
            {statsError ? String(statsError) : ''}
            {weeklyError ? String(weeklyError) : ''}
          </AlertDescription>
        </Alert>
        <Button onClick={handleRefresh} className="flex items-center gap-2">
          <RefreshCw className="w-4 h-4" />
          Try Again
        </Button>
      </div>
    );
  }


  if (!stats || !weeklyStats) {
    return (
      <Alert>
        <AlertDescription>No data available</AlertDescription>
      </Alert>
    );
  }

 const chartData = Object.entries(weeklyStats.daily_stats).map(([date, data]) => ({
    date: new Date(date).toLocaleDateString('en-US', { weekday: 'short' }),
    words: data.words_reviewed,
    accuracy: data.accuracy || 0, // Handle the case where accuracy is not available
  }));

  return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold tracking-tight">Learning Progress</h1>
          <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              className="flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4"/>
            Refresh
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Total Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-center">
                <ProgressCircle
                    value={stats?.completion_rate || 0}
                    size={160}
                />
              </div>
              <div className="mt-4 text-center">
                <p className="text-sm text-gray-600">
                  {stats?.total_words_learned || 0} words mastered
                </p>
                <p className="text-sm text-gray-600">
                  {stats?.words_in_progress || 0} words in progress
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Weekly Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3"/>
                    <XAxis dataKey="date"/>
                    <YAxis/>
                    <Tooltip/>
                    <Line
                        type="monotone"
                        dataKey="words"
                        stroke="#2563eb"
                        name="Words Reviewed"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">
                    Average Retention
                  </p>
                  <p className="text-2xl font-bold">
                    {stats?.average_retention.toFixed(1) || 0}%
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">
                    Weekly Accuracy
                  </p>
                  <p className="text-2xl font-bold">
                    {typeof weeklyStats.average_accuracy === 'number'
                  ? weeklyStats.average_accuracy.toFixed(1)
                  : '0.0'}%
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">
                    Current Streak
                  </p>
                  <p className="text-2xl font-bold">
                    {stats?.current_streak || 0} days
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
  );
};

export default Progress;