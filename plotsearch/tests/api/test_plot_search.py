import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from faker import Faker
from rest_framework import serializers

from forms.models import Form, Section
from leasing.enums import PlotSearchTargetType
from leasing.models import PlanUnit
from plotsearch.enums import SearchClass
from plotsearch.models import AreaSearch, PlotSearch, PlotSearchTarget

fake = Faker("fi_FI")


@pytest.mark.django_db
def test_plot_search_detail(
    django_db_setup,
    admin_client,
    plan_unit_factory,
    plot_search_test_data,
    lease_test_data,
):
    # Attach plan unit for plot search
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )
    PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )

    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert (
        response.data["plot_search_targets"][0]["lease_identifier"]
        == lease_test_data["lease"].identifier.identifier
    )


@pytest.mark.django_db
def test_plot_search_list(django_db_setup, admin_client, plot_search_test_data):

    url = reverse("plotsearch-list")

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert response.data["count"] > 0


@pytest.mark.django_db
def test_plot_search_create_simple(
    django_db_setup, admin_client, plot_search_test_data, lease_test_data,
):
    url = reverse("plotsearch-list")  # list == create

    data = {
        "name": get_random_string(),
    }

    response = admin_client.post(
        url, json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_plot_search_create(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    user_factory,
    plan_unit_factory,
):
    url = reverse("plotsearch-list")  # list == create

    # Add preparer
    user = user_factory(username="test_user")

    # Add master plan unit
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    data = {
        "name": get_random_string(),
        "subtype": plot_search_test_data.subtype.id,
        "stage": plot_search_test_data.stage.id,
        "preparer": user.id,
        "begin_at": timezone.now() + timezone.timedelta(days=30),
        "end_at": timezone.now() + timezone.timedelta(days=60),
        "search_class": SearchClass.PLOT_SEARCH,
        "plot_search_targets": [
            {
                "plan_unit_id": plan_unit.id,
                "target_type": PlotSearchTargetType.SEARCHABLE.value,
            },
        ],
    }

    response = admin_client.post(
        url, json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)
    assert len(response.data["plot_search_targets"]) > 0


@pytest.mark.django_db
def test_plot_search_update(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    user_factory,
    plan_unit_factory,
):
    url = reverse(
        "plotsearch-detail", kwargs={"pk": plot_search_test_data.id}
    )  # detail == update

    # Add preparer
    user = user_factory(username="test_user")

    # Add exist target
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )
    PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )

    # Add new master plan unit
    new_master_plan_unit = plan_unit_factory(
        identifier="PU2",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    updated_end_at = plot_search_test_data.end_at + timezone.timedelta(days=30)

    data = {
        "name": get_random_string(),
        "subtype": plot_search_test_data.subtype.id,
        "stage": plot_search_test_data.stage.id,
        "preparer": user.id,
        "begin_at": plot_search_test_data.begin_at,
        "end_at": updated_end_at,
        "search_class": SearchClass.OTHER,
        "plot_search_targets": [
            {
                "plan_unit_id": new_master_plan_unit.id,
                "target_type": PlotSearchTargetType.DIRECT_RESERVATION.value,
            },
        ],
    }

    response = admin_client.put(url, data=data, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert response.data["end_at"] == serializers.DateTimeField().to_representation(
        updated_end_at
    )
    assert len(response.data["plot_search_targets"]) == 1


@pytest.mark.django_db
def test_plot_search_delete_target(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    user_factory,
    plan_unit_factory,
):
    url = reverse(
        "plotsearch-detail", kwargs={"pk": plot_search_test_data.id}
    )  # detail == update

    # Add preparer
    user = user_factory(username="test_user")

    # Add exist target
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )
    PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )

    updated_end_at = plot_search_test_data.end_at + timezone.timedelta(days=30)

    data = {
        "name": get_random_string(),
        "subtype": plot_search_test_data.subtype.id,
        "stage": plot_search_test_data.stage.id,
        "preparer": user.id,
        "begin_at": plot_search_test_data.begin_at,
        "end_at": updated_end_at,
        "plot_search_targets": [],
    }

    response = admin_client.put(url, data=data, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data["plot_search_targets"]) == 0


@pytest.mark.django_db
def test_plot_search_master_plan_unit_is_deleted(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    plan_unit_factory,
):
    # Attach master plan unit for plot search
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )
    master_plan_unit_id = plan_unit.id
    PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )

    # Delete master plan unit
    PlanUnit.objects.get(pk=master_plan_unit_id).delete()

    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})
    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert not response.data["plot_search_targets"][0]["master_plan_unit_id"]
    assert response.data["plot_search_targets"][0]["is_master_plan_unit_deleted"]
    assert len(response.data["plot_search_targets"][0]["message_label"]) > 0


@pytest.mark.django_db
def test_plot_search_master_plan_unit_is_newer(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    plan_unit_factory,
):
    # Attach master plan unit for plot search
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )
    master_plan_unit_id = plan_unit.id
    PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )
    # Update master plan unit
    master_plan_unit = PlanUnit.objects.get(pk=master_plan_unit_id)
    master_plan_unit.detailed_plan_identifier = "DP1"
    master_plan_unit.save()

    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})
    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert response.data["plot_search_targets"][0]["master_plan_unit_id"] > 0
    assert response.data["plot_search_targets"][0]["is_master_plan_unit_newer"]
    assert len(response.data["plot_search_targets"][0]["message_label"]) > 0


@pytest.mark.django_db
def test_plot_search_master_plan_unit_is_deleted_change_to_new(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    plan_unit_factory,
):
    # Create base master plan units
    master_plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )
    master_plan_unit_id = master_plan_unit.id
    master_plan_unit2 = plan_unit_factory(
        identifier="PU2",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    # Create new master plan unit
    master_plan_unit3 = plan_unit_factory(
        identifier="PU3",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    # Create plot search target, master plan unit will be duplicated on this
    PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data,
        plan_unit=master_plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )
    duplicated_plan_unit_id = master_plan_unit.id
    plot_search_target2 = PlotSearchTarget.objects.create(
        plot_search=plot_search_test_data,
        plan_unit=master_plan_unit2,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )

    # Delete master plan unit which has duplicated to plot search target
    PlanUnit.objects.get(pk=master_plan_unit_id).delete()

    # Get plot search detail
    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})
    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    # Confirm that the master plan unit has deleted
    assert response.data["plot_search_targets"][0]["is_master_plan_unit_deleted"]

    # Change to new plan unit
    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})
    response.data.pop("type")
    response.data.pop("plot_search_targets")
    response.data["plot_search_targets"] = [
        {
            "id": plot_search_target2.id,
            "plan_unit_id": plot_search_target2.plan_unit.id,
            "target_type": plot_search_target2.target_type.value,
        },
        {
            "plan_unit_id": master_plan_unit3.id,
            "target_type": PlotSearchTargetType.SEARCHABLE.value,
        },
    ]

    response = admin_client.put(
        url, data=json.dumps(response.data), content_type="application/json"
    )
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data["plot_search_targets"]) == 2

    # Confirm that the old duplicated plan unit has been deleted
    assert PlanUnit.objects.filter(id=duplicated_plan_unit_id).count() == 0


@pytest.mark.django_db
def test_attach_form_to_plot_search(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    form_factory,
    section_factory,
    field_factory,
    field_type_factory,
):
    form = form_factory(
        name=fake.name(),
        description=fake.sentence(),
        is_template=True,
        title=fake.name(),
    )
    parent_section = section_factory(form=form,)
    child_section = section_factory(form=form, parent=parent_section,)
    field_type = field_type_factory(name=fake.name(), identifier=slugify(fake.name()))
    field_factory(
        label=fake.name(),
        hint_text=fake.name(),
        identifier=slugify(fake.name()),
        validation=fake.name(),
        action=fake.name(),
        section=child_section,
        type=field_type,
    )
    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})
    response = admin_client.patch(
        url, data={"form": form.id}, content_type="application/json"
    )
    assert response.status_code == 200
    assert len(Form.objects.all()) == 2
    assert (
        len(Section.objects.filter(form=Form.objects.exclude(id=form.id).first())) == 2
    )
    assert (
        len(Section.objects.filter(form=Form.objects.filter(id=form.id).first())) == 2
    )
    assert len(Section.objects.all()) == 4

    url = reverse("plotsearch-list")
    response = admin_client.post(
        url,
        data={"name": "Test name", "form": form.id},
        content_type="application/json",
    )
    assert response.status_code == 201
    assert len(Form.objects.all()) == 3
    assert (
        len(Section.objects.filter(form=Form.objects.filter(id=form.id).first())) == 2
    )
    assert len(Section.objects.all()) == 6

    plot_search_id = response.data["id"]

    new_form = form_factory(
        name=fake.name(),
        description=fake.sentence(),
        is_template=True,
        title=fake.name(),
    )
    parent_section = section_factory(form=new_form,)
    child_section = section_factory(form=new_form, parent=parent_section,)
    field_type = field_type_factory(name=fake.name(), identifier=slugify(fake.name()))
    field_factory(
        label=fake.name(),
        hint_text=fake.name(),
        identifier=slugify(fake.name()),
        validation=fake.name(),
        action=fake.name(),
        section=child_section,
        type=field_type,
    )

    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_id})
    response = admin_client.patch(
        url, data={"form": new_form.id}, content_type="application/json"
    )
    assert response.status_code == 200
    assert len(Form.objects.all()) == 4
    assert len(Form.objects.filter(is_template=True)) == 2
    assert len(Form.objects.filter(is_template=False)) == 2
    assert (
        len(Section.objects.filter(form=Form.objects.filter(id=form.id).first())) == 2
    )
    assert len(Section.objects.all()) == 8


@pytest.mark.django_db
def test_attach_decision_to_plot_search(
    django_db_setup,
    admin_client,
    plot_search_test_data,
    lease_test_data,
    decision_factory,
):
    lease = lease_test_data["lease"]

    decision = decision_factory(lease=lease)

    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_test_data.id})
    response = admin_client.patch(
        url,
        data={"decisions": [decision.id,]},  # noqa: E231
        content_type="application/json",
    )
    assert response.status_code == 200
    plot_search_test_data = PlotSearch.objects.get(id=plot_search_test_data.id)
    assert plot_search_test_data.decisions.all()[0].id == decision.id

    url = reverse("plotsearch-list")
    response = admin_client.post(
        url,
        data={"name": "Test name", "decisions": [decision.id,]},  # noqa: E231
        content_type="application/json",
    )
    assert response.status_code == 201
    plot_search_test_data = PlotSearch.objects.get(id=response.data["id"])
    assert plot_search_test_data.decisions.all()[0].id == decision.id


@pytest.mark.django_db
def test_add_target_info_link(
    django_db_setup, admin_client, plot_search_target,
):

    target_info_link_data = {
        "url": fake.uri(),
        "description": fake.sentence(),
        "language": "fi",
    }

    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_target.plot_search.id})
    response = admin_client.get(url)
    assert response.status_code == 200
    payload = response.data
    payload["plot_search_targets"][0]["info_links"].append(target_info_link_data)
    response = admin_client.patch(url, data=payload, content_type="application/json",)
    assert response.status_code == 200

    link_found = False
    for info_link in response.data["plot_search_targets"][0]["info_links"]:
        if "url" in info_link and info_link["url"] == target_info_link_data["url"]:
            link_found = True
            break

    assert link_found


@pytest.mark.django_db
def test_getting_and_editing_and_deleting_existing_info_link(
    django_db_setup,
    admin_client,
    plot_search_target,
    info_link_factory,
    plan_unit_factory,
    lease_test_data,
):
    # add some info links into plot_search_target
    for i in range(3):
        info_link_factory(
            plot_search_target=plot_search_target,
            url=fake.uri(),
            description=fake.sentence(),
            language=["fi", "en", "sv"][i],
        )

    # Fetch info links via api
    url = reverse("plotsearch-detail", kwargs={"pk": plot_search_target.plot_search.id})
    response = admin_client.get(url)
    assert response.status_code == 200

    # choose one info link for editing
    reference_info_link = plot_search_target.info_links.first()
    info_links = response.data["plot_search_targets"][0]["info_links"]
    new_uri = fake.uri()
    for link in info_links:
        if link["id"] == reference_info_link.id:
            # edit url of chosen link
            link["url"] = new_uri

    # patch the list of links with one edited link
    payload = response.data
    payload["plot_search_targets"][0]["info_links"] = info_links
    response = admin_client.patch(url, data=payload, content_type="application/json")
    assert response.status_code == 200

    # check if chosen links url has changed and delete from list (for upcoming delete check)
    has_updated = False
    info_links = response.data["plot_search_targets"][0]["info_links"]
    for link in info_links:
        if link["id"] == reference_info_link.id and link["url"] == new_uri:
            has_updated = True
            del info_links[list.index(info_links, link)]
            break

    assert has_updated

    payload = response.data
    payload["plot_search_targets"][0]["info_links"] = info_links
    # delete reference info link and check it is removed
    response = admin_client.patch(url, data=payload, content_type="application/json")

    assert response.status_code == 200
    is_deleted = True
    for link in response.data["plot_search_targets"][0]["info_links"]:
        if link["id"] == reference_info_link.id:
            is_deleted = False
            break

    assert is_deleted

    master_plan_unit2 = plan_unit_factory(
        identifier="PU2",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    # test with simple payload
    payload = {
        "plot_search_targets": [
            {
                # "plot_search_id": response.data["id"],
                "plan_unit_id": master_plan_unit2.id,
                "target_type": response.data["plot_search_targets"][0]["target_type"],
                "info_links": [
                    {
                        "url": "https://google.com",
                        "description": "foo",
                        "language": "fi",
                    }
                ],
            }
        ]
    }

    response = admin_client.patch(url, data=payload, content_type="application/json")
    assert response.status_code == 200


@pytest.mark.django_db
def test_area_search_detail(
    django_db_setup, admin_client, area_search_test_data,
):
    url = reverse("areasearch-detail", kwargs={"pk": area_search_test_data.id})

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_area_search_list(django_db_setup, admin_client, area_search_test_data):

    url = reverse("areasearch-list")

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert response.data["count"] > 0


@pytest.mark.django_db
def test_area_search_create_simple(
    django_db_setup, admin_client, field_type_factory, area_search_test_data
):
    url = reverse("areasearch-list")  # list == create

    data = {
        "description_area": get_random_string(),
        "description_intended_use": get_random_string(),
        "intended_use": area_search_test_data.intended_use.pk,
        "geometry": area_search_test_data.geometry.geojson,
    }

    field_type_factory(id=1, name=fake.name(), identifier=slugify(fake.name()))
    field_type_factory(id=4, name=fake.name(), identifier=slugify(fake.name()))
    field_type_factory(id=6, name=fake.name(), identifier=slugify(fake.name()))

    response = admin_client.post(
        url, json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json"
    )
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)
    assert AreaSearch.objects.filter(id=response.data["id"]).exists()
    assert (
        AreaSearch.objects.get(id=response.data["id"]).intended_use.id
        == area_search_test_data.intended_use.pk
    )
