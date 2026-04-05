from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Match, Message, Pet


class ChatPollingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', password='pass12345')
        self.owner = User.objects.create_user(username='owner', password='pass12345')
        self.pet = Pet.objects.create(
            owner=self.owner,
            name='Луна',
            species='Кошка',
            breed='Британская',
            age=2,
            gender='female',
            city='Москва',
            bio='Тест',
            photo_url='https://example.com/cat.jpg',
        )
        self.match = Match.objects.create(user=self.user, pet=self.pet)
        self.client.force_login(self.user)

    def test_fetch_messages_returns_only_new(self):
        old_msg = Message.objects.create(match=self.match, sender=self.user, text='Первое')
        new_msg = Message.objects.create(match=self.match, sender=self.owner, text='Ответ')

        response = self.client.get(
            reverse('fetch_messages_api', args=[self.match.id]),
            {'last_id': old_msg.id},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload['messages']), 1)
        self.assertEqual(payload['messages'][0]['id'], new_msg.id)
        self.assertEqual(payload['messages'][0]['mine'], False)
