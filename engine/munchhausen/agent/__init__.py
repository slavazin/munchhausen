"""The forward agent's services: hooks, context packing, proposer, execute (SPEC § 6).

Never imports `truth` or `world`: gold reaches the forward pass only as a `Judgement` from the World port.
"""
