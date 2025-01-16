import { SUGGESTED_MAX_STAKE_BUFFER } from "../../constants/platform";
import { ValidatorAdGlobalState } from "@/interfaces/contracts/ValidatorAd";
import { StakeReqs } from "@/lib/types";
import { FROM_BASE_TO_MICRO_MULTIPLIER, FROM_BASE_TO_MILLI_MULTIPLIER, FROM_MILLI_TO_NANO_MULTIPLIER, ONE_IN_PPM } from "@/constants/units";

export function calculateFeeRound(
  maxStake: bigint,
  feeRoundMin: bigint,
  feeRoundVar: bigint,
): bigint {
  const stakeScaled = Math.floor(Number(maxStake) / FROM_BASE_TO_MICRO_MULTIPLIER);
  const v = Math.floor((Number(feeRoundVar) * stakeScaled) / FROM_MILLI_TO_NANO_MULTIPLIER);
  return BigInt(Math.max(Number(feeRoundMin), v));
}

export function calculateOperationalFee(
  feeRound: bigint,
  roundEnd: bigint,
  roundStart: bigint,
): bigint {
  return (
    BigInt(Math.floor((Number(feeRound) * Number(roundEnd - roundStart)) / FROM_BASE_TO_MILLI_MULTIPLIER))
  );
}

export function calculateNodeRunnerFee(
  stakeReqs: StakeReqs,
  gsValAd: ValidatorAdGlobalState,
): bigint {
  const maxStake = adjustedMaxStakeForGratis(stakeReqs, gsValAd);
  const feeRound = calculateFeeRound(
    maxStake,
    gsValAd.termsPrice.feeRoundMin,
    gsValAd.termsPrice.feeRoundVar,
  );
  const feeSetup = gsValAd.termsPrice.feeSetup;
  const fee = feeSetup + calculateOperationalFee(feeRound, stakeReqs.duration, 0n);

  return fee;
}

export function adjustedMaxStakeForGratis(
  stakeReqs: StakeReqs,
  gsValAd: ValidatorAdGlobalState,
): bigint {
  
  const maxStake = Math.round(Number(stakeReqs.maxStake) / (1 + Number(gsValAd.termsStake.stakeGratis) / ONE_IN_PPM));

  return BigInt(maxStake);
}

export function calculateGivenMaxStake(
  maxStake: bigint,
  gsValAd: ValidatorAdGlobalState,
): bigint {

  let adjusted = BigInt(Math.floor(Number(maxStake) * (1 + Number(gsValAd.termsStake.stakeGratis) / ONE_IN_PPM)));
  if(adjusted > gsValAd.termsStake.stakeMax){
    adjusted = gsValAd.termsStake.stakeMax;
  }

  return BigInt(adjusted);
}

export function calculateFeesPartner(
  partnerCommission: bigint,
  feeSetup: bigint,
  feeRound: bigint,
): [bigint, bigint] {
  const feeSetupPartner = Math.floor((Number(feeSetup) * Number(partnerCommission)) / ONE_IN_PPM);
  const feeRoundPartner = Math.floor((Number(feeRound) * Number(partnerCommission)) / ONE_IN_PPM);

  return [BigInt(feeSetupPartner), BigInt(feeRoundPartner)];
}

export function getSuggestedMaxStake(
  algo: bigint,
): bigint {
  /** Calculate suggested max stake [microAlgo] by increasing current stake [microAlgo] for suggested relative buffer [%].
   * Round to nearest ALGO.
  */
  return BigInt(
    Math.floor(
      Math.ceil(
        Number(algo) * (1 + SUGGESTED_MAX_STAKE_BUFFER / 100) / 10**6
      ) * 10**6
    )
  );
}
