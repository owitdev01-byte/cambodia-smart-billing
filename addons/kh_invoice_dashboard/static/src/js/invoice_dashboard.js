/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class KhInvoiceDashboard extends Component {
    static template = "kh_invoice_dashboard.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            records: [],
            loading: true,
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
            ]
        );
        this.state.loading = false;
    }

    /** Aggregated totals across all companies, used by the KPI cards + chart */
    get totals() {
        const sum = (key) => this.state.records.reduce((acc, r) => acc + (r[key] || 0), 0);
        return {
            total_invoice: sum("total_invoice"),
            draft_invoice: sum("draft_invoice"),
            posted_invoice: sum("posted_invoice"),
            paid_invoice: sum("paid_invoice"),
            overdue_invoice: sum("overdue_invoice"),
            total_sales: sum("total_sales"),
            outstanding_amount: sum("outstanding_amount"),
        };
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