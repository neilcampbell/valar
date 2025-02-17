import { governanceAxios } from "@/lib/axios";

export class GovernanceApi {
  static async fetchGovCommitment(address: string): Promise<bigint | undefined> {
    try {
      if (import.meta.env.VITE_ALGOD_NETWORK === "localnet") {
        // For testing on localnet with emulated mainnet address with commitment
        address = "TI7VKESZJLM66XN5RAUHWW2GPBDC3FS4Y5VK4TYK5K27ZACGLJQTEPLCVE";
        // "HEM2TZSOXOX5RHQWRSO6MOPIZ23ORHZLWMZTSONR4Q4KJBH5MS6M5UDEHM";  // 32713 ALGO
        // "LICZGM5LLXH5CXUCFUJJYTHN2KXO63ZQJMQQPDOVTLRG6TKPZLLWZHRE74";  // 50750 ALGO
        // "TI7VKESZJLM66XN5RAUHWW2GPBDC3FS4Y5VK4TYK5K27ZACGLJQTEPLCVE";  // 27500 ALGO
      }

      const {
        data: { committed_algo_amount, is_eligible },
      } = await governanceAxios.get(`governors/` + address + `/`);

      const committedAlgoAmount = is_eligible ? BigInt(committed_algo_amount) : undefined;

      console.log("Your ALGO governance commitment: ", committedAlgoAmount);

      return committedAlgoAmount;
    } catch (err) {
      console.error("Error fetching governance data ::", err);
    }
  }
}
