import json
import asyncio
import websockets
import threading
from flask import Flask, render_template
from game_history import GameStateHistory
from handle_input import ActionType
from transformation import Transformation
from pygame.locals import *
import pygame
import shapely
import utils
import os
import uuid

# Add this function to save games
def save_game_session(client_id, game_data):
    os.makedirs("sessions", exist_ok=True)
    filename = f"sessions/{client_id}.json"
    with open(filename, "w") as f:
        json.dump({
            "history": game_data['history'].to_json_string(),
            "transformation": json.dumps(game_data['transformation'].to_json()),
            "config": game_data['config']
        }, f)

# Add this function to load games
def load_game_session(client_id):
    filename = f"sessions/{client_id}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
            history = GameStateHistory(config=data['config'])
            history.load_from_json_string(data['history'])
            transformation = Transformation.from_json(data['transformation'])
            return {
                'history': history,
                'transformation': transformation,
                'config': data['config']
            }
    return Non

app = Flask(__name__)
games = {}
lock = threading.Lock()


def handle_web_input(data, transformation, game_history):
    action_type = data.get('action_type')
    actions = []
    
    if action_type == 'mouse_down_left':
        x, y = transformation.screen_to_world(data['x'], data['y'])
        actions.append({
            'action_type': ActionType.MOUSE_DOWN_LEFT,
            'x': x,
            'y': y
        })
    elif action_type == 'mouse_down_right':
        x, y = transformation.screen_to_world(data['x'], data['y'])
        actions.append({
            'action_type': ActionType.MOUSE_DOWN_RIGHT,
            'x': x,
            'y': y
        })
    elif action_type == 'mouse_move':
        x, y = transformation.screen_to_world(data['x'], data['y'])
        actions.append({
            'action_type': ActionType.MOUSE_MOTION,
            'x': x,
            'y': y,
            'rel_x': data['rel_x'],
            'rel_y': data['rel_y'],
            'is_control_pressed': data['is_control_pressed']
        })
    elif action_type == 'mouse_scroll':
        actions.append({
            'action_type': ActionType.MOUSE_SCROLL,
            'x': data['x'],
            'y': data['y'],
            'value': data['value']
        })
    elif action_type == 'key_down':
        key_map = {
            'control': K_LCTRL,
            'a': K_a,
            'b': K_b,
            'c': K_c,
            'd': K_d,
            'e': K_e,
            'f': K_f,
            'g': K_g,
            'h': K_h,
            'i': K_i,
            'j': K_j,
            'k': K_k,
            'l': K_l,
            'm': K_m,
            'n': K_n,
            'o': K_o,
            'p': K_p,
            'r': K_r,
            's': K_s,
            't': K_t,
            'u': K_u,
            'v': K_v,
            'w': K_w,
            'x': K_x,
            'y': K_y,
            'z': K_z,
        }
        if data['key'] in key_map and not data['key'] == 'z':
            actions.append({
                'action_type': ActionType.KEY_DOWN,
                'key': key_map[data['key']]
            })
        elif data['key'] == 'z':
            actions.append({
                'action_type': ActionType.UNDO
            })
    elif action_type == 'reset_view':
        transformation.reset()
    
    if "x" in actions:
        actions["x"], actions["y"] = transformation.screen_to_world(actions["x"], actions["y"])
    if "rel_x" in actions:
        actions["rel_x"], actions["rel_y"] = transformation.screen_to_world(actions["rel_x"], actions["rel_y"])
    
    return actions

def game_state_to_dict(game_state, transformation, config):
    polygons = []
    for polygon_or_multipolygon, color in game_state.get_list_of_shapes_to_draw():
        if hasattr(polygon_or_multipolygon, 'geoms'):  # MultiPolygon
            for polygon in polygon_or_multipolygon.geoms:
                polygons.append({
                    'points': list(polygon.exterior.coords),
                    'color': color
                })
        else:  # Single Polygon
            polygons.append({
                'points': [transformation.world_to_screen(wx, wy) for wx, wy in polygon_or_multipolygon.exterior.coords],
                'color': color
            })
    
    return {
        'polygons': polygons,
        'info': game_state.get_info(),
        'background': game_state.background_to_render_list[game_state.background_to_render_index],
        'board_style': game_state.board_to_render_list[game_state.board_to_render_index]
    }

async def game_handler(websocket):
    client_id = await websocket.recv()
    with lock:
        if client_id not in games:
            config = utils.default_config
            utils.update_colors(config)
            games[client_id] = {
                'history': GameStateHistory(config),
                'transformation': Transformation(0, 0, shapely.Polygon(config["board_polygon"])),
                'config': config
            }
        
        game_data = games[client_id]
        game_history = game_data['history']
        transformation = game_data['transformation']
        config = game_data['config']
    
    # Send initial state
    game_history.update(None)
    state = game_state_to_dict(game_history.current_game_state, transformation, config)
    await websocket.send(json.dumps({
        'type': 'init',
        'state': state,
        'config': config
    }))
    
    # Setup mouse_move buffer
    mouse_move_buffer = []
    buffer_lock = asyncio.Lock()
    frame_duration = 1 / 60  # Adjust FPS as needed
    
    # Start frame processor task
    asyncio.create_task(frame_processor(
        websocket, game_data, transformation, mouse_move_buffer, buffer_lock, frame_duration
    ))
    
    # Handle messages
    async for message in websocket:
        data = json.loads(message)
        action_type = data.get('action_type')
        # Add these new handlers
        if action_type == 'save_game':
            json_str = game_history.to_json_string()
            await websocket.send(json.dumps({
                'type': 'save_game',
                'game_data': json_str
            }))
        elif action_type == 'load_game':
            game_data_str = data['game_data']
            game_history.load_from_json_string(game_data_str)
            # Reset transformation
            transformation.reset()
            # Update game data
            game_data['config'] = game_history.config
            # Send update
            game_history.update(None)
            state = game_state_to_dict(game_history.current_game_state, transformation, game_history.config)
            await websocket.send(json.dumps({
                'type': 'update',
                'state': state
            }))
        elif action_type == 'mouse_move':
            async with buffer_lock:
                mouse_move_buffer.append(data)
        else:
            # Process non-mouse_move actions immediately
            actions = handle_web_input(data, transformation, game_history)
            for action in actions:
                if action["action_type"] == ActionType.MOUSE_SCROLL:
                    transformation.update_self_zoom(action["x"], action["y"], config["zoom_speed"] * action["value"])
                elif action["action_type"] == ActionType.MOUSE_MOTION and action.get("is_control_pressed"):
                    transformation.update_self_drag(action["rel_x"], action["rel_y"])
                else:
                    game_history.update(action)
            # Send update
            game_history.update(None)
            state = game_state_to_dict(game_history.current_game_state, transformation, config)
            await websocket.send(json.dumps({
                'type': 'update',
                'state': state
            }))

async def frame_processor(websocket, game_data, transformation, mouse_move_buffer, buffer_lock, frame_duration):
    while True:
        await asyncio.sleep(frame_duration)
        async with buffer_lock:
            if not mouse_move_buffer:
                continue
            
            # Sum relative movements and get last position
            sum_rel_x = 0
            sum_rel_y = 0
            last_x_screen = None
            last_y_screen = None
            last_is_control_pressed = None

            for data in mouse_move_buffer:
                sum_rel_x += data['rel_x']
                sum_rel_y += data['rel_y']
                last_x_screen = data['x']
                last_y_screen = data['y']
                last_is_control_pressed = data['is_control_pressed']

            # Transform to world coordinates
            transformation = game_data['transformation']
            last_x, last_y = transformation.screen_to_world(last_x_screen, last_y_screen)
            sum_rel_x, sum_rel_y = transformation.screen_to_world(sum_rel_x, sum_rel_y)
            # Create batched action
            actions = [{
                'action_type': ActionType.MOUSE_MOTION,
                'x': last_x,
                'y': last_y,
                'rel_x': sum_rel_x,
                'rel_y': sum_rel_y,
                'is_control_pressed': last_is_control_pressed,
            }]
            
            # Apply actions
            if last_is_control_pressed:
                transformation.update_self_drag(sum_rel_x, sum_rel_y)
            else:
                game_history = game_data['history']
                for action in actions:
                    game_history.update(action)
            
            # Clear buffer
            mouse_move_buffer.clear()
        
        # Send update after processing
        game_history.update(None)
        state = game_state_to_dict(game_history.current_game_state, transformation, game_data['config'])
        await websocket.send(json.dumps({
            'type': 'update',
            'state': state
        }))

@app.route('/')
def index():
    return render_template('index.html')

# Add periodic saving
async def session_saver():
    while True:
        await asyncio.sleep(5)  # Save every 60 seconds
        with lock:
            for client_id, game_data in games.items():
                save_game_session(client_id, game_data)

# Update start_websocket
async def start_websocket():
    os.makedirs("sessions", exist_ok=True)
    async with websockets.serve(game_handler, "localhost", 6789) as server:
        await asyncio.gather(session_saver(), server.serve_forever())

def start_app():
    app.run(port=5000)

if __name__ == '__main__':
    threading.Thread(group=None, target=start_app, daemon=False).start()
    asyncio.run(start_websocket())
    
