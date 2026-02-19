// Domain Entity - User
export interface User {
  id: number;
  uuid: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: 'admin' | 'teacher' | 'student';
  active: boolean;
  created_at: string;
  last_login_at: string;
}

export interface UserProfile {
  id: string;
  userId: string;
  avatar?: string;
  title?: string;
  department?: string;
  bio?: string;
}
