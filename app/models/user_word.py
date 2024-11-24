# app/models/user_word.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, func, Float
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime, timedelta


class UserWord(Base):
    __tablename__ = "user_words"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)

    # Spaced Repetition ve Öğrenme Durumu
    retention_level = Column(Integer, default=0)  # 0-5 arası seviye
    ease_factor = Column(Float, default=2.5)  # SM-2 algoritması için
    interval = Column(Integer, default=0)  # Gün cinsinden sonraki tekrar aralığı
    last_reviewed = Column(DateTime, default=func.now())
    next_review = Column(DateTime, default=func.now())
    times_reviewed = Column(Integer, default=0)
    consecutive_correct = Column(Integer, default=0)

    # Öğrenme Metrikleri
    is_learned = Column(Boolean, default=False)
    confidence_level = Column(Integer, default=0)  # 0-100 arası
    last_response_time = Column(Float, nullable=True)  # Milisaniye cinsinden
    mistakes_count = Column(Integer, default=0)

    # Zaman Damgaları
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="user_words")
    word = relationship("Word", back_populates="user_words")

    def __repr__(self):
        return f"<UserWord user_id={self.user_id} word_id={self.word_id}>"

    def calculate_next_review(self, quality: int):
        """
        SM-2 algoritması ile sonraki tekrar zamanını hesapla
        quality: 0-5 arası değer (0: tamamen unutulmuş, 5: mükemmel hatırlama)
        """
        if quality >= 3:  # Başarılı tekrar
            if self.times_reviewed == 0:
                self.interval = 1
            elif self.times_reviewed == 1:
                self.interval = 6
            else:
                self.interval = int(self.interval * self.ease_factor)

            self.consecutive_correct += 1
            if self.consecutive_correct >= 3:
                self.is_learned = True
        else:  # Başarısız tekrar
            self.interval = 1
            self.consecutive_correct = 0
            self.is_learned = False

        # Ease factor güncelleme
        self.ease_factor = max(1.3, self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

        # Sonraki tekrar zamanını ayarla
        self.next_review = datetime.utcnow() + timedelta(days=self.interval)
        self.times_reviewed += 1
        self.last_reviewed = datetime.utcnow()

    def update_confidence(self, response_time: float, is_correct: bool):
        """
        Güven seviyesini güncelle
        response_time: Milisaniye cinsinden cevap süresi
        is_correct: Cevabın doğru olup olmadığı
        """
        # Cevap süresine göre baz puan (1-100 arası)
        base_score = max(0, min(100, 100 - (response_time / 1000) * 10))

        if is_correct:
            # Doğru cevap durumunda güven seviyesini artır
            self.confidence_level = min(100, self.confidence_level + (base_score * 0.2))
        else:
            # Yanlış cevap durumunda güven seviyesini azalt
            self.confidence_level = max(0, self.confidence_level - 20)
            self.mistakes_count += 1