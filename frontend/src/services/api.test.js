import { beforeEach, describe, expect, it } from 'vitest'
import { tokenStore } from './api.js'

describe('tokenStore', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('stores and reads a session', () => {
    tokenStore.setSession({
      access_token: 'access-1',
      refresh_token: 'refresh-1',
      user: { id: 'user-1', email: 'person@example.com' },
    })

    expect(tokenStore.getAccess()).toBe('access-1')
    expect(tokenStore.getRefresh()).toBe('refresh-1')
    expect(tokenStore.getUser()).toEqual({ id: 'user-1', email: 'person@example.com' })
  })

  it('updates only the stored user when a profile changes', () => {
    tokenStore.setSession({ access_token: 'access-1', refresh_token: 'refresh-1', user: { id: 'user-1' } })
    tokenStore.setUser({ id: 'user-1', full_name: 'Avery Chen' })

    expect(tokenStore.getUser().full_name).toBe('Avery Chen')
    expect(tokenStore.getAccess()).toBe('access-1')
  })

  it('clears every stored key', () => {
    tokenStore.setSession({ access_token: 'access-1', refresh_token: 'refresh-1', user: { id: 'user-1' } })
    tokenStore.clear()

    expect(tokenStore.getAccess()).toBe('')
    expect(tokenStore.getRefresh()).toBe('')
    expect(tokenStore.getUser()).toBeNull()
  })

  it('returns null for malformed stored user JSON', () => {
    window.localStorage.setItem('roleprint.user', '{not-json')
    expect(tokenStore.getUser()).toBeNull()
  })
})
