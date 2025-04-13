import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon, Polygon

def draw_hex_grid(ax, side, cells, rows, cols):
    for cell in cells:
        q = cell.q
        r = cell.r
        if cell.terrain == 'land':
            if hasattr(cell, 'state_color'):
                fill_color = cell.state_color
            else:
                fill_color = '#d2b48c'
        else:
            fill_color = '#a0c4ff'

        x = side * np.sqrt(3) * (q + 0.5 * (r % 2))
        y = side * 1.5 * r

        edge_color = fill_color

        hexagon = RegularPolygon(
            (x, y),
            numVertices=6,
            radius=side,
            orientation=0,
            edgecolor=edge_color,
            facecolor=fill_color,
            linewidth=0.5
        )
        ax.add_patch(hexagon)

    x_max = side * np.sqrt(3) * (cols + 0.5 * ((rows-1) % 2)) + side
    y_max = side * 1.5 * (rows - 1) + side
    ax.set_xlim(-side, x_max)
    ax.set_ylim(-side, y_max)
    ax.set_aspect('equal')
    ax.axis('off')

def get_hex_center(cell, side):
    q = cell.q
    r = cell.r
    x = side * np.sqrt(3) * (q + 0.5 * (r % 2))
    y = side * 1.5 * r
    return np.array([x, y])

def get_border_cells(state, hex_map):
    border_cells = []
    grid = hex_map.grid
    for cell in state.cells:
        r, q = cell.r, cell.q
        offsets = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)] if r % 2 == 0 else [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
        for dr, dq in offsets:
            nr, nq = r + dr, q + dq
            if 0 <= nr < len(grid) and 0 <= nq < len(grid[0]):
                neighbor = grid[nr][nq]
                if neighbor.state_id != cell.state_id:
                    border_cells.append(cell)
                    break
    return border_cells 

def draw_separatist_boundaries(ax, hex_map, hex_size):
    for state in hex_map.states:
        if state.is_separatist:
            border_cells = get_border_cells(state, hex_map)
            if not border_cells:
                continue
            centers = np.array([get_hex_center(cell, hex_size) for cell in border_cells])
            centroid = centers.mean(axis=0)
            angles = np.arctan2(centers[:,1] - centroid[1], centers[:,0] - centroid[0])
            sort_order = np.argsort(angles)
            sorted_centers = centers[sort_order]
            polygon = Polygon(sorted_centers, closed=True, fill=False, edgecolor='black', linestyle='dashed', linewidth=1)
            ax.add_patch(polygon)

def draw_union_boundaries(ax, hex_map, hex_size):
    if not hasattr(hex_map, 'unions'):
        return
    grid = hex_map.grid
    for union in hex_map.unions:
        union_ids = {s.id for s in union.members}
        union_cells = []
        for state in union.members:
            union_cells.extend(state.cells)
        if not union_cells:
            continue
        border_cells = []
        for cell in union_cells:
            r, q = cell.r, cell.q
            offsets = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)] if r % 2 == 0 else \
                      [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
            for dr, dq in offsets:
                nr, nq = r + dr, q + dq
                if 0 <= nr < len(grid) and 0 <= nq < len(grid[0]):
                    neighbor = grid[nr][nq]
                    if neighbor.state_id not in union_ids:
                        border_cells.append(cell)
                        break
        if not border_cells:
            continue
        centers = np.array([get_hex_center(cell, hex_size) for cell in border_cells])
        centroid = centers.mean(axis=0)
        angles = np.arctan2(centers[:, 1] - centroid[1], centers[:, 0] - centroid[0])
        sorted_centers = centers[np.argsort(angles)]
        polygon = Polygon(sorted_centers, closed=True, fill=False,
                          edgecolor='black', linestyle='solid', linewidth=1)
        ax.add_patch(polygon)

def draw_state_external_borders(ax, hex_map, hex_size):
    drawn_segments = set()
    # Смещения для соседей зависят от четности ряда
    offsets_even = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
    offsets_odd  = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
    
    for state in hex_map.states:
        border_cells = get_border_cells(state, hex_map)
        for cell in border_cells:
            center = get_hex_center(cell, hex_size)
            # Вычисляем вершины шестиугольника текущей клетки
            vertices = [center + np.array([np.cos(2*np.pi*i/6 + np.pi/6), np.sin(2*np.pi*i/6 + np.pi/6)]) * hex_size for i in range(6)]
            # Выбираем набор смещений в зависимости от четности ряда
            offsets = offsets_even if cell.r % 2 == 0 else offsets_odd
            for offset in offsets:
                nr = cell.r + offset[0]
                nq = cell.q + offset[1]
                # Если сосед существует и принадлежит тому же государству – пропускаем
                if 0 <= nr < len(hex_map.grid) and 0 <= nq < len(hex_map.grid[0]):
                    neighbor = hex_map.grid[nr][nq]
                    if neighbor.state_id == cell.state_id:
                        continue
                    neighbor_center = get_hex_center(neighbor, hex_size)
                else:
                    # Вычисляем виртуальный центр соседа, если он вне карты
                    neighbor_center = np.array([
                        hex_size * np.sqrt(3) * (nq + 0.5 * (nr % 2)),
                        hex_size * 1.5 * nr
                    ])
                # Вектор от центра текущей клетки к соседу и его угол
                vec = neighbor_center - center
                neighbor_angle = np.arctan2(vec[1], vec[0])
                best_edge = None
                best_diff = 1e6
                # Для каждого ребра вычисляем угол направления (по средней точке ребра)
                for edge in range(6):
                    pt1 = vertices[edge]
                    pt2 = vertices[(edge + 1) % 6]
                    midpoint = (pt1 + pt2) / 2
                    mid_angle = np.arctan2(midpoint[1] - center[1], midpoint[0] - center[0])
                    # Нормализуем разницу углов к интервалу [-pi, pi]
                    diff = abs((neighbor_angle - mid_angle + np.pi) % (2*np.pi) - np.pi)
                    if diff < best_diff:
                        best_diff = diff
                        best_edge = (tuple(pt1), tuple(pt2))
                # Сортировка концов отрезка для предотвращения дублирования
                segment = tuple(sorted(best_edge))
                if segment not in drawn_segments:
                    drawn_segments.add(segment)
                    ax.plot([segment[0][0], segment[1][0]], [segment[0][1], segment[1][1]],
                            color='black', linestyle='solid', linewidth=0.5)

def draw_hex_map(hex_map, hex_size=30):
    rows = hex_map.rows
    cols = hex_map.cols
    cells = hex_map.get_all_cells()
    fig, ax = plt.subplots(figsize=(12, 9))
    draw_hex_grid(ax, hex_size, cells, rows, cols)

    # Добавляем на карту подписи государств (с уменьшенным шрифтом)
    if hasattr(hex_map, 'states'):
        for state in hex_map.states:
            if state.capital is not None:
                center = get_hex_center(state.capital, hex_size)
                ax.plot(center[0], center[1], marker='*', markersize=5, color='red')
                ax.text(center[0], center[1] + hex_size * 0.3, state.name, fontsize=6, fontweight='bold',
                        color='black', ha='center', va='center')
                
    draw_separatist_boundaries(ax, hex_map, hex_size)                
    draw_state_external_borders(ax, hex_map, hex_size)                

    # === Добавляем координатную сетку по краям ===
    for r in range(rows):
        y = r * 1.5 * hex_size
        ax.text(-hex_size * 0.8, y, str(r), ha='right', va='center', fontsize=6, color='gray')
        ax.text((cols - 1) * hex_size * np.sqrt(3) + hex_size + 5, y, str(r),
                ha='left', va='center', fontsize=6, color='gray')

    for q in range(cols):
        x = q * hex_size * np.sqrt(3)
        ax.text(x + (hex_size * np.sqrt(3)) * 0.5, -hex_size * 1.2, str(q),
                ha='center', va='top', fontsize=6, color='gray')
        ax.text(x + (hex_size * np.sqrt(3)) * 0.5, rows * 1.5 * hex_size + hex_size * 0.5, str(q),
                ha='center', va='bottom', fontsize=6, color='gray')

    plt.title("Континенты, государства и столицы")
    plt.show()
