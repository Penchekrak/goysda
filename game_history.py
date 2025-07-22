import json


from game_state import GameState
from handle_input import ActionType
from utils import get_readable_filepath


class GameStateHistory:
    def __init__(self, config):
        self.config = config
        self.current_game_state = GameState(config=config)
        self.history = [self.current_game_state.to_json()]
    
    def update(self, action):
        if action is None:
            self.current_game_state.update(None)
            return 
        
        if action["action_type"] == ActionType.UNDO:
            if len(self.history) >= 2:
                self.history.pop()
                self.current_game_state = GameState(self.config, json=self.history[-1])
            else:
                print("Trying to undo empty position")
            return
        
        actions_counter = self.current_game_state.actions_counter
        self.current_game_state.update(action)
        if not self.current_game_state.is_position_possible:
            self.current_game_state = GameState(self.config, self.history[-1])
            print("Impossible move! The move has been undone")
        elif self.current_game_state.actions_counter != actions_counter:
            self.history.append(self.current_game_state.to_json())
    
    def save_to_file(self, filepath=None):
        if filepath is None:
            filepath = get_readable_filepath()
        
        with open(filepath, "w") as f:
            json.dump({"config": self.config, "history": self.history}, f)
    
    def open_from_a_file(self, filepath):
        self.save_to_file()

        with open(filepath, "r") as f:
            json_info = json.load(f)
        self.history = json_info["history"]
        self.config = json_info["config"]
        self.current_game_state = GameState(self.config, json=self.history[-1])
    
    def to_json_string(self):
        return json.dumps({
            "config": self.config,
            "history": self.history
        })

    def load_from_json_string(self, json_string):
        data = json.loads(json_string)
        self.config = data["config"]
        self.history = data["history"]
        self.current_game_state = GameState(self.config, json=self.history[-1])
