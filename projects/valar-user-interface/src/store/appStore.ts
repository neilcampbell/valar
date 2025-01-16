import { create } from 'zustand';

interface AppState {
  user: { id: string; walletAddress: string } | null;
  setUser: (user: AppState['user']) => void;
}

const useAppStore = create<AppState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));

export default useAppStore;
