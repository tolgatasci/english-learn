import axios from 'axios'
import {Word, WordSuggestion} from "../types";

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Type definitions
interface ProgressStats {
  total_words_learned: number;
  words_in_progress: number;
  completion_rate: number;
  current_streak: number;
  average_retention: number;
}

interface WeeklyStats {
  daily_stats: {
    [key: string]: {
      words_reviewed: number;
      correct_answers: number;
      accuracy: number;
    };
  };
  total_words_reviewed: number;
  average_accuracy: number;
}

// API methods
export const getLearningProgress = async () => {
  try {
    const { data } = await api.get<ProgressStats>('/users/me/statistics');
    return data;
  } catch (error) {
    console.error('Error fetching learning progress:', error);
    throw error;
  }
};
export const suggestWord = async (wordData: WordSuggestion) => {
  const { data } = await api.post('/words/suggest', wordData)
  return data
}
export const addWordToLearning = async (wordId: number) => {
  const { data } = await api.post(`/words/add-to-learning?word_id=${wordId}`)
  return data
}
export const getWeeklyStats = async () => {
  try {
    const { data } = await api.get('/learning/weekly-stats');
    return data;
  } catch (error) {
    const message =
      error.response?.data?.detail || 'Failed to fetch weekly statistics';
    console.error('Error fetching weekly stats:', message);
    throw new Error(message);
  }
};

export const submitWordReview = async (reviewData: {
  word_id: number;
  quality: number;
  was_correct: boolean;
  response_time: number;
}) => {
  try {
    const { data } = await api.post('/words/review', reviewData);
    return data;
  } catch (error) {
    console.error('Error submitting word review:', error);
    throw error;
  }
};
export const getNextLearningWords = async (limit = 10): Promise<Word[] | null> => {
  try {
    const { data } = await api.get(`/words/next-learning-words?limit=${limit}`);
    return data.length > 0 ? data : null;
  } catch (error) {
    console.error('Error fetching next learning words:', error);
    throw error;
  }
};
export const getNextWords = async (limit = 10): Promise<ReviewWord[] | null> => {
  try {
    const { data } = await api.get(`/words/next-words?limit=${limit}`);
    return data.length > 0 ? data : null;
  } catch (error) {
    console.error('Error fetching next words:', error);
    throw error;
  }
};



export const getStreakInfo = async () => {
  try {
    const { data } = await api.get('/learning/streak-info')
    return data
  } catch (error) {
    console.error('Error fetching streak info:', error)
    throw error
  }
}
export const getWordProgress = async () => {
  const { data } = await api.get('/learning/performance-analysis')
  return data
}



// Auth API calls
export const login = async (username: string, password: string) => {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)

  const { data } = await api.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
  return data
}

export const register = async (userData: {
  username: string
  email: string
  password: string
  password_confirm: string
  full_name?: string
}) => {
  const { data } = await api.post('/auth/register', userData)
  return data
}

export const getUserProfile = async () => {
  const { data } = await api.get('/auth/me')
  return data
}

export default api