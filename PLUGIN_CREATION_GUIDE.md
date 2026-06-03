# Django Plugin Manager - Plugin Creation Guide

## Overview
This guide teaches you how to create plugins for the Django Plugin Manager system. It is written based on the **actual backend source code** so everything here reflects how the system truly works.

---

## Plugin Structure

Every plugin must be packaged as a **ZIP file** with the following structure:

```
your-plugin.zip/
├── __init__.py       # Required - Main plugin class
├── logo.png          # Optional - Plugin logo (also accepts .jpg, .jpeg, .svg, .gif)
├── config.json       # Optional - Default plugin configuration
└── templates/        # Optional - Plugin-specific templates (not auto-loaded)
    └── your-plugin/
        └── index.html
```

> **Tip:** The backend also handles ZIPs where files are inside a single subfolder — it will automatically move them to the root. So both structures below work:
> ```
> plugin.zip/__init__.py          ✅ correct
> plugin.zip/my-plugin/__init__.py  ✅ also works (auto-fixed)
> ```

---

## Required: `__init__.py`

Every plugin **must** have an `__init__.py` file containing a class named exactly `Plugin`.

### Minimal Plugin Example

```python
class Plugin:
    name = "My Awesome Plugin"      # Display name (must be a string)
    slug = "my-awesome-plugin"      # Unique URL-safe identifier (must be a string)
    version = "1.0"                 # Plugin version (must be a string)
    description = "Does cool stuff" # Short description (must be a string)

    def render(self, request, config):
        """
        Required method — returns HTML string to display in the plugin page.

        Args:
            request: Django HttpRequest object
            config:  Dict loaded from config.json (empty dict if no config.json)

        Returns:
            str: HTML string
        """
        return "<h1>Hello from my plugin!</h1>"
```

---

## Plugin Class Reference

### Required Attributes
All four attributes are required and **must be strings**. The backend validates each one.

| Attribute     | Type | Description                                                    |
|---------------|------|----------------------------------------------------------------|
| `name`        | str  | Human-readable plugin name shown in the UI                     |
| `slug`        | str  | URL-safe unique identifier (lowercase, hyphens, no spaces)     |
| `version`     | str  | Version string e.g. `"1.0"`, `"2.1.3"`                        |
| `description` | str  | Short description of what the plugin does                      |

> **Note:** The `slug` attribute in your Plugin class is not used for routing. The backend derives the URL slug from the **Plugin Name** you enter in the upload form using Django's `slugify()`. Make sure your class `slug` matches what `slugify(name)` would produce to avoid confusion.

### Required Methods

| Method   | Signature                              | Returns    | Description                        |
|----------|----------------------------------------|------------|------------------------------------|
| `render` | `def render(self, request, config)`    | str (HTML) | Generates the HTML UI for the plugin |

### Optional: `config.json`
Include a `config.json` at the root of your ZIP for default configuration:
```json
{
    "theme": "dark",
    "items_per_page": 10
}
```
This is loaded automatically and passed to `render()` as the `config` dict. If the file is missing, `config` will be an empty dict `{}`.

---

## How the Backend Renders Your Plugin

Understanding this is key to writing plugins that actually work.

1. Your `render()` method returns an **HTML string**.
2. The backend stores that string in a template context variable called `plugin_content`.
3. The Django template renders it with **`{{ plugin_content|safe }}`** — meaning your raw HTML and `<script>` tags are injected directly into the page.
4. Your plugin HTML is inserted **inside** the site's base template, which already loads **Tailwind CSS**.

### What this means for you:
- ✅ You can use Tailwind CSS classes — they're already available.
- ✅ You can include `<script>` tags — they will execute.
- ⚠️ Your HTML shares the page with the base template's elements. **Use unique IDs** to avoid conflicts (prefix everything, e.g. `myplugin-input` not `input`).
- ⚠️ Do **not** use `onclick="myFunc()"` attributes if your function is declared inside an IIFE or module scope — the browser won't find it. Either declare functions on `window` explicitly, or use `addEventListener` instead.

---

## Critical Rules for Writing Plugin JavaScript

### ❌ Problem: `onclick` with scoped functions
```html
<!-- This BREAKS if myFunc is inside an IIFE -->
<button onclick="myFunc()">Click</button>
<script>
(function() {
    function myFunc() { ... }  // scoped — onclick can't reach it!
})();
</script>
```

### ✅ Fix 1: Use `addEventListener` with event delegation (recommended)
```html
<button id="myplugin-btn">Click</button>
<script>
(function() {
    function myFunc() { ... }
    document.getElementById('myplugin-btn').addEventListener('click', myFunc);
})();
</script>
```

### ✅ Fix 2: Attach functions to `window`
```html
<button onclick="myFunc()">Click</button>
<script>
(function() {
    window.myFunc = function() { ... };
})();
</script>
```

### ❌ Problem: ID conflicts with the host page
```html
<!-- Generic IDs may already exist in the base template -->
<input id="input"> 
<ul id="list">
```

### ✅ Fix: Prefix all element IDs
```html
<!-- Use a unique prefix for your plugin -->
<input id="myplugin-input">
<ul id="myplugin-list">
```

### ❌ Problem: Script runs before DOM is ready
If your `<script>` block is placed before your HTML elements, `getElementById` will return `null`.

### ✅ Fix: Always place your `<script>` after your HTML, or guard with `DOMContentLoaded`
```javascript
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init(); // DOM already ready
}
```

### ❌ Problem: Python f-strings break JavaScript
```python
# This BREAKS — Python tries to interpolate {todos} and {index}
html = f"""
<script>
    let todos = [];
    todos.forEach((todo, index) => {{ ... }});
</script>
"""
```

### ✅ Fix: Don't use f-strings for HTML/JS. Use plain triple-quoted strings.
```python
# No f prefix — Python won't touch the braces
html = """
<script>
    let todos = [];
    todos.forEach(function(todo, index) { ... });
</script>
"""
```
If you must use an f-string, escape every brace: `{` → `{{`, `}` → `}}`.

---

## Complete Example: Todo Plugin with Timer

A working plugin that correctly follows all the rules above:

```python
class Plugin:
    name = "Todo App with Timer"
    slug = "todo-timer-plugin"
    version = "1.0"
    description = "A todo list with a countdown timer per task"

    def render(self, request, config):
        html = """
        <div id="ttp-root" style="max-width:700px;margin:0 auto;padding:16px;">
            <h2 style="font-size:1.6rem;font-weight:700;margin-bottom:16px;">Todo + Timer</h2>

            <div style="background:#fff;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.1);padding:16px;margin-bottom:20px;">
                <input id="ttp-input" type="text" placeholder="Task name..."
                    style="width:100%;box-sizing:border-box;padding:8px 12px;border:1px solid #d1d5db;border-radius:6px;font-size:1rem;margin-bottom:10px;" />
                <div style="display:flex;align-items:center;gap:10px;">
                    <label style="font-size:.875rem;color:#6b7280;">Minutes:</label>
                    <input id="ttp-mins" type="number" value="25" min="1"
                        style="width:70px;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:1rem;" />
                    <button id="ttp-addbtn"
                        style="margin-left:auto;background:#2563eb;color:#fff;border:none;padding:8px 18px;border-radius:6px;font-size:1rem;cursor:pointer;">
                        + Add Task
                    </button>
                </div>
            </div>

            <ul id="ttp-list" style="list-style:none;padding:0;margin:0;"></ul>
            <div id="ttp-empty" style="text-align:center;padding:40px;color:#9ca3af;">No tasks yet.</div>
        </div>

        <script>
        (function() {
            var todos = [];
            var timers = {};

            try { todos = JSON.parse(localStorage.getItem('ttp_v1') || '[]'); } catch(e) {}
            todos.forEach(function(t){ t.running = false; });

            function save() {
                localStorage.setItem('ttp_v1', JSON.stringify(
                    todos.map(function(t){
                        return {id:t.id,text:t.text,done:t.done,total:t.total,left:t.left,running:false};
                    })
                ));
            }

            function fmt(s) {
                return (Math.floor(s/60)<10?'0':'')+Math.floor(s/60)+':'+(s%60<10?'0':'')+(s%60);
            }

            function find(id) {
                for(var i=0;i<todos.length;i++) if(todos[i].id===id) return todos[i];
            }

            function stats() {
                var empty = document.getElementById('ttp-empty');
                if(empty) empty.style.display = todos.length ? 'none' : 'block';
            }

            function renderCard(id) {
                var t = find(id);
                var el = document.getElementById('ttp-card-'+id);
                if(!t || !el) return;
                var pct = t.total > 0 ? t.left/t.total : 0;
                var color = t.done ? '#22c55e' : pct > 0.5 ? '#3b82f6' : pct > 0.2 ? '#f59e0b' : '#ef4444';
                var r = 20, circ = (2*Math.PI*r).toFixed(1);
                var offset = (circ * (1-pct)).toFixed(1);
                el.innerHTML =
                    '<div style="display:flex;align-items:center;gap:12px;background:#fff;border-radius:10px;' +
                    'box-shadow:0 1px 3px rgba(0,0,0,.1);padding:14px;opacity:'+(t.done?.6:1)+'">' +
                    '<div style="position:relative;width:48px;height:48px;flex-shrink:0;">' +
                    '<svg width="48" height="48" viewBox="0 0 48 48">' +
                    '<circle cx="24" cy="24" r="'+r+'" fill="none" stroke="#e5e7eb" stroke-width="4"/>' +
                    '<circle cx="24" cy="24" r="'+r+'" fill="none" stroke="'+color+'" stroke-width="4"' +
                    ' stroke-dasharray="'+circ+'" stroke-dashoffset="'+offset+'"' +
                    ' stroke-linecap="round" transform="rotate(-90 24 24)"/></svg>' +
                    '<span style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;' +
                    'font-size:9px;font-weight:700;color:#374151;">'+fmt(t.left)+'</span></div>' +
                    '<div style="flex:1;min-width:0;">' +
                    '<p style="margin:0;font-weight:600;color:'+(t.done?'#9ca3af':'#111827')+';' +
                    'text-decoration:'+(t.done?'line-through':'none')+';overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+
                    t.text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')+'</p>' +
                    '<p style="margin:2px 0 0;font-size:.75rem;color:#9ca3af;">'+Math.round(t.total/60)+' min</p></div>' +
                    '<div style="display:flex;gap:5px;">' +
                    '<button data-id="'+id+'" data-a="start" style="width:30px;height:30px;border-radius:50%;' +
                    'background:#dbeafe;color:#2563eb;border:none;cursor:pointer;opacity:'+((!t.running&&!t.done&&t.left>0)?1:.4)+'">&#9654;</button>' +
                    '<button data-id="'+id+'" data-a="pause" style="width:30px;height:30px;border-radius:50%;' +
                    'background:#fef9c3;color:#b45309;border:none;cursor:pointer;opacity:'+(t.running?1:.4)+'">&#9646;&#9646;</button>' +
                    '<button data-id="'+id+'" data-a="reset" style="width:30px;height:30px;border-radius:50%;' +
                    'background:#f3f4f6;color:#374151;border:none;cursor:pointer;">&#8635;</button>' +
                    '<button data-id="'+id+'" data-a="done" style="width:30px;height:30px;border-radius:50%;' +
                    'background:#dcfce7;color:#16a34a;border:none;cursor:pointer;">&#10003;</button>' +
                    '<button data-id="'+id+'" data-a="del" style="width:30px;height:30px;border-radius:50%;' +
                    'background:#fee2e2;color:#dc2626;border:none;cursor:pointer;">&#10005;</button>' +
                    '</div></div>';
            }

            function stopTimer(id) {
                clearInterval(timers[id]); delete timers[id];
                var t=find(id); if(t) t.running=false;
            }

            function init() {
                var addBtn = document.getElementById('ttp-addbtn');
                var inp    = document.getElementById('ttp-input');
                var list   = document.getElementById('ttp-list');

                // Add button
                addBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    var text = inp.value.trim();
                    var mins = parseInt(document.getElementById('ttp-mins').value) || 25;
                    if(!text) { inp.focus(); inp.style.borderColor='#ef4444'; return; }
                    inp.style.borderColor='#d1d5db';
                    var id = 'ttp'+Date.now();
                    todos.push({id:id,text:text,done:false,total:mins*60,left:mins*60,running:false});
                    save();
                    inp.value = '';
                    var li = document.createElement('li');
                    li.id = 'ttp-card-'+id;
                    li.style.marginBottom = '10px';
                    list.appendChild(li);
                    renderCard(id);
                    stats();
                    inp.focus();
                });

                // Enter key
                inp.addEventListener('keydown', function(e) {
                    if(e.key==='Enter') { e.preventDefault(); addBtn.click(); }
                });

                // Card button clicks via event delegation
                list.addEventListener('click', function(e) {
                    var btn = e.target.closest('button[data-a]');
                    if(!btn) return;
                    e.preventDefault();
                    var id = btn.getAttribute('data-id');
                    var a  = btn.getAttribute('data-a');
                    var t  = find(id);
                    if(!t) return;

                    if(a==='start') {
                        if(t.running||t.done||t.left<=0) return;
                        t.running=true;
                        timers[id]=setInterval(function(){
                            var t2=find(id); if(!t2||!t2.running) return;
                            if(t2.left<=0){ stopTimer(id); save(); renderCard(id); alert('Done: '+t2.text); return; }
                            t2.left--; save(); renderCard(id);
                        },1000);
                        renderCard(id);
                    } else if(a==='pause') {
                        stopTimer(id); save(); renderCard(id);
                    } else if(a==='reset') {
                        stopTimer(id); t.left=t.total; save(); renderCard(id);
                    } else if(a==='done') {
                        stopTimer(id); t.done=!t.done; save(); renderCard(id); stats();
                    } else if(a==='del') {
                        stopTimer(id);
                        todos=todos.filter(function(x){return x.id!==id;});
                        var el=document.getElementById('ttp-card-'+id);
                        if(el) el.remove();
                        save(); stats();
                    }
                });

                // Render saved todos on load
                todos.forEach(function(t){
                    var li=document.createElement('li');
                    li.id='ttp-card-'+t.id;
                    li.style.marginBottom='10px';
                    list.appendChild(li);
                    renderCard(t.id);
                });
                stats();
            }

            // Guard: run after DOM is ready
            if(document.readyState==='loading') {
                document.addEventListener('DOMContentLoaded', init);
            } else {
                init();
            }
        })();
        </script>
        """
        return html
```

---

## How to Package Your Plugin

1. Create a folder for your plugin, e.g. `todo-timer/`
2. Place your `__init__.py` (and optional `logo.png`, `config.json`) **inside** that folder
3. Select all files **inside** the folder — not the folder itself
4. Compress them into a `.zip` file

```
✅ Correct: zip contains __init__.py at root
❌ Wrong:   zip contains todo-timer/__init__.py (folder inside zip)
```
> The backend will fix the "folder inside zip" case automatically, but it's best practice to zip correctly.

---

## How to Upload Your Plugin

1. Go to your Django Plugin Manager site and log in
2. Click **"Upload Plugin"**
3. Fill in:
   - **Plugin Name** — this is used to generate the URL slug via `slugify(name)`
   - **Description** — short description shown in the sidebar
   - **Logo** *(optional)* — or include `logo.png/jpg/svg/gif` inside your ZIP
   - **Plugin Zip File** — your `.zip` file
4. Click **"Upload Plugin"**
5. Your plugin will appear in the sidebar immediately

---

## Upload Error Reference

| Error Message | Cause | Fix |
|---|---|---|
| `"Plugin name is required."` | Name field is empty | Enter a plugin name |
| `"Plugin zip file is required."` | No ZIP selected | Select a `.zip` file |
| `"Please upload a valid .zip file."` | Wrong file type | Ensure filename ends with `.zip` |
| `"Invalid plugin name."` | Name has only special characters | Use letters, numbers, spaces |
| `"A plugin named X already exists."` | Slug collision | Delete the old plugin or use a different name |
| `"Invalid or corrupted ZIP file."` | ZIP is damaged | Re-zip your files |
| `"Plugin zip must contain __init__.py"` | `__init__.py` missing from ZIP root | Zip the files, not the folder |
| `"Plugin __init__.py must contain a Plugin class"` | Class not named `Plugin` | Rename your class to exactly `Plugin` |
| `"Plugin class missing required attribute: X"` | Missing `name`, `slug`, `version`, or `description` | Add the missing attribute |
| `"Plugin attribute X must be a string"` | Attribute is wrong type | Set the attribute to a string value |
| `"Plugin class must have a render method"` | No `render()` method | Add `def render(self, request, config):` |

---

## Runtime Checklist

Before uploading, verify your plugin passes this checklist:

- [ ] `__init__.py` is at the **root** of the ZIP (not inside a subfolder)
- [ ] Class is named exactly **`Plugin`** (capital P)
- [ ] All four required attributes exist and are **strings**: `name`, `slug`, `version`, `description`
- [ ] `render(self, request, config)` method exists and returns a **string**
- [ ] No Python **f-strings** used in your HTML/JS (or all `{}` are escaped as `{{}}`)
- [ ] All HTML element **IDs are unique** — prefixed to avoid host page conflicts
- [ ] No `onclick="func()"` pointing to functions inside an IIFE — use `addEventListener` instead
- [ ] Script is placed **after** your HTML elements, or wrapped in a `DOMContentLoaded` guard
- [ ] Tested locally before packaging

---

## Tips

- **Tailwind CSS is available** — use Tailwind utility classes freely; no CDN link needed in your plugin
- **Use `localStorage`** for client-side data persistence across page reloads
- **Use `data-*` attributes + event delegation** instead of `onclick` for reliable event handling
- **Prefix everything** — IDs, localStorage keys, global variables — with your plugin slug to prevent conflicts
- **Keep it self-contained** — your plugin's entire UI lives in the string returned by `render()`
