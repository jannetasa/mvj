from auditlog.registry import auditlog
from django.contrib.gis.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField
from safedelete.models import SafeDeleteModel

from field_permissions.registry import field_permissions
from leasing.enums import (
    ConstructabilityReportInvestigationState,
    ConstructabilityState,
    ConstructabilityType,
    LeaseAreaAttachmentType,
    LeaseAreaType,
    LocationType,
    PlanUnitStatus,
    PlotType,
    PollutedLandRentConditionState,
)
from leasing.models.lease import Lease
from leasing.models.utils import normalize_identifier
from users.models import User

from .mixins import (
    ArchivableModel,
    NameModel,
    TimeStampedModel,
    TimeStampedSafeDeleteModel,
)


class AbstractAddress(TimeStampedModel):
    # In Finnish: Osoite
    address = models.CharField(verbose_name=_("Address"), max_length=255)

    # In Finnish: Postinumero
    postal_code = models.CharField(
        verbose_name=_("Postal code"), null=True, blank=True, max_length=255
    )

    # In Finnish: Kaupunki
    city = models.CharField(
        verbose_name=_("City"), null=True, blank=True, max_length=255
    )

    class Meta:
        abstract = True


class Land(TimeStampedModel):
    """Land is an abstract class with common fields for leased land,
    real properties, unseparated parcels, and plan units.

    In Finnish: Maa-alue
    """

    # In Finnish: Tunnus
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=255)

    # In Finnish: Kokonaisala / Pinta-ala
    area = models.PositiveIntegerField(verbose_name=_("Area in square meters"))

    # In Finnish: Leikkausala
    section_area = models.PositiveIntegerField(
        verbose_name=_("Section area"), null=True, blank=True
    )

    # In Finnish: Alue
    geometry = models.MultiPolygonField(
        srid=4326, verbose_name=_("Geometry"), null=True, blank=True
    )

    class Meta:
        abstract = True

    def get_normalized_identifier(self):
        return normalize_identifier(self.identifier)


class LeaseArea(Land, ArchivableModel, SafeDeleteModel):
    """
    In Finnish: Vuokra-alue
    """

    lease = models.ForeignKey(
        Lease, on_delete=models.PROTECT, related_name="lease_areas"
    )
    type = EnumField(LeaseAreaType, verbose_name=_("Type"), max_length=30)
    # In Finnish: Sijainti (maanpäällinen, maanalainen)
    location = EnumField(LocationType, verbose_name=_("Location"), max_length=30)

    # Constructability fields
    # In Finnish: Rakentamiskelpoisuus

    # In Finnish: Selvitysaste (Esirakentaminen, johtosiirrot ja kunnallistekniikka)
    preconstruction_state = EnumField(
        ConstructabilityState,
        verbose_name=_("Preconstruction state"),
        null=True,
        blank=True,
        max_length=30,
    )
    # In Finnish: Arvioitu rakentamisvalmiusajankohta (Esirakentaminen)
    preconstruction_estimated_construction_readiness_moment = models.CharField(
        verbose_name=_("Preconstruction estimated construction readiness"),
        null=True,
        blank=True,
        max_length=255,
    )
    # In Finnish: Tarkistusajankohta (Esirakentaminen)
    preconstruction_inspection_moment = models.CharField(
        verbose_name=_("Preconstruction inspection"),
        null=True,
        blank=True,
        max_length=255,
    )

    # In Finnish: Selvitysaste (Purku)
    demolition_state = EnumField(
        ConstructabilityState,
        verbose_name=_("Demolition state"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Selvitysaste (Pilaantunut maa-alue (PIMA))
    polluted_land_state = EnumField(
        ConstructabilityState,
        verbose_name=_("Polluted land state"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Vuokraehdot (kysyminen)
    polluted_land_rent_condition_state = EnumField(
        PollutedLandRentConditionState,
        verbose_name=_("Polluted land rent condition state"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Vuokraehtojen kysymisen päivämäärä
    polluted_land_rent_condition_date = models.DateField(
        verbose_name=_("Polluted land rent condition date"), null=True, blank=True
    )

    # In Finnish: PIMA valmistelija
    polluted_land_planner = models.ForeignKey(
        User,
        verbose_name=_("User"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: ProjectWise kohdenumero
    polluted_land_projectwise_number = models.CharField(
        verbose_name=_("ProjectWise number"), null=True, blank=True, max_length=255
    )

    # In Finnish: Selvitysaste (Rakennettavuusselvitys)
    constructability_report_state = EnumField(
        ConstructabilityState,
        verbose_name=_("Constructability report state"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Rakennettavuusselvityksen tila
    constructability_report_investigation_state = EnumField(
        ConstructabilityReportInvestigationState,
        verbose_name=_("Constructability report investigation state"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Allekirjoituspäivämäärä
    constructability_report_signing_date = models.DateField(
        verbose_name=_("Constructability report signing date"), null=True, blank=True
    )

    # In Finnish: Allekirjoittaja
    constructability_report_signer = models.CharField(
        verbose_name=_("Constructability report signer"),
        null=True,
        blank=True,
        max_length=255,
    )

    # In Finnish: Selvitysaste (Muut)
    other_state = EnumField(
        ConstructabilityState,
        verbose_name=_("Other state"),
        null=True,
        blank=True,
        max_length=30,
    )

    # In Finnish: Päätös (arkistointi)
    archived_decision = models.ForeignKey(
        "leasing.Decision",
        verbose_name=_("Archived decision"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    recursive_get_related_skip_relations = ["lease"]

    def __str__(self):
        return "LeaseArea {}".format(self.type)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease area")
        verbose_name_plural = pgettext_lazy("Model name", "Lease areas")


class LeaseAreaAddress(AbstractAddress):
    lease_area = models.ForeignKey(
        LeaseArea, related_name="addresses", on_delete=models.CASCADE
    )

    # In Finnish: Ensisijainen osoite
    is_primary = models.BooleanField(verbose_name=_("Is primary?"), default=False)

    recursive_get_related_skip_relations = ["lease_area"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease area address")
        verbose_name_plural = pgettext_lazy("Model name", "Lease area addresses")


def get_attachment_file_upload_to(instance, filename):
    return "/".join(["lease_area_attachments", str(instance.lease_area.id), filename])


class LeaseAreaAttachment(TimeStampedSafeDeleteModel):
    """
    In Finnish: Liitetiedosto (Vuokra-alue)
    """

    lease_area = models.ForeignKey(
        LeaseArea, related_name="attachments", on_delete=models.PROTECT
    )

    # In Finnish: Tyyppi
    type = EnumField(LeaseAreaAttachmentType, verbose_name=_("Type"), max_length=30)

    # In Finnish: Tiedosto
    file = models.FileField(
        upload_to=get_attachment_file_upload_to, blank=False, null=False
    )

    # In Finnish: Lataaja
    uploader = models.ForeignKey(
        User, verbose_name=_("Uploader"), related_name="+", on_delete=models.PROTECT
    )

    # In Finnish: Latausaika
    uploaded_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Time uploaded")
    )

    recursive_get_related_skip_relations = ["lease_area", "uploader"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Lease area attachment")
        verbose_name_plural = pgettext_lazy("Model name", "Lease area attachments")


class ConstructabilityDescription(TimeStampedSafeDeleteModel):
    """
    In Finnish: Selitys (Rakentamiskelpoisuus)
    """

    lease_area = models.ForeignKey(
        LeaseArea,
        related_name="constructability_descriptions",
        on_delete=models.CASCADE,
    )
    type = EnumField(ConstructabilityType, verbose_name=_("Type"), max_length=30)
    user = models.ForeignKey(
        User, verbose_name=_("User"), related_name="+", on_delete=models.PROTECT
    )
    text = models.TextField(verbose_name=_("Text"))
    # In Finnish: AHJO diaarinumero
    ahjo_reference_number = models.CharField(
        verbose_name=_("AHJO reference number"), null=True, blank=True, max_length=255
    )
    # In Finnish: Pysyvä?
    is_static = models.BooleanField(verbose_name=_("Is static?"), default=False)

    recursive_get_related_skip_relations = ["lease_area", "user"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Constructability description")
        verbose_name_plural = pgettext_lazy(
            "Model name", "Constructability descriptions"
        )


class Plot(Land):
    """Information about a piece of land regarding a lease area.

    In Finnish: Tontti, but also possibly Määräala or Kiinteistö depending on the context.
    """

    type = EnumField(PlotType, verbose_name=_("Type"), max_length=30)
    # In Finnish: Rekisteröintipäivä
    registration_date = models.DateField(
        verbose_name=_("Registration date"), null=True, blank=True
    )
    # In Finnish: Kumoamispäivä
    repeal_date = models.DateField(verbose_name=_("Repeal date"), null=True, blank=True)
    lease_area = models.ForeignKey(
        LeaseArea, related_name="plots", on_delete=models.CASCADE
    )
    # In Finnish: Sopimushetkellä
    in_contract = models.BooleanField(
        verbose_name=_("At time of contract"), default=False
    )

    recursive_get_related_skip_relations = ["lease_area"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Plot")
        verbose_name_plural = pgettext_lazy("Model name", "Plots")


class PlanUnitType(NameModel):
    """
    In Finnish: Kaavayksikön laji
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plan unit type")
        verbose_name_plural = pgettext_lazy("Model name", "Plan unit types")


class PlotDivisionState(NameModel):
    """
    In Finnish: Tonttijaon vaihe
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plot divisions state")
        verbose_name_plural = pgettext_lazy("Model name", "Plot division states")


class PlanUnitState(NameModel):
    """
    In Finnish: Kaavayksikön olotila
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plan unit state")
        verbose_name_plural = pgettext_lazy("Model name", "Plan unit states")


class PlanUnitIntendedUse(NameModel):
    """
    In Finnish: Kaavayksikön käyttötarkoitus
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plan unit intended use")
        verbose_name_plural = pgettext_lazy("Model name", "Plan unit intended uses")


class PlanUnit(Land):
    """Plan plots are like the atoms of city plans.

    Plan plots are the plan specialization of land areas. While one
    could say that they come before the parcel specializations of land
    areas, they may be planned according to preexisting land areas.
    Plan plots differ from parcels in that they cannot be physically
    owned. Plan plots can be divided (tonttijako).

    In Finnish: Kaavayksikkö
    """

    # In Finnish: Vuokra-alue
    lease_area = models.ForeignKey(
        LeaseArea, related_name="plan_units", on_delete=models.CASCADE
    )

    # In Finnish: Sopimushetkellä
    in_contract = models.BooleanField(
        verbose_name=_("At time of contract"), default=False
    )

    # In Finnish: Tonttijaon tunnus
    plot_division_identifier = models.CharField(
        verbose_name=_("Plot division identifier"),
        max_length=255,
        null=True,
        blank=True,
    )

    # In Finnish: Tonttijaon hyväksymispvm
    plot_division_date_of_approval = models.DateField(
        verbose_name=_("Plot division date of approval"), null=True, blank=True
    )

    # In Finnish: Tonttijaon voimaantulopvm
    plot_division_effective_date = models.DateField(
        verbose_name=_("Plot division effective date"), null=True, blank=True
    )

    # In Finnish: Tonttijaon olotila
    plot_division_state = models.ForeignKey(
        PlotDivisionState,
        verbose_name=_("Plot division state"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Asemakaava
    detailed_plan_identifier = models.CharField(
        verbose_name=_("Detailed plan identifier"),
        max_length=255,
        null=True,
        blank=True,
    )

    # In Finnish: Asemakaavan viimeisin käsittelypvm
    detailed_plan_latest_processing_date = models.DateField(
        verbose_name=_("Detailed plan latest processing date"), null=True, blank=True
    )

    # In Finnish: Asemakaavan viimeisin käsittelypvm selite
    detailed_plan_latest_processing_date_note = models.TextField(
        verbose_name=_("Note for latest processing date"), null=True, blank=True
    )

    # In Finnish: Kaavayksikön laji
    plan_unit_type = models.ForeignKey(
        PlanUnitType,
        verbose_name=_("Plan unit type"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Kaavayksikön olotila
    plan_unit_state = models.ForeignKey(
        PlanUnitState,
        verbose_name=_("Plan unit state"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Kaavayksikön käyttötarkoitus
    plan_unit_intended_use = models.ForeignKey(
        PlanUnitIntendedUse,
        verbose_name=_("Plan unit intended use"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Kaavayksikön tila
    plan_unit_status = EnumField(
        PlanUnitStatus,
        verbose_name=_("Plan unit status"),
        max_length=30,
        default=PlanUnitStatus.PRESENT,
    )

    recursive_get_related_skip_relations = ["lease_area"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Plan unit")
        verbose_name_plural = pgettext_lazy("Model name", "Plan units")


auditlog.register(LeaseArea)
auditlog.register(LeaseAreaAddress)
auditlog.register(ConstructabilityDescription)
auditlog.register(Plot)
auditlog.register(PlanUnit)

field_permissions.register(LeaseArea, exclude_fields=["lease"])
field_permissions.register(LeaseAreaAddress, exclude_fields=["lease_area"])
field_permissions.register(ConstructabilityDescription, exclude_fields=["lease_area"])
field_permissions.register(Plot, exclude_fields=["lease_area"])
field_permissions.register(PlanUnit, exclude_fields=["lease_area"])
