import json

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .email_verification import activate_by_token, send_verification_email
from .forms import (
    DeleteAccountForm,
    LoginForm,
    MeetingPlanForm,
    ModerationAppealForm,
    PetForm,
    ProfileSettingsForm,
    RegisterForm,
    SwipePreferenceForm,
)
from .moderation import is_moderator, recalc_moderation_status
from .models import (
    AbuseReport,
    Match,
    MeetingPlan,
    Message,
    ModerationAppeal,
    Notification,
    Pet,
    Swipe,
    UserBlock,
    UserModerationStatus,
    UserProfileSettings,
    UserSwipePreference,
)
from .rate_limit import rate_limited
from .two_factor import send_login_otp, verify_login_otp

LOGIN_ATTEMPT_LIMIT = 8
LOGIN_BLOCK_SECONDS = 180
PENDING_2FA_USER_KEY = 'pending_2fa_user_id'
PENDING_2FA_REMEMBER_KEY = 'pending_2fa_remember_me'
PENDING_2FA_NEXT_KEY = 'pending_2fa_next'


DEMO_PETS = [
    {
        'name': 'Луна',
        'species': 'Кошка',
        'breed': 'Британская',
        'age': 2,
        'gender': 'female',
        'city': 'Москва',
        'bio': 'Любит смотреть в окно, мурчит даже во сне.',
        'photo_url': 'https://images.unsplash.com/photo-1574158622682-e40e69881006?w=900&fit=crop',
    },
    {
        'name': 'Бадди',
        'species': 'Собака',
        'breed': 'Французский бульдог',
        'age': 3,
        'gender': 'male',
        'city': 'Москва',
        'bio': 'Обожает парки, игрушки и новые знакомства.',
        'photo_url': 'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=900&fit=crop',
    },
    {
        'name': 'Рокси',
        'species': 'Кошка',
        'breed': 'Абиссинская',
        'age': 1,
        'gender': 'female',
        'city': 'Санкт-Петербург',
        'bio': 'Энергичная и очень общительная. Ищет друзей для игр.',
        'photo_url': 'https://images.unsplash.com/photo-1519052537078-e6302a4968d4?w=900&fit=crop',
    },
    {
        'name': 'Макс',
        'species': 'Собака',
        'breed': 'Хаски',
        'age': 4,
        'gender': 'male',
        'city': 'Казань',
        'bio': 'Бегает марафоны и тянет хозяина в приключения.',
        'photo_url': 'https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=900&fit=crop',
    },
]
DEMO_OWNER_USERNAME = 'pet_demo_owner'



def ensure_demo_pets():
    owner, _ = User.objects.get_or_create(
        username='pet_demo_owner',
        defaults={'email': 'demo@pawmate.local'},
    )
    if owner.has_usable_password():
        owner.set_unusable_password()
        owner.save(update_fields=['password'])
    if not owner.last_login:
        owner.last_login = timezone.now()
        owner.save(update_fields=['last_login'])

    if owner.pets.count() == 0:
        for pet_data in DEMO_PETS:
            Pet.objects.create(owner=owner, **pet_data)


def get_user_pref(user):
    pref, _ = UserSwipePreference.objects.get_or_create(user=user)
    return pref


def get_user_settings(user):
    settings_obj, _ = UserProfileSettings.objects.get_or_create(user=user)
    return settings_obj



def next_candidate_for(user, pref=None):
    pref = pref or get_user_pref(user)
    return filtered_candidates_qs(user, pref=pref).order_by('-created_at').first()


def filtered_candidates_qs(user, pref=None):
    pref = pref or get_user_pref(user)
    user_settings = get_user_settings(user)
    swiped_ids = Swipe.objects.filter(user=user).values_list('pet_id', flat=True)
    blocked_ids = UserBlock.objects.filter(user=user).values_list('blocked_user_id', flat=True)
    blocked_by_ids = UserBlock.objects.filter(blocked_user=user).values_list('user_id', flat=True)
    hidden_owner_ids = UserModerationStatus.objects.filter(
        is_under_moderation=True,
        hidden_from_swipe_until__gt=timezone.now(),
    ).values_list('user_id', flat=True)
    qs = (
        Pet.objects.exclude(owner=user)
        .exclude(id__in=swiped_ids)
        .exclude(owner_id__in=blocked_ids)
        .exclude(owner_id__in=blocked_by_ids)
        .exclude(owner_id__in=hidden_owner_ids)
        .filter(age__gte=pref.min_age, age__lte=pref.max_age)
    )
    if pref.species:
        qs = qs.filter(species__icontains=pref.species)
    if pref.city:
        qs = qs.filter(city__icontains=pref.city)
    if pref.active_today:
        qs = qs.filter(owner__last_login__date=timezone.localdate())
    if not user_settings.show_demo_profiles:
        qs = qs.exclude(owner__username=DEMO_OWNER_USERNAME)
    return qs


def pet_to_json(pet):
    return {
        'id': pet.id,
        'name': pet.name,
        'species': pet.species,
        'breed': pet.breed,
        'age': pet.age,
        'gender': pet.get_gender_display(),
        'city': pet.city,
        'bio': pet.bio,
        'photo_url': pet.display_photo,
        'owner': pet.owner.username,
    }


def landing(request):
    context = {
        'total_pets': Pet.objects.count(),
        'total_matches': Match.objects.count(),
        'total_users': User.objects.count(),
    }
    if request.user.is_authenticated:
        context['is_member'] = True
    return render(request, 'core/landing.html', context)


def healthz(request):
    return JsonResponse({'ok': True, 'time': timezone.now().isoformat()})


def how_it_works(request):
    return render(request, 'core/how_it_works.html')


def safety(request):
    return render(request, 'core/safety.html')


def faq(request):
    return render(request, 'core/faq.html')


def privacy(request):
    return render(request, 'core/privacy.html')


def terms(request):
    return render(request, 'core/terms.html')


def community_rules(request):
    return render(request, 'core/community_rules.html')



def _safe_next_url(request):
    target = (request.POST.get('next') or request.GET.get('next') or '').strip()
    if target and url_has_allowed_host_and_scheme(target, {request.get_host()}, require_https=request.is_secure()):
        return target
    return ''


def _login_limit_keys(request):
    ip = request.META.get('REMOTE_ADDR', 'anon')
    username = (request.POST.get('username') or '').strip().lower()
    suffix = f"{ip}:{username}" if username else ip
    return (
        f"auth:login:attempts:{suffix}",
        f"auth:login:block:{suffix}",
    )


def _is_login_blocked(request):
    _, block_key = _login_limit_keys(request)
    blocked_for = cache.get(block_key)
    return int(blocked_for or 0)


def _register_login_failure(request):
    attempts_key, block_key = _login_limit_keys(request)
    attempts = int(cache.get(attempts_key) or 0) + 1
    cache.set(attempts_key, attempts, timeout=LOGIN_BLOCK_SECONDS)
    if attempts >= LOGIN_ATTEMPT_LIMIT:
        cache.set(block_key, LOGIN_BLOCK_SECONDS, timeout=LOGIN_BLOCK_SECONDS)


def _clear_login_limit(request):
    attempts_key, block_key = _login_limit_keys(request)
    cache.delete(attempts_key)
    cache.delete(block_key)


def _mask_email(email: str) -> str:
    local, _, domain = email.partition('@')
    if not local or not domain:
        return '***'
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[:2] + '*' * max(2, len(local) - 2)
    return f'{masked_local}@{domain}'


def _send_verification_with_cooldown(user, request, cooldown_sec: int = 60) -> bool:
    key = f'auth:verify:sent:{user.id}'
    if cache.get(key):
        return False
    send_verification_email(user, request)
    cache.set(key, 1, timeout=cooldown_sec)
    return True


def _set_pending_2fa_session(request, user_id: int, remember_me: bool, next_url: str):
    request.session[PENDING_2FA_USER_KEY] = user_id
    request.session[PENDING_2FA_REMEMBER_KEY] = bool(remember_me)
    request.session[PENDING_2FA_NEXT_KEY] = next_url or ''


def _clear_pending_2fa_session(request):
    for key in (PENDING_2FA_USER_KEY, PENDING_2FA_REMEMBER_KEY, PENDING_2FA_NEXT_KEY):
        request.session.pop(key, None)


def register_view(request):
    if request.user.is_authenticated:
        next_url = _safe_next_url(request)
        return redirect(next_url or 'swipe')

    next_url = _safe_next_url(request)
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save(update_fields=['is_active'])
            _send_verification_with_cooldown(user, request)
            messages.success(request, 'Аккаунт создан. Мы отправили ссылку подтверждения на email.')
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form, 'next': next_url})


def verify_email_view(request, token):
    user, status = activate_by_token(token)
    if status == 'ok':
        messages.success(request, 'Email подтвержден. Теперь можно войти в PawMate.')
        return redirect('login')
    if status == 'expired':
        messages.error(request, 'Ссылка подтверждения истекла. Запроси новую ссылку.')
    elif status == 'already_used':
        messages.info(request, 'Этот email уже подтвержден. Можно войти.')
    else:
        messages.error(request, 'Некорректная ссылка подтверждения.')
    return redirect('login')


@require_POST
@rate_limited('email_resend', limit=10, window_sec=3600)
def resend_verification_email_view(request):
    email = (request.POST.get('email') or '').strip().lower()
    if not email:
        messages.error(request, 'Укажи email для повторной отправки.')
        return redirect('login')

    user = User.objects.filter(email__iexact=email).first()
    if user and not user.is_active:
        sent_now = _send_verification_with_cooldown(user, request)
        masked_email = _mask_email(user.email)
        if sent_now:
            messages.success(request, f'Письмо подтверждения отправлено на {masked_email}.')
        else:
            messages.info(request, f'Письмо уже отправлялось недавно на {masked_email}. Подожди минуту и попробуй снова.')
        return redirect('login')
    messages.success(request, 'Если аккаунт найден и не подтвержден, письмо отправлено повторно.')
    return redirect('login')


@login_required
def dashboard(request):
    pets = request.user.pets.all()
    matches = request.user.matches.select_related('pet')
    recent_matches = matches[:5]
    notifications = request.user.notifications.all()[:5]
    recent_reports = request.user.reports.select_related('pet', 'message').order_by('-created_at')[:6]
    recent_blocks = request.user.blocks.select_related('blocked_user').order_by('-created_at')[:6]
    moderation_status, _ = UserModerationStatus.objects.get_or_create(user=request.user)
    active_hide = bool(
        moderation_status.hidden_from_swipe_until
        and moderation_status.hidden_from_swipe_until > timezone.now()
    )
    messages_count = Message.objects.filter(match__user=request.user).count()
    stats = {
        'pets': pets.count(),
        'matches': matches.count(),
        'messages': messages_count,
    }
    onboarding_items = [
        {'done': pets.exists(), 'text': 'Добавь первого питомца', 'link': 'pet_create', 'link_label': 'Добавить'},
        {'done': matches.exists(), 'text': 'Получи первый мэтч в свайпах', 'link': 'swipe', 'link_label': 'К свайпам'},
        {'done': messages_count > 0, 'text': 'Отправь первое сообщение в чате', 'link': 'chats', 'link_label': 'Открыть чат'},
    ]
    onboarding_done = sum(1 for item in onboarding_items if item['done'])
    return render(
        request,
        'core/dashboard.html',
        {
            'pets': pets,
            'stats': stats,
            'recent_matches': recent_matches,
            'notifications': notifications,
            'recent_reports': recent_reports,
            'recent_blocks': recent_blocks,
            'moderation_status': moderation_status,
            'active_hide': active_hide,
            'onboarding_items': onboarding_items,
            'onboarding_done': onboarding_done,
        },
    )


@login_required
def notifications_history(request):
    notifications_qs = request.user.notifications.select_related('match').all()
    paginator = Paginator(notifications_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/notifications_history.html', {'page_obj': page_obj})


@login_required
def moderation_center(request):
    reports = request.user.reports.select_related('pet', 'match')[:30]
    blocks = request.user.blocks.select_related('blocked_user')[:30]
    return render(request, 'core/moderation.html', {'reports': reports, 'blocks': blocks})


@login_required
def moderation_queue(request):
    if not is_moderator(request.user):
        return redirect('dashboard')
    status_filter = request.GET.get('status', 'open')
    reports_qs = AbuseReport.objects.select_related('reporter', 'target_user', 'pet', 'message')
    if status_filter in {AbuseReport.Status.OPEN, AbuseReport.Status.REVIEWED, AbuseReport.Status.CLOSED}:
        reports_qs = reports_qs.filter(status=status_filter)
    reports = reports_qs.order_by('-created_at')[:120]
    return render(
        request,
        'core/moderation_queue.html',
        {'reports': reports, 'status_filter': status_filter},
    )


@login_required
def my_restrictions(request):
    status, _ = UserModerationStatus.objects.get_or_create(user=request.user)
    active_hide = bool(status.hidden_from_swipe_until and status.hidden_from_swipe_until > timezone.now())
    progress_pct = min(100, int((status.valid_reports_count / 3) * 100)) if status.valid_reports_count else 0
    reports_about = (
        AbuseReport.objects.filter(target_user=request.user)
        .exclude(status=AbuseReport.Status.CLOSED)
        .select_related('reporter', 'pet', 'message')
        .order_by('-created_at')[:20]
    )
    appeal_form = ModerationAppealForm()
    appeals = request.user.moderation_appeals.all()[:10]
    return render(
        request,
        'core/my_restrictions.html',
        {
            'status': status,
            'active_hide': active_hide,
            'reports_about': reports_about,
            'progress_pct': progress_pct,
            'appeal_form': appeal_form,
            'appeals': appeals,
        },
    )


@login_required
@require_POST
@rate_limited('moderation_appeal', limit=8, window_sec=3600)
def submit_moderation_appeal(request):
    form = ModerationAppealForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Заполни текст апелляции.')
        return redirect('my_restrictions')
    ModerationAppeal.objects.create(user=request.user, text=form.cleaned_data['text'])
    messages.success(request, 'Апелляция отправлена. Мы рассмотрим ее и обновим статус.')
    return redirect('my_restrictions')


@login_required
def pet_create(request):
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            pet.save()
            messages.success(request, f'Питомец {pet.name} добавлен.')
            return redirect('dashboard')
    else:
        form = PetForm()
    return render(request, 'core/pet_form.html', {'form': form, 'title': 'Новый питомец'})


@login_required
def pet_edit(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль питомца обновлен.')
            return redirect('dashboard')
    else:
        form = PetForm(instance=pet)
    return render(request, 'core/pet_form.html', {'form': form, 'title': f'Редактировать {pet.name}'})


@login_required
def swipe_view(request):
    ensure_demo_pets()
    pref = get_user_pref(request.user)
    settings_obj = get_user_settings(request.user)

    if request.method == 'POST':
        pref_form = SwipePreferenceForm(request.POST, instance=pref)
        if pref_form.is_valid():
            pref_form.save()
            messages.success(request, 'Фильтры свайпа сохранены.')
            return redirect('swipe')
    else:
        pref_form = SwipePreferenceForm(instance=pref)

    pet = next_candidate_for(request.user, pref=pref)
    remaining = filtered_candidates_qs(request.user, pref=pref).count()
    if not request.user.pets.exists():
        messages.info(request, 'Сначала добавь хотя бы одного своего питомца, чтобы получать релевантные мэтчи.')
    return render(
        request,
        'core/swipe.html',
        {'first_pet': pet, 'remaining': remaining, 'pref_form': pref_form, 'ui_settings': settings_obj},
    )


@login_required
@require_POST
@rate_limited('swipe', limit=120, window_sec=60)
def swipe_api(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    if pet.owner_id == request.user.id:
        return HttpResponseBadRequest('Нельзя свайпать своих питомцев')

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Некорректный JSON')

    liked = bool(payload.get('liked'))
    Swipe.objects.update_or_create(
        user=request.user,
        pet=pet,
        defaults={'liked': liked},
    )

    matched = False
    if liked and ((request.user.id + pet.id) % 3 != 0):
        match, created = Match.objects.get_or_create(user=request.user, pet=pet)
        matched = True
        if created:
            Notification.objects.create(
                user=request.user,
                kind=Notification.Type.MATCH,
                text=f'Новый мэтч: {match.pet.name}',
            )
    elif not liked:
        Match.objects.filter(user=request.user, pet=pet).delete()

    pref = get_user_pref(request.user)
    next_pet = next_candidate_for(request.user, pref=pref)
    remaining = filtered_candidates_qs(request.user, pref=pref).count()

    return JsonResponse(
        {
            'matched': matched,
            'matched_with': pet.name if matched else '',
            'next_pet': pet_to_json(next_pet) if next_pet else None,
            'remaining': remaining,
        }
    )


@login_required
def chats(request):
    blocked_ids = UserBlock.objects.filter(user=request.user).values_list('blocked_user_id', flat=True)
    blocked_by_ids = UserBlock.objects.filter(blocked_user=request.user).values_list('user_id', flat=True)
    matches = (
        request.user.matches.select_related('pet')
        .prefetch_related('messages')
        .exclude(pet__owner_id__in=blocked_ids)
        .exclude(pet__owner_id__in=blocked_by_ids)
    )
    active_match = None
    meeting_form = None
    meeting_plan = None
    unread_raw = (
        request.user.notifications.filter(kind=Notification.Type.MESSAGE, is_read=False, match__isnull=False)
        .values('match_id')
        .annotate(total=Count('id'))
    )
    unread_by_match = {row['match_id']: row['total'] for row in unread_raw}
    if matches.exists():
        active_id = request.GET.get('match')
        if active_id:
            active_match = matches.filter(id=active_id).first()
        if not active_match:
            active_match = matches.first()
    if active_match:
        request.user.notifications.filter(
            kind=Notification.Type.MESSAGE,
            is_read=False,
            match=active_match,
        ).update(is_read=True)
        unread_by_match[active_match.id] = 0
        meeting_plan, _ = MeetingPlan.objects.get_or_create(match=active_match)
        meeting_form = MeetingPlanForm(instance=meeting_plan)
    match_rows = [{'match': m, 'unread': unread_by_match.get(m.id, 0)} for m in matches]

    return render(
        request,
        'core/chat.html',
        {
            'matches': matches,
            'match_rows': match_rows,
            'active_match': active_match,
            'active_messages': active_match.messages.all() if active_match else [],
            'meeting_plan': meeting_plan,
            'meeting_form': meeting_form,
        },
    )


@login_required
@require_POST
@rate_limited('chat_send', limit=45, window_sec=60)
def send_message_api(request, match_id):
    match = get_object_or_404(Match, id=match_id, user=request.user)
    text = request.POST.get('text', '').strip()
    if not text:
        return HttpResponseBadRequest('Пустое сообщение')

    message = Message.objects.create(match=match, sender=request.user, text=text)
    reply_message = None

    # Demo auto-reply to make chat feel alive in MVP mode.
    if message.text.endswith('?'):
        reply_message = Message.objects.create(
            match=match,
            sender=match.pet.owner,
            text='Да! Давай встретимся в парке на выходных.',
        )
        Notification.objects.create(
            user=request.user,
            match=match,
            kind=Notification.Type.MESSAGE,
            text=f'Новый ответ в чате с {match.pet.name}',
        )

    return JsonResponse(
        {
            'ok': True,
            'message': {
                'id': message.id,
                'text': message.text,
                'mine': True,
                'created_at': message.created_at.isoformat(),
            },
            'auto_reply': (
                {
                    'id': reply_message.id,
                    'text': reply_message.text,
                    'mine': False,
                    'created_at': reply_message.created_at.isoformat(),
                }
                if reply_message
                else None
            ),
        }
    )


@login_required
@rate_limited('chat_poll', limit=120, window_sec=60)
def fetch_messages_api(request, match_id):
    match = get_object_or_404(Match, id=match_id, user=request.user)
    last_id_raw = (request.GET.get('last_id') or '0').strip()
    try:
        last_id = int(last_id_raw)
    except ValueError:
        return HttpResponseBadRequest('Некорректный last_id')
    if last_id < 0:
        last_id = 0

    new_messages = match.messages.filter(id__gt=last_id).order_by('id')[:50]
    return JsonResponse(
        {
            'ok': True,
            'messages': [
                {
                    'id': msg.id,
                    'text': msg.text,
                    'mine': msg.sender_id == request.user.id,
                    'created_at': msg.created_at.isoformat(),
                }
                for msg in new_messages
            ],
        }
    )


@login_required
@require_POST
@rate_limited('meeting_update', limit=30, window_sec=60)
def update_meeting_api(request, match_id):
    match = get_object_or_404(Match, id=match_id, user=request.user)
    meeting_plan, _ = MeetingPlan.objects.get_or_create(match=match)
    form = MeetingPlanForm(request.POST, instance=meeting_plan)
    if not form.is_valid():
        return HttpResponseBadRequest('Некорректные данные плана встречи')
    plan = form.save()
    plan.confirmed_by_user = False
    plan.confirmed_by_owner = False
    if plan.status == MeetingPlan.Status.CONFIRMED:
        plan.confirmed_by_user = True
    plan.save(update_fields=['confirmed_by_user', 'confirmed_by_owner'])
    Notification.objects.create(
        user=request.user,
        match=match,
        kind=Notification.Type.MEETING,
        text=f'План встречи обновлен: {match.pet.name}',
    )
    return JsonResponse(
        {
            'ok': True,
            'place': plan.place,
            'status': plan.get_status_display(),
            'starts_at': timezone.localtime(plan.starts_at).strftime('%d.%m %H:%M') if plan.starts_at else '',
            'note': plan.note,
            'confirmed_by_user': plan.confirmed_by_user,
            'confirmed_by_owner': plan.confirmed_by_owner,
        }
    )


@login_required
@require_POST
@rate_limited('meeting_confirm', limit=30, window_sec=60)
def confirm_meeting_api(request, match_id):
    match = get_object_or_404(Match, id=match_id, user=request.user)
    plan, _ = MeetingPlan.objects.get_or_create(match=match)
    plan.confirmed_by_user = True
    force_owner = request.POST.get('force_owner') == '1'
    if match.pet.owner.username == 'pet_demo_owner' or force_owner:
        plan.confirmed_by_owner = True
    if plan.confirmed_by_user and plan.confirmed_by_owner:
        plan.status = MeetingPlan.Status.CONFIRMED
    elif plan.status == MeetingPlan.Status.DRAFT:
        plan.status = MeetingPlan.Status.PROPOSED
    plan.save()
    Notification.objects.create(
        user=request.user,
        match=match,
        kind=Notification.Type.MEETING,
        text=f'Подтверждение встречи: {match.pet.name}',
    )
    return JsonResponse(
        {
            'ok': True,
            'status': plan.get_status_display(),
            'confirmed_by_user': plan.confirmed_by_user,
            'confirmed_by_owner': plan.confirmed_by_owner,
        }
    )


@login_required
@require_POST
@rate_limited('report', limit=20, window_sec=60)
def report_pet_api(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    reason = request.POST.get('reason', '').strip()
    if not reason:
        return HttpResponseBadRequest('Укажи причину жалобы')
    if pet.owner_id == request.user.id:
        return HttpResponseBadRequest('Нельзя отправить жалобу на самого себя')
    AbuseReport.objects.create(
        reporter=request.user,
        target_user=pet.owner,
        pet=pet,
        reason=reason,
    )
    recalc_moderation_status(pet.owner, latest_reason=reason)
    Notification.objects.create(
        user=request.user,
        kind=Notification.Type.MESSAGE,
        text=f'Жалоба отправлена по питомцу {pet.name}',
    )
    return JsonResponse({'ok': True})


@login_required
@require_POST
@rate_limited('block', limit=20, window_sec=60)
def block_pet_owner_api(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    if pet.owner_id == request.user.id:
        return HttpResponseBadRequest('Нельзя блокировать самого себя')
    UserBlock.objects.get_or_create(user=request.user, blocked_user=pet.owner)
    return JsonResponse({'ok': True})


@login_required
@require_POST
@rate_limited('report_message', limit=25, window_sec=60)
def report_message_api(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    if message.match.user_id != request.user.id:
        return HttpResponseBadRequest('Нельзя пожаловаться на чужой чат')
    if message.sender_id == request.user.id:
        return HttpResponseBadRequest('Нельзя отправить жалобу на собственное сообщение')
    reason = request.POST.get('reason', '').strip()
    if not reason:
        return HttpResponseBadRequest('Укажи причину жалобы')
    AbuseReport.objects.create(
        reporter=request.user,
        target_user=message.sender,
        message=message,
        match=message.match,
        reason=reason,
    )
    recalc_moderation_status(message.sender, latest_reason=reason)
    Notification.objects.create(
        user=request.user,
        match=message.match,
        kind=Notification.Type.MESSAGE,
        text='Жалоба на сообщение отправлена модератору',
    )
    return JsonResponse({'ok': True})


@login_required
@require_POST
@rate_limited('unblock', limit=20, window_sec=60)
def unblock_user_api(request, user_id):
    UserBlock.objects.filter(user=request.user, blocked_user_id=user_id).delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
@rate_limited('moderation_action', limit=80, window_sec=60)
def moderation_report_action_api(request, report_id):
    if not is_moderator(request.user):
        return HttpResponseBadRequest('Недостаточно прав')
    report = get_object_or_404(AbuseReport, id=report_id)
    action = request.POST.get('action', '').strip()
    if action not in {'open', 'reviewed', 'closed'}:
        return HttpResponseBadRequest('Некорректное действие')
    status_map = {
        'open': AbuseReport.Status.OPEN,
        'reviewed': AbuseReport.Status.REVIEWED,
        'closed': AbuseReport.Status.CLOSED,
    }
    report.status = status_map[action]
    report.save(update_fields=['status'])
    recalc_moderation_status(report.target_user)
    return JsonResponse({'ok': True, 'new_status': report.get_status_display()})


def login_view(request):
    if request.user.is_authenticated:
        next_url = _safe_next_url(request)
        return redirect(next_url or 'swipe')

    next_url = _safe_next_url(request)
    form = LoginForm(request, data=request.POST or None)
    blocked_for = _is_login_blocked(request) if request.method == 'POST' else 0
    show_resend = False
    resend_email = ''
    masked_resend_email = ''

    if request.method == 'POST':
        if blocked_for:
            messages.error(request, f'Слишком много попыток входа. Подождите {blocked_for} секунд.')
        elif form.is_valid():
            auth_user = form.get_user()
            _clear_login_limit(request)
            settings_obj = UserProfileSettings.objects.filter(user=auth_user).first()
            two_factor_enabled = settings_obj.two_factor_enabled if settings_obj else False
            if two_factor_enabled:
                _set_pending_2fa_session(
                    request,
                    user_id=auth_user.id,
                    remember_me=bool(form.cleaned_data.get('remember_me')),
                    next_url=next_url,
                )
                sent = send_login_otp(auth_user, request)
                if sent:
                    messages.info(request, f'Код входа отправлен на {_mask_email(auth_user.email)}.')
                else:
                    messages.info(request, 'Код уже отправлялся недавно. Проверь почту или запроси новый.')
                return redirect('login_2fa')
            else:
                login(request, auth_user)
                if not form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(0)
                return redirect(next_url or 'swipe')
        else:
            username = (request.POST.get('username') or '').strip()
            raw_password = request.POST.get('password') or ''
            possible_user = User.objects.filter(username=username).first()
            if possible_user and not possible_user.is_active and raw_password and possible_user.check_password(raw_password):
                _send_verification_with_cooldown(possible_user, request)
                show_resend = True
                resend_email = possible_user.email
                masked_resend_email = _mask_email(possible_user.email)
                messages.info(request, f'На почту {masked_resend_email} отправили письмо подтверждения.')
            else:
                _register_login_failure(request)

    return render(
        request,
        'registration/login.html',
        {
            'form': form,
            'next': next_url,
            'show_resend': show_resend,
            'resend_email': resend_email,
            'masked_resend_email': masked_resend_email,
        },
    )


@login_required
def profile_settings_view(request):
    settings_obj = get_user_settings(request.user)
    delete_form = DeleteAccountForm()
    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки профиля сохранены.')
            return redirect('profile_settings')
    else:
        form = ProfileSettingsForm(instance=settings_obj)
    return render(request, 'core/profile_settings.html', {'form': form, 'delete_form': delete_form})


@login_required
@require_POST
@rate_limited('delete_account', limit=5, window_sec=300)
def delete_account_view(request):
    form = DeleteAccountForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Подтверди удаление аккаунта и введи пароль.')
        return redirect('profile_settings')
    if not request.user.check_password(form.cleaned_data['password']):
        messages.error(request, 'Неверный пароль. Аккаунт не удален.')
        return redirect('profile_settings')

    user = request.user
    logout(request)
    user.delete()
    messages.success(request, 'Аккаунт удален.')
    return redirect('landing')


def login_2fa_view(request):
    pending_user_id = request.session.get(PENDING_2FA_USER_KEY)
    if not pending_user_id:
        messages.info(request, 'Сначала введи логин и пароль.')
        return redirect('login')

    user = User.objects.filter(id=pending_user_id).first()
    if not user:
        _clear_pending_2fa_session(request)
        messages.error(request, 'Сессия входа устарела. Попробуй снова.')
        return redirect('login')

    if request.method == 'POST':
        code = (request.POST.get('code') or '').strip()
        status = verify_login_otp(user, code)
        if status == 'ok':
            login(request, user)
            _clear_login_limit(request)
            remember_me = bool(request.session.get(PENDING_2FA_REMEMBER_KEY))
            next_url = request.session.get(PENDING_2FA_NEXT_KEY) or ''
            _clear_pending_2fa_session(request)
            if not remember_me:
                request.session.set_expiry(0)
            return redirect(next_url or 'swipe')
        if status == 'expired':
            messages.error(request, 'Код истек. Запроси новый.')
        elif status == 'locked':
            messages.error(request, 'Слишком много неверных попыток кода. Запроси новый код.')
        elif status == 'invalid':
            messages.error(request, 'Неверный код. Попробуй еще раз.')
        else:
            messages.error(request, 'Код не найден. Запроси новый.')

    return render(request, 'registration/login_2fa.html', {'masked_email': _mask_email(user.email)})


@require_POST
@rate_limited('login_2fa_resend', limit=12, window_sec=3600)
def login_2fa_resend_view(request):
    pending_user_id = request.session.get(PENDING_2FA_USER_KEY)
    if not pending_user_id:
        messages.info(request, 'Сначала введи логин и пароль.')
        return redirect('login')
    user = User.objects.filter(id=pending_user_id).first()
    if not user:
        _clear_pending_2fa_session(request)
        messages.error(request, 'Сессия входа устарела. Попробуй снова.')
        return redirect('login')
    sent = send_login_otp(user, request)
    if sent:
        messages.success(request, f'Новый код отправлен на {_mask_email(user.email)}.')
    else:
        messages.info(request, 'Код уже отправлялся недавно. Подожди минуту и попробуй снова.')
    return redirect('login_2fa')


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)








