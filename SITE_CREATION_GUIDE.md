# Django App Hub - Site Creation Guide

## Overview
This guide teaches you how to create sites for the Django App Hub system. Sites are similar to plugins but have additional features like public access, edit mode toggle, and standalone public URLs.

---

## Site Structure

Every site must be packaged as a **ZIP file** with this structure:

```
your-site.zip/
├── __init__.py       # Required - Main site class
├── logo.png          # Optional - Site logo (also accepts .jpg, .jpeg, .svg, .gif)
├── config.json       # Optional - Default site configuration
└── templates/        # Optional - Site-specific templates (not auto-loaded)
    └── your-site/
        └── index.html
```

> **Tip**: The backend also handles ZIPs where files are inside a single subfolder — it will automatically move them to the root.

---

## Required: `__init__.py`

Every site **must** have an `__init__.py` file containing a class named exactly `Site` (or `Plugin` works too, but `Site` is preferred for clarity).

### Minimal Site Example

```python
class Site:
    name = "My Awesome Site"           # Display name (must be a string)
    slug = "my-awesome-site"       # Unique URL-safe identifier (must be a string)
    version = "1.0"                 # Site version (must be a string)
    description = "Does cool stuff" # Short description (must be a string)

    def render(self, request, config, is_editing=False):
        """
        Required method — returns HTML string to display.
        
        Args:
            request: Django HttpRequest object
            config: Dict loaded from config.json (empty dict if no config.json)
            is_editing: Boolean - True if user is in edit mode, False for public view
        
        Returns:
            str: HTML string
        """
        return "<h1>Hello from my site!</h1>"
```

---

## Site Class Reference

### Required Attributes
All four attributes are required and **must be strings**.

| Attribute     | Type | Description                                                    |
|---------------|------|----------------------------------------------------------------|
| `name`        | str  | Human-readable site name shown in the UI                         |
| `slug`        | str  | URL-safe unique identifier (lowercase, hyphens, no spaces)   |
| `version`     | str  | Version string e.g. `"1.0"`, `"2.1.3"`                        |
| `description` | str  | Short description of what the site does                          |

### Required Methods

| Method   | Signature                                      | Returns    | Description                        |
|----------|--------------------------------------------|------------|------------------------------------|
| `render` | `def render(self, request, config, is_editing=False)`    | str (HTML) | Generates the HTML UI for the site |

### Optional: `config.json`
Include a `config.json` at the root of your ZIP for default configuration:
```json
{
    "theme": "dark",
    "items_per_page": 10
}
```
Loaded automatically and passed to `render()` as the `config` dict.

---

## Key Differences from Plugins

| Feature | Plugin | Site |
|---------|--------|------|
| Class Name | `Plugin` | `Site` (or `Plugin`) |
| Render Signature | `render(self, request, config)` | `render(self, request, config, is_editing=False)` |
| Public Access | No (only logged-in users | Yes (toggleable via `is_public` flag |
| Edit Mode | No | Yes (separate URL `/sites/<slug>/edit/) |
| URLs | `/plugins/<slug>/ | `/sites/<slug>/ (public), `/sites/<slug>/edit/` (edit) |
| `is_editing` Parameter | Not present | Yes, use to show/hide edit controls |

---

## How the Backend Renders Your Site

1. Your `render()` method returns an **HTML string**.
2. Backend stores that string in `app_content`.
3. Django template renders it with **`{{ app_content|safe }}`.
4. Your site HTML is injected into either:
   - **Public view** (`/sites/<slug>/`): standalone page with optional logged-in user bar
   - **Edit view** (`/sites/<slug>/edit/`): page with edit controls, back button, visibility toggle
5. Tailwind CSS is available — use freely.

---

## Using `is_editing` Parameter

Use this to show different UI only in edit mode:
```python
def render(self, request, config, is_editing=False):
    if is_editing:
        edit_controls = """
        <div class="bg-yellow-100 p-4 rounded-lg mb-4">
            <h3 class="font-bold">Edit Mode</h3>
            <p>Only visible to logged-in editors!</p>
        </div>
        """
    else:
        edit_controls = ""
    return edit_controls + "<h1>My Site</h1>"
```

---

## Critical Rules (Same as Plugins)

See Plugin Creation Guide for JS best practices:
- Use unique element IDs
- Use `addEventListener` instead of `onclick` for IIFE
- Avoid f-strings for HTML/JS
- Guard JS after DOM ready

---

## Complete Example: Simple Blog Site

```python
class Site:
    name = "Simple Blog"
    slug = "simple-blog"
    version = "1.0"
    description = "A simple editable blog site"

    def render(self, request, config, is_editing=False):
        posts = config.get('posts', [])
        
        if is_editing:
            edit_ui = """
            <div class="max-w-4xl mx-auto px-4 py-8">
                <div class="bg-blue-50 border border-blue-200 p-6 rounded-xl mb-8">
                    <h2 class="text-2xl font-bold text-blue-900 mb-4">Add New Post</h2>
                    <input id="sb-title" type="text" placeholder="Post title" class="w-full p-3 border rounded-lg mb-3">
                    <textarea id="sb-content" placeholder="Post content" rows="4" class="w-full p-3 border rounded-lg mb-3"></textarea>
                    <button id="sb-add" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">Add Post</button>
                </div>
            </div>
            """
        else:
            edit_ui = ""
        
        posts_html = "".join([
            f"""
            <div class="bg-white p-6 rounded-xl shadow mb-4">
                <h3 class="text-xl font-bold mb-2">{p['title']}</h3>
                <p class="text-gray-600">{p['content']}</p>
            </div>
            """
            for p in posts
        ]) if posts else "<p class='text-gray-500'>No posts yet.</p>"
        
        html = f"""
        <div class="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50">
            <header class="bg-white shadow-sm">
                <div class="max-w-4xl mx-auto px-4 py-12 text-center">
                    <h1 class="text-4xl font-bold text-gray-900">My Blog</h1>
                    <p class="text-gray-600 mt-2">Welcome to my simple blog</p>
                </div>
            </header>
            {edit_ui}
            <main class="max-w-4xl mx-auto px-4 py-8">
                <div id="sb-posts">{posts_html}</div>
            </main>
        </div>
        <script>
        (function() {{
            function init() {{
                var addBtn = document.getElementById('sb-add');
                if (addBtn) {{
                    addBtn.addEventListener('click', function() {{
                        var title = document.getElementById('sb-title').value.trim();
                        var content = document.getElementById('sb-content').value.trim();
                        if (!title || !content) return;
                        fetch('/simple-blog/api/config/', {method: 'GET'})
                            .then(r => r.json())
                            .then(config => {{
                                var posts = config.posts || [];
                                posts.push({{title, content, id: Date.now()}});
                                return fetch('/simple-blog/api/config/set/', {{
                                    method: 'POST',
                                    headers: {{'Content-Type': 'application/json'}},
                                    body: JSON.stringify({{posts}})
                                }});
                            }})
                            .then(() => location.reload());
                    }});
                }}
            }}
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', init);
            }} else {{
                init();
            }}
        }})();
        </script>
        """
        return html
```

---

## How to Package Your Site

Same as plugins:
1. Create folder for site
2. Place `__init__.py` (and optional files) inside
3. Select files **inside** folder → compress to `.zip`

---

## How to Upload Your Site

1. Log in to Django App Hub
2. Go to Dashboard
3. Click **"Upload Site"**
4. Fill form:
   - **Site Name**
   - **Description**
   - **Logo** (optional)
   - **Site Zip File**
5. Click **"Upload Site"**

---

## Site URLs

After upload, your site has two URLs:
- **Public View**: `http://your-domain.com/sites/<your-site-slug>/
- **Edit View**: `http://your-domain.com/sites/<your-site-slug>/edit/` (requires login)

---

## Visibility Toggle

Sites default to **public**. Toggle visibility in edit mode or dashboard.

---

## Generic Config API

Same API endpoints as plugins:
- `GET `
- POST `set`
- POST `update`

---

## Tips

- Use Tailwind CSS freely
- Use `is_editing` to differentiate edit/public views
- Save data via API endpoints for persistence across sessions
- Prefix all IDs to avoid conflicts
