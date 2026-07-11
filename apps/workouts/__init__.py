import os
import sys
import uuid

from flask import request, render_template, redirect, url_for, jsonify

from apps.common.factory import create_app_blueprint
from apps.common.config import (
    load_app_json_config,
    load_json_file,
    save_json_file
)


# 1. Dynamically discover folder name of app

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = os.path.basename(CURRENT_DIR)


try:
    config = load_app_json_config(APP_NAME)
    module_pages = config.get("MODULE_PAGES", {})
    default_key = list(module_pages.keys())[0] if module_pages else "items"
except Exception:
    default_key = "items"


# 2. Instantiate blueprint framework

generated_blueprint = create_app_blueprint(
    APP_NAME,
    default_module_key=default_key
)


# ---------------------------------------------------------
# CUSTOM LAYER: TRI-SECTION WORKOUT COLLECTIONS
# ---------------------------------------------------------


@generated_blueprint.route('/collection/workouts', methods=['GET', 'POST'])
def structured_workout_collection_view():

    """
    Handles CRUD parsing, hydration,
    and pillar filtering for workouts.
    """

    cfg = load_app_json_config(APP_NAME)

    col_conf = cfg.get("COLLECTION_PAGES", {}).get("workouts")

    if not col_conf:
        return "Missing workouts collection configuration", 500

    db_file = col_conf["db_file"]

    source_db = (
        cfg.get("MODULE_PAGES", {})
        .get(col_conf["source_module"], {})
        .get("db_file", "exercises.json")
    )


    if request.method == "POST":

        new_workout = {
            "id": str(uuid.uuid4()),
            "name": request.form.get("name", "").strip(),
            "description": request.form.get("description", "").strip(),
            "strength": request.form.getlist("strength_exercises"),
            "power": request.form.getlist("power_exercises"),
            "speed": request.form.getlist("speed_exercises")
        }


        workouts = load_json_file(db_file)

        if not isinstance(workouts, list):
            workouts = []


        workouts.append(new_workout)

        save_json_file(db_file, workouts)


        return redirect(
            url_for(
                f"{APP_NAME}_app.structured_workout_collection_view"
            )
        )


    # -----------------------------------------------------
    # Hydration Engine
    # -----------------------------------------------------

    all_exercises = load_json_file(source_db)

    if not isinstance(all_exercises, list):
        all_exercises = []


    exercise_map = {
        str(ex["id"]): ex
        for ex in all_exercises
        if isinstance(ex, dict) and "id" in ex
    }


    # Filter options by category

    strength_options = [
        ex for ex in all_exercises
        if isinstance(ex, dict)
        and str(ex.get("category", "")).strip().lower() == "strength"
    ]

    power_options = [
        ex for ex in all_exercises
        if isinstance(ex, dict)
        and str(ex.get("category", "")).strip().lower() == "power"
    ]

    speed_options = [
        ex for ex in all_exercises
        if isinstance(ex, dict)
        and str(ex.get("category", "")).strip().lower() == "speed"
    ]


    raw_workouts = load_json_file(db_file)

    if not isinstance(raw_workouts, list):
        raw_workouts = []


    hydrated_workouts = []


    for wk in raw_workouts:

        if not isinstance(wk, dict):
            continue


        sections = {}


        for pillar in ["strength", "power", "speed"]:

            sections[pillar] = []


            for ref_id in wk.get(pillar, []):

                ref_id_str = str(ref_id).strip()


                if ref_id_str in exercise_map:

                    sections[pillar].append(
                        exercise_map[ref_id_str]
                    )

                else:

                    sections[pillar].append({
                        "id": ref_id_str,
                        "title": "Missing Exercise Reference",
                        "category": "Unknown"
                    })


        hydrated_workouts.append({

            "id": wk.get("id"),

            "name": wk.get(
                "name",
                "Unnamed Workout"
            ),

            "description": wk.get(
                "description",
                ""
            ),

            "strength": sections["strength"],
            "power": sections["power"],
            "speed": sections["speed"],

            "raw_strength_ids": wk.get(
                "strength",
                []
            ),

            "raw_power_ids": wk.get(
                "power",
                []
            ),

            "raw_speed_ids": wk.get(
                "speed",
                []
            )
        })


    return render_template(
        "workout_collections.html",
        collection_key="workouts",
        conf=col_conf,
        collections_list=hydrated_workouts,
        strength_options=strength_options,
        power_options=power_options,
        speed_options=speed_options
    )

# ---------------------------------------------------------
# EDIT WORKOUT COLLECTION
# ---------------------------------------------------------


@generated_blueprint.route(
    '/collection/workouts/edit',
    methods=['POST']
)
def edit_structured_workout():

    """
    Modifies structural workout references.
    """

    cfg = load_app_json_config(APP_NAME)

    col_conf = cfg.get(
        "COLLECTION_PAGES",
        {}
    ).get("workouts")


    if not col_conf:
        return "Missing workouts configuration", 500


    db_file = col_conf["db_file"]


    wk_id = request.form.get("collection_id")

    workouts = load_json_file(db_file)


    if isinstance(workouts, list):

        for i, wk in enumerate(workouts):

            if isinstance(wk, dict) and wk.get("id") == wk_id:

                workouts[i] = {

                    "id": wk_id,

                    "name": request.form.get(
                        "name",
                        ""
                    ).strip(),

                    "description": request.form.get(
                        "description",
                        ""
                    ).strip(),

                    "strength": request.form.getlist(
                        "strength_exercises"
                    ),

                    "power": request.form.getlist(
                        "power_exercises"
                    ),

                    "speed": request.form.getlist(
                        "speed_exercises"
                    )
                }

                break


        save_json_file(
            db_file,
            workouts
        )


    return redirect(
        url_for(
            f"{APP_NAME}_app.structured_workout_collection_view"
        )
    )



# ---------------------------------------------------------
# REORDER WORKOUT COLLECTIONS
# ---------------------------------------------------------


@generated_blueprint.route(
    '/reorder-structured-workouts',
    methods=['POST']
)
def reorder_structured_workouts():

    """
    Handles sorting the top-level workout order.
    """


    req_data = request.get_json() or {}


    ordered_ids = [
        str(x)
        for x in req_data.get(
            "ordered_ids",
            []
        )
    ]


    if not ordered_ids:

        return jsonify({
            "status": "error",
            "message": "Missing sequence identifiers."
        }), 400



    cfg = load_app_json_config(APP_NAME)

    col_conf = cfg.get(
        "COLLECTION_PAGES",
        {}
    ).get("workouts")


    if not col_conf:

        return jsonify({
            "status": "error",
            "message": "Missing workouts configuration."
        }), 500


    db_file = col_conf["db_file"]


    collections = load_json_file(db_file)


    if not isinstance(collections, list):

        return jsonify({
            "status": "error",
            "message": "Source database unmapped."
        }), 500



    col_map = {
        str(c["id"]): c
        for c in collections
        if isinstance(c, dict)
        and "id" in c
    }



    reordered_list = []


    for cid in ordered_ids:

        if cid in col_map:

            reordered_list.append(
                col_map[cid]
            )



    # Preserve any missed records

    for c in collections:

        if (
            isinstance(c, dict)
            and "id" in c
            and str(c["id"]) not in ordered_ids
        ):

            reordered_list.append(c)



    save_json_file(
        db_file,
        reordered_list
    )


    return jsonify({
        "status": "success",
        "sequence_length": len(reordered_list)
    })



# ---------------------------------------------------------
# REORDER EXERCISES INSIDE WORKOUT PILLARS
# ---------------------------------------------------------


@generated_blueprint.route(
    '/reorder-workout-exercises',
    methods=['POST']
)
def reorder_workout_exercises():

    """
    Handles sorting exercises inside:
    strength / power / speed sections.
    """


    req_data = request.get_json() or {}


    workout_id = req_data.get(
        "workout_id"
    )

    pillar = req_data.get(
        "pillar"
    )

    ordered_exercise_ids = req_data.get(
        "ordered_exercise_ids"
    )


    if (
        not workout_id
        or not pillar
        or not ordered_exercise_ids
    ):

        return jsonify({
            "status": "error",
            "message": "Missing layout parameters."
        }), 400



    if pillar not in (
        "strength",
        "power",
        "speed"
    ):

        return jsonify({
            "status": "error",
            "message": "Invalid workout pillar."
        }), 400



    cfg = load_app_json_config(APP_NAME)


    col_conf = cfg.get(
        "COLLECTION_PAGES",
        {}
    ).get("workouts")


    if not col_conf:

        return jsonify({
            "status": "error",
            "message": "Missing workouts configuration."
        }), 500



    db_file = col_conf["db_file"]


    collections = load_json_file(
        db_file
    )


    if not isinstance(collections, list):

        return jsonify({
            "status": "error",
            "message": "Source database unmapped."
        }), 500



    updated = False



    for c in collections:

        if (
            isinstance(c, dict)
            and str(c.get("id")) == str(workout_id)
        ):

            c[pillar] = [
                str(x)
                for x in ordered_exercise_ids
            ]

            updated = True
            break



    if not updated:

        return jsonify({
            "status": "error",
            "message": "Workout configuration target missing."
        }), 404



    save_json_file(
        db_file,
        collections
    )


    return jsonify({
        "status": "success",
        "message": f"Updated inner {pillar} sequence layout."
    })



# ---------------------------------------------------------
# EXPORT BLUEPRINT HANDLE
# ---------------------------------------------------------


target_variable_name = f"{APP_NAME}_blueprint"

setattr(
    sys.modules[__name__],
    target_variable_name,
    generated_blueprint
)