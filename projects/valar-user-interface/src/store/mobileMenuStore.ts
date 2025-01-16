import { create } from "zustand";

interface MobileMenuState {
  mobileMenuOpen: boolean;
  setMobileMenuOpen: (value: boolean) => void;
}

const useMobileMenuStore = create<MobileMenuState>((set) => ({
  mobileMenuOpen: false,
  setMobileMenuOpen: (value) => set(() => ({ mobileMenuOpen: value })),
}));

export default useMobileMenuStore;
