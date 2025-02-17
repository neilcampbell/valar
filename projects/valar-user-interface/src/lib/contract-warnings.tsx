import { algoBigIntToDisplay } from "@/utils/convert";

import { MIN_ALGO_STAKE_FOR_REWARDS } from "../constants/smart-contracts";

export type ContractWarning = {
  type: "governance-commitment" | "rewards-pay" | "rewards-base" | "existing-contract";
  param?: any;
};

export interface WarningConfig {
  title: string;
  getMessage: (param?: any) => React.ReactNode;
}

export const ContractWarningConfig: Record<string, WarningConfig> = {
  /**
   * ===============================================
   *  Account Less then Min_Algo_Stake_For_Rewards
   * ===============================================
   */

  "rewards-base": {
    title: "Staking Rewards",
    getMessage: () => {
      const retiURL = import.meta.env.VITE_RETI_URL;
      return (
        <>
          Your current balance is below {algoBigIntToDisplay(BigInt(MIN_ALGO_STAKE_FOR_REWARDS), "ceil", true, 0)},
          which is the minimum required to be eligible for staking rewards.{" "}
          {retiURL && retiURL !== "null" && (
            <span>
              You can earn staking rewards with your current balance using{" "}
              <a href={retiURL} className="text-secondary" target="_blank" rel="noopener noreferrer">
                Valar's Reti staking pool
              </a>
              .
            </span>
          )}
        </>
      );
    },
  },

  /**
   * ================================================================
   *  Account Less then Min_Algo_Stake_For_Rewards after Payment
   * ================================================================
   */

  "rewards-pay": {
    title: "Staking Rewards",
    getMessage: () => (
      <>
        After paying, your balance will be below{" "}
        {algoBigIntToDisplay(BigInt(MIN_ALGO_STAKE_FOR_REWARDS), "ceil", true, 0)}, which is the minimum required to be
        eligible for staking rewards. Consider topping up your ALGO balance or choose another payment currency before
        continuing.
      </>
    ),
  },

  /**
   * ===================================================
   *  Account Below Governance Commitment after Payment
   * ===================================================
   */
  "governance-commitment": {
    title: "Governance Commitment",
    getMessage: (param: bigint | number) => {
      return (
        <>
          After paying, your balance will be below your Algorand governance commitment (
          {algoBigIntToDisplay(BigInt(param), "ceil", true, 0)}). You will become ineligible in governance. Consider
          topping up your ALGO balance or choose another payment currency before continuing.
        </>
      );
    },
  },

  /**
   * ===========================================
   *   Existing Contract for the given address
   * ===========================================
   */
  "existing-contract": {
    title: "Existing Contract",
    getMessage: () => (
      <>
        You already have an active contract for the given address. You can find it in{" "}
        <a href="/dashboard" className="text-secondary">
          Dashboard
        </a>
        .
      </>
    ),
  },
};
