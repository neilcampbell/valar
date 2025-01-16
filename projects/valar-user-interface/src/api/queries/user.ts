import { NoticeboardGlobalState } from "@/interfaces/contracts/Noticeboard";
import { UserInfo } from "@/interfaces/contracts/User";
import AlgodClient from "algosdk/dist/types/client/v2/algod/algod";

export async function fetchAllVal(
  algodClient: AlgodClient,
  NoticeboardGlobalState: NoticeboardGlobalState,
): Promise<Map<string, UserInfo> | undefined> {
  const validators: Map<string, UserInfo> = new Map();

  let currUser = NoticeboardGlobalState.dllVal.userFirst;

  for (let i = 1; i <= NoticeboardGlobalState.dllVal.cntUsers; i++) {
    const info = await UserInfo.getUserInfo(algodClient, currUser);
    if (info != undefined) {
      validators.set(currUser, info)
    }
    currUser = info!.nextUser;
  }

  return validators
}
