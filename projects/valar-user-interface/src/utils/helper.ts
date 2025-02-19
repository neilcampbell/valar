import { ALGORAND_REWARDS } from "@/constants/smart-contracts";
import { BLOCKS_PER_YEAR } from "@/constants/timing";

export function estimateRateForRounds(currentRound: bigint, stakeOnline: bigint, rounds: bigint): number {
  const roundToPeriod = (round: bigint): number => {
    return Math.floor(Number(round) / ALGORAND_REWARDS.decayRounds);
  };

  const periodInit = roundToPeriod(ALGORAND_REWARDS.startRound);

  const getRewardAtRound = (round: bigint): number => {
    const periodCurr = roundToPeriod(round);
    const rewardAtRound = Math.floor(
      ALGORAND_REWARDS.startReward * (1 - ALGORAND_REWARDS.decayRate / 100) ** (periodCurr - periodInit),
    );
    return rewardAtRound;
  };

  const endRound = currentRound + rounds;
  const roundsRemainInFirstPeriod =
    BigInt(ALGORAND_REWARDS.decayRounds) - (currentRound % BigInt(ALGORAND_REWARDS.decayRounds));

  let rewards = 0;
  if (rounds <= roundsRemainInFirstPeriod) {
    rewards = Number(rounds) * getRewardAtRound(currentRound);
  } else {
    rewards += Number(roundsRemainInFirstPeriod) * getRewardAtRound(currentRound);

    const roundsIntoEndPeriod = endRound % BigInt(ALGORAND_REWARDS.decayRounds);
    rewards += Number(roundsIntoEndPeriod) * getRewardAtRound(endRound);

    for (
      let round = currentRound + roundsRemainInFirstPeriod;
      round < endRound - roundsIntoEndPeriod;
      round += BigInt(ALGORAND_REWARDS.decayRounds)
    ) {
      rewards += ALGORAND_REWARDS.decayRounds * getRewardAtRound(round);
    }
  }

  const returnRate = (rewards / Number(stakeOnline)) * 100;

  return returnRate;
}

export function estimateAPY(currentRound: bigint, stakeOnline: bigint): number {
  return estimateRateForRounds(currentRound, stakeOnline, BigInt(Math.floor(BLOCKS_PER_YEAR)));
}
