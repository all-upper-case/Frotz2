import sys
import os
import re
from flask import Flask, render_template, request, jsonify
from world_manager import WorldManager
from llm_interface import LLMInterface

app = Flask(__name__)
world = WorldManager()
ai = LLMInterface()

def log_system(msg):
    print(f"[SYSTEM] {msg}", flush=True)

@app.route('/update-files', methods=['POST'])
def update_files():
    if request.headers.get('X-Secret-Key') != "JosieSecret123":
        return "Unauthorized", 401
    
    content = request.get_data(as_text=True)
    if not content:
        return jsonify({"status": "error", "message": "No data"}), 400

    updated_files = []
    # Use a trick to prevent the regex from matching itself in the source code
    marker_regex = r'---FILE' + r':(.*?)---'
    parts = re.split(marker_regex, content)
    
    for i in range(1, len(parts), 2):
        filepath = parts[i].strip()
        code = parts[i+1].strip()
        
        folder = os.path.dirname(filepath)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        updated_files.append(filepath)

    return jsonify({"status": "success", "updated": updated_files})

@app.route('/')
def index():
    log_system("Frontend Connected")
    return render_template('index.html')

@app.route('/get_state', methods=['GET'])
def get_state():
    if not world.is_initialized():
        log_system("State requested: UNINITIALIZED")
        return jsonify({"response": "INITIALIZING_GENESIS", "state": None})

    room = world.get_current_room()
    return jsonify({"response": f"### {room['name']}\n{world.describe_room(room)}", "state": get_ui_state()})

@app.route('/reset', methods=['POST'])
def reset_game():
    log_system("HARD RESET TRIGGERED")
    world.hard_reset()
    try:
        log_system("Calling Genesis AI...")
        genesis_data = ai.generate_genesis()

        log_system("Initializing World DB...")
        intro = world.initialize_world(genesis_data)

        room = world.get_current_room()
        log_system("World Created Successfully.")
        return jsonify({
            "response": f"{intro}\n\n### {room['name']}\n{world.describe_room(room)}", 
            "state": get_ui_state()
        })
    except Exception as e:
        log_system(f"Genesis Failed: {str(e)}")
        return jsonify({"response": f"Genesis Failed: {str(e)}", "state": None})

@app.route('/command', methods=['POST'])
def handle_command():
    if not world.is_initialized(): return jsonify({"response": "Uninitialized."})

    user_input = request.json.get('input', '').strip()
    clean = user_input.lower().strip()
    if not user_input: return jsonify({"response": ""})

    log_system(f"Cmd: {user_input}")

    # DISAMBIGUATION CHECK
    if len(clean.split()) > 1: 
        noun = clean.split()[-1]
        if noun not in ['me', 'self', 'myself', 'player']: 
            candidates = world.get_all_visible_items()

            exact_matches = [i for i in candidates if noun == i['name'].lower() or noun in i.get('aliases', [])]
            if len(exact_matches) > 0:
                pass 
            else:
                matches = []
                for item in candidates:
                    if noun in item['name'].lower():
                        matches.append(item['name'])

                if len(set(matches)) > 1:
                    options = ", ".join(set(matches))
                    return jsonify({"response": f"Which one do you mean? ({options})", "state": get_ui_state()})

    # Deterministic Checks
    if clean in ['i', 'inv', 'inventory']:
        p = world.data['player']
        items = [world.data['items'][i]['name'] for i in p['inventory'] if i in world.data['items']]
        worn = [world.data['items'][i]['name'] for i in p.get('worn', []) if i in world.data['items']]
        res = []
        if items: res.append("**Carrying:**\n" + "\n".join([f"- {n}" for n in items]))
        if worn: res.append("**Wearing:**\n" + "\n".join([f"- {n}" for n in worn]))
        return jsonify({"response": "\n\n".join(res) if res else "Carrying nothing.", "state": get_ui_state()})

    if clean in ['l', 'look']:
        room = world.get_current_room()
        return jsonify({"response": f"### {room['name']}\n{world.describe_room(room)}", "state": get_ui_state()})

    if clean.startswith('x ') or clean.startswith('examine '):
        target = clean.split(' ', 1)[1].strip()
        if target in ['me', 'self', 'myself', 'player']:
            return jsonify({"response": world.describe_player(), "state": get_ui_state()})
        item = world.get_item_by_name(target)
        if item: return jsonify({"response": item['description'], "state": get_ui_state()})

    # Movement Logic
    status, target, prev_id = world.move_player(user_input)
    if status == "ok":
        room = world.get_room(target)
        return jsonify({"response": f"### {room['name']}\n{world.describe_room(room)}", "state": get_ui_state()})

    if status == "generate":
        prev = world.get_room(prev_id)
        thread = world.get_narrative_history()
        blueprint = world.data.get('blueprint', '')
        map_sum = world.get_map_summary()

        log_system("Generating New Room...")
        new_data = ai.generate_room(prev, user_input, thread, blueprint, map_sum)
        world.create_room_from_stub(target, new_data)
        room = world.get_room(target)
        return jsonify({"response": f"### {room['name']}\n{world.describe_room(room)}", "state": get_ui_state()})

    if status == "error" and "Invalid direction" in target:
        log_system("Handing off to DM AI...")
        return process_ai_turn(user_input)

    return jsonify({"response": target, "state": get_ui_state()})

@app.route('/models', methods=['GET'])
def list_models():
    models = ai.get_available_models()
    return jsonify(models)

@app.route('/set_model', methods=['POST'])
def set_model():
    model_id = request.json.get('model')
    if model_id:
        ai.model = model_id
        return jsonify({"status": "success", "model": model_id})
    return jsonify({"status": "error"}), 400

def process_ai_turn(inp):
    thread = world.get_narrative_history() 
    context_dump = world.get_context_dump()

    # Check for System Notifications (from previous syncs not yet popped)
    msgs = world.pop_system_notifications()
    full_input = inp
    if msgs:
        sys_msg = "\n\n".join([f"[SYSTEM NOTICE: {m}]" for m in msgs])
        full_input = f"{sys_msg}\n\nPLAYER ACTION: {inp}"

    outcome = ai.process_turn(full_input, thread, context_dump)
    world.apply_outcome(outcome)

    return jsonify({"response": outcome.get("narrative", "..."), "state": get_ui_state()})

# --- GOD MODE ROUTES ---
@app.route('/get_god_state', methods=['GET'])
def get_god_state():
    return jsonify(world.get_god_state())

@app.route('/god_update', methods=['POST'])
def god_update():
    changes = request.json.get('changes', [])
    sys_msg = world.god_mode_update(changes, ai)

    if sys_msg:
        # Trigger immediate AI turn
        thread = world.get_narrative_history()
        context_dump = world.get_context_dump()
        full_input = f"[SYSTEM EVENT]\n{sys_msg}"

        outcome = ai.process_turn(full_input, thread, context_dump)
        world.apply_outcome(outcome)

        return jsonify({
            "response": f"**REALITY SHIFT APPLIED:**\n{outcome.get('narrative', 'State updated.')}",
            "state": get_ui_state()
        })

    return jsonify({"response": "No changes required.", "state": get_ui_state()})

@app.route('/get_debug', methods=['GET'])
def get_debug():
    if os.path.exists("last_turn_debug.txt"):
        with open("last_turn_debug.txt", "r", encoding="utf-8") as f:
            return f.read()
    return jsonify({"error": "No debug info found."})

def get_ui_state():
    if not world.is_initialized(): return None
    room = world.get_current_room()
    p = world.data['player']
    inv = [world.data['items'][i]['name'] for i in p['inventory'] if i in world.data['items']]
    worn = [world.data['items'][i]['name'] for i in p['worn'] if i in world.data['items']]
    body = [world.data['items'][i]['name'] for i in p.get('body', []) if i in world.data['items']]
    return {
        "location": room.get('name', 'Unknown'),
        "inventory": inv,
        "worn": worn,
        "body": body,
        "exits": list(room.get('exits', {}).keys()),
        "total_tokens": world.data.get('meta', {}).get('total_tokens', 0)
    }

if __name__ == "__main__":
    log_system("Server Starting on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)