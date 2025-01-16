/**
 * Constants about smart contract states.
 */

import { strToBytes } from "@/utils/convert"

// Delegator Contract State
export const DC_STATE_READY = strToBytes('\x03');
export const DC_STATE_SUBMITTED = strToBytes('\x04');
export const DC_STATE_LIVE = strToBytes('\x05');
export const DC_STATE_ENDED_NOT_SUBMITTED = strToBytes('\x10');
export const DC_STATE_ENDED_NOT_CONFIRMED = strToBytes('\x11');
export const DC_STATE_ENDED_LIMITS = strToBytes('\x12');
export const DC_STATE_ENDED_WITHDREW = strToBytes('\x13');
export const DC_STATE_ENDED_EXPIRED = strToBytes('\x14');
export const DC_STATE_ENDED_SUSPENDED = strToBytes('\x15');
export const DC_STATE_ENDED_CANNOT_PAY = strToBytes('\x16');
export const DC_STATE_ENDED_MASK = strToBytes('\x10');

// Validator Ad States
export const VA_STATE_CREATED = strToBytes('\x01');
export const VA_STATE_SET = strToBytes('\x04');
export const VA_STATE_READY = strToBytes('\x05');
export const VA_STATE_NOT_READY = strToBytes('\x06');
export const VA_STATE_NOT_LIVE = strToBytes('\x07');
