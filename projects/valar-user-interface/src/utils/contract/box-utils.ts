import { noticeboardAppID } from '@/constants/platform'
import { BoxReference } from '@algorandfoundation/algokit-utils/types/app'
import AlgodClient from 'algosdk/dist/types/client/v2/algod/algod'
import { ABIAddressType } from 'algosdk'

export interface BoxExistsResponse {
  value: Uint8Array
  exists: boolean
}

export class BoxUtils {

  static async getNoticeboardBox(algodClient: AlgodClient, boxName: Uint8Array): Promise<BoxExistsResponse> {
    return BoxUtils.getAppBox(algodClient, noticeboardAppID, boxName)
  }

  static async getAppBox(algodClient: AlgodClient, appId: number, boxName: Uint8Array): Promise<BoxExistsResponse> {
    try {
      const { value } = await algodClient.getApplicationBoxByName(appId, boxName).do()
      return {
        value,
        exists: true,
      }
    } catch (e) {
      return {
        value: new Uint8Array(0),
        exists: false,
      }
    }
  }

  static calculateBoxMBR(boxByteLength: number, boxName: Uint8Array): number {
    const boxNameSize = boxName.length ?? 0
    return 2500 + 400 * (boxNameSize + boxByteLength)
  }

  static createBoxes(appId: number, values: string[]): BoxReference[] {
    return values.map((value) => ({ appId: appId, name: new ABIAddressType().encode(value) }))
  }

  static createBoxesWithLength(appId: number, value: Uint8Array, length: number): BoxReference[] {
    return new Array(length).fill({ appId: appId, name: value })
  }
}
