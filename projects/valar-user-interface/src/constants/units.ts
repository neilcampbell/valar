/**
 * Constants about units and for conversion of units.
 */

import { AssetAmountUnit, AssetDisplay, TimeDisplay, TimeUnit } from "@/lib/types";
import { getUnitsConfig } from "@/utils/config/getUnitsConfig";

const config = getUnitsConfig();

// About time
export const SECONDS_IN_MINUTE = 60;
export const MINUTES_IN_HOUR = 60;
export const HOURS_IN_DAY = 24;
export const DAYS_IN_MONTH = 30;
export const MONTHS_IN_YEAR = 12;

// About metric prefixes
export const FROM_BASE_TO_MILLI_MULTIPLIER = 1_000;
export const FROM_BASE_TO_MICRO_MULTIPLIER = 1_000_000;
export const FROM_MILLI_TO_NANO_MULTIPLIER = 1_000_000;
export const ONE_IN_PPM = 1_000_000;

// Units for time parameters
export class TimeParams {
  static setup: TimeDisplay = {
    unit: config.TimeParams.setup.unit as TimeUnit,
    decimals: config.TimeParams.setup.decimals,
  };
  static confirmation: TimeDisplay = {
    unit: config.TimeParams.confirmation.unit as TimeUnit,
    decimals: config.TimeParams.confirmation.decimals,
  };
  static stake: TimeDisplay = {
    unit: config.TimeParams.stake.unit as TimeUnit,
    decimals: config.TimeParams.stake.decimals,
  };
  static warn: TimeDisplay = {
    unit: config.TimeParams.warn.unit as TimeUnit,
    decimals: config.TimeParams.warn.decimals,
  };
}

export const ALGORAND_DEPOSIT_DECIMALS = config.ALGORAND_DEPOSIT_DECIMALS;

// Units for asset parameters
export class AssetParams {
  static setup: AssetDisplay = {
    unit: config.AssetParams.setup.unit as AssetAmountUnit,
    decimals: config.AssetParams.setup.decimals,
  };
  static total: AssetDisplay = {
    unit: config.AssetParams.total.unit as AssetAmountUnit,
    decimals: config.AssetParams.total.decimals,
  };
  static opMonth: AssetDisplay = {
    unit: config.AssetParams.opMonth.unit as AssetAmountUnit,
    decimals: config.AssetParams.opMonth.decimals,
  };
  static opDuration: AssetDisplay = {
    unit: config.AssetParams.opDuration.unit as AssetAmountUnit,
    decimals: config.AssetParams.opDuration.decimals,
  };
  static opMin: AssetDisplay = {
    unit: config.AssetParams.opMin.unit as AssetAmountUnit,
    decimals: config.AssetParams.opMin.decimals,
  };
  static opVar: AssetDisplay = {
    unit: config.AssetParams.opVar.unit as AssetAmountUnit,
    decimals: config.AssetParams.opVar.decimals,
  };
}

// APY display precision
export const APY_DECIMALS = config.APY_DECIMALS;
