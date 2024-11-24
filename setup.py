# setup.py
import os
import sys
import json
from pathlib import Path
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import hashlib
import datetime

# Load environment variables
load_dotenv()


class DatabaseSetup:
    def __init__(self):
        try:
            self.db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'user': os.getenv('DB_USER', 'root'),
                'password': os.getenv('DB_PASSWORD', ''),
                'port': os.getenv('DB_PORT', '3306'),
                'charset': 'utf8mb4',
                'use_unicode': True,
                # SSL'i devre dışı bırak
                'ssl_disabled': True
            }
            self.db_name = os.getenv('DB_NAME', 'english_learning')
            self.setup_status_file = 'db_setup_status.json'
            self.conn = None
            self.cursor = None

            print("Configuration loaded successfully.")
            print(f"Database: {self.db_name}")
            print(f"Host: {self.db_config['host']}")
            print(f"Port: {self.db_config['port']}")
            print(f"User: {self.db_config['user']}")

        except Exception as e:
            print(f"Error initializing DatabaseSetup: {e}")
            sys.exit(1)

    def connect_database(self):
        """Connect to MySQL server without selecting a database"""
        try:
            # Basitleştirilmiş bağlantı konfigürasyonu
            connection_config = {
                'host': self.db_config['host'],
                'user': self.db_config['user'],
                'password': self.db_config['password'],
                'charset': 'utf8mb4',
                'use_pure': True,  # Pure Python implementation kullan
                'ssl_disabled': True  # SSL'i devre dışı bırak
            }

            self.conn = mysql.connector.connect(**connection_config)
            self.cursor = self.conn.cursor(dictionary=True)
            print("Successfully connected to MySQL server")
            return True
        except Error as e:
            print(f"Error connecting to MySQL server: {e}")
            print("\nBağlantı detayları:")
            print(f"Host: {self.db_config['host']}")
            print(f"User: {self.db_config['user']}")
            print(f"Port: {self.db_config['port']}")
            return False

    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            # Basit bir database oluşturma
            self.cursor.execute(f"DROP DATABASE IF EXISTS {self.db_name}")
            self.cursor.execute(f"CREATE DATABASE {self.db_name}")
            self.cursor.execute(f"USE {self.db_name}")

            # Charset'i database oluşturulduktan sonra ayarla
            self.cursor.execute("SET NAMES utf8mb4")
            self.cursor.execute("SET CHARACTER SET utf8mb4")
            self.cursor.execute("SET character_set_connection=utf8mb4")

            # Tabloları oluştur
            self.create_tables()

            print(f"Database '{self.db_name}' created successfully")
            return True
        except Error as e:
            print(f"Error creating database: {e}")
            return False

    def create_tables(self):
        """Create necessary tables"""
        try:
            self.cursor.execute("""
                        CREATE TABLE users (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            username VARCHAR(50) UNIQUE NOT NULL,
                            email VARCHAR(100) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            full_name VARCHAR(100),
                            daily_goal INT DEFAULT 10,
                            streak_days INT DEFAULT 0,
                            last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            is_active BOOLEAN DEFAULT TRUE,
                            is_superuser BOOLEAN DEFAULT FALSE
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)

            # Words table
            self.cursor.execute("""
                        CREATE TABLE words (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            english VARCHAR(100) UNIQUE NOT NULL,
                            turkish VARCHAR(100) NOT NULL,
                            phonetic VARCHAR(100),
                            difficulty_level INT DEFAULT 1,
                            part_of_speech VARCHAR(20),
                            example_sentence TEXT,
                            example_sentence_translation TEXT,
                            audio_url VARCHAR(255),
                            image_url VARCHAR(255),
                            tags VARCHAR(255),
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)

            # User_Words table with all fields
            self.cursor.execute("""
                        CREATE TABLE user_words (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            user_id INT NOT NULL,
                            word_id INT NOT NULL,
                            retention_level INT DEFAULT 0,
                            ease_factor FLOAT DEFAULT 2.5,
                            `interval` INT DEFAULT 0,
                            last_reviewed DATETIME DEFAULT CURRENT_TIMESTAMP,
                            next_review DATETIME DEFAULT CURRENT_TIMESTAMP,
                            times_reviewed INT DEFAULT 0,
                            consecutive_correct INT DEFAULT 0,
                            is_learned BOOLEAN DEFAULT FALSE,
                            confidence_level INT DEFAULT 0,
                            last_response_time FLOAT DEFAULT NULL,
                            mistakes_count INT DEFAULT 0,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE,
                            INDEX idx_user_word (user_id, word_id),
                            INDEX idx_next_review (next_review),
                            INDEX idx_last_reviewed (last_reviewed)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)



            # Indexleri ekle
            self.cursor.execute("CREATE INDEX idx_user_word ON user_words(user_id, word_id)")
            self.cursor.execute("CREATE INDEX idx_next_review ON user_words(next_review)")
            self.cursor.execute("CREATE INDEX idx_last_reviewed ON user_words(last_reviewed)")

            # Indexleri ayrı ayrı ekle
            self.cursor.execute("CREATE INDEX idx_username ON users(username)")
            self.cursor.execute("CREATE INDEX idx_email ON users(email)")
            self.cursor.execute("CREATE INDEX idx_english ON words(english)")


            # Örnek veriler ekle
            self.insert_sample_data()

            self.conn.commit()
            print("Tables created successfully")
            return True
        except Error as e:
            print(f"Error creating tables: {e}")
            return False

    def insert_sample_data(self):
        """Insert sample data into tables"""
        try:
            # Sample words
            sample_words = [
                ('hello', 'merhaba', 1, 'greeting', 'Hello, how are you?'),
                ('world', 'dünya', 1, 'noun', 'The world is beautiful.'),
                ('computer', 'bilgisayar', 2, 'noun', 'I need a new computer.'),
                ('love', 'sevmek', 1, 'verb', 'I love learning languages.'),
                ('book', 'kitap', 1, 'noun', 'I read a good book yesterday.')
            ]

            insert_word_query = """
                       INSERT INTO words (english, turkish, difficulty_level, part_of_speech, example_sentence)
                       VALUES (%s, %s, %s, %s, %s)
                   """
            self.cursor.executemany(insert_word_query, sample_words)
            self.conn.commit()
            print("Sample data inserted successfully")
            return True
        except Error as e:
            print(f"Error inserting sample data: {e}")
            return False

    def setup(self):
        """Run the complete setup process"""
        print("\nStarting database setup...")

        if not self.connect_database():
            print("Setup failed: Could not connect to database server")
            return False

        if not self.create_database():
            print("Setup failed: Could not create database")
            return False

        print("\nSetup completed successfully!")

        if self.conn:
            self.conn.close()
            print("Database connection closed")

        return True


def main():
    print("=== English Learning App Database Setup ===")

    if not os.path.exists('.env'):
        print("\nHATA: .env dosyası bulunamadı!")
        print("Lütfen .env.example dosyasını .env olarak kopyalayın ve düzenleyin.")
        print("\nÖrnek .env içeriği:")
        print("DB_HOST=localhost")
        print("DB_USER=root")
        print("DB_PASSWORD=your_password")
        print("DB_PORT=3306")
        print("DB_NAME=english_learning")
        sys.exit(1)

    setup = DatabaseSetup()

    try:
        if setup.setup():
            print("\nVeritabanı kurulumu başarıyla tamamlandı!")
            print("Şimdi uygulamayı başlatabilirsiniz:")
            print("uvicorn app.main:app --reload")
        else:
            print("\nVeritabanı kurulumu başarısız oldu!")
            print("Lütfen hata mesajlarını kontrol edin ve tekrar deneyin.")
    except KeyboardInterrupt:
        print("\nKurulum kullanıcı tarafından iptal edildi.")
    except Exception as e:
        print(f"\nBeklenmeyen bir hata oluştu: {e}")


if __name__ == "__main__":
    main()