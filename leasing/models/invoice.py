from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from auditlog.registry import auditlog
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import InvoiceDeliveryMethod, InvoiceState, InvoiceType
from leasing.models import Contact
from leasing.models.mixins import TimeStampedSafeDeleteModel


class ReceivableType(models.Model):
    """
    In Finnish: Saamislaji
    """
    name = models.CharField(verbose_name=_("Name"), max_length=255)
    sap_material_code = models.CharField(verbose_name=_("SAP material code"), null=True, blank=True, max_length=255)
    sap_order_item_number = models.CharField(verbose_name=_("SAP order item number"), null=True, blank=True,
                                             max_length=255)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Receivable type")
        verbose_name_plural = pgettext_lazy("Model name", "Receivable types")

    def __str__(self):
        return self.name


class InvoiceSet(models.Model):
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='invoicesets',
                              on_delete=models.PROTECT)
    # In Finnish: Laskutuskauden alkupvm
    billing_period_start_date = models.DateField(verbose_name=_("Billing period start date"), null=True, blank=True)

    # In Finnish: Laskutuskauden loppupvm
    billing_period_end_date = models.DateField(verbose_name=_("Billing period end date"), null=True, blank=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Invoice set")
        verbose_name_plural = pgettext_lazy("Model name", "Invoice set")

    def create_credit_invoiceset(self, receivable_type=None):
        all_invoices = self.invoices.filter(type=InvoiceType.CHARGE)

        if not all_invoices:
            raise RuntimeError('No refundable invoices found (no invoices with the type "{}" found)'.format(
                InvoiceType.CHARGE.value))

        credit_invoiceset = InvoiceSet.objects.create(
            lease=self.lease,
            billing_period_start_date=self.billing_period_start_date,
            billing_period_end_date=self.billing_period_end_date
        )

        for invoice in all_invoices:
            credit_invoice = invoice.create_credit_invoice(receivable_type=receivable_type)
            if credit_invoice:
                credit_invoiceset.invoices.add(credit_invoice)

        return credit_invoiceset

    def create_credit_invoiceset_for_amount(self, amount=None, receivable_type=None):
        if amount and not receivable_type:
            raise RuntimeError('receivable_type is required if amount is provided.')

        all_invoices = self.invoices.filter(type=InvoiceType.CHARGE)

        if not all_invoices:
            raise RuntimeError('No refundable invoices found (no invoices with the type "{}" found)'.format(
                InvoiceType.CHARGE.value))

        shares = {}
        all_shares = Fraction()

        total_row_count = InvoiceRow.objects.filter(invoice__in=all_invoices,
                                                    receivable_type=receivable_type).count()

        has_tenants = InvoiceRow.objects.filter(invoice__in=all_invoices,
                                                receivable_type=receivable_type,
                                                tenant__isnull=False).count() == total_row_count

        total_row_amount = InvoiceRow.objects.filter(
            invoice__in=all_invoices, receivable_type=receivable_type).aggregate(
                total_row_amount=Sum('amount'))['total_row_amount']

        if amount > total_row_amount:
            raise RuntimeError('Credit amount "{}" is more that total row amount "{}"!'.format(
                amount, total_row_amount))

        for invoice in all_invoices:
            if has_tenants:
                shares[invoice] = invoice.get_fraction_for_receivable_type(receivable_type)
            else:
                shares[invoice] = Fraction(
                    invoice.rows.filter(receivable_type=receivable_type).count(),
                    total_row_count)

            all_shares += shares[invoice]

        if all_shares != 1:
            raise RuntimeError('Shares together do not equal 1/1')

        credit_invoiceset = InvoiceSet.objects.create(
            lease=self.lease,
            billing_period_start_date=self.billing_period_start_date,
            billing_period_end_date=self.billing_period_end_date
        )

        for invoice, fraction in shares.items():
            invoice_credit_amount = Decimal(amount * Decimal(fraction.numerator / fraction.denominator)).quantize(
                Decimal('.01'), rounding=ROUND_HALF_UP)
            credit_invoice = invoice.create_credit_invoice(amount=invoice_credit_amount,
                                                           receivable_type=receivable_type)
            credit_invoiceset.invoices.add(credit_invoice)

        return credit_invoiceset


class Invoice(TimeStampedSafeDeleteModel):
    """
    In Finnish: Lasku
    """
    lease = models.ForeignKey('leasing.Lease', verbose_name=_("Lease"), related_name='invoices',
                              on_delete=models.PROTECT)

    invoiceset = models.ForeignKey(InvoiceSet, verbose_name=_("Invoice set"), related_name='invoices', null=True,
                                   blank=True, on_delete=models.PROTECT)

    # In Finnish: Laskun numero
    number = models.PositiveIntegerField(verbose_name=_("Number"), unique=True, null=True, blank=True)

    # In Finnish: Laskunsaaja
    recipient = models.ForeignKey(Contact, verbose_name=_("Recipient"), on_delete=models.PROTECT)

    # In Finnish: Lähetetty SAP:iin
    sent_to_sap_at = models.DateTimeField(verbose_name=_("Sent to SAP at"), null=True, blank=True)

    # In Finnish: SAP numero
    sap_id = models.CharField(verbose_name=_("SAP ID"), max_length=255, null=True, blank=True)

    # In Finnish: Eräpäivä
    due_date = models.DateField(verbose_name=_("Due date"))

    # In Finnish: Laskutuspvm
    invoicing_date = models.DateField(verbose_name=_("Invoicing date"), null=True, blank=True)

    # In Finnish: Laskun tila
    state = EnumField(InvoiceState, verbose_name=_("State"), max_length=30)

    # In Finnish: Laskutuskauden alkupvm
    billing_period_start_date = models.DateField(verbose_name=_("Billing period start date"), null=True, blank=True)

    # In Finnish: Laskutuskauden loppupvm
    billing_period_end_date = models.DateField(verbose_name=_("Billing period end date"), null=True, blank=True)

    # In Finnish: Lykkäyspvm
    postpone_date = models.DateField(verbose_name=_("Postpone date"), null=True, blank=True)

    # In Finnish: Laskun pääoma
    total_amount = models.DecimalField(verbose_name=_("Total amount"), max_digits=10, decimal_places=2)

    # In Finnish: Laskutettu määrä
    billed_amount = models.DecimalField(verbose_name=_("Billed amount"), max_digits=10, decimal_places=2)

    # In Finnish: Maksamaton määrä
    outstanding_amount = models.DecimalField(verbose_name=_("Outstanding amount"), null=True, blank=True, max_digits=10,
                                             decimal_places=2)

    # In Finnish: Maksukehotuspvm
    payment_notification_date = models.DateField(verbose_name=_("Payment notification date"), null=True, blank=True)

    # In Finnish: Perintäkulu
    collection_charge = models.DecimalField(verbose_name=_("Collection charge"), null=True, blank=True, max_digits=10,
                                            decimal_places=2)

    # In Finnish: Maksukehotus luettelo
    payment_notification_catalog_date = models.DateField(verbose_name=_("Payment notification catalog date"), null=True,
                                                         blank=True)

    # In Finnish: E vai paperilasku
    delivery_method = EnumField(InvoiceDeliveryMethod, verbose_name=_("Delivery method"), max_length=30, null=True,
                                blank=True)

    # In Finnish: Laskun tyyppi
    type = EnumField(InvoiceType, verbose_name=_("Type"), max_length=30)

    # In Finnish: Tiedote
    notes = models.TextField(verbose_name=_("Notes"), blank=True)

    generated = models.BooleanField(verbose_name=_("Is automatically generated?"), default=False)

    # In Finnish: Selite
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)

    # In Finnish: Hyvitetty lasku
    credited_invoice = models.ForeignKey('self', verbose_name=_("Credited invoice"), related_name='credited_invoices',
                                         null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Invoice")
        verbose_name_plural = pgettext_lazy("Model name", "Invoices")

    def __str__(self):
        return str(self.pk)

    def create_credit_invoice(self, row_ids=None, amount=None, receivable_type=None):
        """Create a credit note for this invoice"""
        if self.type != InvoiceType.CHARGE:
            raise RuntimeError(
                'Can not credit invoice with the type "{}". Only type "{}" allowed.'.format(
                    self.type.value if self.type else self.type, InvoiceType.CHARGE.value))

        row_queryset = self.rows.all()
        if row_ids:
            row_queryset = row_queryset.filter(id__in=row_ids)

        if receivable_type:
            row_queryset = row_queryset.filter(receivable_type=receivable_type)

        row_count = row_queryset.count()

        if not row_count:
            raise RuntimeError('No rows to credit')

        has_tenants = row_queryset.filter(tenant__isnull=False).count() == row_count

        new_denominator = None
        if has_tenants:
            new_denominator = row_queryset.aggregate(new_denominator=Sum('tenant__share_numerator'))['new_denominator']

        today = timezone.now().date()

        credit_note = Invoice.objects.create(
            lease=self.lease,
            type=InvoiceType.CREDIT_NOTE,
            recipient=self.recipient,
            due_date=self.due_date,
            invoicing_date=today,
            state=InvoiceState.OPEN,
            total_amount=self.total_amount,
            billed_amount=self.billed_amount,
            billing_period_start_date=self.billing_period_start_date,
            billing_period_end_date=self.billing_period_end_date,
            credited_invoice=self,
        )

        for invoice_row in row_queryset:
            if amount and has_tenants:
                invoice_row_amount = Decimal(
                    amount * Decimal(invoice_row.tenant.share_numerator / new_denominator)).quantize(
                        Decimal('.01'), rounding=ROUND_HALF_UP)
            elif amount:
                invoice_row_amount = amount / row_count
            else:
                invoice_row_amount = invoice_row.amount

            InvoiceRow.objects.create(
                invoice=credit_note,
                tenant=invoice_row.tenant,
                receivable_type=invoice_row.receivable_type,
                billing_period_start_date=invoice_row.billing_period_start_date,
                billing_period_end_date=invoice_row.billing_period_end_date,
                amount=invoice_row_amount,
            )

        # TODO: check if fully refunded when refunding a receivable_type
        if not row_ids and not amount and not receivable_type:
            # TODO: Set only when credit note sent to SAP?
            self.state = InvoiceState.REFUNDED
            self.save()

        return credit_note

    def get_fraction_for_receivable_type(self, receivable_type):
        fraction = Fraction()
        for row in self.rows.all():
            if row.receivable_type != receivable_type or not row.tenant:
                continue

            fraction += Fraction(row.tenant.share_numerator, row.tenant.share_denominator)

        return fraction


class InvoiceRow(TimeStampedSafeDeleteModel):
    """
    In Finnish: Rivi laskulla
    """
    invoice = models.ForeignKey(Invoice, verbose_name=_("Invoice"), related_name='rows',
                                on_delete=models.CASCADE)

    # In Finnish: Vuokralainen
    tenant = models.ForeignKey('leasing.Tenant', verbose_name=_("Tenant"), null=True, blank=True,
                               on_delete=models.PROTECT)

    # In Finnish: Saamislaji
    receivable_type = models.ForeignKey(ReceivableType, verbose_name=_("Receivable type"), on_delete=models.PROTECT)

    # In Finnish: Laskutuskauden alkupvm
    billing_period_start_date = models.DateField(verbose_name=_("Billing period start date"), null=True, blank=True)

    # In Finnish: Laskutuskauden loppupvm
    billing_period_end_date = models.DateField(verbose_name=_("Billing period end date"), null=True, blank=True)

    # In Finnish: Selite
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)

    # In Finnish: Laskutettu määrä
    amount = models.DecimalField(verbose_name=_("Amount"), max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Invoice row")
        verbose_name_plural = pgettext_lazy("Model name", "Invoice rows")


class InvoicePayment(TimeStampedSafeDeleteModel):
    """
    In Finnish: Maksusuoritus
    """
    invoice = models.ForeignKey(Invoice, verbose_name=_("Invoice"), related_name='payments',
                                on_delete=models.CASCADE)

    # In Finnish: Maksettu määrä
    paid_amount = models.DecimalField(verbose_name=_("Paid amount"), max_digits=10, decimal_places=2)

    # In Finnish Maksettu pvm
    paid_date = models.DateField(verbose_name=_("Paid date"))

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Invoice payment")
        verbose_name_plural = pgettext_lazy("Model name", "Invoice payments")


class BankHoliday(models.Model):
    day = models.DateField(verbose_name=_("Day"), unique=True, db_index=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Bank holiday")
        verbose_name_plural = pgettext_lazy("Model name", "Bank holidays")
        ordering = ("day",)

    def __str__(self):
        return str(self.day)


auditlog.register(Invoice)
auditlog.register(InvoiceRow)
auditlog.register(InvoicePayment)
