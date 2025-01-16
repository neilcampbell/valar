/**
 * Constants about Terms & Conditions.
 */

import { getPlatformConfig } from "@/utils/config/getPlatformConfig";

// Get platform configuration
const config = getPlatformConfig();

/**
 * -----------------------------------------------------
 * -----------------------------------------------------
 *         SHA256 of latest Terms & Conditions
 * -----------------------------------------------------
 * -----------------------------------------------------
 */
export const TC_LATEST = config.tc;

/**
 * -----------------------------------------------------
 * -----------------------------------------------------
 *    Resolving SHA256 of Terms & Conditions to links
 * -----------------------------------------------------
 * -----------------------------------------------------
 */
export const TERMS_AND_CONDITIONS: Map<string, string> = new Map([
  ["d0e93dc94155a9cbafed736d945c5c0004d2d8a653e0fad1b57358185e08f2fb", "https://github.com/ValarStaking/valar/tree/master/terms-of-use/valar-terms-of-use_2025-01-15_d0e93dc94155a9cbafed736d945c5c0004d2d8a653e0fad1b57358185e08f2fb.pdf"],
]);

