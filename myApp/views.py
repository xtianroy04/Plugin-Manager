import os
import zipfile
import json
import importlib.util
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView, LoginView
from django.contrib.auth import logout
from django.contrib import messages
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from .models import App, ActivityLog


def get_app_context():
    return {
        'plugins': App.objects.filter(type='plugin', is_active=True),
        'sites': App.objects.filter(type='site', is_active=True)
    }


@login_required
def dashboard(request):
    context = get_app_context()
    context['all_plugins'] = App.objects.filter(type='plugin')
    context['all_sites'] = App.objects.filter(type='site')
    return render(request, 'dashboard.html', context)


# ------------------ Plugin Views ------------------
@login_required
def plugin_list(request):
    context = get_app_context()
    context['all_plugins'] = App.objects.filter(type='plugin')
    return render(request, 'plugins/list.html', context)


@login_required
def plugin_upload(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        app_zip = request.FILES.get('app_zip')
        logo = request.FILES.get('logo')
        description = request.POST.get('description', '').strip()

        # Validate required fields
        if not name:
            return render(request, 'apps/upload.html', {
                'error': 'Name is required.',
                'app_type': 'plugin',
                **get_app_context()
            })
        if not app_zip:
            return render(request, 'apps/upload.html', {
                'error': 'Zip file is required.',
                'app_type': 'plugin',
                **get_app_context()
            })

        # Validate zip file
        if not app_zip.name.endswith('.zip'):
            return render(request, 'apps/upload.html', {
                'error': 'Please upload a valid .zip file.',
                'app_type': 'plugin',
                **get_app_context()
            })

        slug = slugify(name)
        if not slug:
            return render(request, 'apps/upload.html', {
                'error': 'Invalid name. Please use letters, numbers, and spaces.',
                'app_type': 'plugin',
                **get_app_context()
            })

        app_dir = settings.APPS_ROOT / slug

        if app_dir.exists():
            return render(request, 'apps/upload.html', {
                'error': f'A plugin named "{name}" already exists.',
                'app_type': 'plugin',
                **get_app_context()
            })

        try:
            os.makedirs(app_dir, exist_ok=True)

            # Validate zip file is not corrupted
            try:
                with zipfile.ZipFile(app_zip, 'r') as zip_ref:
                    bad_file = zip_ref.testzip()
                    if bad_file:
                        raise Exception(f'Corrupted file in zip: {bad_file}')
                    zip_ref.extractall(app_dir)
            except zipfile.BadZipFile:
                raise Exception('Invalid or corrupted ZIP file.')

            # Check if __init__.py is at root or in a subfolder
            init_file = app_dir / '__init__.py'
            if not init_file.exists():
                for item in os.listdir(app_dir):
                    subfolder = app_dir / item
                    if subfolder.is_dir():
                        test_init = subfolder / '__init__.py'
                        if test_init.exists():
                            for file in os.listdir(subfolder):
                                src = subfolder / file
                                dst = app_dir / file
                                os.rename(src, dst)
                            os.rmdir(subfolder)
                            init_file = app_dir / '__init__.py'
                            break
                else:
                    raise Exception('Zip must contain __init__.py')

            spec = importlib.util.spec_from_file_location('app_module', init_file)
            app_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app_module)

            if not hasattr(app_module, 'Plugin'):
                raise Exception('__init__.py must contain a Plugin class')

            app_class = app_module.Plugin

            # Validate required Plugin class attributes
            required_attrs = ['name', 'slug', 'version', 'description']
            for attr in required_attrs:
                if not hasattr(app_class, attr):
                    raise Exception(f'Plugin class missing required attribute: {attr}')
                if not isinstance(getattr(app_class, attr), str):
                    raise Exception(f'Plugin attribute "{attr}" must be a string')

            if not hasattr(app_class, 'render') or not callable(getattr(app_class, 'render')):
                raise Exception('Plugin class must have a "render" method')

            app_config = {}

            config_file = app_dir / 'config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    app_config = json.load(f)

            app = App.objects.create(
                name=name,
                slug=slug,
                type='plugin',
                version=getattr(app_class, 'version', '1.0'),
                description=getattr(app_class, 'description', description),
                app_dir=str(app_dir),
                config=app_config,
                is_public=False
            )

            # Use uploaded logo if provided, otherwise check ZIP for logo
            if logo:
                app.logo = logo
                app.save()
            else:
                logo_extensions = ['png', 'jpg', 'jpeg', 'svg', 'gif']
                for ext in logo_extensions:
                    logo_path = app_dir / f'logo.{ext}'
                    if logo_path.exists():
                        from django.core.files import File
                        with open(logo_path, 'rb') as f:
                            app.logo.save(f'logo.{ext}', File(f))
                        break

            messages.success(request, f'Plugin "{name}" uploaded successfully!')
            ActivityLog.objects.create(
                user=request.user,
                action='plugin_upload',
                details=f'Uploaded plugin: {name}'
            )
            return redirect('dashboard')

        except Exception as e:
            import shutil
            if app_dir.exists():
                shutil.rmtree(app_dir)
            return render(request, 'apps/upload.html', {
                'error': str(e),
                'app_type': 'plugin',
                **get_app_context()
            })

    return render(request, 'apps/upload.html', {
        'app_type': 'plugin',
        **get_app_context()
    })


@login_required
def plugin_detail(request, slug):
    app = get_object_or_404(App, slug=slug, type='plugin', is_active=True)
    init_file = Path(app.app_dir) / '__init__.py'

    spec = importlib.util.spec_from_file_location('app_module', init_file)
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    app_class = app_module.Plugin
    app_instance = app_class()

    app_content = ''
    if hasattr(app_instance, 'render'):
        app_content = app_instance.render(request, app.config)

    context = get_app_context()
    context['app'] = app
    context['app_content'] = app_content
    return render(request, 'plugins/detail.html', context)


@login_required
def plugin_delete(request, slug):
    app = get_object_or_404(App, slug=slug, type='plugin')

    if request.method == 'POST':
        import shutil
        app_name = app.name
        app_dir = Path(app.app_dir)
        if app_dir.exists():
            shutil.rmtree(app_dir)
        app.delete()
        messages.success(request, f'Plugin "{app_name}" deleted successfully!')
        ActivityLog.objects.create(
            user=request.user,
            action='plugin_delete',
            details=f'Deleted plugin: {app_name}'
        )
        return redirect('dashboard')

    context = get_app_context()
    context['app'] = app
    return render(request, 'apps/delete.html', context)


# ------------------ Site Views ------------------
def site_public(request, slug):
    app = get_object_or_404(App, slug=slug, type='site', is_active=True)
    
    # Check if site is private and user not logged in
    if not app.is_public and not request.user.is_authenticated:
        messages.warning(request, 'This site is private. Please log in to view it.')
        return redirect('login')

    init_file = Path(app.app_dir) / '__init__.py'

    spec = importlib.util.spec_from_file_location('app_module', init_file)
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    app_class = app_module.Site if hasattr(app_module, 'Site') else app_module.Plugin
    app_instance = app_class()

    app_content = ''
    if hasattr(app_instance, 'render'):
        app_content = app_instance.render(request, app.config, is_editing=False)

    return render(request, 'sites/public.html', {
        'app': app,
        'app_content': app_content,
        'user': request.user
    })


@login_required
def site_edit(request, slug):
    app = get_object_or_404(App, slug=slug, type='site', is_active=True)
    init_file = Path(app.app_dir) / '__init__.py'

    spec = importlib.util.spec_from_file_location('app_module', init_file)
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    app_class = app_module.Site if hasattr(app_module, 'Site') else app_module.Plugin
    app_instance = app_class()

    app_content = ''
    if hasattr(app_instance, 'render'):
        app_content = app_instance.render(request, app.config, is_editing=True)

    context = get_app_context()
    context['app'] = app
    context['app_content'] = app_content
    return render(request, 'sites/edit.html', context)


@login_required
def site_upload(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        app_zip = request.FILES.get('app_zip')
        logo = request.FILES.get('logo')
        description = request.POST.get('description', '').strip()

        if not name:
            return render(request, 'apps/upload.html', {
                'error': 'Name is required.',
                'app_type': 'site',
                **get_app_context()
            })
        if not app_zip:
            return render(request, 'apps/upload.html', {
                'error': 'Zip file is required.',
                'app_type': 'site',
                **get_app_context()
            })

        if not app_zip.name.endswith('.zip'):
            return render(request, 'apps/upload.html', {
                'error': 'Please upload a valid .zip file.',
                'app_type': 'site',
                **get_app_context()
            })

        slug = slugify(name)
        if not slug:
            return render(request, 'apps/upload.html', {
                'error': 'Invalid name. Please use letters, numbers, and spaces.',
                'app_type': 'site',
                **get_app_context()
            })

        app_dir = settings.APPS_ROOT / slug

        if app_dir.exists():
            return render(request, 'apps/upload.html', {
                'error': f'A site named "{name}" already exists.',
                'app_type': 'site',
                **get_app_context()
            })

        try:
            os.makedirs(app_dir, exist_ok=True)

            try:
                with zipfile.ZipFile(app_zip, 'r') as zip_ref:
                    bad_file = zip_ref.testzip()
                    if bad_file:
                        raise Exception(f'Corrupted file in zip: {bad_file}')
                    zip_ref.extractall(app_dir)
            except zipfile.BadZipFile:
                raise Exception('Invalid or corrupted ZIP file.')

            init_file = app_dir / '__init__.py'
            if not init_file.exists():
                for item in os.listdir(app_dir):
                    subfolder = app_dir / item
                    if subfolder.is_dir():
                        test_init = subfolder / '__init__.py'
                        if test_init.exists():
                            for file in os.listdir(subfolder):
                                src = subfolder / file
                                dst = app_dir / file
                                os.rename(src, dst)
                            os.rmdir(subfolder)
                            init_file = app_dir / '__init__.py'
                            break
                else:
                    raise Exception('Zip must contain __init__.py')

            spec = importlib.util.spec_from_file_location('app_module', init_file)
            app_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app_module)

            if not (hasattr(app_module, 'Site') or hasattr(app_module, 'Plugin')):
                raise Exception('__init__.py must contain a Site or Plugin class')

            app_class = app_module.Site if hasattr(app_module, 'Site') else app_module.Plugin

            required_attrs = ['name', 'slug', 'version', 'description']
            for attr in required_attrs:
                if not hasattr(app_class, attr):
                    raise Exception(f'Class missing required attribute: {attr}')
                if not isinstance(getattr(app_class, attr), str):
                    raise Exception(f'Attribute "{attr}" must be a string')

            if not hasattr(app_class, 'render') or not callable(getattr(app_class, 'render')):
                raise Exception('Class must have a "render" method')

            app_config = {}

            config_file = app_dir / 'config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    app_config = json.load(f)

            app = App.objects.create(
                name=name,
                slug=slug,
                type='site',
                version=getattr(app_class, 'version', '1.0'),
                description=getattr(app_class, 'description', description),
                app_dir=str(app_dir),
                config=app_config,
                is_public=True
            )

            if logo:
                app.logo = logo
                app.save()
            else:
                logo_extensions = ['png', 'jpg', 'jpeg', 'svg', 'gif']
                for ext in logo_extensions:
                    logo_path = app_dir / f'logo.{ext}'
                    if logo_path.exists():
                        from django.core.files import File
                        with open(logo_path, 'rb') as f:
                            app.logo.save(f'logo.{ext}', File(f))
                        break

            messages.success(request, f'Site "{name}" uploaded successfully!')
            ActivityLog.objects.create(
                user=request.user,
                action='site_upload',
                details=f'Uploaded site: {name}'
            )
            return redirect('dashboard')

        except Exception as e:
            import shutil
            if app_dir.exists():
                shutil.rmtree(app_dir)
            return render(request, 'apps/upload.html', {
                'error': str(e),
                'app_type': 'site',
                **get_app_context()
            })

    return render(request, 'apps/upload.html', {
        'app_type': 'site',
        **get_app_context()
    })


@login_required
def site_delete(request, slug):
    app = get_object_or_404(App, slug=slug, type='site')

    if request.method == 'POST':
        import shutil
        app_name = app.name
        app_dir = Path(app.app_dir)
        if app_dir.exists():
            shutil.rmtree(app_dir)
        app.delete()
        messages.success(request, f'Site "{app_name}" deleted successfully!')
        ActivityLog.objects.create(
            user=request.user,
            action='site_delete',
            details=f'Deleted site: {app_name}'
        )
        return redirect('dashboard')

    context = get_app_context()
    context['app'] = app
    return render(request, 'apps/delete.html', context)


@login_required
def site_toggle_visibility(request, slug):
    app = get_object_or_404(App, slug=slug, type='site')
    app.is_public = not app.is_public
    app.save()
    messages.success(request, f'Site "{app.name}" is now {"public" if app.is_public else "private"}!')
    return redirect('dashboard')


# ------------------ Generic API Endpoints for ALL Apps ------------------
@login_required
@require_http_methods(["GET"])
def app_get_config(request, slug):
    app = get_object_or_404(App, slug=slug, is_active=True)
    return JsonResponse(app.config)


@login_required
@require_http_methods(["POST"])
def app_set_config(request, slug):
    app = get_object_or_404(App, slug=slug, is_active=True)
    try:
        data = json.loads(request.body)
        app.config = data
        app.save()
        return JsonResponse({'success': True, 'config': app.config})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def app_update_config(request, slug):
    app = get_object_or_404(App, slug=slug, is_active=True)
    try:
        data = json.loads(request.body)
        app.config.update(data)
        app.save()
        return JsonResponse({'success': True, 'config': app.config})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def app_custom_api(request, slug, method_name):
    app = get_object_or_404(App, slug=slug, is_active=True)
    
    init_file = Path(app.app_dir) / '__init__.py'
    spec = importlib.util.spec_from_file_location('app_module', init_file)
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    
    app_class = app_module.Plugin if hasattr(app_module, 'Plugin') else app_module.Site
    app_instance = app_class()
    
    method_name = f'api_{method_name}'
    if hasattr(app_instance, method_name) and callable(getattr(app_instance, method_name)):
        method = getattr(app_instance, method_name)
        try:
            data = json.loads(request.body) if request.body else {}
            result = method(request, app.config, data)
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'error': f'Method {method_name} not found'}, status=404)


@login_required
def activity_log(request):
    logs = ActivityLog.objects.filter(user=request.user)[:100]
    context = get_app_context()
    context['logs'] = logs
    return render(request, 'activity_log.html', context)


@method_decorator(login_required, name='dispatch')
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_app_context())
        return context


@method_decorator(login_required, name='dispatch')
class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'registration/password_change_done.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_app_context())
        return context


def get_active_sessions_for_user(user):
    """Get all active sessions for a given user"""
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_id = user._meta.pk.value_to_string(user)
    user_sessions = []
    for session in active_sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == user_id:
            user_sessions.append(session)
    return user_sessions


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_app_context())
        return context
    
    def form_valid(self, form):
        # Get user trying to login
        user = form.get_user()
        
        # Check for existing active sessions
        active_sessions = get_active_sessions_for_user(user)
        
        # Remove current session from check (if any)
        if self.request.session.session_key:
            active_sessions = [s for s in active_sessions if s.session_key != self.request.session.session_key]
        
        # Check if user submitted 'take over'
        if 'take_over' in self.request.POST:
            # Invalidate all other sessions
            for session in active_sessions:
                session.delete()
            # Log the login activity
            ActivityLog.objects.create(
                user=user,
                action='login',
                details=f'Took over existing session'
            )
            return super().form_valid(form)
        
        # If there are existing active sessions
        if active_sessions:
            # Show the prompt
            return self.render_to_response(self.get_context_data(
                form=form,
                show_takeover_prompt=True,
                active_session_count=len(active_sessions)
            ))
        
        # Log the normal login activity
        ActivityLog.objects.create(
            user=user,
            action='login',
            details='Normal login'
        )
        return super().form_valid(form)


class CustomLogoutView(auth_views.LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            ActivityLog.objects.create(
                user=request.user,
                action='logout',
                details='User logged out'
            )
        return super().dispatch(request, *args, **kwargs)
