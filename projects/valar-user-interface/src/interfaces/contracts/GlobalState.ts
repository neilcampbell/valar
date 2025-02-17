import { Buffer } from "buffer";

type GlobalStateValue = {
  bytes: string;
  uint: number;
  type: number;
};

export type GlobalStateJSONConfig<T> = {
  [key: string]: {
    [K in keyof T]: {
      fieldName: K;
      getValue: (value: GlobalStateValue) => T[K];
    };
  }[keyof T];
};

export class GlobalState {
  /**
   * ======================================================================
   *       RaW GlobalState Object(not type cast) from Raw Data (JSON)
   * ======================================================================
   */

  static getRawGlobalStateFromJSON<T>(
    encodedStateEntries: Array<{ key: string; value: any }>,
    jsonConfig: GlobalStateJSONConfig<T>,
  ): Partial<T> {
    const globalState: Partial<T> = {};

    encodedStateEntries.forEach((item: any) => {
      const decodedKey = Buffer.from(item.key, "base64").toString("utf8");
      if (decodedKey in jsonConfig) {
        globalState[jsonConfig[decodedKey].fieldName] = jsonConfig[decodedKey].getValue(item.value);
      }
    });

    return globalState;
  }

  /**
   * ===========================================
   *       Decoded-Key Object from Raw Data
   * ===========================================
   */
  static getDecodedKeyState(encodedStateEntries: any): { [key: string]: any } {
    const gs: { [key: string]: any } = {};

    encodedStateEntries.forEach((item: any) => {
      const decodedKey = Buffer.from(item.key, "base64").toString("utf8");
      gs[decodedKey] = item.value;
    });

    return gs;
  }
}
