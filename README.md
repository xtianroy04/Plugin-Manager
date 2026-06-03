# Django WordPress-like Plugin Manager

A powerful Django web application that allows users to upload, manage, and run custom plugins, similar to WordPress!

## Features

- 🔐 **User Authentication**: Secure login/logout system
- 📦 **Plugin Upload**: Upload plugins as ZIP files
- 🎨 **Modern UI**: Built with Tailwind CSS + HyperUI + Poppins font
- 📋 **Plugin Management**: List, view, and delete plugins
- 🔧 **Automatic Logo Detection**: Use logo from ZIP or upload separately
- ✅ **Comprehensive Validation**: Prevents invalid plugins from being uploaded
- 💬 **User Feedback**: Success/error messages for all actions
- 📝 **JSON Configuration**: Plugins can include config.json for custom settings

## Tech Stack

- **Backend**: Django 6.0.5
- **Frontend**: Tailwind CSS (CDN), HyperUI
- **Font**: Poppins from Google Fonts
- **Database**: SQLite (default)

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Django 6.0.5
- Pillow library

### 2. Installation

1. Clone or download this project
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install django pillow
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Create a superuser (optional but recommended):
   ```bash
   python manage.py createsuperuser
   ```
   A default superuser is already created with credentials:
   - Username: `admin`
   - Password: `admin123`
6. Start the server:
   ```bash
   python manage.py runserver
   ```
7. Visit http://127.0.0.1:8000 in your browser

## Creating Plugins

### Plugin Structure

Each plugin must be packaged as a **ZIP file** with the following structure:

```
my-awesome-plugin.zip
├── __init__.py       # Required - Main plugin class
├── logo.png          # Optional - Plugin logo (png/jpg/svg/gif)
├── config.json       # Optional - Plugin configuration
└── templates/        # Optional - Plugin-specific templates
    └── my-awesome-plugin/
        └── index.html
```

### Required `__init__.py`

```python
class Plugin:
    name = "My Awesome Plugin"
    slug = "my-awesome-plugin"
    version = "1.0"
    description = "A simple plugin that does awesome things!"

    def render(self, request, config):
        """
        Required method to render the plugin UI.
        
        Args:
            request: Django request object
            config: Plugin configuration dict from config.json (or empty dict)
            
        Returns:
            str: HTML string to display
        """
        return f"""
        <div class="max-w-md mx-auto bg-white p-6 rounded-lg shadow-md">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">{self.name}</h2>
            <p class="text-gray-600 mb-4">{self.description}</p>
            <p class="text-sm text-gray-500">Version: {self.version}</p>
        </div>
        """
```

### Example: Todo Plugin

We've included a sample Todo Plugin! Check the `todo_plugin/` folder in this project.

## Usage

1. **Login**: Go to http://127.0.0.1:8000 and log in
2. **Upload Plugin**: Click "Upload Plugin" in the sidebar
3. **Fill Details**:
   - Plugin Name (required)
   - Description (optional)
   - Logo (optional - or include in ZIP)
   - Plugin ZIP File (required)
4. **View Plugins**: All uploaded plugins show in the sidebar
5. **Delete Plugins**: Click delete button (with confirmation)

## Security Warning

⚠️ **IMPORTANT**: This plugin manager executes user-uploaded Python code directly.

- Only use this system with **trusted plugins and users**
- Never use this on a public/production server with untrusted users
- Be careful with plugins from unknown sources

## Project Structure

```
Django/
├── myApp/                  # Main application
│   ├── migrations/         # Database migrations
│   ├── templates/          # Application templates
│   │   └── plugins/        # Plugin management templates
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py           # Plugin model
│   ├── tests.py
│   ├── urls.py             # App URLs
│   └── views.py            # Views for plugin management
├── mysite/                 # Project configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py         # Django settings
│   ├── urls.py             # Project URLs
│   └── wsgi.py
├── templates/              # Global templates
│   ├── base.html
│   └── registration/
│       └── login.html
├── todo_plugin/            # Sample todo plugin source
├── venv/                   # Virtual environment (gitignored)
├── media/                  # Media files (user uploads, gitignored)
├── db.sqlite3              # SQLite database (gitignored)
├── manage.py               # Django management script
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── Plan.md                 # Project plan and system flow diagram
├── ChangeLog.md            # Change log
└── PLUGIN_CREATION_GUIDE.md # Comprehensive plugin creation guide
```

## Plugin API Reference

### Plugin Class Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | str | ✅ Yes | Human-readable plugin name |
| `slug` | str | ✅ Yes | URL-safe unique identifier (lowercase, hyphens) |
| `version` | str | ✅ Yes | Plugin version (e.g., "1.0", "2.1.3") |
| `description` | str | ✅ Yes | Short description of what the plugin does |

### Plugin Class Methods

| Method | Returns | Required | Description |
|--------|---------|----------|-------------|
| `render(request, config)` | str (HTML) | ✅ Yes | Generates the plugin UI |

## Troubleshooting

For detailed troubleshooting, see [PLUGIN_CREATION_GUIDE.md](PLUGIN_CREATION_GUIDE.md).

## Contributing

Feel free to fork and modify this project!

## License

This project is open source and available for personal use.

## Credits

- Built with ❤️ using Django
- UI components from [HyperUI](https://www.hyperui.dev/)
- Font: [Poppins](https://fonts.google.com/specimen/Poppins)
