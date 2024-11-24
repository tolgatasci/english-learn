import { Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from '@/contexts/AuthContext'

// Pages
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Dashboard from '@/pages/Dashboard'
import Learn from '@/pages/Learn'
import Review from '@/pages/Review'
import Progress from '@/pages/Progress'
import MainLayout from '@/components/layout/MainLayout'
import { Toaster } from "@/components/ui/toaster"

const App = () => {
  return (
      <>
    <Routes>

      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected routes */}
      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/learn" element={<Learn />} />
        <Route path="/review" element={<Review />} />
        <Route path="/progress" element={<Progress />} />
      </Route>
    </Routes>
            <Toaster />
      </>
  )
}

export default App