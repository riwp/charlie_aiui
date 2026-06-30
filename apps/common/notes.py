from flask import request, render_template, redirect, url_for
from apps.common.config import load_json_file, save_json_file

def handle_generic_note(pagetype, note_conf, endpoint_redirect):
    filename = note_conf["db_file"]

    if request.method == 'POST':
        data = load_json_file(filename)
        if isinstance(data, list): data = {}
        data['title'] = note_conf["title"]
        data['description'] = note_conf["description"]
        data['text'] = request.form.get('page_text', '')
        save_json_file(filename, data)
        return redirect(url_for(endpoint_redirect, pagetype=pagetype))

    data = load_json_file(filename)
    text_content = data.get('text', '') if isinstance(data, dict) else ""

    return render_template(
        'note.html',
        title=note_conf["title"],
        description=note_conf["description"],
        text_content=text_content,
        pagetype=pagetype,
        theme_color=note_conf.get("accent_color", "success")
    )