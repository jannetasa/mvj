from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import NameModel


class RuleMaker(NameModel):
    pass


class RuleType(NameModel):
    pass


class Rule(models.Model):
    """
    In Finnish: Päätös
    """
    # In Finnish: Päättäjä
    rule_maker = models.ForeignKey(RuleMaker, verbose_name=_("Rule maker"), on_delete=models.PROTECT)

    # In Finnish: Päätöspäivämäärä
    rule_date = models.DateField(verbose_name=_("Rule date"))

    # In Finnish: Pykälä
    rule_clause = models.CharField(verbose_name=_("Rule clause"), max_length=255)

    # In Finnish: Päätöksen tyyppi
    rule_type = models.ForeignKey(RuleType, verbose_name=_("Rule type"), on_delete=models.PROTECT)

    # In Finnish: Selite
    rule_description = models.TextField(verbose_name=_("Rule description"))
