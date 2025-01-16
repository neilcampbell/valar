import dataclasses

import tests.noticeboard.validator_ad_interface as va
import tests.validator_ad.delegator_contract_interface as dc


# ----------------------------------------------------------------------------
# ------ Classes for creation of Validator Ads and Delegator Contracts  ------
# ----------------------------------------------------------------------------
@dataclasses.dataclass(kw_only=True)
class DelCo:
    acc_idx: int | None = None  # None creates a new account. To reuse the last account, put -1.
    state: dc.POSSIBLE_STATES = "LIVE"

@dataclasses.dataclass(kw_only=True)
class ValAd:
    acc_idx: int | None = None  # None creates a new account. To reuse the last account, put -1.
    state: va.POSSIBLE_STATES = "READY"
    dels: list[DelCo] | None = None  # List of delegator contracts created under this ad
