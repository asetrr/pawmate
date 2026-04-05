import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import MeetingPlanForm, PetForm, RegisterForm, SwipePreferenceForm
from .models import Match, MeetingPlan, Message, Notification, Pet, Swipe, UserSwipePreference


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


def next_candidate_for(user, pref=None):
    pref = pref or get_user_pref(user)
    return filtered_candidates_qs(user, pref=pref).order_by('-created_at').first()


def filtered_candidates_qs(user, pref=None):
    pref = pref or get_user_pref(user)
    swiped_ids = Swipe.objects.filter(user=user).values_list('pet_id', flat=True)
    qs = (
        Pet.objects.exclude(owner=user)
        .exclude(id__in=swiped_ids)
        .filter(age__gte=pref.min_age, age__lte=pref.max_age)
    )
    if pref.species:
        qs = qs.filter(species__icontains=pref.species)
    if pref.city:
        qs = qs.filter(city__icontains=pref.city)
    if pref.active_today:
        qs = qs.filter(owner__last_login__date=timezone.localdate())
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
        'photo_url': pet.photo_url,
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


def how_it_works(request):
    return render(request, 'core/how_it_works.html')


def safety(request):
    return render(request, 'core/safety.html')


def faq(request):
    return render(request, 'core/faq.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('swipe')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Аккаунт создан. Добавь питомца и начинай свайпать.')
            return redirect('pet_create')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    pets = request.user.pets.all()
    matches = request.user.matches.select_related('pet')
    recent_matches = matches[:5]
    notifications = request.user.notifications.all()[:10]
    stats = {
        'pets': pets.count(),
        'matches': matches.count(),
        'messages': Message.objects.filter(match__user=request.user).count(),
    }
    return render(
        request,
        'core/dashboard.html',
        {
            'pets': pets,
            'stats': stats,
            'recent_matches': recent_matches,
            'notifications': notifications,
        },
    )


@login_required
def pet_create(request):
    if request.method == 'POST':
        form = PetForm(request.POST)
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
        form = PetForm(request.POST, instance=pet)
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
        {'first_pet': pet, 'remaining': remaining, 'pref_form': pref_form},
    )


@login_required
@require_POST
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
    matches = request.user.matches.select_related('pet').prefetch_related('messages')
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
@require_POST
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


def login_view(request):
    if request.user.is_authenticated:
        return redirect('swipe')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('swipe')

    return render(request, 'registration/login.html', {'form': form})
