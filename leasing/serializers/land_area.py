from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.models import ConstructabilityDescription, Decision
from leasing.models.land_area import (
    LeaseAreaAddress,
    LeaseAreaAttachment,
    PlanUnitIntendedUse,
    PlotDivisionState,
)
from leasing.serializers.decision import DecisionSerializer
from users.models import User
from users.serializers import UserSerializer

from ..models import LeaseArea, PlanUnit, PlanUnitState, PlanUnitType, Plot
from .utils import (
    FileSerializerMixin,
    InstanceDictPrimaryKeyRelatedField,
    NameModelSerializer,
    UpdateNestedMixin,
)


class PlanUnitTypeSerializer(NameModelSerializer):
    class Meta:
        model = PlanUnitType
        fields = "__all__"


class PlanUnitStateSerializer(NameModelSerializer):
    class Meta:
        model = PlanUnitState
        fields = "__all__"


class PlanUnitIntendedUseSerializer(NameModelSerializer):
    class Meta:
        model = PlanUnitIntendedUse
        fields = "__all__"


class PlotDivisionStateSerializer(NameModelSerializer):
    class Meta:
        model = PlotDivisionState
        fields = "__all__"


class PublicPlanUnitSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    plan_unit_status = serializers.CharField(read_only=True)
    decisions = DecisionSerializer(
        many=True, source="lease_area.lease.decisions", allow_null=True, required=False
    )

    class Meta:
        model = PlanUnit
        fields = (
            "id",
            "identifier",
            "area",
            "section_area",
            "in_contract",
            "is_master",
            "decisions",
            "plot_division_identifier",
            "plot_division_date_of_approval",
            "plot_division_effective_date",
            "detailed_plan_identifier",
            "detailed_plan_latest_processing_date",
            "detailed_plan_latest_processing_date_note",
            "plot_division_state",
            "plan_unit_type",
            "plan_unit_state",
            "plan_unit_status",
            "plan_unit_intended_use",
            "geometry",
        )


class PlanUnitSerializer(
    FieldPermissionsSerializerMixin, PublicPlanUnitSerializer,
):
    def override_permission_check_field_name(self, field_name):
        if field_name == "decisions" and self.context["request"].user.has_perm(
            "leasing.view_decision"
        ):
            return "id"
        return field_name

    class Meta:
        model = PlanUnit
        fields = (
            "id",
            "identifier",
            "area",
            "section_area",
            "in_contract",
            "is_master",
            "decisions",
            "plot_division_identifier",
            "plot_division_date_of_approval",
            "plot_division_effective_date",
            "plot_division_state",
            "detailed_plan_identifier",
            "detailed_plan_latest_processing_date",
            "detailed_plan_latest_processing_date_note",
            "plan_unit_type",
            "plan_unit_state",
            "plan_unit_status",
            "plan_unit_intended_use",
            "geometry",
        )


class PlanUnitCreateUpdateSerializer(
    EnumSupportSerializerMixin,
    UpdateNestedMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    plan_unit_type = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlanUnitType,
        queryset=PlanUnitType.objects.filter(),
        related_serializer=PlanUnitTypeSerializer,
        allow_null=True,
        required=False,
    )
    plan_unit_state = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlanUnitState,
        queryset=PlanUnitState.objects.filter(),
        related_serializer=PlanUnitStateSerializer,
        allow_null=True,
        required=False,
    )
    plan_unit_intended_use = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlanUnitIntendedUse,
        queryset=PlanUnitIntendedUse.objects.filter(),
        related_serializer=PlanUnitIntendedUseSerializer,
        allow_null=True,
        required=False,
    )
    plot_division_state = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlotDivisionState,
        queryset=PlotDivisionState.objects.filter(),
        related_serializer=PlotDivisionStateSerializer,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = PlanUnit
        fields = (
            "id",
            "identifier",
            "area",
            "section_area",
            "in_contract",
            "is_master",
            "plot_division_identifier",
            "plot_division_date_of_approval",
            "plot_division_effective_date",
            "plot_division_state",
            "detailed_plan_identifier",
            "detailed_plan_latest_processing_date",
            "detailed_plan_latest_processing_date_note",
            "plan_unit_type",
            "plan_unit_state",
            "plan_unit_intended_use",
            "geometry",
        )


class PlanUnitListWithIdentifiersSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    lease_identifier = serializers.CharField(
        read_only=True, source="lease_area.lease.identifier.identifier"
    )
    lease_area_identifier = serializers.CharField(
        read_only=True, source="lease_area.identifier"
    )
    plan_unit_status = serializers.CharField(read_only=True)

    class Meta:
        model = PlanUnit
        fields = (
            "id",
            "identifier",
            "plan_unit_status",
            "lease_area_identifier",
            "lease_identifier",
        )


class PlotSerializer(
    EnumSupportSerializerMixin,
    UpdateNestedMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Plot
        fields = (
            "id",
            "identifier",
            "area",
            "section_area",
            "type",
            "registration_date",
            "repeal_date",
            "in_contract",
            "geometry",
        )


class PlotIdentifierSerializer(serializers.ModelSerializer,):
    class Meta:
        model = Plot
        fields = (
            "id",
            "identifier",
        )


class ConstructabilityDescriptionSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    user = UserSerializer(read_only=True)

    class Meta:
        model = ConstructabilityDescription
        fields = (
            "id",
            "type",
            "user",
            "text",
            "ahjo_reference_number",
            "is_static",
            "modified_at",
        )


class ConstructabilityDescriptionCreateUpdateSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    modified_at = serializers.ReadOnlyField()

    class Meta:
        model = ConstructabilityDescription
        fields = (
            "id",
            "type",
            "user",
            "text",
            "ahjo_reference_number",
            "is_static",
            "modified_at",
        )


class LeaseAreaAddressSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = LeaseAreaAddress
        fields = ("id", "address", "postal_code", "city", "is_primary")


class LeaseAreaAttachmentSerializer(
    FileSerializerMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    uploader = UserSerializer()
    file = serializers.SerializerMethodField("get_file_url")
    filename = serializers.SerializerMethodField("get_file_filename")

    class Meta:
        model = LeaseAreaAttachment
        fields = (
            "id",
            "type",
            "file",
            "filename",
            "uploader",
            "uploaded_at",
            "lease_area",
        )
        download_url_name = "leaseareaattachment-download"

    def override_permission_check_field_name(self, field_name):
        if field_name == "filename":
            return "file"

        return field_name


class LeaseAreaAttachmentCreateUpdateSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    uploader = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = LeaseAreaAttachment
        fields = ("id", "type", "file", "uploader", "uploaded_at", "lease_area")
        read_only_fields = ("uploaded_at",)


class FilterLeaseAreaPlotListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(in_contract=True) | data.filter(is_master=True)
        return super().to_representation(data)


class LeaseAreaPlotSerializer(PlotSerializer):
    class Meta:
        model = Plot
        list_serializer_class = FilterLeaseAreaPlotListSerializer
        fields = (
            "id",
            "identifier",
            "area",
            "section_area",
            "type",
            "registration_date",
            "repeal_date",
            "in_contract",
            "geometry",
        )


class LeaseAreaSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    addresses = LeaseAreaAddressSerializer(many=True, required=False, allow_null=True)
    plots = LeaseAreaPlotSerializer(many=True, required=False, allow_null=True)
    plan_units = PlanUnitSerializer(many=True, required=False, allow_null=True)
    polluted_land_planner = UserSerializer()
    constructability_descriptions = ConstructabilityDescriptionSerializer(
        many=True, required=False, allow_null=True
    )
    attachments = LeaseAreaAttachmentSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LeaseArea
        fields = (
            "id",
            "identifier",
            "area",
            "section_area",
            "addresses",
            "type",
            "location",
            "plots",
            "plan_units",
            "preconstruction_state",
            "preconstruction_estimated_construction_readiness_moment",
            "preconstruction_inspection_moment",
            "demolition_state",
            "polluted_land_state",
            "polluted_land_rent_condition_state",
            "polluted_land_rent_condition_date",
            "polluted_land_planner",
            "polluted_land_projectwise_number",
            "constructability_report_state",
            "constructability_report_investigation_state",
            "constructability_report_signing_date",
            "constructability_report_signer",
            "other_state",
            "constructability_descriptions",
            "archived_at",
            "archived_note",
            "archived_decision",
            "geometry",
            "attachments",
        )


class LeaseAreaListSerializer(LeaseAreaSerializer):
    plots = None
    plan_units = None
    constructability_descriptions = None
    attachments = None

    class Meta:
        model = LeaseArea
        fields = (
            "id",
            "identifier",
            "area",
            "section_area",
            "addresses",
            "type",
            "location",
            "archived_at",
            "archived_note",
        )


class LeaseAreaWithGeometryListSerializer(LeaseAreaListSerializer):
    class Meta:
        model = LeaseArea
        fields = (
            "id",
            "identifier",
            "area",
            "section_area",
            "addresses",
            "type",
            "location",
            "archived_at",
            "archived_note",
            "geometry",
        )


class LeaseAreaCreateUpdateSerializer(
    EnumSupportSerializerMixin,
    UpdateNestedMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    addresses = LeaseAreaAddressSerializer(many=True, required=False, allow_null=True)
    plots = PlotSerializer(many=True, required=False, allow_null=True)
    plan_units = PlanUnitCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    polluted_land_planner = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=User.objects.all(),
        related_serializer=UserSerializer,
        required=False,
        allow_null=True,
    )
    constructability_descriptions = ConstructabilityDescriptionCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    archived_decision = InstanceDictPrimaryKeyRelatedField(
        instance_class=Decision,
        queryset=Decision.objects.all(),
        related_serializer=DecisionSerializer,
        required=False,
        allow_null=True,
    )
    attachments = LeaseAreaAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = LeaseArea
        fields = (
            "id",
            "identifier",
            "area",
            "section_area",
            "addresses",
            "type",
            "location",
            "plots",
            "plan_units",
            "preconstruction_state",
            "preconstruction_estimated_construction_readiness_moment",
            "preconstruction_inspection_moment",
            "demolition_state",
            "polluted_land_state",
            "polluted_land_rent_condition_state",
            "polluted_land_rent_condition_date",
            "polluted_land_planner",
            "polluted_land_projectwise_number",
            "constructability_report_state",
            "constructability_report_investigation_state",
            "constructability_report_signing_date",
            "constructability_report_signer",
            "other_state",
            "constructability_descriptions",
            "archived_at",
            "archived_note",
            "archived_decision",
            "geometry",
            "attachments",
        )
