import { ValTermsPricingInterface, ValTermsStakeLimitsInterface, ValTermsTimingInterface, ValTermsWarningsInterface } from "@/interfaces/contracts/ValidatorAd";

export type PricingSectionTypeContract = {
  currency: bigint;
  setupFee: bigint;
  operationalFee: bigint;
};

export type EligibilitySectionType = {
  asa1Amount: bigint;
  asa1Id: bigint;
  asa2Amount: bigint;
  asa2Id: bigint;
};

export type TimingSectionTypeContract = {
  roundsSetup: bigint;
  roundsConfirm: bigint;
};

export type DataSectionsType = {
  pricing: PricingSectionTypeContract | ValTermsPricingInterface;
  stakeLimits: undefined | ValTermsStakeLimitsInterface;
  warnings: ValTermsWarningsInterface;
  timings: TimingSectionTypeContract | ValTermsTimingInterface;
  eligibility: EligibilitySectionType;
};