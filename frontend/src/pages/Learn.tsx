import React, { useState } from 'react'
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query'
import { Volume2, Mic, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { useToast } from "@/components/ui/use-toast"
import { getNextLearningWords, submitWordReview } from '@/services/api'
import {addWordToLearning} from "../services/api.ts";

interface Word {
  id: number
  english: string
  turkish: string
  example_sentence: string
  example_sentence_translation?: string
  phonetic?: string
  image_url: string
}

const Learn: React.FC = () => {
  const [currentWordIndex, setCurrentWordIndex] = useState(0)
  const [isListening, setIsListening] = useState(false)
  const { toast } = useToast()
  let mediaStream: MediaStream | null = null
  const queryClient = useQueryClient()

   const { data: words = [], isError, error, refetch: fetchNextWords, isLoading } = useQuery<Word[]>({
    queryKey: ['nextLearningWords'],
    queryFn: () => getNextLearningWords(5),
    retry: 1,
  })

  const currentWord = words[currentWordIndex]

    const moveToNextWord = async () => {
    if (currentWordIndex < words.length - 1) {
      setCurrentWordIndex(prev => prev + 1)
    } else {
      await queryClient.invalidateQueries({ queryKey: ['nextLearningWords'] })
      setCurrentWordIndex(0)
    }
  }
  const addToLearningMutation = useMutation({
    mutationFn: addWordToLearning,
    onSuccess: async () => {
      toast({
        title: "Kelime Eklendi",
        description: "Kelime öğrenme listenize eklendi.",
        duration: 2000,
      })
      await moveToNextWord()
    },
    onError: () => {
      toast({
        title: "Hata",
        description: "Kelime eklenirken bir hata oluştu.",
        variant: "destructive",
        duration: 3000,
      })
    }
  })

  const startSpeechRecognition = (stream: MediaStream) => {
    if (!('webkitSpeechRecognition' in window)) {
      toast({
        title: "Tarayıcı Desteği Yok",
        description: "Tarayıcınız konuşma tanımayı desteklemiyor.",
        variant: "destructive",
        duration: 3000,
      })
      return
    }

    const recognition = new (window as any).webkitSpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = 'en-US'

    recognition.onstart = () => {
      setIsListening(true)
      toast({
        title: "Dinleniyor",
        description: "Lütfen kelimeyi söyleyin...",
        duration: 2000,
      })
    }

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript.toLowerCase()
      const spokenWord = transcript.trim()
      const correctWord = currentWord?.english.toLowerCase()

      if (spokenWord === correctWord) {
        toast({
          title: "Doğru telaffuz!",
          description: "Harika! Telaffuzunuz doğru.",
          duration: 2000,
        })
      } else {
        toast({
          title: "Tekrar deneyin",
          description: `Söylediğiniz: "${spokenWord}". Doğrusu: "${correctWord}"`,
          variant: "destructive",
          duration: 3000,
        })
      }
      setIsListening(false)
    }

    recognition.onerror = () => {
      setIsListening(false)
      stream.getTracks().forEach(track => track.stop())
      toast({
        title: "Mikrofon Hatası",
        description: "Lütfen mikrofon ayarlarınızı kontrol edin.",
        variant: "destructive",
        duration: 3000,
      })
    }

    recognition.onend = () => {
      setIsListening(false)
      stream.getTracks().forEach(track => track.stop())
    }

    recognition.start()
  }

  const requestMicrophoneAccess = async () => {
    try {
      // Önceki stream varsa temizle
      if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop())
      }

      // Yeni bir stream al ve izin iste
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      })

      // İzin verildiyse konuşma tanımayı başlat
      startSpeechRecognition(mediaStream)

    } catch (err) {
      console.error('Mikrofon izni hatası:', err)
      toast({
        title: "Mikrofon İzni Gerekli",
        description: "Konuşma özelliğini kullanmak için lütfen mikrofon iznini etkinleştirin. Tarayıcı ayarlarından mikrofon iznini kontrol edin.",
        variant: "destructive",
        duration: 5000,
      })
      setIsListening(false)
    }
  }

  const handleListen = () => {
    if (currentWord?.english) {
      const utterance = new SpeechSynthesisUtterance(currentWord.english)
      utterance.lang = 'en-US'
      window.speechSynthesis.speak(utterance)
    }
  }

  const submitReview = useMutation({
    mutationFn: submitWordReview,
    onSuccess: async () => {
      if (currentWord) {
        // Önce kelimeyi öğrenme listesine ekle
        await addToLearningMutation.mutateAsync(currentWord.id)

        // Sonra bir sonraki kelimeye geç
        if (currentWordIndex < words.length - 1) {
          setCurrentWordIndex(prev => prev + 1)
        } else {
          fetchNextWords()
          setCurrentWordIndex(0)
        }
      }
    }
  })
const submitReviewMutation = useMutation({
    mutationFn: submitWordReview,
    onSuccess: async () => {
      toast({
        title: "Başarılı",
        description: "Kelime başarıyla gözden geçirildi.",
        duration: 2000,
      })
      await moveToNextWord()
    },
    onError: (error) => {
      console.error('Review error:', error)
      toast({
        title: "Hata",
        description: "Kelime gözden geçirilirken bir hata oluştu.",
        variant: "destructive",
        duration: 3000,
      })
    }
  })
const handleKnown = async () => {
    if (currentWord) {
      try {
        // Önce kelimeyi öğrenme listesine ekle
        await addToLearningMutation.mutateAsync(currentWord.id)

        // Sonra review'ı gönder
        await submitReviewMutation.mutateAsync({
          word_id: currentWord.id,
          quality: 5,
          was_correct: true,
          response_time: 1000
        })
      } catch (error) {
        console.error('Known error:', error)
      }
    }
  }

    const handleSkip = async () => {
    if (currentWord) {
      try {
        await addToLearningMutation.mutateAsync(currentWord.id)
      } catch (error) {
        console.error('Skip error:', error)
      }
    }
  }


  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Yeni Kelimeler Öğren</h1>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Hata</AlertTitle>
          <AlertDescription>
            {error instanceof Error ? error.message : 'Kelimeler yüklenirken hata oluştu'}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!currentWord) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Yeni Kelimeler Öğren</h1>
        <Card>
          <CardHeader>
            <CardTitle>Kelime Bulunamadı</CardTitle>
            <CardDescription>
              Şu an için tüm kelimeleri tamamladınız!
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center space-y-4">
            <AlertCircle className="h-12 w-12 text-blue-500" />
            <p className="text-center text-gray-600">
              Öğrendiğiniz kelimeleri tekrar edebilir veya daha sonra yeni kelimeler için geri gelebilirsiniz.
            </p>
            <Button
              variant="outline"
              onClick={() => window.location.href = '/review'}
            >
              Öğrenilen Kelimeleri Tekrar Et
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Yeni Kelimeler Öğren</h1>

      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Yeni Kelimeler</CardTitle>
          <CardDescription>
            Yeni kelimeler öğrenin ve pratik yapın
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-8">
            {currentWord?.image_url && (
              <div className="flex justify-center">
                <img
                  src={currentWord.image_url}
                  alt={currentWord.english}
                  className="w-48 h-48 object-cover rounded-lg"
                />
              </div>
            )}

            <div className="text-center">
              <h3 className="text-3xl font-bold mb-2">{currentWord?.english}</h3>
              <p className="text-xl text-gray-600">{currentWord?.turkish}</p>
              {currentWord?.phonetic && (
                <p className="text-sm text-gray-500 mt-1">{currentWord.phonetic}</p>
              )}
            </div>

            <div className="space-y-4">
              <div className="flex justify-center space-x-4">
                <Button
                  variant="outline"
                  className="flex items-center space-x-2"
                  onClick={handleListen}
                >
                  <Volume2 className="w-4 h-4" />
                  <span>Dinle</span>
                </Button>
                <Button
                  variant="outline"
                  className="flex items-center space-x-2"
                  onClick={requestMicrophoneAccess}
                  disabled={isListening}
                >
                  <Mic className="w-4 h-4" />
                  <span>{isListening ? 'Dinleniyor...' : 'Konuş'}</span>
                </Button>
              </div>

              {currentWord?.example_sentence && (
                <div className="p-4 bg-gray-50 rounded-lg space-y-2">
                  <p className="text-gray-600">
                    {currentWord.example_sentence}
                  </p>
                  {currentWord.example_sentence_translation && (
                    <p className="text-gray-500 text-sm">
                      {currentWord.example_sentence_translation}
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="flex justify-center space-x-4">
              <Button
                variant="outline"
                onClick={handleSkip}
                disabled={addToLearningMutation.isPending}
              >
                {addToLearningMutation.isPending ? 'İşleniyor...' : 'Geç'}
              </Button>
              <Button
                onClick={handleKnown}
                disabled={addToLearningMutation.isPending || submitReviewMutation.isPending}
              >
                {(addToLearningMutation.isPending || submitReviewMutation.isPending) ? 'İşleniyor...' : 'Biliyorum'}
              </Button>
            </div>

            <div className="text-center text-sm text-gray-500">
              Kelime {currentWordIndex + 1} / {words.length}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Learn