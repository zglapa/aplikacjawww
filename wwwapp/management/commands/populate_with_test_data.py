import django.db.utils
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from wwwapp.models import UserProfile, Article, ArticleContentHistory, Workshop, WorkshopCategory, \
    WorkshopType, WorkshopParticipant, Camp
from typing import Tuple, List, Union
from faker import Faker
from faker.providers import profile, person, date_time, internet
import random

"""
Command implementing database population. 
Useful for making test fixtures. 
"""


class Command(BaseCommand):
    args = ''
    help = 'Populate the database with data for development'
    LOCALE = 'pl_PL'
    NUM_OF_USERS = 50
    NUM_OF_WORKSHOPS = 5
    NUM_OF_ARTICLES = 2
    NUM_OF_CATEGORIES = 2
    NUM_OF_TYPES = 2

    """
    Constructor of the command
    """
    def __init__(self) -> None:
        fake = Faker(self.LOCALE)
        fake.add_provider(profile)
        fake.add_provider(person)
        fake.add_provider(date_time)
        fake.add_provider(internet)
        self.fake = fake

        super().__init__()

    """
    Create and returns a fake random user.
    """
    def fake_user(self) -> Tuple[User, UserProfile]:
        ok = False
        while not ok:
            ok = True
            try:
                profile_data = self.fake.profile()
                user = User.objects.create_user(profile_data['username'], profile_data['mail'], 'password')
                user.first_name = self.fake.first_name()
                user.last_name = self.fake.last_name()
                user.save()

                user.userprofile.gender = profile_data['sex']
                user.userprofile.school = "TEST"
                user.userprofile.matura_exam_year = self.fake.date_this_year().year
                user.userprofile.how_do_you_know_about = self.fake.text()
                user.userprofile.profile_page = self.fake.text()
                user.userprofile.cover_letter = self.fake.text()
                user.userprofile.save()

                # user.userprofile.user_info.pesel = pesel=profile_data['ssn']
                # user.userprofile.user_info.address=profile_data['address']
                # user.userprofile.user_info.comments=self.fake.text(100)
                # user.userprofile.user_info.save()
            except django.db.utils.IntegrityError:
                ok = False

        return user, user.userprofile

    """
    Returns a zero padded string representation of the given number
    or an empty string if the argument is not present
    """
    @staticmethod
    def tail_for_sequence(sequence: Union[int, None]) -> str:
        if sequence is not None:
            return '{0:04d}'.format(sequence)
        else:
            return ''

    """
    Creates and returns a fake random article with a random edit history
    """
    def fake_article(self, users: List[User], sequence: Union[str, None] = None) -> Article:
        article = Article(name=self.fake.uri_page() + self.tail_for_sequence(sequence),
                          title=self.fake.text(),
                          content=self.fake.paragraph(),
                          modified_by=random.choice(users),
                          on_menubar=random.choice([False, True]))

        article.save()

        for i in range(2, 4):
            ArticleContentHistory(version=i,
                                  article=article,
                                  content=self.fake.paragraph(),
                                  modified_by=random.choice(users),
                                  time=self.fake.date_time_this_year()).save()

        return article

    """
    Creates and returns a random category
    """
    def fake_category(self, year: Camp) -> WorkshopCategory:
        c = WorkshopCategory(year=year, name=self.fake.text(10))
        c.save()
        return c

    """
    Creates and returns a random type
    """
    def fake_type(self, year: Camp) -> WorkshopType:
        c = WorkshopType(year=year, name=self.fake.text(10))
        c.save()
        return c

    """
    Creates a fake random workshops with 5 random participants
    """
    def fake_workshop(self,
                      lecturer: UserProfile,
                      participants: List[UserProfile],
                      types: List[WorkshopType],
                      categories: List[WorkshopCategory],
                      sequence: Union[str, None] = None) -> Workshop:
        workshop_type = random.choice(types)
        workshop = Workshop(name=self.fake.uri_page() + self.tail_for_sequence(sequence),
                            title=self.fake.text(10),
                            proposition_description=self.fake.paragraph(),
                            type=workshop_type,
                            year=workshop_type.year,
                            status='Z',
                            page_content=self.fake.paragraph(),
                            page_content_is_public=True,
                            is_qualifying=True)
        workshop.save()

        for participant in participants:
            info = WorkshopParticipant(workshop=workshop,
                                       participant=participant,
                                       comment=self.fake.paragraph())
            info.save()

        workshop.category.add(random.choice(categories))
        workshop.lecturer.add(lecturer)
        workshop.save()

        return workshop

    """
    Handles the command
    """
    def handle(self, *args, **options) -> None:
        if not settings.DEBUG:
            print("Command not allowed in production")
            return

        User.objects.create_superuser("admin", "admin@admin.admin", "admin")

        users = []
        user_profiles = []
        for i in range(self.NUM_OF_USERS):
            (user, user_profile) = self.fake_user()
            users.append(user)
            user_profiles.append(user_profile)

        articles = []
        for i in range(self.NUM_OF_ARTICLES):
            articles.append(self.fake_article(users, i))

        year = Camp.objects.get()  # The year object for the current year is created by the initial migration

        types = []
        for i in range(self.NUM_OF_TYPES):
            types.append(self.fake_type(year))

        categories = []
        for i in range(self.NUM_OF_CATEGORIES):
            categories.append(self.fake_category(year))

        lecturers = user_profiles[:self.NUM_OF_WORKSHOPS]
        participants = user_profiles[self.NUM_OF_WORKSHOPS:]
        participants = [participants[self.NUM_OF_WORKSHOPS * i:self.NUM_OF_WORKSHOPS * (i + 1)] for i in
                        range(len(participants) // self.NUM_OF_WORKSHOPS)]

        workshops = []
        for i, (lecturer, participants) in enumerate(zip(lecturers, participants)):
            workshops.append(self.fake_workshop(lecturer, participants, types, categories, i))
