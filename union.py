import random
import numpy as np
from states import STATE_NAMES

UNION_NAMES = [
    "Испания", "Ларвентия", "Дигория", "Элгон", "Аравения", "Сабания", "Вебрия", "Аговина",
    "Ригория", "Бирталия", "Кантагалия", "Фрадония", "Тузбрия", "Авения", "Гагалия", "Шаголия",
    "Тигалия", "Босбия", "Фидорра", "Черногория", "Орта", "Эбардия", "Фитикан", "Гидорра", 
    "Портупезун", "Макемонт", "Арбия", "Диния", "Титалия", "Энватия", "Марговина", "Бедорра",
    "Умния", "Нигория", "Слоговина", "Эскабрия", "Тузния", "Влеватия", "Балегон", "Мения", 
    "Фрадония", "Эталия", "Фрагон", "Хорватия", "Ниталия", "Сагалия", "Саговина", "Среммонт",
    "Илусия", "Багория", "Андадокия", "Литикан", "Шубардия", "Аталия", "Коталия", "Умта",
    "Мадпания", "Энвантия", "Абты", "Ватикан", "Анты", "Ация", "Вегон", "Сердорра", "Фимонт"
]

# Класс для представления унии.
class Union:
    def __init__(self, union_id, name, members):
        self.union_id = union_id
        self.name = name
        self.members = members  # Список объектов State

def get_hex_neighbors(cell, grid):
    """Возвращает соседей клетки (гекс-связность) — 6 соседей."""
    r = cell.r
    q = cell.q
    neighbors = []
    if r % 2 == 0:
        offsets = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
    else:
        offsets = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
    for dr, dq in offsets:
        nr = r + dr
        nq = q + dq
        if 0 <= nr < len(grid) and 0 <= nq < len(grid[0]):
            neighbors.append(grid[nr][nq])
    return neighbors

def have_land_border(state1, state2, grid):
    """
    Проверяет, имеют ли два государства общую сухопутную границу.
    Проходит по всем клеткам одного государства и, используя get_hex_neighbors, 
    ищет хотя бы одну клетку, соседствующую с клеткой второго государства.
    """
    for cell in state1.cells:
        for neighbor in get_hex_neighbors(cell, grid):
            if neighbor.state_id == state2.id:
                return True
    return False

def similar_ideology(state1, state2, get_coalition):
    """
    Проверяет, принадлежат ли идеологии state1 и state2 к одной коалиции.
    """
    return get_coalition(state1.ideology_zone) == get_coalition(state2.ideology_zone)

def power_difference_within(state1, state2, threshold=10):
    return abs(state1.power - state2.power) <= threshold

def form_unions(hex_map, get_coalition):
    """
    Формирует унии среди независимых государств, удовлетворяющих условиям:
      - Имеют общую сухопутную границу.
      - Идеологически совместимы.
      - Разница сил не превышает 10.
    Каждое государство может быть членом только одной унии.
    Сформированные унии сохраняются в hex_map.unions.
    """
    unions = []
    union_id_counter = 0
    independent_states = [s for s in hex_map.states if not hasattr(s, 'union_id') or s.union_id is None]
    for state in independent_states:
        if hasattr(state, 'union_id') and state.union_id is not None:
            continue
        union_members = [state]
        state.union_id = union_id_counter
        for other in independent_states:
            if other.id == state.id:
                continue
            if hasattr(other, 'union_id') and other.union_id is not None:
                continue
            border_ok = any(have_land_border(member, other, hex_map.grid) for member in union_members)
            ideology_ok = all(similar_ideology(member, other, get_coalition) for member in union_members)
            avg_power = sum(member.power for member in union_members) / len(union_members)
            power_ok = abs(other.power - avg_power) <= 10
            if border_ok and ideology_ok and power_ok:
                union_members.append(other)
                other.union_id = union_id_counter
        if len(union_members) > 1:
            available_names = [name for name in UNION_NAMES if name not in [u.name for u in unions]]
            union_name = available_names[0] if available_names else f"Union_{union_id_counter}"
            new_union = Union(union_id_counter, union_name, union_members)
            unions.append(new_union)
            union_id_counter += 1
    hex_map.unions = unions
    return unions

def simulate_union_battle(hex_map, union, enemy_state, silent=False):
    """
    Симулирует битву между унией и враждебным государством enemy_state.
    Каждое государство унии с границей с врагом ведёт свою битву индивидуально,
    используя собственную силу. Победившие страны получают положительные очки победы,
    проигравшие – отрицательные (равные количеству теряемых клеток).
    Победители могут равномерно перечислить часть своих очков для покрытия потерь союзников.
    Если у проигравшего не получилось покрыть потери, он теряет недостающие клетки.
    Оставшиеся у победителей очки используются для захвата клеток противника.
    """
    grid = hex_map.grid
    # Определяем членов унии, имеющих контакт с enemy_state (сухопутно или через побережье)
    union_members_with_border = []
    for state in union.members:
        if have_land_border(state, enemy_state, grid):
            union_members_with_border.append(state)
        else:
            for cell in state.cells:
                if getattr(cell, 'is_coastal', False):
                    for neighbor in get_hex_neighbors(cell, grid):
                        if neighbor.state_id == enemy_state.id:
                            union_members_with_border.append(state)
                            break
                    if state in union_members_with_border:
                        break
    if not union_members_with_border:
        if not silent:
            print("Ни один член унии не имеет связи с врагом. Бой не проводится.")
        return None

    # Симулируем индивидуальную битву для каждого участника унии
    battle_results = {}  # state -> очки победы (vp), положительные если выиграл, отрицательные если проиграл
    for state in union_members_with_border:
        rounds = random.randint(15, 25)
        state_score = 0
        enemy_score = 0
        for _ in range(rounds):
            s_roll = random.randint(1, state.power)
            e_roll = random.randint(1, enemy_state.power)
            if s_roll > e_roll:
                state_score += 1
            elif e_roll > s_roll:
                enemy_score += 1
        vp = state_score - enemy_score
        battle_results[state] = vp
        if not silent:
            print(f"{state.name} vs {enemy_state.name}: {state_score} : {enemy_score}, vp = {vp}")

    # Разбиваем результаты на победителей и проигравших
    winners = [state for state, vp in battle_results.items() if vp > 0]
    losers = [state for state, vp in battle_results.items() if vp < 0]

    # Для каждого проигравшего пытаемся покрыть потери за счёт победителей
    for loser in losers:
        required_cover = abs(battle_results[loser])
        if winners:
            contribution_per_winner = required_cover / len(winners)
            total_contributed = 0
            for winner in winners:
                available = battle_results[winner]
                contribution = min(available, contribution_per_winner)
                battle_results[winner] -= contribution
                total_contributed += contribution
            if total_contributed >= required_cover:
                if not silent:
                    print(f"{loser.name}: Потери полностью покрыты союзниками.")
            else:
                deficit = required_cover - total_contributed
                capture_cells_for_enemy(loser, enemy_state, deficit, grid, silent)
                if not silent:
                    print(f"{loser.name}: Потери не покрыты на {deficit} клеток, они теряются.")
        else:
            capture_cells_for_enemy(loser, enemy_state, required_cover, grid, silent)
            if not silent:
                print(f"{loser.name} проиграл без поддержки союзников и теряет {required_cover} клеток.")

    # Победители используют остаток своих очков для захвата клеток у врага
    total_captured = 0
    for winner in winners:
        remaining_vp = battle_results[winner]
        if remaining_vp > 0:
            captured = capture_enemy_cells(winner, enemy_state, remaining_vp, grid, silent)
            total_captured += captured
            if not silent:
                print(f"{winner.name} захватывает {captured} клеток у {enemy_state.name}.")
    return (battle_results, total_captured)

def capture_cells_for_enemy(loser, enemy_state, num_cells, grid, silent=False):
    """
    Захватывает у проигравшего клетки в количестве num_cells.
    Кандидаты выбираются среди прибрежных участков (is_coastal) с terrain == 'land'.
    Захваченные клетки переходят к enemy_state.
    """
    candidate_cells = [cell for cell in loser.cells if cell.terrain == 'land' and getattr(cell, 'is_coastal', False)]
    to_capture = candidate_cells[:min(int(num_cells), len(candidate_cells))]
    for cell in to_capture:
        cell.state_id = enemy_state.id
        cell.state_color = enemy_state.color
        enemy_state.cells.append(cell)
        loser.cells.remove(cell)
    if not silent:
        print(f"{loser.name} теряет {len(to_capture)} клеток, которые захватываются {enemy_state.name}.")

def capture_enemy_cells(winner, enemy_state, num_cells, grid, silent=False):
    """
    Победитель захватывает клетки у enemy_state в количестве, равном num_cells.
    Кандидаты выбираются среди прибрежных (is_coastal) клеток с terrain == 'land'.
    """
    candidate_cells = [cell for cell in enemy_state.cells if cell.terrain == 'land' and getattr(cell, 'is_coastal', False)]
    to_capture = candidate_cells[:min(int(num_cells), len(candidate_cells))]
    for cell in to_capture:
        cell.state_id = winner.id
        cell.state_color = winner.color
        winner.cells.append(cell)
        enemy_state.cells.remove(cell)
    return len(to_capture)

return_value = None  # Чтобы избежать синтаксической ошибки при копировании файла
