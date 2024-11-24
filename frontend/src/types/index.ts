export interface Word {
  id: number
  english: string
  turkish: string
  example_sentence: string
  phonetic?: string
  part_of_speech: string
}

export interface WordSuggestion {
  english: string
  turkish: string
  example_sentence: string
  part_of_speech: string
}