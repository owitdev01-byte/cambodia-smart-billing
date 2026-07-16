/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { formatMonetary } from "@web/views/fields/formatters";

export class KhInvoiceDashboard extends Component {
    static template = "kh_invoice_dashboard.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            records: [],
            loading: true,
            rateMap: {},   // { currency_id: rate }  — rate relative to Odoo's common base currency
            khrId: false,  // res.currency id for KHR, once resolved
        });
        this.chartCanvas = useRef("chartCanvas");
        this.chart = null;

        onWillStart(async () => {
            // Odoo ships Chart.js in the backend bundle already, this just
            // guarantees it's loaded before we touch `window.Chart`.
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData();
        });

        onMounted(() => {
            this.renderChart();
        });
    }

    async loadData() {
        this.state.records = await this.orm.searchRead(
            "kh.invoice.dashboard",
            [],
            [
                "company_id",
                "total_invoice",
                "draft_invoice",
                "posted_invoice",
                "paid_invoice",
                "overdue_invoice",
                "total_sales",
                "outstanding_amount",
                "last_updated",
                "currency_id",
            ]
        );

        await this.loadCurrencyRates();
        this.state.loading = false;
    }

    /**
     * Fetches the `rate` field for every currency actually used by the records,
     * plus KHR, in one call. Odoo's `res.currency.rate` field is always expressed
     * relative to the same implicit base currency, so:
     *   converted_amount = amount * (rate_to / rate_from)
     * works regardless of which currency happens to be the "base" (rate = 1).
     */
    async loadCurrencyRates() {
        const currencyIds = new Set(
            this.state.records
                .map((r) => (r.currency_id ? r.currency_id[0] : false))
                .filter(Boolean)
        );

        // KHR may not be "active" by default in a fresh Odoo install — bypass
        // the active filter so we still find it even if it's archived.
        const khrResults = await this.orm.searchRead(
            "res.currency",
            [["name", "=", "KHR"]],
            ["id", "name", "symbol", "rate"],
            { context: { active_test: false } }
        );
        const khr = khrResults[0] || null;
        this.state.khrId = khr ? khr.id : false;
        if (khr) {
            currencyIds.add(khr.id);
        }

        if (currencyIds.size === 0) {
            this.state.rateMap = {};
            return;
        }

        const rates = await this.orm.searchRead(
            "res.currency",
            [["id", "in", [...currencyIds]]],
            ["id", "rate"],
            { context: { active_test: false } }
        );
        this.state.rateMap = Object.fromEntries(rates.map((r) => [r.id, r.rate]));
    }

    /** Formats a number as money using the row's own currency (falls back to plain number) */
    formatMoney(amount, rec) {
        const currencyId = rec && rec.currency_id ? rec.currency_id[0] : false;
        if (!currencyId) {
            return amount.toLocaleString();
        }
        return formatMonetary(amount, { currencyId });
    }

    /** Formats a number as Khmer Riel (៛), no decimals, thousands-separated */
    formatKHR(amount) {
        const rounded = Math.round(amount || 0);
        return "៛" + rounded.toLocaleString("en-US");
    }

    /** Converts `amount` (in `fromCurrencyId`) into KHR using live rates. Returns null if not resolvable. */
    convertToKHR(amount, fromCurrencyId) {
        const khrId = this.state.khrId;
        if (!khrId || !fromCurrencyId) {
            return null;
        }
        const fromRate = this.state.rateMap[fromCurrencyId];
        const khrRate = this.state.rateMap[khrId];
        if (!fromRate || !khrRate) {
            return null;
        }
        return amount * (khrRate / fromRate);
    }

    /** KHR equivalent for a single record's total_sales / outstanding_amount */
    khrFor(rec, key) {
        const currencyId = rec.currency_id ? rec.currency_id[0] : false;
        const converted = this.convertToKHR(rec[key] || 0, currencyId);
        return converted === null ? null : this.formatKHR(converted);
    }

    /** Timestamp shown in the print-only header */
    get generatedAt() {
        return new Date().toLocaleString();
    }

    /** Aggregated totals across all companies, used by the KPI cards + chart */
    get totals() {
        const sum = (key) => this.state.records.reduce((acc, r) => acc + (r[key] || 0), 0);

        // Convert each record to KHR individually, THEN sum — summing raw
        // amounts across different currencies first would be meaningless.
        const sumKHR = (key) =>
            this.state.records.reduce((acc, r) => {
                const currencyId = r.currency_id ? r.currency_id[0] : false;
                const converted = this.convertToKHR(r[key] || 0, currencyId);
                return acc + (converted || 0);
            }, 0);

        return {
            total_invoice: sum("total_invoice"),
            draft_invoice: sum("draft_invoice"),
            posted_invoice: sum("posted_invoice"),
            paid_invoice: sum("paid_invoice"),
            overdue_invoice: sum("overdue_invoice"),
            total_sales: sum("total_sales"),
            outstanding_amount: sum("outstanding_amount"),
            total_sales_khr: sumKHR("total_sales"),
            outstanding_amount_khr: sumKHR("outstanding_amount"),
        };
    }

    /** Native-currency formatted total, using the first record's currency as a display default */
    formatTotal(key) {
        const rec = this.state.records[0];
        if (!rec) {
            return this.totals[key].toLocaleString();
        }
        return this.formatMoney(this.totals[key], rec);
    }

    renderChart() {
        if (!this.chartCanvas.el || typeof Chart === "undefined") {
            return;
        }
        if (this.chart) {
            this.chart.destroy();
        }
        const t = this.totals;
        this.chart = new Chart(this.chartCanvas.el, {
            type: "doughnut",
            data: {
                labels: ["Draft", "Posted", "Paid", "Overdue"],
                datasets: [
                    {
                        data: [t.draft_invoice, t.posted_invoice, t.paid_invoice, t.overdue_invoice],
                        backgroundColor: ["#f6c343", "#4a90d9", "#3ac47d", "#d92550"],
                        borderWidth: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom" },
                },
            },
        });
    }

    async onRefresh() {
        this.state.loading = true;
        await this.loadData();
        this.renderChart();
    }

    onPrint() {
        // Uses the @media print rules in invoice_dashboard.scss to hide
        // the navbar/control panel and print only the dashboard content.
        window.print();
    }
}

registry.category("actions").add("kh_invoice_dashboard_client_action", KhInvoiceDashboard);