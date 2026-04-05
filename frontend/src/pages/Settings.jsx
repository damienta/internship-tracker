import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

const inputClass = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
const labelClass = 'block text-xs font-semibold tracking-wide text-gray-600 uppercase mb-1'

function toSkillArray(value) {
  return value
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

function mergeSkills(existing, incoming) {
  const merged = [...existing]
  const seen = new Set(existing.map((s) => s.toLowerCase()))

  incoming.forEach((skill) => {
    const clean = String(skill || '').trim()
    if (!clean) return
    const key = clean.toLowerCase()
    if (!seen.has(key)) {
      seen.add(key)
      merged.push(clean)
    }
  })

  return merged
}

function getInvalidSkills(skills) {
  const validSkillPattern = /^[a-zA-Z0-9+#./()\-\s]{1,40}$/
  return skills.filter((skill) => !validSkillPattern.test(skill))
}

export default function Settings() {
  const { user, logout, updateUser } = useAuth()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')

  const [profile, setProfile] = useState({
    full_name: '',
    university: '',
    degree: '',
    skills: [],
    weekly_digest_enabled: false,
  })

  const [skillsInput, setSkillsInput] = useState('')
  const [availableSkills, setAvailableSkills] = useState([])
  const [selectedSkill, setSelectedSkill] = useState('')

  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_new_password: '',
  })

  const [deletePassword, setDeletePassword] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState('')
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false)
  const [showDeleteAccountModal, setShowDeleteAccountModal] = useState(false)
  const [showIdentityModal, setShowIdentityModal] = useState(false)
  const [identityForm, setIdentityForm] = useState({
    username: '',
    email: '',
    current_password: '',
  })

  useEffect(() => {
    if (!user?.id) {
      setLoading(false)
      return
    }

    const loadSettings = async () => {
      setLoading(true)
      try {
        const [profileRes, skillsRes] = await Promise.all([
          api.get(`/profile/${user.id}`),
          api.get('/skills'),
        ])

        const profileData = profileRes?.data?.profile || {}
        setUsername(profileRes?.data?.username || '')
        setEmail(profileRes?.data?.email || '')
        setIdentityForm((prev) => ({
          ...prev,
          username: profileRes?.data?.username || '',
          email: profileRes?.data?.email || '',
        }))

        setProfile((prev) => ({
          ...prev,
          ...profileData,
          skills: Array.isArray(profileData.skills) ? profileData.skills : [],
          weekly_digest_enabled: Boolean(profileData.weekly_digest_enabled),
        }))
        updateUser({
          username: profileRes?.data?.username || user?.username,
          email: profileRes?.data?.email || user?.email,
        })
        setSkillsInput((Array.isArray(profileData.skills) ? profileData.skills : []).join(', '))

        const skillList = Array.isArray(skillsRes?.data) ? skillsRes.data : []
        setAvailableSkills(skillList)
        setSelectedSkill(skillList[0] || '')
      } catch {
        toast.error('Error: Failed to load settings.')
      } finally {
        setLoading(false)
      }
    }

    loadSettings()
  }, [user?.id])

  const handleProfileChange = (e) => {
    const { name, value } = e.target
    setProfile((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const addSelectedSkill = () => {
    if (!selectedSkill) return
    const merged = mergeSkills(toSkillArray(skillsInput), [selectedSkill])
    setSkillsInput(merged.join(', '))
    toast.success('Skill added to your profile list.')
  }

  const handleNotificationToggle = (enabled) => {
    setProfile((prev) => ({ ...prev, weekly_digest_enabled: enabled }))
  }

  const saveProfile = async () => {
    if (!user?.id) return
    setSaving(true)
    try {
      const parsedSkills = toSkillArray(skillsInput)
      const invalidSkills = getInvalidSkills(parsedSkills)
      if (invalidSkills.length > 0) {
        toast.error(`Error: Invalid skill format: ${invalidSkills.join(', ')}`)
        return
      }

      const payload = {
        full_name: profile.full_name,
        university: profile.university,
        degree: profile.degree,
        skills: parsedSkills,
        weekly_digest_enabled: Boolean(profile.weekly_digest_enabled),
      }

      const { data } = await api.put(`/profile/${user.id}`, payload)
      const savedProfile = data?.profile || payload

      setProfile((prev) => ({
        ...prev,
        ...savedProfile,
        skills: Array.isArray(savedProfile.skills) ? savedProfile.skills : [],
        weekly_digest_enabled: Boolean(savedProfile.weekly_digest_enabled),
      }))
      setSkillsInput((Array.isArray(savedProfile.skills) ? savedProfile.skills : []).join(', '))

      toast.success('Settings saved.')
    } catch (err) {
      const message = err?.response?.data?.error || 'Failed to save settings.'
      toast.error(`Error: ${message}`)
    } finally {
      setSaving(false)
    }
  }

  const changePassword = async () => {
    if (!user?.id) return

    if (!passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_new_password) {
      toast.error('Error: Fill in all password fields.')
      return
    }

    if (passwordForm.new_password.length < 8) {
      toast.error('Error: New password must be at least 8 characters.')
      return
    }

    if (passwordForm.new_password !== passwordForm.confirm_new_password) {
      toast.error('Error: New passwords do not match.')
      return
    }

    try {
      await api.post('/account/change-password', {
        user_id: user.id,
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      })

      setPasswordForm({ current_password: '', new_password: '', confirm_new_password: '' })
      setShowChangePasswordModal(false)
      toast.success('Password updated.')
    } catch (err) {
      const message = err?.response?.data?.error || 'Could not update password.'
      toast.error(`Error: ${message}`)
    }
  }

  const deleteAccount = async () => {
    if (!user?.id) return

    if (!deletePassword) {
      toast.error('Error: Enter your password.')
      return
    }

    if (deleteConfirm !== 'DELETE') {
      toast.error('Error: Type DELETE to confirm account removal.')
      return
    }

    try {
      await api.delete(`/account/${user.id}`, { data: { password: deletePassword } })
      setShowDeleteAccountModal(false)
      setDeletePassword('')
      setDeleteConfirm('')
      logout()
      toast.success('Account deleted.')
      navigate('/register')
    } catch (err) {
      const message = err?.response?.data?.error || 'Could not delete account.'
      toast.error(`Error: ${message}`)
    }
  }

  const updateIdentity = async () => {
    if (!user?.id) return

    const newUsername = String(identityForm.username || '').trim()
    const newEmail = String(identityForm.email || '').trim().toLowerCase()
    const currentPassword = String(identityForm.current_password || '')

    if (!currentPassword) {
      toast.error('Error: Enter your current password.')
      return
    }

    if (!newUsername || !newEmail) {
      toast.error('Error: Username and email are required.')
      return
    }

    try {
      const { data } = await api.patch('/account/id', {
        user_id: user.id,
        username: newUsername,
        email: newEmail,
        current_password: currentPassword,
      })

      const updatedUser = data?.user || {}
      setUsername(updatedUser.username || newUsername)
      setEmail(updatedUser.email || newEmail)
      setIdentityForm({ username: updatedUser.username || newUsername, email: updatedUser.email || newEmail, current_password: '' })
      updateUser({ username: updatedUser.username || newUsername, email: updatedUser.email || newEmail })
      setShowIdentityModal(false)
      toast.success('Username/email updated.')
    } catch (err) {
      const message = err?.response?.data?.error || 'Could not update username/email.'
      toast.error(`Error: ${message}`)
    }
  }

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-10">
        <p className="text-sm text-gray-500">Loading settings...</p>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-10 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">User Settings</h1>
          <p className="text-sm text-gray-500">Manage your profile, skills, and account basics.</p>
        </div>

        <button
          type="button"
          onClick={saveProfile}
          disabled={saving}
          className="px-5 py-2.5 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>

      <section className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Username</label>
            <input className={`${inputClass} bg-gray-50`} value="" placeholder={username || 'username'} disabled />
          </div>

          <div>
            <label className={labelClass}>Email</label>
            <input className={`${inputClass} bg-gray-50`} value="" placeholder={email || 'email@example.com'} disabled />
          </div>

          <div>
            <label className={labelClass}>Full Name</label>
            <input
              name="full_name"
              className={inputClass}
              value={profile.full_name && profile.full_name !== 'None' ? profile.full_name : ''}
              onChange={handleProfileChange}
              placeholder="e.g. John Doe"
            />
          </div>

          <div>
            <label className={labelClass}>University</label>
            <input
              name="university"
              className={inputClass}
              value={profile.university && profile.university !== 'None' ? profile.university : ''}
              onChange={handleProfileChange}
              placeholder="e.g. University of Southampton"
            />
          </div>

          <div className="md:col-span-2">
            <label className={labelClass}>Degree</label>
            <input
              name="degree"
              className={inputClass}
              value={profile.degree && profile.degree !== 'None' ? profile.degree : ''}
              onChange={handleProfileChange}
              placeholder="e.g. BSc Computer Science"
            />
          </div>
        </div>
      </section>

      <section className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Skills</h2>
        <p className="text-sm text-gray-500 mb-4">Select from suggested skills to add them to your list.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Your Skills (comma-separated)</label>
            <input
              className={inputClass}
              value={skillsInput}
              onChange={(e) => setSkillsInput(e.target.value)}
              placeholder="python, sql, react, docker"
            />
          </div>

          <div>
            <label className={labelClass}>Select From Suggested Skills</label>
            <div className="flex gap-2">
              <select
                className={inputClass}
                value={selectedSkill}
                onChange={(e) => setSelectedSkill(e.target.value)}
              >
                {availableSkills.map((skill) => (
                  <option key={skill} value={skill}>{skill}</option>
                ))}
              </select>
              <button
                type="button"
                onClick={addSelectedSkill}
                className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 whitespace-nowrap"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Notifications</h2>
        <p className="text-sm text-gray-500 mb-4">Toggle whether notification preferences are enabled for your account.</p>

        <div className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 p-3">
          <p className="text-sm font-semibold text-slate-900">Enable notifications</p>
          <label className="inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              checked={Boolean(profile.weekly_digest_enabled)}
              onChange={(e) => handleNotificationToggle(e.target.checked)}
            />
          </label>
        </div>
      </section>

      <section className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Account Basics</h2>

        <div className="space-y-4">
          <div className="p-4 border border-gray-200 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-3">Account Details</h3>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setShowChangePasswordModal(true)}
                className="px-4 py-2 text-sm rounded-lg bg-slate-800 text-white hover:bg-slate-900"
              >
                Change Password
              </button>
              <button
                type="button"
                onClick={() => setShowIdentityModal(true)}
                className="px-4 py-2 text-sm rounded-lg bg-slate-800 text-white hover:bg-slate-900"
              >
                Update Username/Email
              </button>
            </div>
          </div>

          <div className="p-4 border border-gray-200 rounded-lg">
            <h3 className="font-semibold text-red-700 mb-2">Delete Account</h3>
            <button
              type="button"
              onClick={() => setShowDeleteAccountModal(true)}
              className="px-4 py-2 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700"
            >
              Delete My Account
            </button>
          </div>
        </div>
      </section>

      {showChangePasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-md bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Confirm Password Change</h3>
            <p className="text-sm text-gray-600 mb-4">Enter your current password and your new password twice.</p>

            <div className="space-y-3">
              <div>
                <label className={labelClass}>Current Password</label>
                <input
                  type="password"
                  className={inputClass}
                  value={passwordForm.current_password}
                  onChange={(e) => setPasswordForm((prev) => ({ ...prev, current_password: e.target.value }))}
                />
              </div>

              <div>
                <label className={labelClass}>New Password</label>
                <input
                  type="password"
                  className={inputClass}
                  value={passwordForm.new_password}
                  onChange={(e) => setPasswordForm((prev) => ({ ...prev, new_password: e.target.value }))}
                />
              </div>

              <div>
                <label className={labelClass}>New Password Again</label>
                <input
                  type="password"
                  className={inputClass}
                  value={passwordForm.confirm_new_password}
                  onChange={(e) => setPasswordForm((prev) => ({ ...prev, confirm_new_password: e.target.value }))}
                />
              </div>
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                className="px-3 py-2 text-sm rounded-lg border border-gray-300 hover:bg-gray-50"
                onClick={() => {
                  setShowChangePasswordModal(false)
                  setPasswordForm({ current_password: '', new_password: '', confirm_new_password: '' })
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="px-3 py-2 text-sm rounded-lg bg-slate-800 text-white hover:bg-slate-900"
                onClick={changePassword}
              >
                Confirm Change
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteAccountModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-md bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-lg font-semibold text-red-700 mb-1">Delete Account</h3>
            <p className="text-sm text-gray-600 mb-4">This action cannot be undone.</p>

            <div className="space-y-3">
              <div>
                <label className={labelClass}>Confirm Password</label>
                <input
                  type="password"
                  className={inputClass}
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  placeholder="Enter your password"
                />
              </div>

              <div>
                <label className={labelClass}>Type DELETE</label>
                <input
                  className={inputClass}
                  value={deleteConfirm}
                  onChange={(e) => setDeleteConfirm(e.target.value)}
                  placeholder="DELETE"
                />
              </div>
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                className="px-3 py-2 text-sm rounded-lg border border-gray-300 hover:bg-gray-50"
                onClick={() => {
                  setShowDeleteAccountModal(false)
                  setDeletePassword('')
                  setDeleteConfirm('')
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="px-3 py-2 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700"
                onClick={deleteAccount}
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {showIdentityModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-md bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Update Username and Email</h3>
            <p className="text-sm text-gray-600 mb-4">Confirm with your current password to save changes.</p>

            <div className="space-y-3">
              <div>
                <label className={labelClass}>New Username</label>
                <input
                  className={inputClass}
                  value={identityForm.username}
                  onChange={(e) => setIdentityForm((prev) => ({ ...prev, username: e.target.value }))}
                />
              </div>

              <div>
                <label className={labelClass}>New Email</label>
                <input
                  type="email"
                  className={inputClass}
                  value={identityForm.email}
                  onChange={(e) => setIdentityForm((prev) => ({ ...prev, email: e.target.value }))}
                />
              </div>

              <div>
                <label className={labelClass}>Current Password</label>
                <input
                  type="password"
                  className={inputClass}
                  value={identityForm.current_password}
                  onChange={(e) => setIdentityForm((prev) => ({ ...prev, current_password: e.target.value }))}
                />
              </div>
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                className="px-3 py-2 text-sm rounded-lg border border-gray-300 hover:bg-gray-50"
                onClick={() => {
                  setShowIdentityModal(false)
                  setIdentityForm((prev) => ({ ...prev, current_password: '' }))
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="px-3 py-2 text-sm rounded-lg bg-slate-800 text-white hover:bg-slate-900"
                onClick={updateIdentity}
              >
                Confirm Update
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
