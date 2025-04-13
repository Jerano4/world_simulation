import random
import matplotlib.colors as mcolors
import numpy as np
from collections import deque

STATE_NAMES = [
    "Герцепезун", "Тимонт", "Арабания", "Эстребия", "Гаталия", "Эстрегалия", "Макеты", "Алусия", "Кация", "Абгалия", 
    "Допезун", "Бадония", "Серталия", "Кагалия", "Догория", "Бачлусия", "Пардония", "Тидония", "Феты", "Герцегория", 
    "Туздония", "Фивения", "Герцеталия", "Лейпезун", "Орбания", "Допания", "Медония", "Грепезун", "Симонт", "Бепания", 
    "Типания", "Фелусия", "Гитикан", "Эстреция", "Гредорра", "Мальталия", "Андония", "Тиция", "Добания", "Фебардия", 
    "Андатурия", "Сарбия", "Арания", "Сардония", "Дурдиния", "Кугалия", "Зения", "Потикан", "Слодорра", "Макемонт", 
    "Гитурия", "Арты", "Фата", "Тузпания", "Эдорра", "Пьебия", "Бачты", "Атдорра", "Ломдония", "Тигалия", "Дурватия", 
    "Зеговина", "Пагалия", "Пония", "Гацилия", "Брабия", "Атбия", "Сердорра", "Поты", "Метика", "Эгалия", "Кридорра", 
    "Кодония", "Ригория", "Иты", "Фрадорра", "Арбрия", "Энпансия", "Ведорра", "Лейтика", "Лагалия", "Гимонт", "Влеговина", 
    "Хорбия", "Дотурия", "Тоспезун", "Шуталия", "Доция", "Лейдорра", "Баления", "Трагория", "Гиротикан", "Латалия", 
    "Аспания", "Абватия", "Веталия", "Крипания", "Валенсия", "Севилья", "Пьепания", "Эстредония", "Чернотикан", "Влеция", 
    "Андабия", "Бачция", "Энвения", "Фигория", "Бачвения", "Анталия", "Мальговина", "Сибрия", "Сидорра", "Араталия", 
    "Элбия", "Мадлисия", "Набия", "Гидорра", "Братикан", "Копания", "Лейдиния", "Ларбия", "Калисия", "Ваталия", "Тузлисия", 
    "Лабания", "Пания", "Турбания", "Македорра", "Сарцилия", "Сергалия", "Серпания", "Диватия", "Марталия", "Ация", 
    "Черноговина", "Асдиния", "Ломпезун", "Хординия", "Арбардия", "Асвентия", "Зебания", "Хорвения", "Маддония", "Фиция", 
    "Орбардия", "Босбания", "Нагалия", "Герцеговина", "Элпезун", "Куция" 
]

CONTRAST_COLORS = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#46f0f0", "#f032e6", "#bcf60c", "#fabebe",
    "#008080", "#e6beff", "#9a6324", "#fffac8", "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075", "#808080",
    "#ffe0b3", "#ff7f00", "#8dd3c7", "#fb8072", "#80b1d3", "#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd",
    "#ccebc5", "#ffed6f", "#1f78b4", "#33a02c", "#e31a1c", "#ff69b4", "#b15928", "#6a3d9a", "#b2df8a", "#cab2d6",
    "#a6cee3", "#999999", "#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3"
]

class State:
    def __init__(self, id, color, name=None):
        self.id = id
        self.color = color
        self.cells = []  # клетки, принадлежащие государству
        self.name = name if name is not None else f"Государство {id+1}"
        self.capital = None  # клетка столицы
        self.power = random.randint(80, 120)
        # Идеологические координаты
        self.ideology_x = None
        self.ideology_y = None
        self.ideology_zone = None
        self.stability = 5
        self.is_separatist = False
        self.parent_id = None
        self.birth_step = None
        self.separatist_timer = None
        self.history = []

class Map:
    def __init__(self, rows, cols, num_continents=25):
        self.rows = rows
        self.cols = cols
        self.num_continents = num_continents
        self.grid = [[None for q in range(cols)] for r in range(rows)]
        self.states = []
 
    def get_all_cells(self):
        return [cell for row in self.grid for cell in row]

    def get_neighbors(self, r, q):
        neighbors = []
        for dr, dq in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nq = r + dr, q + dq
            if 0 <= nr < self.rows and 0 <= nq < self.cols:
                neighbors.append(self.grid[nr][nq])
        return neighbors

    def get_hex_neighbors(self, r, q):
        if r % 2 == 0:
            offsets = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
        else:
            offsets = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
        neighbors = []
        for dr, dq in offsets:
            nr, nq = r + dr, q + dq
            if 0 <= nr < self.rows and 0 <= nq < self.cols:
                neighbors.append((nr, nq))
        return neighbors

    def cell_position(self, cell):
        x = np.sqrt(3) * (cell.q + 0.5 * (cell.r % 2))
        y = 1.5 * cell.r
        return x, y

    def state_centroid(self, state):
        positions = [self.cell_position(cell) for cell in state.cells]
        centroid_x = sum(x for x, y in positions) / len(positions)
        centroid_y = sum(y for x, y in positions) / len(positions)
        return centroid_x, centroid_y

    def generate_states(self, count):
        # Собираем все сушевые клетки
        all_land_cells = [cell for row in self.grid for cell in row if cell and cell.terrain == 'land']
        random.shuffle(all_land_cells)
        start_cells = all_land_cells[:count]

        # Подготовка уникальных случайных названий
        names = list(STATE_NAMES)  # копия списка
        random.shuffle(names)

        colors = list(CONTRAST_COLORS)
        random.shuffle(colors)

        for i, start_cell in enumerate(start_cells):
            name = names.pop() if names else f"Государство {i+1}"
            state = State(i, colors[i % len(colors)], name=name)
            # Случайная сила уже установлена в конструкторе
            state.cells.append(start_cell)
            start_cell.state_id = state.id
            start_cell.state_color = state.color
            self.states.append(state)

        # Расширяем территории
        from collections import deque
        queue = deque(start_cells)
        while queue:
            current = queue.popleft()
            state_id = current.state_id
            for neighbor in self.get_neighbors(current.r, current.q):
                if neighbor.state_id is None and neighbor.terrain == 'land':
                    neighbor.state_id = state_id
                    neighbor.state_color = self.states[state_id].color
                    self.states[state_id].cells.append(neighbor)
                    queue.append(neighbor)

        # Привязываем оставшиеся не назначенные клетки к ближайшему государству
        for row in self.grid:
            for cell in row:
                if cell and cell.terrain == 'land' and cell.state_id is None:
                    best_state = min(self.states, key=lambda state: np.hypot(*(np.array(self.cell_position(cell)) - np.array(self.state_centroid(state)))))
                    cell.state_id = best_state.id
                    cell.state_color = best_state.color
                    best_state.cells.append(cell)

        for state in self.states:
            state.capital = self.select_capital(state)

    def is_border_cell(self, cell, state):
        neighbors = self.get_hex_neighbors(cell.r, cell.q)
        for nr, nq in neighbors:
            neighbor = self.grid[nr][nq]
            if neighbor is None or neighbor.state_id != state.id:
                return True
        return False

    def select_capital(self, state):
        positions = [self.cell_position(cell) for cell in state.cells]
        centroid_x = sum(x for x, y in positions) / len(positions)
        centroid_y = sum(y for x, y in positions) / len(positions)
        interior_cells = [cell for cell in state.cells if not self.is_border_cell(cell, state)]
        candidates = interior_cells if interior_cells else state.cells
        def distance(cell):
            x, y = self.cell_position(cell)
            return np.hypot(x - centroid_x, y - centroid_y)
        capital = min(candidates, key=distance)
        capital.is_capital = True
        return capital
