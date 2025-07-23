import json
import threading
import os
import uuid
import shapely
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from game_history import GameStateHistory
from handle_input import ActionType
from transformation import Transformation
from pygame.locals import *
import pygame
import utils



def print_error_if_occured(func):
    def rt(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            import traceback
            print(e)
            traceback.print_exc(e)
    return rt


@print_error_if_occured
def save_game_session(client_id, game_data):
    os.makedirs("sessions", exist_ok=True)
    filename = f"sessions/{client_id}.json"
    with open(filename, "w") as f:
        json.dump({
            "history": game_data['history'].to_json_string(),
            "transformation": game_data['transformation'].to_json(),
            "config": game_data['config']
        }, f)

@print_error_if_occured
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
    return None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

games = {}
lock = threading.Lock()
# Setup mouse_move buffers for each client
mouse_move_buffers = {}

@print_error_if_occured
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
    
    return actions

@print_error_if_occured
def game_state_to_dict(game_state, transformation, config):
    polygons = []
    for polygon_or_multipolygon, color in game_state.get_list_of_shapes_to_draw():
        if hasattr(polygon_or_multipolygon, 'geoms'):  # MultiPolygon
            for polygon in polygon_or_multipolygon.geoms:
                polygons.append({
                    'points': [transformation.world_to_screen(wx, wy) for wx, wy in polygon.exterior.coords],
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

@app.route('/')
@print_error_if_occured
def index():
    return render_template('index.html')

@socketio.on('connect')
@print_error_if_occured
def handle_connect(*args):
    print("Client connected")

@socketio.on('register')
@print_error_if_occured
def handle_register(client_id):
    join_room(client_id)
    with lock:
        if client_id not in games:
            config = utils.default_config
            utils.update_colors(config)
            games[client_id] = {
                'history': GameStateHistory(config),
                'transformation': Transformation(0, 0, shapely.Polygon(config["board_polygon"])),
                'config': config
            }
            # Initialize mouse move buffer for this client
            mouse_move_buffers[client_id] = []
        
        game_data = games[client_id]
        game_history = game_data['history']
        transformation = game_data['transformation']
        config = game_data['config']
    
    # Send initial state
    game_history.update(None)
    state = game_state_to_dict(game_history.current_game_state, transformation, config)
    socketio.emit('init', {
        'type': 'init',
        'state': state,
        'config': config
    }, room=client_id)


@socketio.on('join_new_group')
def join_new_group(data):
    client_id, new_group = data
    print(f"{client_id = } joins {new_group = }")
    leave_room(client_id)
    join_room(new_group)


@socketio.on('game_action')
@print_error_if_occured
def handle_game_action(data):
    client_id = data.get('client_id')
    
    if client_id not in games:
        return
    
    game_data = games[client_id]
    game_history = game_data['history']
    transformation = game_data['transformation']
    config = game_data['config']
    
    action_type = data.get('action_type')
    
    # Handle special actions
    if action_type == 'save_game':
        json_str = game_history.to_json_string()
        socketio.emit('save_game', {
            'type': 'save_game',
            'game_data': json_str
        }, room=client_id)
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
        socketio.emit('update', {
            'type': 'update',
            'state': state
        }, room=client_id)
    elif action_type == 'mouse_move':
        # Add to mouse move buffer for batched processing
        with lock:
            mouse_move_buffers[client_id].append(data)
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
        socketio.emit('update', {
            'type': 'update',
            'state': state
        }, room=client_id)

@print_error_if_occured
def process_mouse_moves():
    """Process batched mouse moves for all clients"""
    while True:
        with lock:
            for client_id, buffer in list(mouse_move_buffers.items()):
                if not buffer or client_id not in games:
                    continue
                
                game_data = games[client_id]
                transformation = game_data['transformation']
                game_history = game_data['history']
                
                # Sum relative movements and get last position
                sum_rel_x = 0
                sum_rel_y = 0
                last_x_screen = None
                last_y_screen = None
                last_is_control_pressed = None

                for data in buffer:
                    sum_rel_x += data['rel_x']
                    sum_rel_y += data['rel_y']
                    last_x_screen = data['x']
                    last_y_screen = data['y']
                    last_is_control_pressed = data['is_control_pressed']

                # Transform to world coordinates
                last_x, last_y = transformation.screen_to_world(last_x_screen, last_y_screen)
                
                # Create batched action
                action = {
                    'action_type': ActionType.MOUSE_MOTION,
                    'x': last_x,
                    'y': last_y,
                    'rel_x': sum_rel_x,
                    'rel_y': sum_rel_y,
                    'is_control_pressed': last_is_control_pressed,
                }
                
                # Apply actions
                if last_is_control_pressed:
                    transformation.update_self_drag(sum_rel_x, sum_rel_y)
                else:
                    game_history.update(action)
                
                # Clear buffer
                buffer.clear()
                
                # Send update
                game_history.update(None)
                state = game_state_to_dict(game_history.current_game_state, transformation, game_data['config'])
                socketio.emit('update', {
                    'type': 'update',
                    'state': state
                }, room=client_id)

                # print(f"sending update {client_id = }, stone = {[elem for elem in state['polygons'] if "black" in elem["color"]][0]}")
        
        # Wait for next frame
        socketio.sleep(1/60)

@print_error_if_occured
def save_sessions_periodically():
    """Periodically save all game sessions"""
    while True:
        socketio.sleep(5)  # Save every 5 seconds
        with lock:
            for client_id, game_data in games.items():
                save_game_session(client_id, game_data)

@socketio.on('disconnect')
@print_error_if_occured
def handle_disconnect(*args):
    print("Client disconnected")
    # Could add client cleanup here if needed

if __name__ == '__main__':
    os.makedirs("sessions", exist_ok=True)
    
    # Start background threads
    socketio.start_background_task(process_mouse_moves)
    socketio.start_background_task(save_sessions_periodically)
    
    # Start the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
