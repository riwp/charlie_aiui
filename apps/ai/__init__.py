import os
import re
import uuid
import time
import glob
import subprocess
from flask import Blueprint, render_template, request, jsonify, redirect, url_for

# --- MASTER ROUTING CONFIGURATION ---
#URL_PREFIX = "ai"  # Change this single variable to change paths, config loads, and routing keys

# --- MASTER ROUTING CONFIGURATION ---
# Dynamically extracts the current folder name (e.g., "ai") to manage paths, config loads, and routes
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
URL_PREFIX = os.path.basename(CURRENT_DIR)

# --- Core Infrastructure Integrations ---
from apps.common.config import load_app_json_config
from apps.common.lists import handle_generic_list

# --- Custom Engine Heavy Workers ---
from apps.common import gemini_bot, fetch_html

# Instantiate blueprint with absolute workspace prefix mapping safely wrapped with a leading slash
ai_blueprint = Blueprint('ai_blueprint', __name__, url_prefix=f"/{URL_PREFIX}")

# --- CONFIGURATION CONSTANTS & DIRECTORIES ---
FILE_CATEGORIES = {
    "ai", "cooking", "economy", "health", "investing", "mma_drill", 
    "mma_general", "politics", "science", "tech", "other"
}

TEMP_DIRECTORY = "TEMP_DIRECTORY"
PROMPT_PATH = "prompts"

# FIX: Keep paths completely localized directly inside apps/ folder structure dynamically
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_OUTPUTS = os.path.join(CURRENT_DIR, "saved_outputs")

# Initialize runtime folder matrix architectures dynamically
for path in [TEMP_DIRECTORY, PROMPT_PATH, SAVED_OUTPUTS]:
    os.makedirs(path, exist_ok=True)

for category in FILE_CATEGORIES:
    os.makedirs(os.path.join(SAVED_OUTPUTS, category), exist_ok=True)


# --- CONTEXT ISOLATION PROCESSOR ---
@ai_blueprint.context_processor
def inject_ai_context():
    cfg = load_app_json_config(URL_PREFIX)
    return dict(nav_links=cfg.get("NAV_LINKS", []), app_title=cfg.get("APP_TITLE"))


# --- INTERNAL PIPELINE UTILITIES ---
def determine_fabric_type(text):
    if not text: return 'text'
    url_match = re.search(r'https?://[^\s]+', text)
    if url_match:
        url = url_match.group(0).lower()
        if 'youtube.com' in url or 'youtu.be' in url: return 'video'
        return 'web'
    return 'text'

def extract_url(text):
    match = re.search(r'https?://[^\s]+', text)
    return match.group(0) if match else None

def download_youtube_transcript(url):
    temp_id = str(uuid.uuid4())
    output_pattern = os.path.join(TEMP_DIRECTORY, f"{temp_id}.%(ext)s")
    try:
        subprocess.run([
            "yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs",
            "--sub-lang", "en", "--convert-subs", "srt", "-o", output_pattern, url
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for srt_file in glob.glob(os.path.join(TEMP_DIRECTORY, f"{temp_id}*.srt")):
            with open(srt_file, "r", encoding="utf-8") as f:
                content = f.read()
            text = re.sub(r"\d+\n|\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}", "", content)
            text = re.sub(r"\s{2,}", " ", text).strip()
            os.remove(srt_file)
            return text
        return None
    except Exception:
        return None

def get_prompt_text_md(filename):
    target_path = os.path.join(PROMPT_PATH, filename)
    if os.path.exists(target_path):
        with open(target_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "You are an advanced, context-aware utility assistant."


# --- CORE STRUCTURAL ROUTING WORKSPACE ---
@ai_blueprint.route('/')
def home():
    return redirect(url_for('ai_blueprint.generic_list_view', module_key=f'{URL_PREFIX}_summarization'))

# FIX: Map nested file lists to folder items before parsing payload downstream arrays
@ai_blueprint.route(f'/page/{URL_PREFIX}_savedfiles')
def ai_savedfiles():
    categories = sorted(list(FILE_CATEGORIES))
    
    folder_manifest = {}
    for category in categories:
        path = os.path.join(SAVED_OUTPUTS, category)
        if os.path.exists(path):
            folder_manifest[category] = sorted(os.listdir(path))
        else:
            folder_manifest[category] = []
            
    return render_template(f"{URL_PREFIX}_savedfiles.html", categories=categories, folder_manifest=folder_manifest)

@ai_blueprint.route('/explorer')
def ai_explorer():
    category = request.args.get('category', '').strip().lower()
    path = os.path.join(SAVED_OUTPUTS, category)
    files = sorted(os.listdir(path)) if os.path.exists(path) else []
    return render_template(f"{URL_PREFIX}_explorer.html", category=category, files=files)

@ai_blueprint.route('/page/<module_key>', methods=['GET', 'POST'])
def generic_list_view(module_key):
    if module_key == f"{URL_PREFIX}_savedfiles": 
        return redirect(url_for('ai_blueprint.ai_savedfiles'))
        
    if module_key == f"{URL_PREFIX}_explorer": 
        return redirect(url_for('ai_blueprint.ai_explorer', category=request.args.get('category', '')))
    
    cfg = load_app_json_config(URL_PREFIX)
    conf = cfg.get("MODULE_PAGES", {}).get(module_key, {})
    
    patterns = []
    if os.path.exists(PROMPT_PATH):
        patterns = [os.path.splitext(f)[0] for f in os.listdir(PROMPT_PATH) if f.endswith(".md")]
    if not patterns:
        patterns = ["summarize", "extract_wisdom", "write_essay", "analyze_code"]
        
    categories = sorted(list(FILE_CATEGORIES))
    
    if module_key == f"{URL_PREFIX}_summarization":
        return render_template(f"{URL_PREFIX}_summarization.html", conf=conf, patterns=patterns, default_pattern="summarize", categories=categories)
        
    return handle_generic_list(module_key, conf, 'ai_blueprint.generic_list_view')


# --- HIGH-PERFORMANCE SERVICE HOOK ENDPOINTS ---
@ai_blueprint.route('/get_file_content', methods=['POST'])
def get_file_content():
    data = request.get_json() or {}
    category = data.get("category", "").strip().lower()
    file_path = os.path.join(SAVED_OUTPUTS, category, data.get("filename", ""))
    
    if ".." in file_path or not os.path.exists(file_path):
        return jsonify({"content": "Empty trace pipeline payload index."}), 400
        
    with open(file_path, "r", encoding="utf-8") as f:
        return jsonify({"content": f.read()})

@ai_blueprint.route("/stream_insights", methods=["POST"])
def stream_insights_endpoint():
    data = request.get_json() or {}
    user_prompt = data.get("prompt_text", "").strip()
    pattern_selection = data.get("pattern_select", "summarize")
    
    system_instruction = get_prompt_text_md(f"{pattern_selection}.md")
    f_type = determine_fabric_type(user_prompt)
    url = extract_url(user_prompt)
    content = user_prompt
    
    if url:
        if f_type == 'video':
            content = download_youtube_transcript(url) or user_prompt
        elif f_type == 'web':
            content = fetch_html(url) or user_prompt
    
    try:
        output = gemini_bot.generate_insight(prompt=content, system_instruction=system_instruction)
    except Exception as e:
        output = f"Inference Node Pipeline Tracking Interruption: {str(e)}"
        
    return jsonify({"output": output})

@ai_blueprint.route("/save_output", methods=['POST'])
def save_output_endpoint():
    data = request.get_json() or {}
    filename = data.get('filename', '').strip()
    content = data.get('content', '').strip()
    category = data.get('category', 'other').lower().strip()
    
    if category not in FILE_CATEGORIES:
        category = "other"
    if not filename:
        filename = "unnamed_insight"
        
    safe_filename = re.sub(r'[\\/:*?"<>| ]', '_', f"{category}_{filename}")
    unique_filename = f"{safe_filename}_{time.strftime('%Y%m%d-%H%M%S')}.txt"
    
    save_dir = os.path.join(SAVED_OUTPUTS, category)
    os.makedirs(save_dir, exist_ok=True)
    
    try:
        with open(os.path.join(save_dir, unique_filename), 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'message': f'File saved successfully inside JSON outputs: {unique_filename}'})
    except Exception as e:
        return jsonify({'message': f'File IO Stream Error: {str(e)}'}), 500