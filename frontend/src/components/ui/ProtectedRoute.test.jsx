import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './ProtectedRoute.jsx'

const { state } = vi.hoisted(() => ({
  state: { user: null, loading: false },
}))

vi.mock('../../context/AuthContext.jsx', () => ({
  useAuth: () => state,
}))

function renderRoute() {
  return render(
    <MemoryRouter initialEntries={['/settings?tab=privacy']}>
      <Routes>
        <Route
          path="/settings"
          element={<ProtectedRoute><div>Private content</div></ProtectedRoute>}
        />
        <Route path="/login" element={<div>Login screen</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('renders children for a signed-in user', () => {
    state.user = { id: 'user-1', email: 'person@example.com' }
    state.loading = false
    renderRoute()

    expect(screen.getByText('Private content')).toBeInTheDocument()
  })

  it('shows a loader while the session is being checked', () => {
    state.user = null
    state.loading = true
    renderRoute()

    expect(screen.getByRole('status')).toHaveTextContent(/Checking your session/i)
    expect(screen.queryByText('Private content')).not.toBeInTheDocument()
  })

  it('redirects anonymous visitors to login', () => {
    state.user = null
    state.loading = false
    renderRoute()

    expect(screen.getByText('Login screen')).toBeInTheDocument()
    expect(screen.queryByText('Private content')).not.toBeInTheDocument()
  })
})
