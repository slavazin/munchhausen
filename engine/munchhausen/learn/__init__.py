"""The backward pass (SPEC § 7, § 9): observe, group, nominate, adjudicate, backtest, lifecycle.

Never imports `truth` or `world` (SPEC § 7.4 Don't): a learning loop that reads gold measures nothing.
Replays are scored against the case store's confirmed figures only.
"""
