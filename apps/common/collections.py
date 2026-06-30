import uuid
from flask import request, render_template, redirect, url_for, jsonify
from apps.common.config import load_json_file, save_json_file

def handle_generic_collection(collection_key, col_conf, source_module_conf, endpoint_redirect):
    db_file = col_conf["db_file"]

    if request.method == 'POST':
        chosen_ids = request.form.getlist('items')
        new_collection = {
            "id": str(uuid.uuid4()),
            "name": request.form.get('name'),
            "description": request.form.get('description'),
            "drills": chosen_ids,
            "is_video": request.form.get('is_video') == 'true'
        }
        collections = load_json_file(db_file)
        if not isinstance(collections, list):
            collections = []
        collections.append(new_collection)
        save_json_file(db_file, collections)
        return redirect(url_for(endpoint_redirect, collection_key=collection_key))

    all_source_items = load_json_file(source_module_conf["db_file"]) if source_module_conf else []
    raw_collections = load_json_file(db_file)
    
    if not isinstance(raw_collections, list):
        raw_collections = []
        
    item_map = {str(item['id']): item for item in all_source_items if isinstance(item, dict) and 'id' in item}
    hydrated_collections = []

    for c in raw_collections:
        if not isinstance(c, dict): 
            continue
        if "id" not in c:
            c["id"] = str(uuid.uuid4())
            save_json_file(db_file, raw_collections)
            
        hydrated_items = []
        saved_ids = c.get("drills", c.get("items", []))
        inner_ids = []
        
        for ref_id in saved_ids:
            ref_id_str = str(ref_id).strip()
            inner_ids.append(ref_id_str)
            if ref_id_str in item_map:
                hydrated_items.append(item_map[ref_id_str])
            else:
                hydrated_items.append({
                    "id": ref_id_str, 
                    "title": "Missing Link Reference", 
                    "url": "#",
                    "description": "Item was dropped from source logs.", 
                    "category": "Missing", 
                    "subcategory": "None"
                })
                
        hydrated_collections.append({
            "id": c.get("id"), 
            "name": c.get("name", "Unnamed Group"), 
            "description": c.get("description", ""),
            "items": hydrated_items, 
            "inner_ids": inner_ids, 
            "is_video": c.get("is_video", False)
        })

    return render_template(
        'collection.html',
        collection_key=collection_key,
        conf=col_conf,
        collections_list=hydrated_collections,
        source_items=all_source_items,
        str=str  # Passed down explicitly for structural inline string-casting match tests
    )

def handle_edit_collection(collection_key, col_conf):
    col_id = request.form.get('collection_id')
    collections = load_json_file(col_conf["db_file"])
    if not isinstance(collections, list):
        return
        
    for i, c in enumerate(collections):
        if isinstance(c, dict) and c.get('id') == col_id:
            collections[i] = {
                "id": col_id,
                "name": request.form.get('name'),
                "description": request.form.get('description'),
                "drills": request.form.getlist('items'),
                "is_video": request.form.get('is_video') == 'true'
            }
            break
    save_json_file(col_conf["db_file"], collections)

def handle_delete_collection(collection_key, col_conf):
    col_id = request.form.get('collection_id')
    collections = load_json_file(col_conf["db_file"])
    if isinstance(collections, list):
        collections = [c for c in collections if isinstance(c, dict) and c.get('id') != col_id]
        save_json_file(col_conf["db_file"], collections)

def handle_reorder_collection(collection_key, col_conf):
    """
    Asynchronously reads re-ordered IDs array maps from UI fetch cycles, sorts
    persisted database index arrays to match tracking sequences, and writes to flat-file storage.
    """
    req_data = request.get_json()
    if not req_data or "ordered_ids" not in req_data:
        return jsonify({"status": "error", "message": "Missing sequence identifiers map payload."}), 400
        
    ordered_ids = [str(x) for x in req_data["ordered_ids"]]
    collections = load_json_file(col_conf["db_file"])
    
    if not isinstance(collections, list):
        return jsonify({"status": "error", "message": "Target source repository data is unmapped."}), 500

    col_map = {str(c["id"]): c for c in collections if isinstance(c, dict) and "id" in c}
    
    reordered_list = []
    for cid in ordered_ids:
        if cid in col_map:
            reordered_list.append(col_map[cid])
            
    # Append any remaining collections that weren't captured in the frontend array map
    for c in collections:
        if isinstance(c, dict) and "id" in c and str(c["id"]) not in ordered_ids:
            reordered_list.append(c)

    save_json_file(col_conf["db_file"], reordered_list)
    return jsonify({"status": "success", "sequence_length": len(reordered_list)})