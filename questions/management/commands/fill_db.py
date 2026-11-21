import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from faker import Faker

from core.models import Profile
from questions.models import Tag, Question, Answer, QuestionLike, AnswerLike


class Command(BaseCommand):
    help = 'Наполняет базу данных тестовыми данными с заданным коэффициентом ratio'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int, help='Коэффициент наполнения (например, 10000)')

    def handle(self, *args, **options):
        ratio = options['ratio']
        if ratio <= 0:
            self.stderr.write('ratio должен быть больше 0')
            return

        fake = Faker('ru_RU')
        batch_size = 5000

        self.stdout.write('Подготовка тестовых текстов через Faker...')
        titles_pool = [fake.sentence(nb_words=8).rstrip('.') + '?' for _ in range(500)]
        texts_pool = [fake.paragraph(nb_sentences=4) for _ in range(500)]
        answers_pool = [fake.paragraph(nb_sentences=3) for _ in range(500)]
        words_pool = list({fake.word().lower() for _ in range(500)})

        existing_users_count = User.objects.count()
        existing_tags_count = Tag.objects.count()
        hashed_password = make_password('password123')

        self.stdout.write(f'Создание {ratio} пользователей и профилей...')
        users = [
            User(
                username=f'user_{existing_users_count + i}_{fake.user_name()[:12]}',
                email=f'user_{existing_users_count + i}@voprosik.test',
                password=hashed_password,
            )
            for i in range(1, ratio + 1)
        ]
        created_users = User.objects.bulk_create(users, batch_size=batch_size)
        user_ids = [u.id for u in created_users]

        profiles = [Profile(user_id=uid) for uid in user_ids]
        Profile.objects.bulk_create(profiles, batch_size=batch_size)

        self.stdout.write(f'Создание {ratio} тегов...')
        tags = [
            Tag(name=f'{words_pool[i % len(words_pool)]}_{existing_tags_count + i}')
            for i in range(1, ratio + 1)
        ]
        created_tags = Tag.objects.bulk_create(tags, batch_size=batch_size)
        tag_ids = [t.id for t in created_tags]

        questions_count = ratio * 10
        self.stdout.write(f'Создание {questions_count} вопросов...')
        question_ids = []
        through_model = Question.tags.through
        m2m_batch = []

        for start in range(0, questions_count, batch_size):
            end = min(start + batch_size, questions_count)
            q_batch = [
                Question(
                    title=f'{random.choice(titles_pool)} (#{i + 1})',
                    text=random.choice(texts_pool),
                    author_id=random.choice(user_ids),
                    rating=random.randint(-5, 50),
                )
                for i in range(start, end)
            ]
            created_q = Question.objects.bulk_create(q_batch, batch_size=batch_size)
            for q in created_q:
                question_ids.append(q.id)
                picked_tags = random.sample(tag_ids, k=min(3, len(tag_ids)))
                for tid in picked_tags:
                    m2m_batch.append(through_model(question_id=q.id, tag_id=tid))

            if len(m2m_batch) >= batch_size * 3:
                through_model.objects.bulk_create(m2m_batch, batch_size=batch_size)
                m2m_batch.clear()

        if m2m_batch:
            through_model.objects.bulk_create(m2m_batch, batch_size=batch_size)
            m2m_batch.clear()

        answers_count = ratio * 100
        self.stdout.write(f'Создание {answers_count} ответов...')
        answer_ids = []
        for start in range(0, answers_count, batch_size):
            end = min(start + batch_size, answers_count)
            a_batch = [
                Answer(
                    question_id=question_ids[i % questions_count],
                    author_id=random.choice(user_ids),
                    text=random.choice(answers_pool),
                    is_correct=(i % 10 == 0),
                    rating=random.randint(-2, 20),
                )
                for i in range(start, end)
            ]
            created_a = Answer.objects.bulk_create(a_batch, batch_size=batch_size)
            answer_ids.extend(a.id for a in created_a)

        q_likes_count = ratio * 100
        a_likes_count = ratio * 100
        num_users = len(user_ids)

        self.stdout.write(f'Создание {q_likes_count} оценок для вопросов...')
        ql_batch = []
        for i in range(q_likes_count):
            q_idx = i % questions_count
            round_num = i // questions_count
            u_idx = (q_idx + round_num) % num_users
            ql_batch.append(
                QuestionLike(
                    user_id=user_ids[u_idx],
                    question_id=question_ids[q_idx],
                    value=1 if i % 4 != 0 else -1,
                )
            )
            if len(ql_batch) >= batch_size:
                QuestionLike.objects.bulk_create(ql_batch, batch_size=batch_size, ignore_conflicts=True)
                ql_batch.clear()
        if ql_batch:
            QuestionLike.objects.bulk_create(ql_batch, batch_size=batch_size, ignore_conflicts=True)

        self.stdout.write(f'Создание {a_likes_count} оценок для ответов...')
        al_batch = []
        for i in range(a_likes_count):
            a_idx = i % answers_count
            round_num = i // answers_count
            u_idx = (a_idx + round_num) % num_users
            al_batch.append(
                AnswerLike(
                    user_id=user_ids[u_idx],
                    answer_id=answer_ids[a_idx],
                    value=1 if i % 5 != 0 else -1,
                )
            )
            if len(al_batch) >= batch_size:
                AnswerLike.objects.bulk_create(al_batch, batch_size=batch_size, ignore_conflicts=True)
                al_batch.clear()
        if al_batch:
            AnswerLike.objects.bulk_create(al_batch, batch_size=batch_size, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f'Готово! Добавлено: {ratio} юзеров, {ratio} тегов, '
            f'{questions_count} вопросов, {answers_count} ответов, '
            f'{q_likes_count + a_likes_count} оценок.'
        ))