
from smart_contracts.artifacts.noticeboard.client import (
    NoticeboardAssetInfo,
    NoticeboardFees,
    NoticeboardTermsNodeLimits,
    NoticeboardTermsTiming,
)

# -----------------------------------
# -----        Constants        -----
# -----------------------------------
# All values assume block times defined below, where relevant
ASSUMED_BLOCK_TIME = 2.8 # In seconds
BLOCKS_PER_DAY = 24 * 60 * 60 / ASSUMED_BLOCK_TIME

# --- --- --- Noticeboard state --- --- ---
NB_STATE = "SET"



# ----------------------------------
# -------  Noticeboard terms -------
# ----------------------------------
TC_SHA256 = bytes([0xBC] * 32)  # SHA256 of Terms&Conditions

NOTICEBOARD_FEES = NoticeboardFees(
    commission_min = 10**5,     # Platform commission in ppm = 10%
    val_user_reg=5*10**(6),     # 5 ALGO validator registration fee to prevent spamming [in microALGO]
    del_user_reg=0,             # 0 ALGO delegator registration fee to incentivize staking [in microALGO]
    val_ad_creation=5*10**(6),  # 5 ALGO validator ad creation fee to prevent spamming [in microALGO]
    del_contract_creation=0,    # 0 ALGO delegator contract creation fee to incentivize staking [in microALGO]
)

NOTICEBOARD_TERMS_TIMING = NoticeboardTermsTiming(
    rounds_duration_min_min = round(14 * BLOCKS_PER_DAY),     # Minimum staking duration:  ~14 days [in rounds]
    rounds_duration_max_max = round(120 * BLOCKS_PER_DAY),    # Maximum staking duration: ~120 days [in rounds]
    before_expiry = round(7 * BLOCKS_PER_DAY),                # Expiry notifications: ~7 days before end [in rounds]
    report_period = round(2 * BLOCKS_PER_DAY),                # Period of expiry notifications: ~2 day [in rounds]
)

# Define asset to accept as payment on the platform
# If None and it is a test deployment, a new asset will be created by dispenser.
# If 0, ALGO is used for payment.
# If not None, the asset must exist on the network.
# Example: 31566704 = USDC (on Mainnet) - its base unit is microUSDC.
ACCEPTED_ASSET_ID = None
ACCEPTED_ASSET_INFO = NoticeboardAssetInfo(
    accepted = True,
    fee_round_min_min = round(5*10**6 / (30 * BLOCKS_PER_DAY) * 10**3),             # ~5 USDC/month [in nanoUSDC/round = (milli baseUSDC)/round]  # noqa: E501
    fee_round_var_min = round(0*10**6 / ((30 * BLOCKS_PER_DAY) * 10**5) * 10**9),   #  0 USDC/(month * 100k ALGO) [in femtoUSDC/(round * ALGO) = (nano baseUSDC)/(round * ALGO)]  # noqa: E501
    fee_setup_min = 5*10**5,                                                        # 0.5 USDC [in microUSDC = baseUSDC]
)

NOTICEBOARD_TERMS_NODE = NoticeboardTermsNodeLimits(
    stake_max_max = 6*10**(7+6),      # Maximum stake per account that a node can accept [in microALGO] = 60M ALGO (70M ALGO is limit for rewards)  # noqa: E501
    stake_max_min = 0,                # Minimum stake per account that a node must be able to accept [in microALGO] = 0 ALGO  # noqa: E501
    cnt_del_max_max = 4,              # Maximum number of delegators per ad (i.e. node) = 4 (before performance degradation)  # noqa: E501
)
