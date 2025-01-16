/**
 * This file is based on: https://github.com/algorandfoundation/reti/blob/ea9d362d1e0ea0c864da816d69476283304b52e6/ui/src/utils/paramsCache.ts
 * which is licensed based on the following license:
 *
 * MIT License
 *
 * Copyright (c) 2024 Algorand Foundation
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 *
 *
 * Changes to this code are licensed under the same conditions as the rest of this project.
 */

import { ClientManager } from '@algorandfoundation/algokit-utils/types/client-manager'
import algosdk from 'algosdk'
import { getAlgodConfigFromViteEnvironment } from '@/utils/config/getAlgoClientConfigs'
import { SuggestedParamsWithMinFee } from 'algosdk/dist/types/types/transactions/base';
import { ASSUMED_BLOCK_TIME, PARAM_UPDATE } from '@/constants/timing';
import { FROM_BASE_TO_MILLI_MULTIPLIER } from '@/constants/units';

interface CachedParams {
  suggestedParams: SuggestedParamsWithMinFee;
  round: bigint;
  timestamp: number;
}

/**
 * This singleton class should be used to fetch suggested transaction parameters and current round.
 * It will cache the parameters for PARAM_UPDATE minutes to avoid refetching for every transaction.
 * It between cache updates, it estimates the current round based on elapsed time since last update
 * and ASSUMED_BLOCK_TIME.
 *
 * @method getSuggestedParams - Static method to fetch suggested transaction parameters.
 * @returns {Promise<SuggestedParamsWithMinFee>} Suggested transaction parameters with min fee.
 * @example
 * const suggestedParams = await ParamsCache.getSuggestedParams();
 * @see {@link https://developer.algorand.org/docs/rest-apis/algod/#get-v2transactionsparams}
 *
 * @method getRound - Static method to fetch current round.
 * @returns {Promise<bigint>} Suggested transaction parameters.
 * @example
 * const round = await ParamsCache.getRound();
 */
export class ParamsCache {
  private static instance: ParamsCache | null = null;
  private client: algosdk.Algodv2;
  private cache: CachedParams | null = null;
  private network: string | null = null;

  private constructor() {
    const algodConfig = getAlgodConfigFromViteEnvironment()
    this.client = ClientManager.getAlgodClient({
      server: algodConfig.server,
      port: algodConfig.port,
      token: algodConfig.token,
    });
    this.network = algodConfig.network;
  }

  public static async getSuggestedParams(): Promise<SuggestedParamsWithMinFee> {
    if (!this.instance) {
      this.instance = new ParamsCache();
    }
    return (await this.instance.fetchAndCacheParams()).suggestedParams;
  }

  public static async getRound(): Promise<bigint> {
    if (!this.instance) {
      this.instance = new ParamsCache();
    }
    return (await this.instance.fetchAndCacheParams()).round;
  }

  private async fetchAndCacheParams(): Promise<CachedParams> {
    const now = Date.now();
    const staleTime = PARAM_UPDATE;

    if (this.cache && (now - this.cache.timestamp) < staleTime) {
      if(this.network === "localnet"){
        return this.cache;
      } else {
        return {
          suggestedParams: this.cache.suggestedParams,
          round: this.cache.round + BigInt(Math.floor((now - this.cache.timestamp) / FROM_BASE_TO_MILLI_MULTIPLIER / ASSUMED_BLOCK_TIME)),
          timestamp: this.cache.timestamp,
        };
      }
    }

    const suggestedParams = await this.client.getTransactionParams().do()
    this.cache = {
      suggestedParams,
      round: BigInt(suggestedParams.firstRound),
      timestamp: now,
    }
    return this.cache;
  }

  // Reset instance for testing purposes
  public static resetInstance() {
    this.instance = null;
  }
}