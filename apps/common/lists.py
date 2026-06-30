import uuid
from flask import request, render_template, redirect, url_for
from apps.common.config import load_json_file, save_json_file

def handle_generic_list(module_key, module_conf, endpoint_redirect):
    db_file = module_conf["db_file"]
    cat_file = module_conf["categories_file"]

    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        subcategory = request.form.get('subcategory', '').strip()
        raw_url = request.form.get('url', '').strip()
        is_video = request.form.get('is_video') == 'true'

        if is_video and ("youtube.com" in raw_url or "youtu.be" in raw_url):
            if "watch?v=" in raw_url:
                video_id = raw_url.split("watch?v=")[1].split("&")[0]
                raw_url = f"https://www.youtube.com/embed/{video_id}"
            elif "youtu.be/" in raw_url:
                video_id = raw_url.split("youtu.be/")[1].split("?")[0]
                raw_url = f"https://www.youtube.com/embed/{video_id}"

        new_item = {
            "id": str(uuid.uuid4()),
            "category": category,
            "subcategory": subcategory,
            "title": request.form.get('title', '').strip(),
            "description": request.form.get('description', '').strip(),
            "url": raw_url,
            "is_video": is_video
        }
        
        items = load_json_file(db_file)
        items.append(new_item)
        save_json_file(db_file, items)
        
        cats = load_json_file(cat_file)
        if not any(c.get('category', '').lower() == category.lower() and c.get('subcategory', '').lower() == subcategory.lower() for c in cats):
            if category and subcategory:
                cats.append({"category": category, "subcategory": subcategory})
                save_json_file(cat_file, cats)
                    
        return redirect(url_for(endpoint_redirect, module_key=module_key))

    items = load_json_file(db_file)
    for item in items:
        if isinstance(item, dict) and "id" not in item:
            item["id"] = str(uuid.uuid4())
            save_json_file(db_file, items)

    cats_data = load_json_file(cat_file)
    unique_cats = sorted(list(set(c['category'] for c in cats_data if 'category' in c)))
    unique_subcats = sorted(list(set(c['subcategory'] for c in cats_data if 'subcategory' in c)))

    return render_template(
        'list.html',
        module_key=module_key,
        conf=module_conf,
        items_list=items,
        categories=unique_cats,
        subcategories=unique_subcats
    )

def handle_delete_item(module_key, module_conf):
    item_id = request.form.get('item_id')
    items = load_json_file(module_conf["db_file"])
    cat_file = module_conf["categories_file"]

    target_cat, target_sub = None, None
    for i in items:
        if isinstance(i, dict) and i.get('id') == item_id:
            target_cat = i.get('category', '').strip()
            target_sub = i.get('subcategory', '').strip()
            break

    items = [i for i in items if isinstance(i, dict) and i.get('id') != item_id]
    save_json_file(module_conf["db_file"], items)

    if target_cat and target_sub:
        still_used = any(i.get('category', '').lower() == target_cat.lower() and i.get('subcategory', '').lower() == target_sub.lower() for i in items)
        if not still_used:
            cats = load_json_file(cat_file)
            cats = [c for c in cats if not (c.get('category', '').lower() == target_cat.lower() and c.get('subcategory', '').lower() == target_sub.lower())]
            save_json_file(cat_file, cats)

def handle_edit_item(module_key, module_conf):
    item_id = request.form.get('item_id')
    items = load_json_file(module_conf["db_file"])
    cat_file = module_conf["categories_file"]
    
    category = request.form.get('category', '').strip()
    subcategory = request.form.get('subcategory', '').strip()
    raw_url = request.form.get('url', '').strip()
    is_video = request.form.get('is_video') == 'true'

    if is_video and ("youtube.com" in raw_url or "youtu.be" in raw_url):
        if "watch?v=" in raw_url:
            video_id = raw_url.split("watch?v=")[1].split("&")[0]
            raw_url = f"https://www.youtube.com/embed/{video_id}"
        elif "youtu.be/" in raw_url:
            video_id = raw_url.split("youtu.be/")[1].split("?")[0]
            raw_url = f"https://www.youtube.com/embed/{video_id}"
    
    old_cat, old_sub = None, None
    for item in items:
        if isinstance(item, dict) and item.get('id') == item_id:
            old_cat = item.get('category', '').strip()
            old_sub = item.get('subcategory', '').strip()
            break

    for i, item in enumerate(items):
        if isinstance(item, dict) and item.get('id') == item_id:
            items[i] = {
                "id": item_id,
                "title": request.form.get('title', '').strip(),
                "category": category,
                "subcategory": subcategory,
                "url": raw_url,
                "description": request.form.get('description', '').strip(),
                "is_video": is_video
            }
            break
    save_json_file(module_conf["db_file"], items)
    
    cats = load_json_file(cat_file)
    if old_cat and old_sub:
        still_used = any(i.get('category', '').lower() == old_cat.lower() and i.get('subcategory', '').lower() == old_sub.lower() for i in items)
        if not still_used:
            cats = [c for c in cats if not (c.get('category', '').lower() == old_cat.lower() and c.get('subcategory', '').lower() == old_sub.lower())]

    if category and subcategory:
        if not any(c.get('category', '').lower() == category.lower() and c.get('subcategory', '').lower() == subcategory.lower() for c in cats):
            cats.append({"category": category, "subcategory": subcategory})
    save_json_file(cat_file, cats)