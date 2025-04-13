import os
import pickle
import random 
import csv 
from continent_generator import Map  
from visualize import draw_hex_map
from states import Map as StatesMap
from war import simulate_battles, absorb_isolated_groups
from separatism import trigger_separatism, process_separatist_states
from ideology import assign_random_ideology, ideological_drift, get_ideology_zone, get_coalition
 
save_file = 'saved_map.pkl'
map_loaded = os.path.exists(save_file)

if map_loaded:
    with open(save_file, 'rb') as f:
        hex_map = pickle.load(f)
    print("Карта загружена из файла.")
else:
    hex_map = Map(rows=50, cols=80, num_continents=25)
    print("Карта сгенерирована.")

if not hasattr(hex_map, 'states') or not hex_map.states:
    states_map = StatesMap(hex_map.rows, hex_map.cols)
    states_map.grid = hex_map.grid
    states_map.generate_states(count=25)
    hex_map.states = states_map.states
    print("Государства сгенерированы.")

if not hasattr(hex_map, 'step'):
    hex_map.step = 1
else:
    hex_map.step += 1
 
# Если идеология уже задана, не сбрасываем, а только корректируем дрейфом.
for state in hex_map.states:
    delta = random.randint(-3, 3)
    state.power += delta
    state.power = max(10, state.power)
    state.stability += delta
    state.stability = max(-10, min(state.stability, 10))

    if state.ideology_x is None or state.ideology_y is None:
        assign_random_ideology(state)
    else:
        ideological_drift(state)
    state.ideology_zone = get_ideology_zone(state.ideology_x, state.ideology_y)

    if not hasattr(state, 'history'):
        state.history = []
    state.history.append({
        'step': hex_map.step,      
        'id': state.id,
        'name': state.name,
        'power': state.power,
        'ideology_x': state.ideology_x,
        'ideology_y': state.ideology_y,
        'zone': state.ideology_zone,
        'stability': state.stability
    })

for state in list(hex_map.states):  # копия списка, так как он может измениться
    if state.stability < 0:
        if random.random() < 0.25:
            trigger_separatism(state, hex_map, hex_map.step)
process_separatist_states(hex_map, hex_map.step)

simulate_battles(hex_map, hex_map.states, max_battles=5)
absorb_isolated_groups(hex_map, threshold=3)
draw_hex_map(hex_map)  

log_file = "state_log.csv"
file_exists = os.path.exists(log_file)
with open(log_file, "a", newline='', encoding="utf-8") as f:
    fieldnames = ['step', 'id', 'name', 'power', 'ideology_x', 'ideology_y', 'zone', 'stability']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
    # Записываем историю для каждого государства, независимо от того, было ли оно уничтожено.
    for state in hex_map.states:
        for entry in state.history:
            # Если по каким-то причинам в записи нет поля id, добавляем его.
            if "id" not in entry:
                entry["id"] = state.id
            writer.writerow(entry)
 
with open(save_file, 'wb') as f:
    pickle.dump(hex_map, f)
