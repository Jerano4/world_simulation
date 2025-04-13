import random
import math
from ideology import can_attack

def get_hex_neighbors(cell, grid):
    """Возвращает соседей клетки на гекс-карте с учетом четности строки."""
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

def is_straight_water_path(cell1, cell2, grid):
    if cell1.r == cell2.r:
        row = cell1.r
        start = min(cell1.q, cell2.q)
        end = max(cell1.q, cell2.q)
        for col in range(start + 1, end):
            if grid[row][col].terrain != 'ocean':
                return False
        return True
    elif cell1.q == cell2.q:
        col = cell1.q
        start = min(cell1.r, cell2.r)
        end = max(cell1.r, cell2.r)
        for row in range(start + 1, end):
            if grid[row][col].terrain != 'ocean':
                return False
        return True
    else:
        return False

def has_straight_water_path(attacker, defender, grid):
    for a_cell in attacker.cells:
        if not getattr(a_cell, 'is_coastal', False):
            continue
        for d_cell in defender.cells:
            if not getattr(d_cell, 'is_coastal', False):
                continue
            if is_straight_water_path(a_cell, d_cell, grid):
                return True
    return False

def is_border_with_winner(cell, winner, grid):
    for neighbor in get_hex_neighbors(cell, grid):
        if neighbor.terrain == 'land' and neighbor.state_id == winner.id:
            return True
    return False

def get_enclave_cells(state, grid):
    if not state.capital:
        return state.cells
    visited = set()
    queue = [state.capital]
    visited.add(state.capital)
    while queue:
        current = queue.pop(0)
        for neighbor in get_hex_neighbors(current, grid):
            if neighbor in state.cells and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return [cell for cell in state.cells if cell not in visited]

def distance(cell1, cell2):
    return math.sqrt((cell1.q - cell2.q) ** 2 + (cell1.r - cell2.r) ** 2)

def simulate_battle(attacker, defender, hex_map, silent=False):
    # Определяем тип войны: сначала проверяем наличие сухопутной границы через гекс-соседей.
    land_border = False
    for a_cell in attacker.cells:
        for neighbor in get_hex_neighbors(a_cell, hex_map.grid):
            if neighbor.state_id == defender.id:
                land_border = True
                break
        if land_border:
            break

    war_type = None
    if land_border:
        war_type = "land"
    else:
        if has_straight_water_path(attacker, defender, hex_map.grid):
            war_type = "water"
    if not war_type:
        return None  # Бой невозможен

    # Симуляция боевых раундов (15-25 раундов).
    rounds = random.randint(15, 25)
    attacker_score = 0
    defender_score = 0
    for _ in range(rounds):
        a_roll = random.randint(1, attacker.power)
        d_roll = random.randint(1, defender.power)
        if a_roll > d_roll:
            attacker_score += 1
        elif d_roll > a_roll:
            defender_score += 1

    score_diff = abs(attacker_score - defender_score)
    if score_diff == 0:
        return None  # Ничья

    if attacker_score > defender_score:
        winner, loser = attacker, defender
    else:
        winner, loser = defender, attacker

    if not silent:
        print(f"{attacker.name} ({attacker.ideology_zone}) атакует {defender.name} ({defender.ideology_zone}) ({war_type} война)")
        print(f"Результаты боя: {attacker_score} : {defender_score}")

    # Определяем кандидатов на захват:
    if war_type == "water":
        candidate_cells = [cell for cell in loser.cells if cell.is_coastal]
    else:
        candidate_cells = loser.cells[:]

    if loser.capital is not None:
        candidate_cells = [cell for cell in candidate_cells if cell != loser.capital]
    # Если победитель является сепаратистом, он может захватывать ТОЛЬКО клетки,
    # которые граничат с уже имеющейся территорией победителя.
    if winner.is_separatist:
        candidate_cells = [cell for cell in candidate_cells if is_border_with_winner(cell, winner, hex_map.grid)]
        
    if not candidate_cells:
        if not silent:
            print("Нет доступных клеток для захвата (с учетом ограничений доступа).")
        return None

    # Определяем анклавные клетки проигравшего.
    enclave_cells = get_enclave_cells(loser, hex_map.grid)
    enclave_candidates = [cell for cell in candidate_cells if cell in enclave_cells and is_border_with_winner(cell, winner, hex_map.grid)]
    
    # Если у победителя нет столицы (например, он сепаратист), сортируем по (r, q), иначе по расстоянию до столицы.
    if winner.capital is None:
        enclave_candidates.sort(key=lambda c: (c.r, c.q))
        remaining_candidates = [cell for cell in candidate_cells if cell not in enclave_candidates]
        remaining_candidates.sort(key=lambda c: (c.r, c.q))
    else:
        enclave_candidates.sort(key=lambda c: distance(c, winner.capital))
        remaining_candidates = [cell for cell in candidate_cells if cell not in enclave_candidates]
        remaining_candidates.sort(key=lambda c: distance(c, winner.capital))
    selected_cells = enclave_candidates + remaining_candidates
    captured_cells = selected_cells[:min(score_diff, len(selected_cells))]

    total_loser_cells = len(loser.cells)
    if score_diff >= total_loser_cells:
        if not silent:
            print(f"{winner.name} наносит сокрушительный удар, {loser.name} полностью уничтожено!")
        captured_cells = loser.cells[:]  # захватываем все клетки, включая столицу
        loser.cells.clear()
        if loser.capital is not None:
            loser.capital.is_capital = False
            loser.capital = None

        elif loser.capital is not None:
            capital_neighbors = get_hex_neighbors(loser.capital, hex_map.grid)
            if not any(neighbor in loser.cells and neighbor != loser.capital for neighbor in capital_neighbors):
                if not silent:
                    print(f"Столица {loser.name} изолирована – {loser.name} капитулирует!")
                captured_cells = loser.cells[:]  # захватываем все оставшиеся клетки, включая столицу
                loser.cells.clear()
                loser.capital.is_capital = False
                loser.capital = None

    for cell in captured_cells:
        cell.state_id = winner.id
        cell.state_color = winner.color
        winner.cells.append(cell)
        if cell in loser.cells:
            loser.cells.remove(cell)
            
    if loser.capital is not None:
        capital_neighbors = get_hex_neighbors(loser.capital, hex_map.grid)
        if not any(neighbor.state_id == loser.id for neighbor in capital_neighbors):
            if not silent:
                print(f"Столица {loser.name} полностью изолирована – {loser.name} прекращает существование!")
            # Передаём все оставшиеся клетки проигравшего победителю.
            remaining = loser.cells[:]
            for cell in remaining:
                cell.state_id = winner.id
                cell.state_color = winner.color
                winner.cells.append(cell)
            loser.cells.clear()
            loser.capital.is_capital = False
            loser.capital = None

    if not silent:
        print(f"{winner.name} захватывает {len(captured_cells)} клеток у {loser.name}.\n")
    return (winner, loser)

def simulate_battles(hex_map, states, max_battles=5):
    # Первый этап: гарантированные битвы с сепаратистами.
    separatist_pairs = []
    for state in states:
        if state.is_separatist:
            parent = next((s for s in states if s.id == state.parent_id), None)
            if parent:
                separatist_pairs.append((parent, state))
    # Для каждой уникальной пары родитель – сепаратист, проводим битву (одна на ход).
    for parent, separatist in random.sample(separatist_pairs, len(separatist_pairs)):
        result = simulate_battle(parent, separatist, hex_map, silent=True)
        if result is not None:
            # Если в результате битвы одна из сторон полностью уничтожена, выводим сообщение.
            winner, loser = result
            if len(loser.cells) == 0:
                print(f"{loser.name} (сепаратизм) уничтожено и исключается из дальнейших битв.")
                states.remove(loser)
    # Второй этап: обычные битвы между независимыми государствами.
    independent_states = [s for s in states if not s.is_separatist]
    battle_count = 0
    while battle_count < max_battles:
        possible_pairs = []
        for attacker in independent_states:
            for defender in independent_states:
                if attacker.id == defender.id:
                    continue
                if not can_attack(attacker, defender):
                    continue
                possible_pairs.append((attacker, defender))
        if not possible_pairs:
            print("Нет возможных битв среди независимых государств.")
            break
        random.shuffle(possible_pairs)
        battle_happened = False
        for attacker, defender in possible_pairs:
            if len(attacker.cells) == 0 or len(defender.cells) == 0:
                continue
            result = simulate_battle(attacker, defender, hex_map, silent=False)
            if result is not None:
                battle_count += 1
                battle_happened = True
                winner, loser = result
                if len(loser.cells) == 0:
                    print(f"{loser.name} уничтожено и исключается из дальнейших битв.")
                    states.remove(loser)
                break  # Одна битва за итерацию.
        if not battle_happened:
            print("Больше нет подходящих битв среди независимых государств.")
            break
    print(f"Проведено битв среди независимых: {battle_count}")

def absorb_isolated_groups(hex_map, threshold=3):
    """
    Ищет в карте небольшие изолированные группы клеток одного государства,
    которые не содержат столицу и имеют размер меньше или равный threshold.
    Для каждой такой группы производится поиск соседних государств (по 6-связи)
    и определяется сосед с максимальной силой. Все клетки группы присоединяются к нему.
    """
    grid = hex_map.grid
    rows = len(grid)
    cols = len(grid[0])
    # матрица для отметок посещённых клеток
    visited = [[False for _ in range(cols)] for _ in range(rows)]
    changes = []  # список изменений: (группа клеток, старое государство, новое государство)

    # Перебираем все клетки карты
    for r in range(rows):
        for q in range(cols):
            cell = grid[r][q]
            # Пропускаем нейтральные клетки или клетки, уже посещённые в поиске компоненты
            if cell.state_id is None or visited[r][q]:
                continue

            # Выполняем BFS для поиска связной компоненты, принадлежащей одному государству
            group = []
            queue = [(r, q)]
            visited[r][q] = True
            while queue:
                cr, cq = queue.pop(0)
                current_cell = grid[cr][cq]
                if current_cell.state_id != cell.state_id:
                    continue
                group.append(current_cell)
                for neighbor in get_hex_neighbors(current_cell, grid):
                    nr, nq = neighbor.r, neighbor.q
                    if not visited[nr][nq] and neighbor.state_id == cell.state_id:
                        visited[nr][nq] = True
                        queue.append((nr, nq))

            # Получаем объект государства, которому принадлежат клетки группы
            old_state = next((s for s in hex_map.states if s.id == cell.state_id), None)
            if old_state is None:
                continue

            # Если в группе содержится столица, пропускаем её (даже если размер небольшой)
            if old_state.capital in group:
                continue

            # Если группа слишком большая, её не трогаем
            if len(group) > threshold:
                continue

            # Определяем соседние государства, принадлежащие клеткам, прилегающим к группе
            neighbor_states = {}
            for group_cell in group:
                for neighbor in get_hex_neighbors(group_cell, grid):
                    if neighbor.state_id is None:
                        continue
                    if neighbor.state_id != old_state.id:
                        ns = next((s for s in hex_map.states if s.id == neighbor.state_id), None)
                        if ns:
                            neighbor_states[ns.id] = ns
            if not neighbor_states:
                continue

            # Выбираем из соседних государств то, у которого максимальная сила (поле power)
            target_state = max(neighbor_states.values(), key=lambda s: s.power)
            changes.append((group, old_state, target_state))

    # Применяем изменения: переводим клетки из маленьких групп к выбранному государству
    for group, old_state, new_state in changes:
        for cell in group:
            if cell in old_state.cells:
                old_state.cells.remove(cell)
            cell.state_id = new_state.id
            cell.state_color = new_state.color
            new_state.cells.append(cell)


