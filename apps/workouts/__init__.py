import os
import sys
import uuid
from flask import request, render_template, redirect, url_for, jsonify
from apps.common.factory import create_app_blueprint
from apps.common.config import load_app_json_config, load_json_file, save_json_file

# 1. Dynamically discover folder name of app
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = os.path.basename(CURRENT_DIR)

try:
    config = load_app_json_config(APP_NAME)
    module_pages = config.get("MODULE_PAGES", {})
    default_key = list(module_pages.keys())[0] if module_pages else 'items'
except Exception:
    default_key = 'items'

# 2. Instantiate the blueprint framework
generated_blueprint = create_app_blueprint(APP_NAME, default_module_key=default_key)


# --- CUSTOM LAYER: TRI-SECTION WORKOUT COLLECTIONS ---

@generated_blueprint.route('/collection/workouts', methods=['GET', 'POST'])
def structured_workout_collection_view():
    """Handles CRUD parsing, hydration, and isolated pillar filtering for target workouts."""
    cfg = load_app_json_config(APP_NAME)
    col_conf = cfg.get("COLLECTION_PAGES", {}).get("workouts")
    
    db_file = col_conf["db_file"]
    source_db = cfg.get("MODULE_PAGES", {}).get(col_conf["source_module"], {}).get("db_file", "exercises.json")
    
    if request.method == 'POST':
        new_workout = {
            "id": str(uuid.uuid4()),
            "name": request.form.get('name', '').strip(),
            "description": request.form.get('description', '').strip(),
            "strength": request.form.getlist('strength_exercises'),
            "power": request.form.getlist('power_exercises'),
            "speed": request.form.getlist('speed_exercises')
        }
        workouts = load_json_file(db_file)
        if not isinstance(workouts, list): 
            workouts = []
        workouts.append(new_workout)
        save_json_file(db_file, workouts)
        return redirect(url_for(f"{APP_NAME}_app.structured_workout_collection_view"))

    # Hydration Engine Matrix
    all_exercises = load_json_file(source_db)
    if not isinstance(all_exercises, list):
        all_exercises = []

    exercise_map = {str(ex['id']): ex for ex in all_exercises if isinstance(ex, dict) and 'id' in ex}
    
    # FILTER OPTIONS BY RELEVANT CATEGORY (CASE-INSENSITIVE)
# FILTER OPTIONS BY RELEVANT CATEGORY (CASE-INSENSITIVE)
    strength_options = [ex for ex in all_exercises if isinstance(ex, dict) and str(ex.get('category', '')).strip().lower() == 'strength']
    power_options = [ex for ex in all_exercises if isinstance(ex, dict) and str(ex.get('category', '')).strip().lower() == 'power']
    speed_options = [ex for ex in all_exercises if isinstance(ex, dict) and str(ex.get('category', '')).strip().lower() == 'speed']

    raw_workouts = load_json_file(db_file)
    if not isinstance(raw_workouts, list): 
        raw_workouts = []
    
    hydrated_workouts = []
    for wk in raw_workouts:
        if not isinstance(wk, dict): 
            continue
        
        sections = {}
        for pillar in ['strength', 'power', 'speed']:
            sections[pillar] = []
            for ref_id in wk.get(pillar, []):
                ref_id_str = str(ref_id).strip()
                if ref_id_str in exercise_map:
                    sections[pillar].append(exercise_map[ref_id_str])
                else:
                    sections[pillar].append({
                        "id": ref_id_str, 
                        "title": "Missing Exercise Reference", 
                        "category": "Unknown"
                    })

        hydrated_workouts.append({
            "id": wk.get("id"),
            "name": wk.get("name", "Unnamed Workout"),
            "description": wk.get("description", ""),
            "strength": sections['strength'],
            "power": sections['power'],
            "speed": sections['speed'],
            "raw_strength_ids": wk.get("strength", []),
            "raw_power_ids": wk.get("power", []),
            "raw_speed_ids": wk.get("speed", [])
        })

    return render_template(
        'workout_collections.html',
        collection_key="workouts",
        conf=col_conf,
        collections_list=hydrated_workouts,
        strength_options=strength_options,
        power_options=power_options,
        speed_options=speed_options
    )

@generated_blueprint.route('/collection/workouts/edit', methods=['POST'])
def edit_structured_workout():
    """Modifies structural item references mapped within structural pillar indices."""
    cfg = load_app_json_config(APP_NAME)
    db_file = cfg.get("COLLECTION_PAGES", {}).get("workouts")["db_file"]
    
    wk_id = request.form.get('collection_id')
    workouts = load_json_file(db_file)
    
    if isinstance(workouts, list):
        for i, wk in enumerate(workouts):
            if isinstance(wk, dict) and wk.get('id') == wk_id:
                workouts[i] = {
                    "id": wk_id,
                    "name": request.form.get('name', '').strip(),
                    "description": request.form.get('description', '').strip(),
                    "strength": request.form.getlist('strength_exercises'),
                    "power": request.form.getlist('power_exercises'),
                    "speed": request.form.getlist('speed_exercises')
                }
                break
        save_json_file(db_file, workouts)
    return redirect(url_for(f"{APP_NAME}_app.structured_workout_collection_view"))


# 4. Inject runtime system expected routing module handle variables
target_variable_name = f"{APP_NAME}_blueprint"
setattr(sys.modules[__name__], target_variable_name, generated_blueprint)