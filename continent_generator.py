import random
import numpy as np

class Cell:
    def __init__(self, q, r):
        self.q = q  # координата столбца
        self.r = r  # координата строки
        self.state_id = None  # id государства
        self.terrain = 'ocean'  # по умолчанию океан
        # Новые атрибуты для работы с водными объектами
        self.water_body_id = None   # будет присвоен в label_water_bodies()
        self.is_oceanic = False       # True, если водоем касается края карты (океан)
        self.is_coastal = False       # True, если клетка суши примыкает к воде
        self.coastal_water_ids = []   # список water_body_id водных объектов, к которым примыкает

class Map: 
    def __init__(self, rows, cols, num_continents=3):
        self.rows = rows
        self.cols = cols
        self.num_continents = num_continents
        self.grid = [[Cell(q, r) for q in range(cols)] for r in range(rows)]
        self.generate_terrain()
        # После генерации ландшафта назначаем водные объекты и помечаем прибрежные клетки
        self.label_water_bodies()
        self.mark_coastal_cells()

    def generate_terrain(self):
        # Генерация случайных центров континентов
        continent_centers = []
        while len(continent_centers) < self.num_continents:
            cx = random.randint(5, self.cols - 5)
            cy = random.randint(5, self.rows - 5)
            if all(np.sqrt((cx - x)**2 + (cy - y)**2) > 15 for x, y in continent_centers):
                continent_centers.append((cy, cx))

        # Генерация континентов с плавными переходами
        for r in range(self.rows):
            for q in range(self.cols):
                distances = [np.sqrt((q - cx)**2 * 0.5 + (r - cy)**2 * 1.5) for cy, cx in continent_centers]  
                min_dist = min(distances)
                # Генерация плавных контуров суши (уменьшаем шум и порог)
                value = np.exp(-min_dist / 8) + np.random.normal(0, 0.05)  
                if value > 0.5:
                    self.grid[r][q].terrain = 'land'
                else:
                    self.grid[r][q].terrain = 'ocean'

        # Убираем островки из одной клетки
        for r in range(self.rows):
            for q in range(self.cols):
                if self.grid[r][q].terrain == 'land':
                    # Если нет соседей суши, превращаем в океан
                    if all(neighbor.terrain == 'ocean' for neighbor in self.get_neighbors(r, q)):
                        self.grid[r][q].terrain = 'ocean'

        # Убираем континенты, которые касаются краёв карты
        for r in range(self.rows):
            for q in range(self.cols):
                if r < 1 or r >= self.rows - 1 or q < 1 or q >= self.cols - 1:
                    if self.grid[r][q].terrain == 'land':
                        self.grid[r][q].terrain = 'ocean'

    def get_all_cells(self):
        return [cell for row in self.grid for cell in row]

    def get_neighbors(self, r, q):
        neighbors = []
        for dr, dq in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nq = r + dr, q + dq
            if 0 <= nr < self.rows and 0 <= nq < self.cols:
                neighbors.append(self.grid[nr][nq])  # Добавляем сами клетки, а не их координаты
        return neighbors

    def label_water_bodies(self):
        """Проходит по всем клеткам с terrain 'ocean' и группирует их в водоёмы.
           Если водоём касается края карты, он помечается как океанический."""
        water_body_id = 0
        for r in range(self.rows):
            for q in range(self.cols):
                cell = self.grid[r][q]
                if cell.terrain == 'ocean' and cell.water_body_id is None:
                    queue = [cell]
                    water_cells = []
                    cell.water_body_id = water_body_id
                    while queue:
                        current = queue.pop(0)
                        water_cells.append(current)
                        for neighbor in self.get_neighbors(current.r, current.q):
                            if neighbor.terrain == 'ocean' and neighbor.water_body_id is None:
                                neighbor.water_body_id = water_body_id
                                queue.append(neighbor)
                    is_oceanic = any((c.r == 0 or c.r == self.rows - 1 or c.q == 0 or c.q == self.cols - 1) for c in water_cells)
                    for c in water_cells:
                        c.is_oceanic = is_oceanic
                    water_body_id += 1

    def mark_coastal_cells(self):
        """Помечает сушу как прибрежную, если у неё есть соседняя водная клетка.
           Также сохраняет список water_body_id, к которым клетка примыкает."""
        for r in range(self.rows):
            for q in range(self.cols):
                cell = self.grid[r][q]
                if cell.terrain == 'land':
                    coastal_ids = []
                    for neighbor in self.get_neighbors(r, q):
                        if neighbor.terrain == 'ocean':
                            coastal_ids.append(neighbor.water_body_id)
                    if coastal_ids:
                        cell.is_coastal = True
                        cell.coastal_water_ids = list(set(coastal_ids))
                    else:
                        cell.is_coastal = False
                        cell.coastal_water_ids = []