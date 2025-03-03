import os.path
from decimal import Decimal

from crispy_forms.bootstrap import FormActions, StrictButton, PrependedAppendedText, Alert, AppendedText
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, HTML, Field
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.forms import ModelChoiceField, ModelMultipleChoiceField
from django.forms import ModelForm, FileInput, FileField
from django.forms.fields import ImageField, ChoiceField, DateField
from django.forms.forms import Form
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.forms.widgets import Textarea, Widget
from django.template import Template, Context
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_select2.forms import Select2MultipleWidget, Select2Widget
import tinymce.widgets
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

from .templatetags.wwwtags import qualified_mark
from .models import UserProfile, Article, Workshop, WorkshopCategory, \
    WorkshopType, WorkshopUserProfile, WorkshopParticipant, Camp, Solution, SolutionFile, NewsPost


class InitializedTinyMCE(tinymce.widgets.TinyMCE):
    def __init__(self, mce_attrs=None, **kwargs):
        mce_attrs_all = {'content_css': staticfiles_storage.url('dist/main.css')}
        mce_attrs = mce_attrs or {}
        mce_attrs_all.update(mce_attrs)
        super().__init__(mce_attrs=mce_attrs_all, **kwargs)


class UserProfilePageForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfilePageForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.include_media = False
        self.helper.layout.fields.append(FormActions(
            HTML('<a role="button" class="btn btn-outline-dark btn-sm mx-1 my-3" href="{% url "profile" user.id %}" target="_blank" title="Otwiera się w nowej karcie">Podgląd twojego profilu</a>'),
            StrictButton('Zapisz', type='submit', css_class='btn-outline-primary btn-lg mx-1 my-3'),
            css_class='text-right'
        ))

    class Meta:
        model = UserProfile
        fields = ['profile_page']
        labels = {'profile_page': "Strona profilowa"}
        widgets = {'profile_page': InitializedTinyMCE()}


class UserCoverLetterForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserCoverLetterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.include_media = False
        self.helper.layout.fields.append(FormActions(
            HTML('<a role="button" class="btn btn-outline-dark btn-sm mx-1 my-3" href="{% url "profile" user.id %}" target="_blank" title="Otwiera się w nowej karcie">Podgląd twojego profilu</a>'),
            StrictButton('Zapisz', type='submit', css_class='btn-outline-primary btn-lg mx-1 my-3'),
            css_class='text-right'
        ))

    class Meta:
        model = UserProfile
        fields = ['cover_letter']
        labels = {'cover_letter': "List motywacyjny"}
        widgets = {'cover_letter': InitializedTinyMCE()}


class UserProfileForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False  # We have to put two Forms in one <form> :(
        self.helper.disable_csrf = True  # Already added by UserForm
        self.helper.include_media = False
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout.fields.append(FormActions(
            HTML('<a role="button" class="btn btn-outline-dark btn-sm mx-1 my-3" href="{% url "profile" user.id %}" target="_blank" title="Otwiera się w nowej karcie">Podgląd twojego profilu</a>'),
            StrictButton('Zapisz', type='submit', css_class='btn-outline-primary btn-lg mx-1 my-3'),
            css_class='text-right row'
        ))

    class Meta:
        model = UserProfile
        fields = ['gender', 'school', 'matura_exam_year', 'how_do_you_know_about']
        labels = {
            'gender': 'Płeć',
            'school': 'Szkoła lub uniwersytet',
            'matura_exam_year': 'Rok zdania matury',
            'how_do_you_know_about': 'Skąd wiesz o WWW?',
        }


class UserForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False  # We have to put two Forms in one <form> :(
        self.helper.include_media = False
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Imię',
            'last_name': 'Nazwisko',
            'email': 'E-mail',
        }


class ArticleForm(ModelForm):
    # These articles have a special purpose - their names cannot be changed because they are used in code,
    # and they are not supposed to ever have a title in the database or be placed on the menubar
    SPECIAL_ARTICLES = {
        'index': 'Strona główna',
        'template_for_workshop_page': 'Szablon strony warsztatów'
    }

    class Meta:
        model = Article
        fields = ['title', 'name', 'on_menubar', 'content']
        labels = {
            'title': 'Tytuł',
            'name': 'Nazwa (w URLach)',
            'on_menubar': 'Umieść w menu',
            'content': 'Treść',
        }

    def __init__(self, user, article_url, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.include_media = False

        mce_attrs = {}
        if self.instance and self.instance.pk:
            mce_attrs = settings.TINYMCE_DEFAULT_CONFIG_WITH_IMAGES.copy()
            mce_attrs['automatic_uploads'] = True
            mce_attrs['images_upload_url'] = reverse('article_edit_upload', kwargs={'name': self.instance.name})
        if self.instance and self.instance.name == 'index':
            # Allow iframe on main page for Facebook embed
            mce_attrs['valid_elements'] = settings.TINYMCE_DEFAULT_CONFIG['valid_elements'] + ',iframe'
        self.fields['content'].widget = InitializedTinyMCE(mce_attrs=mce_attrs)

        is_special = kwargs['instance'] and kwargs['instance'].pk and \
                     kwargs['instance'].name in ArticleForm.SPECIAL_ARTICLES.keys()

        layout = []
        if is_special:
            del self.fields['name']
            del self.fields['title']
            del self.fields['on_menubar']
        else:
            layout.append(PrependedAppendedText('name',
                article_url[0],
                article_url[1],
                template="%s/layout/prepended_appended_text_with_mobile_support.html"
            ))
            layout.append('title')
            layout.append('on_menubar')

            if not user.has_perm('wwwapp.can_put_on_menubar'):
                self.fields['on_menubar'].disabled = True
        layout.append('content')
        layout.append(FormActions(
            StrictButton('Zapisz', type='submit', css_class='btn-outline-primary btn-lg mx-1 my-3'),
            css_class='text-right',
        ))
        self.helper.layout = Layout(*layout)


class WorkshopForm(ModelForm):
    class CategoryChoiceField(ModelMultipleChoiceField):
        def label_from_instance(self, obj):
            return obj.name

    class TypeChoiceField(ModelChoiceField):
        def label_from_instance(self, obj):
            return obj.name

    # Note that the querysets for category and type are overwritten in __init__, but the argument is required here
    category = CategoryChoiceField(label="Kategorie", queryset=WorkshopCategory.objects.all(),
                                   widget=Select2MultipleWidget(attrs={'width': '200px'}))
    type = TypeChoiceField(label="Rodzaj zajęć", queryset=WorkshopType.objects.all(),
                           widget=Select2Widget(attrs={'width': '200px'}))

    qualification_problems = FileField(required=False, widget=FileInput(), label='Zadania kwalifikacyjne (wymagany format PDF):',
                                       validators=[FileExtensionValidator(allowed_extensions=['pdf'])])

    class Meta:
        model = Workshop
        fields = ['title', 'name', 'type', 'category', 'proposition_description',
                  'qualification_problems', 'is_qualifying', 'solution_uploads_enabled',
                  'max_points', 'qualification_threshold', 'short_description',
                  'page_content', 'page_content_is_public']
        labels = {
            'title': 'Tytuł',
            'name': 'Nazwa (w URLach)',
            'proposition_description': 'Opis propozycji warsztatów',
            'is_qualifying': 'Czy warsztaty są kwalifikujące',
            'solution_uploads_enabled': 'Czy przesyłanie rozwiązań przez stronę jest włączone',
            'max_points': 'Maksymalna liczba punktów możliwa do uzyskania',
            'qualification_threshold': 'Minimalna liczba punktów potrzebna do kwalifikacji',
            'short_description': 'Krótki opis warsztatów',
            'page_content': 'Strona warsztatów',
            'page_content_is_public': 'Zaznacz, jeśli opis jest gotowy i może już być publiczny.'
        }
        help_texts = {
            'short_description': 'Zachęć uczestnika do zainteresowania się Twoimi warsztatami w max 140 znakach. Wyświetlany na stronie z programem.',
            'is_qualifying': '(odznacz, jeśli nie zamierzasz dodawać zadań i robić kwalifikacji)',
            'solution_uploads_enabled': 'Od edycji 2021 uczestnicy przesyłają rozwiązania zadań kwalifikacyjnych przez stronę zamiast maila. Jeśli z jakiegoś powodu bardzo chcesz wyłączyć tę funkcję, skontaktuj się z organizatorami.',
            'qualification_threshold': '(wpisz dopiero po sprawdzeniu zadań)',
            'max_points': '(możesz postawić punkty bonusowe powyżej tej wartości, ale tylko do max. {}%)'.format(settings.MAX_POINTS_PERCENT)
        }

    def __init__(self, *args, workshop_url, has_perm_to_edit=True, has_perm_to_disable_uploads=False, profile_warnings=None, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.include_media = False

        # Disable fields that should be disabled
        if not self.instance.is_workshop_editable() or not has_perm_to_edit:
            for field in self.fields.values():
                field.disabled = True

        if self.instance.status:
            # The proposition cannot be edited once the workshop has a status set
            self.fields['proposition_description'].disabled = True

        if not has_perm_to_disable_uploads:
            self.fields['solution_uploads_enabled'].disabled = True

        # Make sure only current category and type choices are displayed
        if self.instance is None:
            raise ValueError('WorkshopForm must be provided with an instance with the .year field already set')
        year = self.instance.year
        self.fields['category'].queryset = WorkshopCategory.objects.filter(year=year)
        self.fields['type'].queryset = WorkshopType.objects.filter(year=year)

        # Display link to current qualification tasks:
        if self.instance.qualification_problems:
            self.fields['qualification_problems'].help_text = format_html('Aktualnie: <a href="{}" target="_blank">{}</a>', reverse('qualification_problems', args=[self.instance.year.pk, self.instance.name]), os.path.basename(self.instance.qualification_problems.path))
        else:
            self.fields['qualification_problems'].help_text = 'Aktualnie: brak'

        # Configure TinyMCE settings
        mce_attrs = {}
        mce_attrs['readonly'] = self.fields['proposition_description'].disabled  # does not seem to respect the Django field settings for some reason
        self.fields['proposition_description'].widget = InitializedTinyMCE(mce_attrs=mce_attrs)

        mce_attrs = settings.TINYMCE_DEFAULT_CONFIG_WITH_IMAGES.copy()
        if self.instance and self.instance.pk:
            mce_attrs['automatic_uploads'] = True
            mce_attrs['images_upload_url'] = reverse('workshop_edit_upload', kwargs={'year': self.instance.year.pk, 'name': self.instance.name})
        mce_attrs['readonly'] = self.fields['page_content'].disabled  # does not seem to respect the Django field settings for some reason
        self.fields['page_content'].widget = InitializedTinyMCE(mce_attrs=mce_attrs)

        # Layout
        self.fieldset_general = Fieldset(
            "Ogólne",
            Div(
                Div(PrependedAppendedText('name',
                    workshop_url[0] + '<b>' + str(year.pk) + '</b>' + workshop_url[1],
                    workshop_url[2],
                    template="%s/layout/prepended_appended_text_with_mobile_support.html"
                ), css_class='col-lg-12'),
                Div('title', css_class='col-lg-12'),
                css_class='row'
            ),
            Div(
                Div('type', css_class='col-lg-6'),
                Div('category', css_class='col-lg-6'),
                css_class='row'
            ),
        )
        if profile_warnings:
            for message in profile_warnings:
                self.fieldset_general.fields.append(Alert(content=message, dismiss=False, css_class='alert-info'))
        self.fieldset_proposal = Fieldset(
            "Opis propozycji",
            'proposition_description',
        )
        self.fieldset_qualification = Fieldset(
            "Kwalifikacja",
            'is_qualifying',
            Div(
                'qualification_problems',
                Div(
                    Div('max_points', css_class='col-lg-6'),
                    Div('qualification_threshold', css_class='col-lg-6'),
                    css_class='row'
                ),
                'solution_uploads_enabled',
                css_id='qualification_settings'
            ),
        )
        self.fieldset_public_page = Fieldset(
            "Strona warsztatów",
            'short_description',
            'page_content',
            'page_content_is_public'
        )
        self.fieldset_submit = FormActions(
            StrictButton('Zapisz' if self.instance and self.instance.pk else 'Zgłoś!', type='submit', css_class='btn-outline-primary btn-lg mx-1 my-3'),
            css_class='text-right',
        )

        if not self.instance or not self.instance.is_publicly_visible():
            for field in [
                  'qualification_problems', 'is_qualifying', 'solution_uploads_enabled',
                  'max_points', 'qualification_threshold', 'short_description',
                  'page_content', 'page_content_is_public']:
                del self.fields[field]

            self.helper.layout = Layout(
                self.fieldset_general,
                self.fieldset_proposal,
                self.fieldset_submit,
            )
        else:
            if not has_perm_to_edit:
                self.helper.layout = Layout(
                    self.fieldset_general,
                    self.fieldset_proposal,
                    self.fieldset_qualification,
                    self.fieldset_public_page,
                )
            else:
                self.helper.layout = Layout(
                    self.fieldset_general,
                    self.fieldset_proposal,
                    self.fieldset_qualification,
                    self.fieldset_public_page,
                    self.fieldset_submit,
                )

    def clean(self):
        super(WorkshopForm, self).clean()
        if not self.instance.is_workshop_editable():
            raise ValidationError('Nie można edytować warsztatów z poprzednich lat')

    def validate_unique(self):
        # Must remove year field from exclude in order
        # for the unique_together constraint to be enforced.
        exclude = self._get_validation_exclusions()
        exclude.remove('year')

        try:
            self.instance.validate_unique(exclude=exclude)
        except ValidationError as e:
            self._update_errors(e.message_dict)


class WorkshopParticipantPointsForm(ModelForm):
    def __init__(self, *args, participant_view=False, **kwargs):
        super(WorkshopParticipantPointsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.include_media = False
        self.helper.form_tag = False
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout = Layout(
            AppendedText(
                'qualification_result',
                'na&nbsp;<b>{}</b>&nbsp;możliwych'.format(self.instance.workshop.max_points) if self.instance.workshop.max_points is not None else None,
                css_class='col-md-3'
            ),
            'comment',
            # I don't think there is any proper way to render a field-like constant text using crispy forms :<
            HTML(format_html('''
                <div id="div_id_mark" class="form-group row">
                    <label for="id_mark" class="col-form-label col-lg-3">
                        Zakwalifikowano
                    </label>

                    <div class="col-lg-9">
                        <div id="id_mark" class="form-control px-0" style="border: 0;">
                            {}
                        </div>
                        {}
                    </div>
                </div>
            ''',
            qualified_mark(self.instance.is_qualified()),
            mark_safe('<small id="hint_id_mark" class="form-text text-muted">To pole jest wypełniane automatycznie na podstawie progu kwalifikacji ustawionego w edytorze warsztatów</small>') if not participant_view else ''))
        )
        if not participant_view:
            self.helper.layout.fields.append(
                FormActions(
                    StrictButton('Zapisz', type='submit', css_class='btn-outline-primary btn-lg mx-1 my-3'),
                    css_class='text-right row'
                )
            )

            self.fields['comment'].help_text = 'Komentarz jest widoczny dla uczestnika na stronie z wynikami kwalifikacji oraz w widoku rozwiązania'
            self.fields['qualification_result'].help_text = 'Maksymalną liczbę punktów możliwą do uzyskania można ustawić w edytorze warsztatów. Możesz postawić punkty bonusowe powyżej tej wartości, ale tylko do {}% wartości bazowej.'.format(settings.MAX_POINTS_PERCENT)

        for field in self.fields.values():
            # autocomplete=off fixes a problem on Firefox where the form fields don't reset on reload, making the save button visibility desync
            field.widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})
            field.required = False

        if not self.instance.workshop.is_qualification_editable() or participant_view:
            for field in self.fields.values():
                field.disabled = True

    class Meta:
        model = WorkshopParticipant
        fields = ['qualification_result', 'comment']
        widgets = {'comment': Textarea(attrs={'rows': 4})}

    def clean(self):
        super(WorkshopParticipantPointsForm, self).clean()
        if not self.instance.workshop.is_qualification_editable():
            raise ValidationError('Nie można edytować warsztatów z poprzednich lat')

        if 'qualification_result' in self.cleaned_data and self.cleaned_data['qualification_result'] is not None:
            if not self.instance.workshop.max_points:
                raise ValidationError({'qualification_result': 'Przed wpisaniem wyników, ustaw maksymalną liczbę punktów możliwą do uzyskania'})

            if self.cleaned_data['qualification_result'] > self.instance.workshop.max_points * (Decimal(settings.MAX_POINTS_PERCENT) / 100):
                raise ValidationError({'qualification_result': 'Nie możesz postawić więcej niż {}% maksymalnej liczby punktów'.format(settings.MAX_POINTS_PERCENT)})


class SolutionForm(ModelForm):
    class Meta:
        model = Solution
        fields = ['message']
        widgets = {'message': Textarea(attrs={'rows': 4})}

    def __init__(self, *args, is_editable=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # handled in template
        self.helper.layout = Layout(
            'message',
        )
        if not is_editable:
            self.fields['message'].disabled = True


class LinkWidget(Widget):
    def __init__(self, link, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.link = link
        self.text = text

    def render(self, name, value, attrs=None, renderer=None):
        return Template('<a href="{{link}}">{{text}}</a>').render(Context({'link': self.link, 'text': self.text}))


class ConstantTextWidget(Widget):
    def render(self, name, value, attrs=None, renderer=None):
        if not value:
            return '-'
        return Template('{{text}}').render(Context({'text': value}))


class SolutionFileForm(ModelForm):
    class Meta:
        model = SolutionFile
        fields = ['file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['file'].disabled = True
            self.fields['file'].widget = LinkWidget(
                link='file/{}/'.format(self.instance.pk),
                text=str(self.instance),
            )
            self.fields['last_changed'] = DateField(widget=ConstantTextWidget(), required=False, disabled=True, label='Ostatnia zmiana', initial=self.instance.last_changed)
        else:
            self.fields['last_changed'] = DateField(widget=ConstantTextWidget(), required=False, disabled=True, label='Ostatnia zmiana')


class BaseSolutionFileInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, is_editable=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # handled in template
        self.helper.disable_csrf = True  # added by SolutionForm
        self.helper.include_media = False
        self.helper.template = 'bootstrap4/table_inline_formset.html'
        self.extra = 1 if not self.instance.pk else 0
        self.can_delete = is_editable


SolutionFileFormSet = inlineformset_factory(Solution, SolutionFile, form=SolutionFileForm, formset=BaseSolutionFileInlineFormSet,
                                            widgets={'file': FileInput()}, extra=0)


class TinyMCEUpload(Form):
    file = ImageField()


class MailFilterForm(Form):
    filter = ChoiceField(label='Metoda filtrowania')

    def __init__(self, filter_methods, *args, **kwargs):
        self.filter_methods = filter_methods
        super().__init__(*args, **kwargs)
        self.fields['filter'].choices = [(k, v[1]) for k, v in self.filter_methods.items()]

        self.helper = FormHelper(self)
        self.helper.include_media = False
        self.helper.layout.fields.append(FormActions(
            StrictButton('Filtruj', type='submit', css_class='btn-outline-primary mx-1 my-3 w-100'),
            css_class='text-right',
        ))

    @property
    def filter_id(self):
        return self.cleaned_data['filter']

    @property
    def filter_method(self):
        return self.filter_methods[self.cleaned_data['filter']][0]

    @property
    def filter_name(self):
        return self.filter_methods[self.cleaned_data['filter']][1]

class NewsPostForm(ModelForm):

    class Meta:
        model = NewsPost
        fields = ['title', 'content']
        labels = {
            'title': 'Tytuł',
            'content': 'Treść',
        }

    def __init__(self, user, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.include_media = False

        layout = []
        layout.append('title')
        layout.append('content')
        layout.append(FormActions(
            StrictButton('Zapisz', type='submit', css_class='btn-outline-primary btn-lg mx-1 my-3'),
            css_class='text-right',
        ))
        self.helper.layout = Layout(*layout)
