import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Volume2, Check, X } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/utils/cn'
import { getNextWords, submitWordReview } from '@/services/api'
import { PartOfSpeechEnum } from '@/schemas/word'

const Review = () => {
  const [userAnswer, setUserAnswer] = useState('')
  const [showAnswer, setShowAnswer] = useState(false)
  const [startTime, setStartTime] = useState(Date.now())
  const queryClient = useQueryClient()

  const { data: words, refetch: fetchNextWord, isLoading } = useQuery({
    queryKey: ['reviewWord'],
    queryFn: () => getNextWords(1),
  })

  const word = words?.[0]

  const submitReviewMutation = useMutation({
    mutationFn: async ({ wordId, quality, wasCorrect }) => {
      const responseTime = Date.now() - startTime
      return submitWordReview({
        word_id: wordId,
        quality,
        was_correct: wasCorrect,
        response_time: responseTime,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviewWord'] })
      setUserAnswer('')
      setShowAnswer(false)
      setStartTime(Date.now())
      fetchNextWord()
    },
  })

  const handleCheck = () => {
    if (!showAnswer) {
      setShowAnswer(true)
      return
    }

    if (word) {
      const isCorrect = userAnswer.toLowerCase().trim() === word.english.toLowerCase().trim()
      const quality = isCorrect ? 5 : 2

      submitReviewMutation.mutate({
        wordId: word.id,
        quality,
        wasCorrect: isCorrect,
      })
    }
  }

  const handleSkip = () => {
    if (word) {
      submitReviewMutation.mutate({
        wordId: word.id,
        quality: 1,
        wasCorrect: false,
      })
    }
  }

  const playAudio = () => {
    if (word) {
      const utterance = new SpeechSynthesisUtterance(word.english)
      window.speechSynthesis.speak(utterance)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!word) {
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-gray-500">No words available for review.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Review Words</h1>

      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Review</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-8">
            <div className="text-center">
              <h3 className="text-3xl font-bold mb-2">{word.turkish}</h3>
              {showAnswer && (
                <div className="mt-4">
                  <p className="text-xl text-green-600">{word.english}</p>
                  {word.example_sentence && (
                    <p className="text-sm text-gray-600 mt-2">
                      Example: {word.example_sentence}
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="space-y-4">
              <div className="flex justify-center">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={playAudio}
                  className="rounded-full"
                >
                  <Volume2 className="w-4 h-4" />
                </Button>
              </div>

              <input
                type="text"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                className={cn(
                  "w-full max-w-md mx-auto block text-center p-2 border rounded-md",
                  showAnswer && (
                    userAnswer.toLowerCase().trim() === word.english.toLowerCase().trim()
                      ? "border-green-500 bg-green-50"
                      : "border-red-500 bg-red-50"
                  )
                )}
                placeholder="Type the English translation"
                onKeyDown={(e) => e.key === 'Enter' && handleCheck()}
                disabled={showAnswer}
              />
            </div>

            <div className="flex justify-center space-x-4">
              <Button
                variant="outline"
                onClick={handleSkip}
                className="flex items-center space-x-2"
              >
                <X className="w-4 h-4" />
                <span>Skip</span>
              </Button>
              <Button
                onClick={handleCheck}
                className="flex items-center space-x-2"
              >
                <Check className="w-4 h-4" />
                <span>{showAnswer ? 'Next' : 'Check'}</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Review