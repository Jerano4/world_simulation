import random
import numpy as np
from states import State, STATE_NAMES, CONTRAST_COLORS
from ideology import get_ideology_zone

class StateRegistry:
    def __init__(self):
        self.next_id = 0
        self.assigned_ids = set()

    def get_new_id(self):
        # Если полученный id уже занят, увеличиваем счетчик до первого свободного.
        while self.next_id in self.assigned_ids:
            self.next_id += 1
        new_id = self.next_id
        self.assigned_ids.add(new_id)
        self.next_id += 1
        return new_id

    def register_existing_id(self, state_id):
        self.assigned_ids.add(state_id)
        if state_id >= self.next_id:
            self.next_id = state_id + 1


def get_hex_neighbors(cell, grid):
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

def is_border(cell, parent_state, grid):
    for neighbor in get_hex_neighbors(cell, grid):
        if neighbor is None or neighbor.state_id != parent_state.id:
            return True
    return False

def get_contiguous_cluster(start_cell, parent_state, grid, cluster_size=5):
    cluster = []
    visited = set()
    queue = [start_cell]
    visited.add(start_cell)
    while queue and len(cluster) < cluster_size:
        cell = queue.pop(0)
        # Добавляем клетку в кластер, только если она принадлежит родительскому государству и не является столицей.
        if cell in parent_state.cells and cell != parent_state.capital:
            cluster.append(cell)
        if len(cluster) >= cluster_size:
            break
        for neighbor in get_hex_neighbors(cell, grid):
            if neighbor in parent_state.cells and neighbor not in visited and neighbor != parent_state.capital:
                visited.add(neighbor)
                queue.append(neighbor)
    return cluster

def select_capital_for_state(state, grid):
    """
    Выбирает столицу для данного государства.
    Расчитывается центр масс территории (с использованием координат клетки в offset-системе),
    затем выбирается та клетка (среди внутренних, если они есть), которая минимально удалена от центра.
    Флаг is_capital клетки устанавливается в True.
    """
    # Функция для вычисления позиции клетки на карте.
    def cell_position(cell):
        x = np.sqrt(3) * (cell.q + 0.5 * (cell.r % 2))
        y = 1.5 * cell.r
        return np.array([x, y])
    positions = [cell_position(cell) for cell in state.cells]
    centroid = sum(positions) / len(positions)
    # Определяем внутренние (не пограничные) клетки
    interior = [cell for cell in state.cells if not is_border(cell, state, grid)]
    candidates = interior if interior else state.cells
    def dist(cell):
        pos = cell_position(cell)
        return np.linalg.norm(pos - centroid)
    capital = min(candidates, key=dist)
    capital.is_capital = True
    return capital

def initialize_state_registry(hex_map):
    """
    Если у карты еще нет реестра госид, создает его.
    Также регистрируются уже существующие id.
    """
    if not hasattr(hex_map, 'state_registry'):
        hex_map.state_registry = StateRegistry()
        for state in hex_map.states:
            hex_map.state_registry.register_existing_id(state.id)


def trigger_separatism(parent_state, hex_map, current_step):
    """
    Пытается инициировать сепаратизм у parent_state.
    Если процесс успешен, создается новое государство с уникальным id,
    полученным через hex_map.state_registry.get_new_id().
    """
    grid = hex_map.grid
    # Инициализируем реестр, если его еще нет.
    initialize_state_registry(hex_map)
    
    # Исключаем столицу из пограничных клеток.
    border_cells = [cell for cell in parent_state.cells
                    if is_border(cell, parent_state, grid) and cell != parent_state.capital]
    if not border_cells:
        return None
    # Выбираем случайную пограничную клетку как отправную точку.
    start_cell = random.choice(border_cells)
    # Собираем связный кластер из клеток размером 5.
    cluster = get_contiguous_cluster(start_cell, parent_state, grid, cluster_size=5)
    if len(cluster) < 5:
        return None

    # Убираем выбранные клетки из территории родительского государства.
    for cell in cluster:
        if cell in parent_state.cells:
            parent_state.cells.remove(cell)
    
    # Проверка окружения столицы:
    capital_neighbors = get_hex_neighbors(parent_state.capital, grid)
    if not any(neighbor.state_id == parent_state.id for neighbor in capital_neighbors):
        print(f"Окружение столицы: {parent_state.name} прекращает существование, оставшиеся территории переходят к сепаратистскому образованию.")
        full_cluster = cluster.copy() + list(parent_state.cells)
        parent_state.cells.clear()
        parent_state.capital.is_capital = False
        parent_state.capital = None

        total_power = sum(s.power for s in hex_map.states)
        avg_power = total_power / len(hex_map.states) if hex_map.states else parent_state.power
        new_power = int(avg_power)
        new_ideology_x = random.randint(-10, 10)
        new_ideology_y = random.randint(-10, 10)
        attempts = 0
        while get_ideology_zone(new_ideology_x, new_ideology_y) == parent_state.ideology_zone and attempts < 10:
            new_ideology_x = random.randint(-10, 10)
            new_ideology_y = random.randint(-10, 10)
            attempts += 1
        new_zone = get_ideology_zone(new_ideology_x, new_ideology_y)
        used_names = {s.name for s in hex_map.states}
        available_names = [name for name in STATE_NAMES if name not in used_names]
        new_name = random.choice(available_names) if available_names else f"State_{hex_map.state_registry.next_id}"
        new_color = random.choice(CONTRAST_COLORS)

        # Получаем уникальный id через реестр.
        new_id = hex_map.state_registry.get_new_id()
        new_state = State(new_id, new_color, name=new_name)

        new_state.power = new_power
        new_state.ideology_x = new_ideology_x
        new_state.ideology_y = new_ideology_y
        new_state.ideology_zone = new_zone
        new_state.stability = 5
        new_state.is_separatist = True
        new_state.parent_id = parent_state.id
        new_state.birth_step = current_step
        new_state.separatist_timer = 5
        new_state.cells = full_cluster.copy()
        for cell in new_state.cells:
            cell.state_id = new_state.id
            cell.state_color = new_state.color

        hex_map.states.append(new_state)
        print(f"Сепарация: {new_state.name} отделяется от {parent_state.name}.")
        if parent_state in hex_map.states:
            hex_map.states.remove(parent_state)
        return new_state

    # Стандартный путь создания сепаратистского государства, если столица не окружена.
    total_power = sum(s.power for s in hex_map.states)
    avg_power = total_power / len(hex_map.states) if hex_map.states else parent_state.power
    new_power = int(avg_power)
    new_ideology_x = random.randint(-10, 10)
    new_ideology_y = random.randint(-10, 10)
    attempts = 0
    while get_ideology_zone(new_ideology_x, new_ideology_y) == parent_state.ideology_zone and attempts < 10:
        new_ideology_x = random.randint(-10, 10)
        new_ideology_y = random.randint(-10, 10)
        attempts += 1
    new_zone = get_ideology_zone(new_ideology_x, new_ideology_y)
    used_names = {s.name for s in hex_map.states}
    available_names = [name for name in STATE_NAMES if name not in used_names]
    new_name = random.choice(available_names) if available_names else f"State_{hex_map.state_registry.next_id}"
    new_color = random.choice(CONTRAST_COLORS)

    new_id = hex_map.state_registry.get_new_id()
    new_state = State(new_id, new_color, name=new_name)

    new_state.power = new_power
    new_state.ideology_x = new_ideology_x
    new_state.ideology_y = new_ideology_y
    new_state.ideology_zone = new_zone
    new_state.stability = 5
    new_state.is_separatist = True
    new_state.parent_id = parent_state.id
    new_state.birth_step = current_step
    new_state.separatist_timer = 5
    new_state.cells = cluster.copy()
    for cell in new_state.cells:
        cell.state_id = new_state.id
        cell.state_color = new_state.color

    hex_map.states.append(new_state)
    print(f"Сепарация: {new_state.name} отделяется от {parent_state.name}.")
    return new_state

def process_separatist_states(hex_map, current_step):
    states_to_remove = []
    for state in list(hex_map.states):
        if state.is_separatist:
            state.separatist_timer -= 1
            if state.separatist_timer <= 0:
                if len(state.cells) >= 5:
                    # Сепаратист получает независимость.
                    state.is_separatist = False
                    state.parent_id = None
                    state.stability = 5
                    used_names = {s.name for s in hex_map.states}
                    available_names = [name for name in STATE_NAMES if name not in used_names]
                    state.name = random.choice(available_names) if available_names else f"State_{len(hex_map.states)+1}"
                    # Назначаем новую столицу.
                    state.capital = select_capital_for_state(state, hex_map.grid)
                    state.color = random.choice(CONTRAST_COLORS)
                    for cell in state.cells:
                        cell.state_color = state.color
                    print(f"Государство {state.name} получило независимость!")
                else:
                    # Сепаратист подавлен – возвращаем клетки родительскому государству.
                    parent = next((s for s in hex_map.states if s.id == state.parent_id), None)
                    if parent:
                        for cell in state.cells:
                            cell.state_id = parent.id
                            cell.state_color = parent.color
                            parent.cells.append(cell)
                    print(f"Сепаратизм {state.name} подавлен.")
                    states_to_remove.append(state)
    for s in states_to_remove:
        hex_map.states.remove(s)

def select_capital_for_state(state, grid):
    """
    Выбирает столицу для данного государства, используя гекс-сетку.
    Рассчитывается центр масс территории, затем выбирается клетка, которая минимально удалена от центра.
    Устанавливается флаг is_capital.
    """
    def cell_position(cell):
        x = np.sqrt(3) * (cell.q + 0.5 * (cell.r % 2))
        y = 1.5 * cell.r
        return np.array([x, y])
    positions = [cell_position(cell) for cell in state.cells]
    centroid = sum(positions) / len(positions)
    # Определяем внутренние клетки (не пограничные).
    def is_border_cell(cell):
        for neighbor in get_hex_neighbors(cell, grid):
            if neighbor is None or neighbor.state_id != state.id:
                return True
        return False
    interior_cells = [cell for cell in state.cells if not is_border_cell(cell)]
    candidates = interior_cells if interior_cells else state.cells
    def dist(cell):
        return np.linalg.norm(cell_position(cell) - centroid)
    capital = min(candidates, key=dist)
    capital.is_capital = True
    return capital