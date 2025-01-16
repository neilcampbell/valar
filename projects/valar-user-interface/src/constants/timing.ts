/**
 * Constants related to time and block rounds.
 */

import { getTimingConfig } from "@/utils/config/getTimingConfig";
import { DAYS_IN_MONTH, HOURS_IN_DAY, MINUTES_IN_HOUR, MONTHS_IN_YEAR, SECONDS_IN_MINUTE } from "./units";

const config = getTimingConfig();

// About block rounds
export const ASSUMED_BLOCK_TIME = config.assumedBlockTime; // [s]
export const BLOCKS_PER_DAY = SECONDS_IN_MINUTE * MINUTES_IN_HOUR * HOURS_IN_DAY / ASSUMED_BLOCK_TIME;
export const BLOCKS_PER_MONTH = BLOCKS_PER_DAY * DAYS_IN_MONTH;
export const BLOCKS_PER_YEAR = BLOCKS_PER_MONTH * MONTHS_IN_YEAR;

// About UI re-fetching update frequency
export const PARAM_UPDATE = config.paramUpdate; // [ms]
export const FETCH_INTERVAL = config.openDrawerFetchInterval; // [ms]
