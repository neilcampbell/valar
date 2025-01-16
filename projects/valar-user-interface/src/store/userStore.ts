import { UserInfo } from '@/interfaces/contracts/User';
import { KeyRegParams } from '@/lib/types';
import { create } from 'zustand';

export interface User {
  address: string;
  algo: bigint;
  assets: Map<bigint, bigint>;
  keyRegParams: KeyRegParams | undefined;
  trackedPerformance: boolean; 
  userInfo: UserInfo | undefined;
}

export interface UserStore {
  user: User | null;
  setUser: (user: UserStore['user']) => void;
}

const useUserStore = create<UserStore>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));

export default useUserStore;
