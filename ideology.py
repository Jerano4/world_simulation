import random

def assign_random_ideology(state):
    state.ideology_x = random.randint(-10, 10)
    state.ideology_y = random.randint(-10, 10)

def ideological_drift(state):
    state.ideology_x = max(-10, min(10, state.ideology_x + random.randint(-3, 3)))
    state.ideology_y = max(-10, min(10, state.ideology_y + random.randint(-3, 3)))

def get_ideology_zone(x, y):
    if x == 0 or y == 0:
        return "нейтральная зона"
    if (-10 <= x <= -3 and 7 <= y <= 10) or (-10 <= x <= -7 and 3 <= y <= 6):
        return "ультра-красный"
    if (3 <= x <= 10 and 7 <= y <= 10) or (7 <= x <= 10 and 3 <= y <= 6):
        return "ультра-синий"
    if (-10 <= x <= -7 and -10 <= y <= -3) or (-6 <= x <= -3 and -10 <= y <= -7):
        return "ультра-зелёный"
    if (3 <= x <= 10 and -10 <= y <= -7) or (7 <= x <= 10 and -6 <= y <= -3):
        return "ультра-жёлтый"
    if (-10 <= x <= -1 and 1 <= y <= 2) or (-2 <= x <= -1 and 3 <= y <= 10) or (-6 <= x <= -3 and 3 <= y <= 6):
        return "красный"
    if (1 <= x <= 10 and 1 <= y <= 2) or (1 <= x <= 2 and 3 <= y <= 10) or (3 <= x <= 6 and 3 <= y <= 6):
        return "синий"
    if (-10 <= x <= -1 and -2 <= y <= -1) or (-2 <= x <= -1 and -10 <= y <= -3) or (-6 <= x <= -3 and -6 <= y <= -3):
        return "зелёный"
    if (1 <= x <= 10 and -2 <= y <= -1) or (1 <= x <= 2 and -10 <= y <= -3) or (3 <= x <= 6 and -6 <= y <= -3):
        return "жёлтый"
    return "неизвестно"

def get_coalition(zone):
    """Возвращает коалиционное имя: для ультра-версии отбрасываем префикс 'ультра-'."""
    if zone.startswith("ультра-"):
        return zone[len("ультра-"):]
    return zone

def is_radical(state):
    zone = get_ideology_zone(state.ideology_x, state.ideology_y)
    return zone.startswith("ультра")

def can_attack(attacker, defender):
    # Нельзя атаковать нейтральное государство
    if get_ideology_zone(defender.ideology_x, defender.ideology_y) == "нейтральная зона":
        return False
    if not is_radical(attacker):
        return False
    attacker_zone = get_ideology_zone(attacker.ideology_x, attacker.ideology_y)
    defender_zone = get_ideology_zone(defender.ideology_x, defender.ideology_y)
    if get_coalition(attacker_zone) == get_coalition(defender_zone):
        return False
    return True
