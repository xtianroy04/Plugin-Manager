# Django WordPress-like Plugin Manager Plan

---

## Change Tracking
All implementation changes and updates are logged in `ChangeLog.MD`.

---

## System Flow Diagram (Mermaid)
```mermaid
flowchart TD
    A[User Opens Site] --> B{Is Authenticated?}
    B -->|No| C[Redirect to Login Page]
    C --> D[User Enters Credentials]
    D --> E[Django Auth Validates]
    E -->|Success| F[Redirect to Dashboard]
    E -->|Fail| C
    B -->|Yes| F
    F --> G[plugin_list View]
    G --> H{Choose Action}
    H -->|Upload New Plugin| I[plugin_upload View - GET]
    I --> J[Show HyperUI Upload Form]
    J --> K[User Submits ZIP + Form]
    K --> L[plugin_upload View - POST]
    L --> M[Validate ZIP File]
    M --> N[Extract ZIP to media/plugins/<slug>/]
    N --> O[Scan __init__.py for Plugin Class]
    O --> P[Save Plugin Record to DB]
    P --> Q[Redirect to plugin_list]
    H -->|Click Plugin in Sidebar| R[plugin_detail View]
    R --> S[Load Plugin from DB]
    S --> T[Dynamically Import Plugin Class]
    T --> U[Call plugin.render(request, config)]
    U --> V[Render HyperUI Detail Page]
    H -->|Delete Plugin| W[plugin_delete View]
    W --> X[Delete Plugin Folder from Media]
    X --> Y[Delete Plugin Record from DB]
    Y --> Q
    H -->|Logout| Z[Django Logout View]
    Z --> C
```

## 1. Plugin Package Standard (Like WordPress)
Each plugin is a **ZIP file** with this structure:
```
my_plugin.zip
├── __init__.py       # Main plugin file (REQUIRED - must have Plugin class)
├── logo.png          # Optional plugin logo (also accepts logo.jpg)
├── config.json       # Optional default configuration
└── templates/        # Optional plugin-specific templates
    └── my_plugin/
        └── index.html
```

### Required `Plugin` Class in `__init__.py`
```python
class Plugin:
    name = "My Plugin"           # Display name
    slug = "my_plugin"           # Unique identifier (no spaces)
    version = "1.0"              # Version string
    description = "My plugin"    # Short description

    def render(self, request, config=None):
        # Return HTML string or Django TemplateResponse
        return "<h1>My Plugin Interface</h1>"
```

---

## 2. Data Model (`myApp/models.py`)
```python
from django.db import models

class Plugin(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    version = models.CharField(max_length=50, default="1.0")
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='plugins/logos/', blank=True, null=True)
    plugin_dir = models.CharField(max_length=500)  # Path to extracted plugin folder
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
```

---

## 3. Project Settings (`mysite/settings.py`)
Add:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Optional: Create plugins directory if not exists
import os
PLUGINS_ROOT = MEDIA_ROOT / 'plugins'
os.makedirs(PLUGINS_ROOT, exist_ok=True)

# Static files config
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

---

## 4. Views (`myApp/views.py`)
Use `@login_required` decorator on ALL plugin views:
- `plugin_list`: Show sidebar with active plugins + upload button + logout link
- `plugin_upload`: Handle zip upload → extract → scan → save to DB
- `plugin_detail`: Load plugin class → call `render()` → display interface
- `plugin_delete`: Delete plugin folder + DB record
- `plugin_toggle`: Activate/deactivate plugin (optional)

---

## 5. Templates (HyperUI + Tailwind CSS)
Use **Tailwind CSS CDN** + **HyperUI components** for all UI:
- Add Tailwind CDN to base template: `<script src="https://cdn.tailwindcss.com"></script>`
- Add HyperUI component references (copy-paste from https://www.hyperui.dev/)

Template files:
- `templates/base.html`: Base template with Tailwind CDN, HyperUI sidebar/nav + logout button
- `templates/registration/login.html`: Login page using HyperUI Form components
- `templates/plugins/list.html`: Extend base, use HyperUI Sidebar + Card components for plugin list
- `templates/plugins/detail.html`: Extend base, use HyperUI Container/Card for plugin interface
- `templates/plugins/upload.html`: Extend base, use HyperUI File Input + Form components

### HyperUI Components to Use
- Sidebar: https://www.hyperui.dev/components/application-ui/sidebars
- Cards: https://www.hyperui.dev/components/marketing/cards
- Forms: https://www.hyperui.dev/components/forms
- Buttons: https://www.hyperui.dev/components/application-ui/buttons

---

## 6. URLs
- `mysite/urls.py`: Add Django auth urls, media serving (dev only) + include myApp urls
- `myApp/urls.py`:
  - `/` → plugin_list
  - `/upload/` → plugin_upload
  - `/<slug>/` → plugin_detail
  - `/<slug>/delete/` → plugin_delete
  - `/<slug>/toggle/` → plugin_toggle (optional)

### Auth URLs (included in `mysite/urls.py`)
```python
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    # ... other urls
]
```

### Settings for Auth
Add to `mysite/settings.py`:
```python
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'  # Redirect to dashboard after login
LOGOUT_REDIRECT_URL = 'login'
```

---

## 7. Implementation Steps
1. Update `models.py` with Plugin model
2. Update `settings.py` with media + static + auth config
3. Install dependencies: `pip install pillow python-magic` (for file validation)
4. Create superuser: `python manage.py createsuperuser`
5. Create `templates/registration/login.html` with HyperUI login form
6. Create `templates/base.html` with Tailwind CDN + HyperUI base layout + logout
7. Create views (all with `@login_required`) for upload/extract/load/render/delete
8. Create plugin templates (list/upload/detail) using HyperUI components
9. Configure urls (add auth urls + plugin urls)
10. Make migrations + migrate
11. Test login/logout + sample plugin zip

---

## SECURITY WARNING
⚠️ **EXTREMELY HIGH RISK**: Dynamically importing/executing user-uploaded Python code allows full server takeover.
- Only use this system if you **100% trust all plugin uploaders**
- Never use on production servers with untrusted users
- Add strict validation (file type checks, code scanning, sandboxing) if possible
