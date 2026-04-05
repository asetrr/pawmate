from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from core.forms import PetForm, MAX_PET_PHOTO_BYTES


class PetFormTests(TestCase):
    def _base_data(self):
        return {
            'name': 'Луна',
            'species': 'Кошка',
            'breed': 'Британская',
            'age': 2,
            'gender': 'female',
            'city': 'Москва',
            'bio': 'Ласковая и активная.',
            'photo_url': '',
        }

    def _image_file(self, width=200, height=200, quality=85):
        image = Image.effect_noise((width, height), 100).convert('RGB')
        stream = BytesIO()
        image.save(stream, format='JPEG', quality=quality)
        return SimpleUploadedFile(
            'pet.jpg',
            stream.getvalue(),
            content_type='image/jpeg',
        )

    def test_requires_photo_or_url(self):
        form = PetForm(data=self._base_data(), files={})
        self.assertFalse(form.is_valid())
        self.assertIn('Добавь фото питомца', form.non_field_errors()[0])

    def test_rejects_oversized_photo(self):
        data = self._base_data()
        huge = self._image_file(width=4200, height=4200, quality=95)
        self.assertGreater(huge.size, MAX_PET_PHOTO_BYTES)
        form = PetForm(data=data, files={'photo': huge})
        self.assertFalse(form.is_valid())
        self.assertIn('Максимум 6 МБ', form.errors['photo'][0])

    def test_accepts_valid_photo_url_without_file(self):
        data = self._base_data()
        data['photo_url'] = 'https://images.example.com/pet.jpg'
        form = PetForm(data=data, files={})
        self.assertTrue(form.is_valid())
