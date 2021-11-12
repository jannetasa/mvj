from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets

from forms.models import Answer, Choice, Field, Form, Section
from forms.serializers.form import AnswerSerializer, FormSerializer


class FormViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    # create is disabled
    # TODO: Add permission check for delete and edit functions to prevent deleting template forms (is_template = True)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_template"]
    serializer_class = FormSerializer

    def get_queryset(self):
        queryset = Form.objects.prefetch_related(
            Prefetch(
                "sections",
                queryset=Section.objects.prefetch_related(
                    Prefetch(
                        "fields",
                        queryset=Field.objects.prefetch_related(
                            Prefetch(
                                "choices",
                                queryset=Choice.objects.prefetch_related("field"),
                            )
                        ),
                    ),
                    "subsections",
                ),
            )
        )
        return queryset


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
