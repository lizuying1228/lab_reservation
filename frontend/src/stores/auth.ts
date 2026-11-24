import { defineStore } from 'pinia'
import { ref } from 'vue'
import http from '../api/http'

export type Role = 'superuser' | 'student' | 'labadmin' | 'unknown'

export const useAuthStore = defineStore('auth', () => {
  const access = ref(localStorage.getItem('access') || '')
  const refresh = ref(localStorage.getItem('refresh') || '')
  const profile = ref<any>(null)
  const role = ref<Role>('unknown')
  const identity = ref<any>(null)

  async function login(username: string, password: string) {
    const { data } = await http.post('/users/login/', { username, password })
    access.value = data.access
    refresh.value = data.refresh
    localStorage.setItem('access', data.access)
    localStorage.setItem('refresh', data.refresh)
    await loadIdentity()
  }

  async function loadIdentity() {
    const { data } = await http.get('/users/me/')
    profile.value = data.user || data
    // /users/ is superuser-only; check it first because superusers may also
    // have permission to read student/admin resources.
    try {
      await http.get('/users/', { params: { page_size: 1 } })
      role.value = 'superuser'
      identity.value = null
      return
    } catch {}
    try {
      const { data: adminData } = await http.get('/labadmins/', { params: { page_size: 100 } })
      const rows = Array.isArray(adminData) ? adminData : (adminData.results || [])
      const own = rows.find((item: any) => item.user?.id === profile.value?.id || item.user === profile.value?.id)
      if (own || rows.length) {
        role.value = 'labadmin'
        identity.value = own || rows[0]
        return
      }
    } catch {}
    try {
      const { data: studentData } = await http.get('/students/', { params: { page_size: 100 } })
      const rows = Array.isArray(studentData) ? studentData : (studentData.results || [])
      const own = rows.find((item: any) => item.user?.id === profile.value?.id || item.user === profile.value?.id)
      if (own || rows.length) {
        role.value = 'student'
        identity.value = own || rows[0]
        return
      }
    } catch {}
    role.value = 'unknown'
    identity.value = null
  }

  async function logout() {
    try {
      if (refresh.value) await http.post('/users/logout/', { refresh: refresh.value })
    } finally {
      access.value = ''
      refresh.value = ''
      profile.value = null
      identity.value = null
      role.value = 'unknown'
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
    }
  }

  function clearLocal() {
    access.value = ''
    refresh.value = ''
    profile.value = null
    identity.value = null
    role.value = 'unknown'
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
  }

  return { access, refresh, profile, role, identity, login, loadIdentity, logout, clearLocal }
})
