import React from 'react'
import { Outlet, NavLink as RouterLink, useNavigate } from 'react-router-dom'
import { Menu, LogOut, Settings, User, BookOpen, LayoutDashboard, Repeat, TrendingUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'

interface NavLinkProps {
  to: string
  children: React.ReactNode
  icon: React.ReactNode
}

const NavLink: React.FC<NavLinkProps> = ({ to, children, icon }) => (
  <RouterLink
    to={to}
    className={({ isActive }) =>
      `flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
        isActive
          ? "bg-blue-100 text-blue-700"
          : "text-gray-700 hover:bg-gray-100"
      }`
    }
  >
    <div className="mr-3">{icon}</div>
    {children}
  </RouterLink>
)

const MainLayout: React.FC = () => {
  const { user, logout } = useAuth()
  const [showUserMenu, setShowUserMenu] = React.useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <nav className="bg-white shadow-sm fixed w-full z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <BookOpen className="h-8 w-8 text-blue-600" />
              <h1 className="ml-2 text-xl font-bold text-gray-900">
                English Learning App
              </h1>
            </div>

            <div className="flex items-center">
              <div className="relative">
                <Button
                  variant="ghost"
                  className="flex items-center"
                  onClick={() => setShowUserMenu(!showUserMenu)}
                >
                  <span className="mr-2">{user?.username}</span>
                  <User className="h-5 w-5" />
                </Button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 ring-1 ring-black ring-opacity-5">
                    <button
                      className="flex w-full items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => {
                        setShowUserMenu(false)
                        logout()
                      }}
                    >
                      <LogOut className="mr-3 h-4 w-4" />
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Sidebar and Content */}
      <div className="flex pt-16">
        {/* Sidebar */}
        <div className="w-64 fixed h-full bg-white shadow-sm">
          <nav className="mt-5 px-4 space-y-2">
            <NavLink to="/dashboard" icon={<LayoutDashboard className="h-5 w-5" />}>
              Dashboard
            </NavLink>
            <NavLink to="/learn" icon={<BookOpen className="h-5 w-5" />}>
              Learn
            </NavLink>
            <NavLink to="/review" icon={<Repeat className="h-5 w-5" />}>
              Review
            </NavLink>
            <NavLink to="/progress" icon={<TrendingUp className="h-5 w-5" />}>
              Progress
            </NavLink>
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 ml-64">
          <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export default MainLayout