from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import logging
import os
import json
import time
import random
from datetime import datetime
import requests
from deep_translator import GoogleTranslator
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Word:
    english: str
    turkish: str
    phonetic: str
    difficulty_level: int
    part_of_speech: str
    example_sentence: str
    example_sentence_translation: str
    image_url: str
    audio_url: str
    tags: List[str]


class WordCollector:
    def __init__(self):
        self.translator = GoogleTranslator(source='en', target='tr')
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.logger = self.setup_logger()
        self.common_words = self.load_common_words()
        self.pexels_api_key = 'x'
        self.image_cache = {}

    def setup_logger(self):
        """Setup logging configuration"""
        logger = logging.getLogger('WordCollector')
        logger.setLevel(logging.INFO)

        # File handler
        fh = logging.FileHandler('word_collector.log')
        fh.setLevel(logging.INFO)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger

    def load_common_words(self) -> Set[str]:
        """Load common English words"""
        return {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at"
        }

    def get_words_from_datamuse(self, limit=50) -> List[str]:
        """Get word list from Datamuse API"""
        words = set()
        try:
            # Daha fazla topic ekleyelim
            topics = ['art', 'science', 'nature', 'food', 'technology',
                      'business', 'health', 'education', 'sports', 'music',
                      'travel', 'fashion', 'entertainment', 'politics', 'history']

            for topic in topics:
                # Her topic için farklı API endpointlerini kullanalım
                endpoints = [
                    f"https://api.datamuse.com/words?topics={topic}&max={limit}",
                    f"https://api.datamuse.com/words?ml={topic}&max={limit}",
                    f"https://api.datamuse.com/words?rel_syn={topic}&max={limit}"
                ]

                for url in endpoints:
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        for word_data in data:
                            word = word_data.get('word', '')
                            # Kelime uzunluğu kontrolünü biraz genişletelim
                            if (word.isalpha() and 2 <= len(word) <= 15 and
                                    ' ' not in word):  # Tek kelime olsun
                                words.add(word)
                    time.sleep(0.1)  # Rate limiting
        except Exception as e:
            self.logger.error(f"Error fetching words from Datamuse API: {str(e)}")
        return list(words)
    def get_category_words(self) -> List[str]:
        """Get categorized word list"""
        categories = {
            'Basic': [
                'hello', 'goodbye', 'please', 'thank', 'sorry',
                'good', 'bad', 'yes', 'no', 'help'
            ],
            'Numbers': [
                'one', 'two', 'three', 'four', 'five',
                'first', 'second', 'third', 'last', 'many'
            ],
            'Time': [
                'day', 'night', 'morning', 'evening', 'today',
                'tomorrow', 'yesterday', 'week', 'month', 'year'
            ],
            'Food': [
                'food', 'water', 'bread', 'milk', 'meat',
                'fruit', 'apple', 'banana', 'coffee', 'tea'
            ],
            'Family': [
                'family', 'mother', 'father', 'sister', 'brother',
                'child', 'baby', 'friend', 'wife', 'husband'
            ],
            'Body': [
                'head', 'hand', 'foot', 'eye', 'nose',
                'mouth', 'hair', 'body', 'arm', 'leg'
            ],
            'Actions': [
                'walk', 'run', 'eat', 'drink', 'sleep',
                'work', 'study', 'speak', 'listen', 'write'
            ],
            'Places': [
                'home', 'house', 'school', 'office', 'shop',
                'city', 'country', 'street', 'room', 'park'
            ],
            'Feelings': [
                'happy', 'sad', 'angry', 'tired', 'hungry',
                'love', 'hate', 'fear', 'hope', 'want'
            ],
            'Weather': [
                'hot', 'cold', 'rain', 'snow', 'wind',
                'sun', 'cloud', 'storm', 'warm', 'cool'
            ]
        }
        return [word for words in categories.values() for word in words]

    def get_frequency_words(self) -> List[str]:
        """Get frequently used words"""
        return """
        the be to of and a in that have i
        it for not on with he as you do at
        this but his by from they we say her she
        or an will my one all would there their what
        so up out if about who get which go me when
        make can like time no just him know take people
        into year your good some could them see other than
        then now look only come its over think also back
        """.split()

    def get_academic_words(self) -> List[str]:
        """Get academic words"""
        return """
        analyze research theory method data study result
        process system function structure context evidence
        factor approach concept phase resource principle
        element section aspect impact practice technique
        source strategy document category procedure test
        """.split()

    def generate_basic_phonetic(self, word: str) -> str:
        """Generate basic phonetic representation"""
        phonetic_map = {
            'a': 'æ', 'e': 'ɛ', 'i': 'ɪ', 'o': 'ɒ', 'u': 'ʌ',
            'th': 'θ', 'ch': 'tʃ', 'sh': 'ʃ', 'ph': 'f',
            'wh': 'w', 'gh': 'g',
        }
        phonetic = word.lower()
        for old, new in phonetic_map.items():
            phonetic = phonetic.replace(old, new)
        return f"/{phonetic}/"

    def get_phonetic(self, word: str) -> str:
        """Get phonetic transcription"""
        cache_file = os.path.join(self.cache_dir, f'phonetic_{word}.json')

        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)['phonetic']

        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(url)
            data = response.json()

            if isinstance(data, list) and len(data) > 0:
                phonetic = data[0].get('phonetic', '')
                if phonetic:
                    with open(cache_file, 'w') as f:
                        json.dump({'phonetic': phonetic}, f)
                    return phonetic

        except Exception as e:
            self.logger.error(f"Error fetching phonetic for {word}: {str(e)}")

        return self.generate_basic_phonetic(word)

    def get_image_url(self, word: str) -> Optional[str]:
        """Get image URL from Pexels API"""
        try:
            headers = {
                'Authorization': self.pexels_api_key
            }

            part_of_speech = self.guess_part_of_speech(word)
            search_modifiers = {
                'noun': f"object {word}",
                'verb': f"action {word}",
                'adjective': f"concept {word}",
                'adverb': f"manner {word}"
            }

            modified_query = search_modifiers.get(part_of_speech, word)
            url = f'https://api.pexels.com/v1/search?query={modified_query}&per_page=1&orientation=square'
            response = requests.get(url, headers=headers)
            data = response.json()

            if data.get('photos') and len(data['photos']) > 0:
                return data['photos'][0]['src']['medium']

        except Exception as e:
            self.logger.error(f"Error getting image for {word}: {str(e)}")

        return None

    def get_audio_url(self, word: str) -> str:
        """Get audio URL"""
        return f"https://translate.google.com/translate_tts?ie=UTF-8&q={word}&tl=en&client=tw-ob"

    def get_example_sentence(self, word: str) -> Dict[str, str]:
        """Get example sentence"""
        cache_file = os.path.join(self.cache_dir, f'example_{word}.json')

        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)

        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(url)
            data = response.json()

            if isinstance(data, list) and len(data) > 0:
                for meaning in data[0].get('meanings', []):
                    for definition in meaning.get('definitions', []):
                        if 'example' in definition:
                            example = definition['example']
                            translation = self.translator.translate(example)
                            result = {
                                'english': example,
                                'turkish': translation
                            }
                            with open(cache_file, 'w') as f:
                                json.dump(result, f)
                            return result

        except Exception as e:
            self.logger.error(f"Error getting example for {word}: {str(e)}")

        default_example = f"This is a {word}."
        return {
            'english': default_example,
            'turkish': self.translator.translate(default_example)
        }

    def calculate_difficulty(self, word: str) -> int:
        """Calculate word difficulty level"""
        score = 0

        # Length factor
        length = len(word)
        if length <= 4:
            score += 0
        elif length <= 6:
            score += 1
        elif length <= 8:
            score += 2
        else:
            score += 3

        # Common word check
        if word.lower() in self.common_words:
            score -= 1

        # Complex patterns
        patterns = ['th', 'ch', 'sh', 'ph', 'wh', 'gh']
        score += sum(1 for pattern in patterns if pattern in word.lower())

        # Syllable count
        vowels = len([char for char in word if char.lower() in 'aeiou'])
        score += vowels // 2

        return max(1, min(5, score + 1))

    def guess_part_of_speech(self, word: str) -> str:
        """Guess part of speech based on word patterns"""
        suffixes = {
            'noun': ['ness', 'ment', 'ship', 'tion', 'sion', 'ity', 'er', 'or', 'ist'],
            'verb': ['ate', 'ify', 'ize', 'ise', 'ed', 'ing'],
            'adjective': ['able', 'ible', 'al', 'ful', 'ic', 'ive', 'less', 'ous'],
            'adverb': ['ly']
        }

        word = word.lower()
        for pos, suffix_list in suffixes.items():
            if any(word.endswith(suffix) for suffix in suffix_list):
                return pos

        return 'noun'

    def generate_tags(self, word: str, difficulty: int) -> List[str]:
        """Generate word tags"""
        tags = [f"level-{difficulty}"]

        if word.lower() in self.common_words:
            tags.append("common")

        if len(word) <= 4:
            tags.append("basic")
        elif len(word) >= 8:
            tags.append("advanced")

        pos = self.guess_part_of_speech(word)
        tags.append(pos)

        if difficulty <= 2:
            tags.append("beginner-friendly")
        elif difficulty >= 4:
            tags.append("advanced-level")

        return tags

    def process_word(self, word: str) -> Optional[Word]:
        """Process a single word"""
        # Eğer kelime daha önce işlenmişse atla
        if os.path.exists(os.path.join(self.cache_dir, f'example_{word}.json')):
            return None

        try:
            # Önce basit kontrollerden geçirelim
            if not word.isalpha() or len(word) < 2:
                return None

            # Kelimeyi normalize edelim
            word = word.lower().strip()

            translation = self.translator.translate(word)
            if not translation or translation == word:
                return None

            phonetic = self.get_phonetic(word)
            difficulty = self.calculate_difficulty(word)
            part_of_speech = self.guess_part_of_speech(word)
            example = self.get_example_sentence(word)

            # Örnek cümle kontrolü
            if example['english'] == f"This is a {word}.":
                # Varsayılan örnek cümle gelmiş, başka bir tane deneyelim
                time.sleep(1)
                example = self.get_example_sentence(word)

            image_url = self.get_image_url(word)
            audio_url = self.get_audio_url(word)
            tags = self.generate_tags(word, difficulty)

            return Word(
                english=word,
                turkish=translation,
                phonetic=phonetic,
                difficulty_level=difficulty,
                part_of_speech=part_of_speech,
                example_sentence=example['english'],
                example_sentence_translation=example['turkish'],
                image_url=image_url,
                audio_url=audio_url,
                tags=tags
            )

        except Exception as e:
            self.logger.error(f"Error processing word {word}: {str(e)}")
            return None

    def save_to_database(self, word: Word) -> None:
        """Save word to database"""
        try:
            conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                ssl_disabled=True
            )
            cursor = conn.cursor()

            sql = """
            INSERT INTO words (
                english, turkish, phonetic, difficulty_level,
                part_of_speech, example_sentence, example_sentence_translation,
                image_url, audio_url, tags
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                turkish = VALUES(turkish),
                phonetic = VALUES(phonetic),
                difficulty_level = VALUES(difficulty_level),
                part_of_speech = VALUES(part_of_speech),
                example_sentence = VALUES(example_sentence),
                example_sentence_translation = VALUES(example_sentence_translation),
                image_url = VALUES(image_url),
                audio_url = VALUES(audio_url),
                tags = VALUES(tags)
            """

            values = (
                word.english,
                word.turkish,
                word.phonetic,
                word.difficulty_level,
                word.part_of_speech,
                word.example_sentence,
                word.example_sentence_translation,
                word.image_url,
                word.audio_url,
                ','.join(word.tags)
            )

            cursor.execute(sql, values)
            conn.commit()
            self.logger.info(f"Successfully saved word: {word.english}")

        except Exception as e:
            self.logger.error(f"Database error for word {word.english}: {str(e)}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn.is_connected():
                conn.close()

    def collect_words_from_all_sources(self, count_per_source=20) -> List[str]:
        words = set()

        # Datamuse API'den kelimeler
        words.update(self.get_words_from_datamuse(count_per_source))

        # Kategori bazlı kelimeler
        category_words = self.get_category_words()
        words.update(random.sample(category_words, min(count_per_source, len(category_words))))

        # Sık kullanılan kelimeler
        frequency_words = self.get_frequency_words()
        words.update(random.sample(frequency_words, min(count_per_source, len(frequency_words))))

        # Akademik kelimeler
        academic_words = self.get_academic_words()
        words.update(random.sample(academic_words, min(count_per_source, len(academic_words))))

        return list(words)

    def reset_processed_words():
        if os.path.exists('processed_words.txt'):
            os.remove('processed_words.txt')
    def save_progress(self, processed_words: List[str]):
        """Save processed words to file"""
        with open('processed_words.txt', 'a') as f:
            for word in processed_words:
                f.write(f"{word}\n")

    def load_processed_words(self) -> Set[str]:
        """Load previously processed words"""
        processed = set()
        if os.path.exists('processed_words.txt'):
            with open('processed_words.txt', 'r') as f:
                processed.update(line.strip() for line in f)
        return processed


def main():
    collector = WordCollector()

    while True:
        try:
            processed_words = collector.load_processed_words()

            # Her seferinde farklı sayıda kelime deneyelim
            count = random.randint(50, 200)
            words = collector.collect_words_from_all_sources(count_per_source=count)

            # Kelime listesini karıştıralım
            random.shuffle(words)

            # İşlenmemiş kelimeleri al
            new_words = [w for w in words if w not in processed_words]
            print(f"\nFound {len(new_words)} new words to process")

            if not new_words:
                print("No new words to process. Trying different sources...")
                # Farklı bir API endpoint'i deneyelim
                extra_words = collector.get_words_from_datamuse(limit=100)
                new_words = [w for w in extra_words if w not in processed_words]

                if not new_words:
                    print("Still no new words. Waiting before next attempt...")
                    time.sleep(5)
                    continue

            newly_processed = []
            for word in new_words[:50]:  # Her seferde en fazla 50 kelime işleyelim
                print(f"\nProcessing word: {word}")
                processed_word = collector.process_word(word)

                if processed_word:
                    collector.save_to_database(processed_word)
                    newly_processed.append(word)
                    print(f"Successfully processed and saved: {word}")

                time.sleep(1)  # API rate limiting

            collector.save_progress(newly_processed)

            print(f"\nProcessed {len(newly_processed)} new words")
            print("\nWaiting before next batch...")
            time.sleep(5)

        except KeyboardInterrupt:
            print("\nScript stopped by user.")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Retrying in 30 seconds...")
            time.sleep(2)
if __name__ == "__main__":
    try:
        print("Starting continuous word collection. Press Ctrl+C to stop.")
        main()
    except KeyboardInterrupt:
        print("\nScript terminated by user.")