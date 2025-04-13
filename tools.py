def transfer_cell(hex_map, r, q, new_state_id):
    grid = hex_map.grid
    if not (0 <= r < len(grid)) or not (0 <= q < len(grid[0])):
        print(f"Клетка ({r}, {q}) вне границ карты.")
        return

    cell = grid[r][q]
    old_state = next((s for s in hex_map.states if s.id == cell.state_id), None)
    new_state = next((s for s in hex_map.states if s.id == new_state_id), None)

    if not new_state:
        print(f"Государство с ID {new_state_id} не найдено.")
        return

    if old_state:
        if cell in old_state.cells:
            old_state.cells.remove(cell)
        # Если это была столица
        if old_state.capital == cell:
            old_state.capital.is_capital = False
            old_state.capital = None
            print(f"Внимание: клетка была столицей государства {old_state.name} — столица сброшена.")

    cell.state_id = new_state.id
    cell.state_color = new_state.color
    new_state.cells.append(cell)

    