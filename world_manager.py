import json
import os
import shutil
import uuid
import re

SAVE_DIR = "saves"
BACKUP_DIR = "backups"

DIRECTION_MAP = {
    "n": "north", "north": "north", "s": "south", "south": "south",
    "e": "east", "east": "east", "w": "west", "west": "west",
    "u": "up", "up": "up", "d": "down", "down": "down"
}

class WorldManager:
    def __init__(self):
        if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)
        self.world_name = self._get_world_name()
        self.save_path = os.path.join(SAVE_DIR, f"{self.world_name}.json")
        self.data = self.load_game()
        if self.data: self.ensure_schema()

    def _get_world_name(self):
        if os.path.exists("lore.txt"):
            with open("lore.txt", "r", encoding="utf-8") as f:
                first = f.readline().strip()
                if first.startswith("WORLD_NAME:"):
                    return "".join(c for c in first.split(":", 1)[1].strip().lower() if c.isalnum() or c == '_')
        return "default_world"

    def load_game(self):
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r', encoding='utf-8') as f: return json.load(f)
            except: pass
        return None

    def save_game(self):
        with open(self.save_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def is_initialized(self):
        return self.data is not None

    def ensure_schema(self):
        if not self.data: return
        player = self.data.setdefault('player', {})
        player.setdefault('inventory', [])
        player.setdefault('worn', [])
        player.setdefault('current_room', 'room_start')
        player.setdefault('description', 'You look ordinary.')
        player.setdefault('aliases', ['me', 'myself', 'self', 'player'])

        self.data.setdefault('characters', {})
        self.data.setdefault('blueprint', 'Explore.')
        self.data.setdefault('meta', {}).setdefault('total_tokens', 0)
        self.data.setdefault('pending_notifications', [])

        if 'narrative_thread' in self.data and isinstance(self.data['narrative_thread'], str):
            self.data['narrative_log'] = [self.data['narrative_thread']]
            del self.data['narrative_thread']
        self.data.setdefault('narrative_log', [])

        if 'rooms' in self.data:
            self.data['rooms'] = {k: v for k, v in self.data['rooms'].items() if v is not None}

        for room in self.data.get('rooms', {}).values():
            if not isinstance(room, dict): continue
            room.setdefault('items', []); room.setdefault('characters', [])
            room.setdefault('exits', {}); room.setdefault('name', 'Unknown')
            base = room.get('base_description')
            if not base or "You can see here:" in base:
                room['base_description'] = self._strip_generated_content(room.get('description', '...'))

        for item in self.data.get('items', {}).values():
            if not isinstance(item, dict): continue
            item.setdefault('id', f"i_{uuid.uuid4().hex[:4]}")
            item.setdefault('name', 'thing'); item.setdefault('aliases', [])
            item['aliases'] = [a.lower() for a in item.get('aliases', [])]
            item.setdefault('description', '...'); item.setdefault('carryable', True)
            item.setdefault('visible', True)

    def _strip_generated_content(self, text):
        if not text: return "..."
        cleaned = re.split(r'\n\s*(You can see here:|Others present:)', text)[0].strip()
        if not cleaned: return text if len(text) < 200 else "A hazy area." 
        return cleaned

    def update_metrics(self, usage):
        if usage and 'total_tokens' in usage:
            self.data['meta']['total_tokens'] += usage['total_tokens']

    def get_map_summary(self):
        lines = []
        for rid, room in list(self.data['rooms'].items()):
            if not isinstance(room, dict): continue
            ex = ", ".join(f"{k}->{v}" for k, v in room.get('exits', {}).items())
            lines.append(f"Room: {room.get('name', 'Unknown')} (ID: {rid}) | Exits: {ex}")
        return "\n".join(lines)

    def get_context_dump(self):
        room = self.get_current_room()
        if not room: return "Void."

        lines = [f"CURRENT LOCATION: {room.get('name', 'Unknown')}", f"DESC: {room.get('base_description', '...')}", ""]

        lines.append("[PLAYER CHARACTER]")
        lines.append(f"CURRENT DESCRIPTION: {self.data['player'].get('description', 'Ordinary.')}")
        lines.append("")

        lines.append("[HERE - Items visible in this room]")
        visible_items = []
        for iid in room.get('items', []):
            item = self.data['items'].get(iid)
            if item and item.get('visible', True):
                visible_items.append(f"- {item['name']} (ID: {iid}): {item['description']}")
        if not visible_items: lines.append("(Nothing)")
        else: lines.extend(visible_items)

        lines.append("\n[INVENTORY - Items carried]")
        if not self.data['player']['inventory']:
            lines.append("(Nothing)")
        else:
            for iid in self.data['player']['inventory']:
                item = self.data['items'].get(iid)
                if item: lines.append(f"- {item['name']} (ID: {iid}): {item['description']}")

        lines.append("\n[WORN - Items equipped]")
        if not self.data['player']['worn']:
            lines.append("(Nothing)")
        else:
            for iid in self.data['player']['worn']:
                item = self.data['items'].get(iid)
                if item: lines.append(f"- {item['name']} (ID: {iid}): {item['description']}")

        lines.append("\n[ALL ROOMS - Global Map Context]")
        for rid, rdata in list(self.data['rooms'].items()):
            if not isinstance(rdata, dict): continue
            lines.append(f"- {rdata.get('name', 'Unknown')} (ID: {rid}): {rdata.get('base_description', '...')[:100]}...")

        return "\n".join(lines)

    def get_narrative_history(self):
        return "\n".join([f"- {entry}" for entry in self.data.get('narrative_log', [])])

    def pop_system_notifications(self):
        msgs = self.data.get('pending_notifications', [])
        self.data['pending_notifications'] = []
        self.save_game()
        return msgs

    def find_item_id_by_name(self, name):
        """Looks up an item ID by name in the ENTIRE database (Visible or Void)."""
        if not name: return None
        clean = name.lower().strip()
        if clean in ['me', 'self', 'myself', 'player']: return None

        all_ids = list(self.data['items'].keys())

        # Exact Match
        for iid in all_ids:
            item = self.data['items'][iid]
            if not isinstance(item, dict): continue
            if item.get('name', '').lower() == clean: return iid
            if clean in item.get('aliases', []): return iid

        # Partial Match
        for iid in all_ids:
            item = self.data['items'][iid]
            if not isinstance(item, dict): continue
            if clean in item.get('name', '').lower(): return iid

        return None

    def find_room_id_by_name(self, name):
        if not name: return None
        clean = name.lower().strip()
        for rid, r in list(self.data['rooms'].items()):
            if not isinstance(r, dict): continue
            if r.get('name', '').lower() == clean: return rid
            if clean in r.get('name', '').lower(): return rid 
        return None

    def initialize_world(self, genesis_data):
        start_tokens = genesis_data.get("_usage", {}).get("total_tokens", 0)
        items_db = {}

        start_desc = self._strip_generated_content(genesis_data.get('starting_room_description', '...'))
        rooms_db = {
            "room_start": {
                "id": "room_start", 
                "name": genesis_data.get('starting_room_name', 'Start'),
                "description": start_desc, 
                "base_description": start_desc,
                "exits": {}, "items": [], "characters": [], "visited": True
            }
        }

        self.data = {
            "narrative_log": [genesis_data.get('intro_text', '') + " " + genesis_data.get('narrative_thread', '')],
            "blueprint": genesis_data.get('blueprint', 'Explore.'),
            "meta": {"total_tokens": start_tokens},
            "player": {
                "current_room": "room_start", "inventory": [], "worn": [],
                "description": genesis_data.get('player_description', 'You look ordinary.'),
                "aliases": ['me', 'self', 'player']
            },
            "characters": {}, "rooms": rooms_db, "items": items_db
        }

        for d in genesis_data.get('new_exits', []):
            norm = DIRECTION_MAP.get(d.lower())
            if norm:
                stub_id = f"room_{uuid.uuid4().hex[:8]}"
                rooms_db[stub_id] = {
                    "id": stub_id, "name": "Unknown", "description": None,
                    "base_description": None, "exits": {self.get_opposite_dir(norm): "room_start"},
                    "items": [], "characters": [], "visited": False
                }
                rooms_db["room_start"]['exits'][norm] = stub_id

        self.apply_outcome({"actions": [], "state_updates": genesis_data.get("state_updates", [])})
        self.ensure_schema()
        self.save_game()
        return genesis_data.get('intro_text', 'Welcome.')

    def hard_reset(self):
        if os.path.exists(self.save_path):
            if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
            shutil.move(self.save_path, os.path.join(BACKUP_DIR, f"{self.world_name}_{uuid.uuid4().hex[:4]}.json"))
        self.data = None

    def get_current_room(self):
        return self.data['rooms'].get(self.data['player']['current_room']) if self.data else None

    def get_room(self, rid):
        return self.data['rooms'].get(rid) if self.data else None

    def describe_room(self, room=None):
        room = room or self.get_current_room()
        if not room: return "Void."
        base = room.get('base_description')
        if not base: 
            base = self._strip_generated_content(room.get('description', '...'))
            room['base_description'] = base
        visible = []
        for iid in room.get('items', []):
            item = self.data['items'].get(iid)
            if item and item.get('visible', True): visible.append(item['name'])
        item_line = f"\n\nYou can see here: {', '.join(visible)}." if visible else ""
        composed = f"{base}{item_line}".strip()
        room['description'] = composed
        return composed

    def describe_player(self):
        p = self.data['player']
        base = p.get('description', 'You look ordinary.')
        body = [self.data['items'][iid]['name'] for iid in p.get('body', []) if iid in self.data['items']]
        worn = [self.data['items'][iid]['name'] for iid in p.get('worn', []) if iid in self.data['items']]
        inv = [self.data['items'][iid]['name'] for iid in p.get('inventory', []) if iid in self.data['items']]
        
        body_text = f"\n\nDistinguishing features: {', '.join(body)}." if body else ""
        worn_text = f"\n\nYou are wearing: {', '.join(worn)}." if worn else ""
        inv_text = f"\nYou are carrying: {', '.join(inv)}." if inv else ""
        return f"{base}{body_text}{worn_text}{inv_text}".strip()

    def get_all_visible_items(self):
        room = self.get_current_room()
        candidates = []
        def add_source(source_list):
            for iid in source_list:
                item = self.data['items'].get(iid)
                if item and item.get('visible', True): candidates.append(item)
        add_source(self.data['player']['inventory'])
        add_source(self.data['player']['worn'])
        add_source(room.get('items', []))
        return candidates

    def get_item_by_name(self, query):
        query = query.lower().strip()
        candidates = self.get_all_visible_items()
        for item in candidates:
            if not item: continue
            if query in item.get('aliases', []) or query == item.get('name', '').lower(): return item
        for item in candidates:
            if not item: continue
            if query in item.get('name', '').lower(): return item
        return None

    def move_player(self, d_input):
        direction = DIRECTION_MAP.get(d_input.lower())
        if not direction: return "error", "Invalid direction.", None
        curr = self.get_current_room()
        target_id = curr.get('exits', {}).get(direction)
        if not target_id: return "error", "You can't go that way.", curr.get('id')
        self.data['player']['current_room'] = target_id
        target = self.get_room(target_id)
        if target.get('description') is None: return "generate", target_id, curr.get('id')
        target['visited'] = True
        self.describe_room(target)
        self.save_game()
        return "ok", target_id, curr.get('id')

    def create_room_from_stub(self, stub_id, ai_data):
        room = self.data['rooms'][stub_id]
        base = self._strip_generated_content(ai_data.get('room_description', '...'))
        room['name'] = ai_data.get('room_name', 'Unknown')
        room['base_description'] = base
        if "_usage" in ai_data: self.update_metrics(ai_data["_usage"])
        if "blueprint_update" in ai_data: self.data['blueprint'] = ai_data['blueprint_update']
        original_room = self.data['player']['current_room']
        self.data['player']['current_room'] = stub_id
        self.apply_outcome({"state_updates": ai_data.get("state_updates", [])})
        self.data['player']['current_room'] = original_room
        for d in ai_data.get('new_exits', []):
            norm = DIRECTION_MAP.get(d.lower())
            if norm and norm not in room.get('exits', {}):
                new_id = f"room_{uuid.uuid4().hex[:8]}"
                self.data['rooms'][new_id] = {
                    "id": new_id, "name": "Unknown", "description": None, "base_description": None,
                    "exits": {self.get_opposite_dir(norm): stub_id}, "items": [], "characters": [], "visited": False
                }
                room['exits'][norm] = new_id
        self.describe_room(room)
        self.save_game()

    def apply_outcome(self, outcome):
        if not isinstance(outcome, dict): return
        if "_usage" in outcome: self.update_metrics(outcome["_usage"])
        if 'narrative_summary_update' in outcome: 
            self.data['narrative_log'].append(outcome['narrative_summary_update'])

        updates = outcome.get('state_updates', [])
        for up in updates:
            tool = up.get('tool', '').strip()
            name = up.get('name', '').strip()
            if not name: continue
            clean_name = name.lower()

            if clean_name in ['self', 'me', 'myself', 'player']:
                if tool == "Description":
                    self.data['player']['description'] = up.get('description', self.data['player']['description'])
                continue 

            if tool == "Description":
                desc = up.get('description', '...')
                aliases = up.get('aliases', [])
                is_body_part = up.get('location') == 'body'
                
                iid = self.find_item_id_by_name(name)
                if iid:
                    self.data['items'][iid]['description'] = desc
                    if is_body_part: self.data['items'][iid]['body_part'] = True
                    if aliases: 
                        current_aliases = set(self.data['items'][iid]['aliases'])
                        current_aliases.update([a.lower() for a in aliases])
                        self.data['items'][iid]['aliases'] = list(current_aliases)
                else:
                    new_id = f"i_{uuid.uuid4().hex[:6]}"
                    self.data['items'][new_id] = {
                        "id": new_id, "name": name,
                        "aliases": [clean_name] + [a.lower() for a in aliases],
                        "description": desc, "carryable": not is_body_part, 
                        "visible": True, "body_part": is_body_part
                    }

            elif tool == "Location":
                loc = up.get('location', '').lower()
                iid = self.find_item_id_by_name(name)
                if not iid: continue
                player = self.data['player']
                
                # Cleanup existing locations
                for r in self.data['rooms'].values():
                    if isinstance(r, dict) and iid in r.get('items', []): r['items'].remove(iid)
                if iid in player['inventory']: player['inventory'].remove(iid)
                if iid in player['worn']: player['worn'].remove(iid)
                if iid in player.get('body', []): player['body'].remove(iid)

                if loc == "nowhere": pass
                elif loc == "inventory": player['inventory'].append(iid)
                elif loc == "worn": player['worn'].append(iid)
                elif loc == "body":
                    player.setdefault('body', [])
                    player['body'].append(iid)
                    self.data['items'][iid]['body_part'] = True
                    self.data['items'][iid]['carryable'] = False
                elif loc == "here": self.data['rooms'][player['current_room']]['items'].append(iid)
                else:
                    target_rid = self.find_room_id_by_name(loc)
                    if target_rid: self.data['rooms'][target_rid]['items'].append(iid)
                    else: self.data['rooms'][current_room_id]['items'].append(iid)

        self.describe_room()
        self.save_game()

    def get_god_state(self):
        if not self.data: return {}
        items_out = []
        for iid, item in self.data['items'].items():
            loc = "Void"
            if iid in self.data['player']['inventory']: loc = "Inventory"
            elif iid in self.data['player']['worn']: loc = "Worn"
            else:
                for rid, r in self.data['rooms'].items():
                    if iid in r.get('items', []):
                        loc = f"Room: {r['name']}"
                        break
            items_out.append({
                "id": iid, "name": item['name'], "location": loc, 
                "description": item['description'], "aliases": ", ".join(item['aliases'])
            })
        rooms_out = [{"id": r, "name": d['name']} for r, d in self.data['rooms'].items()]
        return {"items": items_out, "rooms": rooms_out}

    def god_mode_update(self, changes, ai_interface):
        logs = []
        for change in changes:
            iid = change['id']
            if iid not in self.data['items']: continue
            item = self.data['items'][iid]

            if 'newAliases' in change:
                item['aliases'] = [a.strip().lower() for a in change['newAliases'].split(',')]
            if 'newDescription' in change and change['newDescription']:
                item['description'] = change['newDescription']
                logs.append(f"{item['name']} description updated.")

            new_loc = change.get('newLocation')
            if new_loc:
                player = self.data['player']
                old_loc_name = "unknown"
                for r in self.data['rooms'].values():
                    if iid in r.get('items', []): 
                        old_loc_name = r['name']
                        r['items'].remove(iid)
                if iid in player['inventory']: 
                    old_loc_name = "Inventory"
                    player['inventory'].remove(iid)
                if iid in player['worn']: 
                    old_loc_name = "Worn"
                    player['worn'].remove(iid)

                loc_name_for_log = new_loc
                if new_loc == "Inventory": player['inventory'].append(iid)
                elif new_loc == "Worn": player['worn'].append(iid)
                elif new_loc == "Void": pass
                else: 
                    if new_loc in self.data['rooms']:
                        self.data['rooms'][new_loc]['items'].append(iid)
                        loc_name_for_log = self.data['rooms'][new_loc]['name']

                logs.append(f"Moved {item['name']} from {old_loc_name} to {loc_name_for_log}.")

            if change.get('fixInstruction'):
                response = ai_interface.generate_fix(item['name'], item['description'], change['fixInstruction'])
                if 'description' in response:
                    item['description'] = response['description']
                    logs.append(f"{item['name']} auto-fixed by AI.")

        self.describe_room()
        self.save_game()

        if logs:
            return "For continuity and error correction, the game engine has automatically applied the following changes:\n" + "\n".join(logs) + "\nIf these changes contradict recent narrative, please use the Description tool to write updated descriptions treating these changes as established facts."
        return None

    def get_opposite_dir(self, d):
        return {"north":"south","south":"north","east":"west","west":"east","up":"down","down":"up"}.get(d)