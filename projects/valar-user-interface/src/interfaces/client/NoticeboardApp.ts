import { NoticeboardClient } from "@/contracts/Noticeboard";
import { NoticeboardGlobalState } from "../contracts/Noticeboard";

export interface NoticeboardApp {
  appId: number
  client: NoticeboardClient
  globalState: NoticeboardGlobalState | undefined
}