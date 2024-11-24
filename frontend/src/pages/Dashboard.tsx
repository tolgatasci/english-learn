import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Flame, Book, CheckCircle, Clock } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ProgressCircle } from '@/components/ui/progress-circle'
import { getLearningProgress, getStreakInfo } from '@/services/api'
const Dashboard: React.FC = () => {
  const { data: progressData, isLoading: isProgressLoading } = useQuery({
    queryKey: ['dailyProgress'],
    queryFn: getLearningProgress
  })

  const { data: streakData, isLoading: isStreakLoading } = useQuery({
    queryKey: ['streak'],
    queryFn: getStreakInfo
  })

  const cardClasses = "bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow"

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Welcome Back!</h1>
        <Button className="hidden sm:flex">Start Learning</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Daily Progress Card */}
        <Card className={cardClasses}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Today's Progress
            </CardTitle>
            <Book className="h-5 w-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="mt-2">
              <div className="text-2xl font-bold text-gray-900">
                {isProgressLoading ? "..." : `${progressData?.words_reviewed_today || 0} words`}
              </div>
              <p className="text-sm text-gray-500">
                Daily goal: {progressData?.daily_goal || 0} words
              </p>
              <div className="mt-4">
                <ProgressCircle
                  value={(progressData?.words_reviewed_today / progressData?.daily_goal * 100) || 0}
                  size={60}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Streak Card */}
        <Card className={cardClasses}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Current Streak
            </CardTitle>
            <Flame className="h-5 w-5 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="mt-2">
              <div className="text-2xl font-bold text-gray-900">
                {isStreakLoading ? "..." : `${streakData?.current_streak || 0} days`}
              </div>
              <p className="text-sm text-gray-500">
                {streakData?.today_activity ? "You've studied today!" : "Keep the streak going!"}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Words Learned Card */}
        <Card className={cardClasses}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Words Mastered
            </CardTitle>
            <CheckCircle className="h-5 w-5 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="mt-2">
              <div className="text-2xl font-bold text-gray-900">
                {progressData?.total_words_learned || 0}
              </div>
              <p className="text-sm text-gray-500">Total words learned</p>
            </div>
          </CardContent>
        </Card>

        {/* Next Review Card */}
        <Card className={cardClasses}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Next Review
            </CardTitle>
            <Clock className="h-5 w-5 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="mt-2">
              <div className="text-2xl font-bold text-gray-900">
                {progressData?.words_due || 0} words
              </div>
              <Button
                className="w-full mt-4"
                variant="outline"
                onClick={() => window.location.href = '/review'}
              >
                Start Review
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className={cardClasses}>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            {/* Activity list will go here */}
            <div className="text-center text-gray-500 py-8">
              Start learning to see your activity here!
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Dashboard