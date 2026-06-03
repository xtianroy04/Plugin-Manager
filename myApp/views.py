import os
import zipfile
import json
import importlib.util
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils.text import slugify
from .models import Plugin


def get_plugin_context():
    return {'plugins': Plugin.objects.all()}


@login_required
def plugin_list(request):
    plugins = Plugin.objects.all()
    context = get_plugin_context()
    context['all_plugins'] = plugins
    return render(request, 'plugins/list.html', context)


@login_required
def plugin_upload(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        plugin_zip = request.FILES.get('plugin_zip')
        logo = request.FILES.get('logo')
        description = request.POST.get('description', '').strip()

        # Validate required fields
        if not name:
            return render(request, 'plugins/upload.html', {
                'error': 'Plugin name is required.',
                **get_plugin_context()
            })
        if not plugin_zip:
            return render(request, 'plugins/upload.html', {
                'error': 'Plugin zip file is required.',
                **get_plugin_context()
            })

        # Validate zip file
        if not plugin_zip.name.endswith('.zip'):
            return render(request, 'plugins/upload.html', {
                'error': 'Please upload a valid .zip file.',
                **get_plugin_context()
            })

        slug = slugify(name)
        if not slug:
            return render(request, 'plugins/upload.html', {
                'error': 'Invalid plugin name. Please use letters, numbers, and spaces.',
                **get_plugin_context()
            })

        plugin_dir = settings.PLUGINS_ROOT / slug

        if plugin_dir.exists():
            return render(request, 'plugins/upload.html', {
                'error': f'A plugin named "{name}" already exists.',
                **get_plugin_context()
            })

        try:
            os.makedirs(plugin_dir, exist_ok=True)

            # Validate zip file is not corrupted
            try:
                with zipfile.ZipFile(plugin_zip, 'r') as zip_ref:
                    # Test zip integrity
                    bad_file = zip_ref.testzip()
                    if bad_file:
                        raise Exception(f'Corrupted file in zip: {bad_file}')
                    zip_ref.extractall(plugin_dir)
            except zipfile.BadZipFile:
                raise Exception('Invalid or corrupted ZIP file.')

            # Check if __init__.py is at root or in a subfolder
            init_file = plugin_dir / '__init__.py'
            if not init_file.exists():
                # Look in subfolders
                for item in os.listdir(plugin_dir):
                    subfolder = plugin_dir / item
                    if subfolder.is_dir():
                        test_init = subfolder / '__init__.py'
                        if test_init.exists():
                            # Move files from subfolder to root
                            for file in os.listdir(subfolder):
                                src = subfolder / file
                                dst = plugin_dir / file
                                os.rename(src, dst)
                            os.rmdir(subfolder)
                            init_file = plugin_dir / '__init__.py'
                            break
                else:
                    raise Exception('Plugin zip must contain __init__.py')

            spec = importlib.util.spec_from_file_location('plugin_module', init_file)
            plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_module)

            if not hasattr(plugin_module, 'Plugin'):
                raise Exception('Plugin __init__.py must contain a Plugin class')

            plugin_class = plugin_module.Plugin

            # Validate required Plugin class attributes
            required_attrs = ['name', 'slug', 'version', 'description']
            for attr in required_attrs:
                if not hasattr(plugin_class, attr):
                    raise Exception(f'Plugin class missing required attribute: {attr}')
                if not isinstance(getattr(plugin_class, attr), str):
                    raise Exception(f'Plugin attribute "{attr}" must be a string')

            # Validate required render method
            if not hasattr(plugin_class, 'render') or not callable(getattr(plugin_class, 'render')):
                raise Exception('Plugin class must have a "render" method')

            plugin_config = {}

            config_file = plugin_dir / 'config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    plugin_config = json.load(f)

            plugin = Plugin.objects.create(
                name=name,
                slug=slug,
                version=getattr(plugin_class, 'version', '1.0'),
                description=getattr(plugin_class, 'description', description),
                plugin_dir=str(plugin_dir),
                config=plugin_config
            )

            # Use uploaded logo if provided, otherwise check ZIP for logo
            if logo:
                plugin.logo = logo
                plugin.save()
            else:
                # Check for logo files in the plugin directory
                logo_extensions = ['png', 'jpg', 'jpeg', 'svg', 'gif']
                for ext in logo_extensions:
                    logo_path = plugin_dir / f'logo.{ext}'
                    if logo_path.exists():
                        from django.core.files import File
                        with open(logo_path, 'rb') as f:
                            plugin.logo.save(f'logo.{ext}', File(f))
                        break

            messages.success(request, f'Plugin "{name}" uploaded successfully!')
            return redirect('plugin_list')

        except Exception as e:
            import shutil
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)
            return render(request, 'plugins/upload.html', {
                'error': str(e),
                **get_plugin_context()
            })

    return render(request, 'plugins/upload.html', get_plugin_context())


@login_required
def plugin_detail(request, slug):
    plugin = get_object_or_404(Plugin, slug=slug, is_active=True)
    init_file = Path(plugin.plugin_dir) / '__init__.py'

    spec = importlib.util.spec_from_file_location('plugin_module', init_file)
    plugin_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin_module)
    plugin_class = plugin_module.Plugin
    plugin_instance = plugin_class()

    plugin_content = ''
    if hasattr(plugin_instance, 'render'):
        plugin_content = plugin_instance.render(request, plugin.config)

    context = get_plugin_context()
    context['plugin'] = plugin
    context['plugin_content'] = plugin_content
    return render(request, 'plugins/detail.html', context)


@login_required
def plugin_delete(request, slug):
    plugin = get_object_or_404(Plugin, slug=slug)

    if request.method == 'POST':
        import shutil
        plugin_name = plugin.name
        plugin_dir = Path(plugin.plugin_dir)
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)
        plugin.delete()
        messages.success(request, f'Plugin "{plugin_name}" deleted successfully!')
        return redirect('plugin_list')

    context = get_plugin_context()
    context['plugin'] = plugin
    return render(request, 'plugins/delete.html', context)