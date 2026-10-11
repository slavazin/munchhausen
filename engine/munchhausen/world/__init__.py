"""The world: dataset adapters, quirk packs, the question stream and the authority (SPEC § 4).

This package sits on the evaluation side of the boundary. It holds hidden tags (quirk ids per question)
and may read `truth`. The engine reaches it only through the `World` port.
"""
