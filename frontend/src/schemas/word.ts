export enum PartOfSpeechEnum {
  Noun = 'noun',
  Verb = 'verb',
  Adjective = 'adjective',
  Adverb = 'adverb',
  Preposition = 'preposition',
  Conjunction = 'conjunction',
  Pronoun = 'pronoun',
  Interjection = 'interjection',
}

export class WordResponse {
  id: number;
  english: string;
  turkish: string;
  phonetic?: string;
  difficulty_level: number;
  part_of_speech: PartOfSpeechEnum | null;
  example_sentence?: string;
  example_sentence_translation?: string;
  audio_url?: string;
  image_url?: string;
  tags?: string;

  constructor(data: {
    id: number;
    english: string;
    turkish: string;
    phonetic?: string;
    difficulty_level: number;
    part_of_speech?: string;
    example_sentence?: string;
    example_sentence_translation?: string;
    audio_url?: string;
    image_url?: string;
    tags?: string;
  }) {
    this.id = data.id;
    this.english = data.english;
    this.turkish = data.turkish;
    this.phonetic = data.phonetic;
    this.difficulty_level = data.difficulty_level;
    this.part_of_speech = data.part_of_speech
      ? (PartOfSpeechEnum[data.part_of_speech.toLowerCase() as keyof typeof PartOfSpeechEnum] || null)
      : null;
    this.example_sentence = data.example_sentence;
    this.example_sentence_translation = data.example_sentence_translation;
    this.audio_url = data.audio_url;
    this.image_url = data.image_url;
    this.tags = data.tags;
  }
}