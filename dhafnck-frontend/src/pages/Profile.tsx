import React, { useContext, useState } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { User, Mail, Shield, Calendar, Edit2, Save, X, Lock, Settings } from 'lucide-react';

export const Profile: React.FC = () => {
  const authContext = useContext(AuthContext);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState<'account' | 'security' | 'preferences'>('account');
  const [formData, setFormData] = useState({
    username: authContext?.user?.username || '',
    email: authContext?.user?.email || '',
  });

  if (!authContext) {
    return <div>Loading...</div>;
  }

  const { user } = authContext;

  if (!user) {
    return <div>Please log in to view your profile.</div>;
  }

  const handleEdit = () => {
    setIsEditing(true);
    setFormData({
      username: user.username,
      email: user.email,
    });
  };

  const handleCancel = () => {
    setIsEditing(false);
    setFormData({
      username: user.username,
      email: user.email,
    });
  };

  const handleSave = async () => {
    try {
      // TODO: Implement API call to update user profile
      alert("Profile updated successfully!");
      setIsEditing(false);
    } catch (error) {
      alert("Failed to update profile. Please try again.");
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Profile</h1>
        <p className="text-gray-600 mt-2">Manage your account settings and preferences</p>
      </div>

      <div className="grid gap-6">
        {/* Profile Header Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="h-20 w-20 rounded-full bg-primary flex items-center justify-center text-white text-2xl font-bold">
                  {getInitials(user.username)}
                </div>
                <div>
                  <CardTitle className="text-2xl">{user.username}</CardTitle>
                  <CardDescription className="text-base">{user.email}</CardDescription>
                </div>
              </div>
              {!isEditing ? (
                <Button onClick={handleEdit} variant="outline">
                  <Edit2 className="mr-2 h-4 w-4" />
                  Edit Profile
                </Button>
              ) : (
                <div className="space-x-2">
                  <Button onClick={handleSave} size="sm">
                    <Save className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                  <Button onClick={handleCancel} variant="outline" size="sm">
                    <X className="mr-2 h-4 w-4" />
                    Cancel
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
        </Card>

        {/* Simple Tab Navigation */}
        <div className="flex space-x-4 border-b">
          <button
            className={`pb-2 px-1 ${activeTab === 'account' ? 'border-b-2 border-primary font-semibold' : ''}`}
            onClick={() => setActiveTab('account')}
          >
            <User className="inline mr-2 h-4 w-4" />
            Account
          </button>
          <button
            className={`pb-2 px-1 ${activeTab === 'security' ? 'border-b-2 border-primary font-semibold' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            <Lock className="inline mr-2 h-4 w-4" />
            Security
          </button>
          <button
            className={`pb-2 px-1 ${activeTab === 'preferences' ? 'border-b-2 border-primary font-semibold' : ''}`}
            onClick={() => setActiveTab('preferences')}
          >
            <Settings className="inline mr-2 h-4 w-4" />
            Preferences
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'account' && (
          <Card>
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
              <CardDescription>
                Update your account details and personal information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="username" className="text-sm font-medium">
                  <User className="inline mr-2 h-4 w-4" />
                  Username
                </label>
                <Input
                  id="username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  disabled={!isEditing}
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  <Mail className="inline mr-2 h-4 w-4" />
                  Email Address
                </label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={!isEditing}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  <Calendar className="inline mr-2 h-4 w-4" />
                  User ID
                </label>
                <Input value={user.id} disabled />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  <Shield className="inline mr-2 h-4 w-4" />
                  Roles
                </label>
                <div className="flex gap-2">
                  {user.roles.map((role) => (
                    <span
                      key={role}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {role}
                    </span>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === 'security' && (
          <Card>
            <CardHeader>
              <CardTitle>Security Settings</CardTitle>
              <CardDescription>
                Manage your password and security preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <Button variant="outline" className="w-full">
                  Change Password
                </Button>
                <Button variant="outline" className="w-full">
                  Enable Two-Factor Authentication
                </Button>
                <Button variant="outline" className="w-full">
                  Manage Sessions
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === 'preferences' && (
          <Card>
            <CardHeader>
              <CardTitle>Preferences</CardTitle>
              <CardDescription>
                Customize your application experience
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="theme" className="text-sm font-medium">Theme</label>
                <select
                  id="theme"
                  className="w-full px-3 py-2 border rounded-md"
                  disabled={!isEditing}
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="system">System</option>
                </select>
              </div>
              <div className="space-y-2">
                <label htmlFor="notifications" className="text-sm font-medium">Email Notifications</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="notifications"
                    className="rounded"
                    disabled={!isEditing}
                  />
                  <label htmlFor="notifications" className="font-normal">
                    Receive email notifications for important updates
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};