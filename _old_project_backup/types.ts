
export enum NavTab {
  DASHBOARD = 'dashboard',
  TUTOR = 'tutor',
  CREATOR = 'creator',
  VISION = 'vision'
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isThinking?: boolean;
}

export interface LearningPathItem {
  title: string;
  category: string;
  duration: string;
  image: string;
  description: string;
}

export interface PersonalityStyle {
  id: string;
  name: string;
  icon: string;
  description: string;
}

export interface UserProfile {
  name: string;
  hobbies: string;
  goals: string;
  onboarded: boolean;
}
