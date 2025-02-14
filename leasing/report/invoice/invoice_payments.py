from django import forms
from django.utils.translation import ugettext_lazy as _
from rest_framework.response import Response

from leasing.models.invoice import InvoicePayment
from leasing.report.excel import ExcelCell, ExcelRow, SumCell
from leasing.report.report_base import ReportBase


def get_invoice_number(obj):
    return obj.invoice.number


def get_lease_id(obj):
    return obj.invoice.lease.get_identifier_string()


class InvoicePaymentsReport(ReportBase):
    name = _("Invoice payments")
    description = _(
        "Show all the payments that have been paid between the start and the end date"
    )
    slug = "invoice_payments"
    input_fields = {
        "start_date": forms.DateField(label=_("Start date"), required=True),
        "end_date": forms.DateField(label=_("End date"), required=True),
    }
    output_fields = {
        "invoice_number": {"source": get_invoice_number, "label": _("Invoice number")},
        "lease_id": {"source": get_lease_id, "label": _("Lease id")},
        "paid_date": {"label": _("Paid date"), "format": "date"},
        "paid_amount": {"label": _("Paid amount"), "format": "money", "width": 13},
        "filing_code": {"label": _("Filing code")},
    }

    def get_data(self, input_data):
        qs = (
            InvoicePayment.objects.filter(
                paid_date__gte=input_data["start_date"],
                paid_date__lte=input_data["end_date"],
            )
            .select_related(
                "invoice",
                "invoice__lease",
                "invoice__lease__identifier",
                "invoice__lease__identifier__type",
                "invoice__lease__identifier__district",
                "invoice__lease__identifier__municipality",
            )
            .order_by("paid_date")
        )

        return qs

    def get_response(self, request):
        report_data = self.get_data(self.get_input_data(request))
        serialized_report_data = self.serialize_data(report_data)

        if request.accepted_renderer.format != "xlsx":
            return Response(serialized_report_data)

        # Add totals row to xlsx output
        count = len(serialized_report_data)

        totals_row = ExcelRow()
        totals_row.cells.append(ExcelCell(column=0, value=str(_("Total"))))
        totals_row.cells.append(SumCell(column=3, target_ranges=[(0, 3, count - 1, 3)]))
        serialized_report_data.append(totals_row)

        return Response(serialized_report_data)
