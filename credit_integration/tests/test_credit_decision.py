import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse


@pytest.mark.django_db
def test_get_credit_decisions_endpoint(
    client,
    user_factory,
    credit_decision_reason_factory,
    business_credit_decision_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()
    client.login(username=user.username, password=password)

    permission_names = [
        "view_creditdecision",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    business_id = "1234567-8"
    business_credit_decision_factory(
        business_id=business_id,
        reasons=(credit_decision_reason_factory(), credit_decision_reason_factory()),
    )

    data = {"business_id": business_id}
    response = client.get(
        reverse("credit_integration:get-credit-decisions"), data=data, format="json"
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_get_credit_decisions_without_access_right(
    client,
    user_factory,
    credit_decision_reason_factory,
    business_credit_decision_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()
    client.login(username=user.username, password=password)

    business_id = "1234567-8"
    business_credit_decision_factory(
        business_id=business_id,
        reasons=(credit_decision_reason_factory(), credit_decision_reason_factory()),
    )

    data = {"business_id": business_id}
    response = client.get(
        reverse("credit_integration:get-credit-decisions"), data=data, format="json"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_send_credit_decision_inquiry_endpoint(
    client,
    user_factory,
    credit_decision_reason_factory,
    business_credit_decision_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()

    permission_names = [
        "send_creditdecision_inquiry",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username=user.username, password=password)

    business_id = "1234567-8"
    business_credit_decision_factory(
        business_id=business_id,
        reasons=(credit_decision_reason_factory(), credit_decision_reason_factory()),
    )

    data = {"business_id": business_id}
    response = client.post(
        reverse("credit_integration:send-credit-decision-inquiry"),
        data=data,
        format="json",
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_send_credit_decision_inquiry_endpoint_without_access_right(
    client,
    user_factory,
    credit_decision_reason_factory,
    business_credit_decision_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()

    client.login(username=user.username, password=password)

    business_id = "1234567-8"
    business_credit_decision_factory(
        business_id=business_id,
        reasons=(credit_decision_reason_factory(), credit_decision_reason_factory()),
    )

    data = {"business_id": business_id}
    response = client.post(
        reverse("credit_integration:send-credit-decision-inquiry"),
        data=data,
        format="json",
    )

    assert response.status_code == 403
