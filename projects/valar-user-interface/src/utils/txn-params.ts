import { ParamsCache } from './paramsCache'

export class TxnParams {
  static async setTxnFees(feeMultiplier: number, isFlatFee: boolean) {
    const sp = await ParamsCache.getSuggestedParams();
    sp.fee = feeMultiplier * sp.minFee;
    sp.flatFee = isFlatFee;

    return sp;
  }
}
