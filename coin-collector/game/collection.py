"""
collection: figures out which coins the player collects this frame.
"""


def check_collection(player, coins):
    """
    Returns newly collected coins and marks them unavailable for later frames.
    """
    player_rect = player.get_rect()
    collected = []
    for coin in coins:
        if not coin.collected and player_rect.colliderect(coin.get_rect()):
            coin.collected = True
            collected.append(coin)
    return collected
