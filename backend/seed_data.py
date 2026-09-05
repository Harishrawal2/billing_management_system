import asyncio
from datetime import datetime, timedelta, timezone
from prisma import Prisma
from backend.app.services.billing_service import calculate_invoice_totals, calculate_item_totals
from backend.app.schemas.invoice import InvoiceItemCreate

async def seed_data(db: Prisma = None):
    should_disconnect = False
    if db is None:
        db = Prisma()
        await db.connect()
        should_disconnect = True

    try:
        # Check if already seeded
        client_count = await db.client.count()
        if client_count > 0:
            print("PostgreSQL database already contains records. Skipping seed.")
            return

        print("Seeding initial billing data into PostgreSQL using Prisma...")
        
        # 1. Clients
        c1 = await db.client.create(data={
            "name": "Sarah Jenkins",
            "company": "Nexus Dynamic Labs",
            "email": "sarah.j@nexusdynamics.io",
            "phone": "+1 (415) 890-1234",
            "address": "500 Howard St, Suite 400, San Francisco, CA 94105",
            "tax_id": "US-CA-8921820",
        })

        c2 = await db.client.create(data={
            "name": "David Thorne",
            "company": "Horizon Health Network",
            "email": "d.thorne@horizonhealth.org",
            "phone": "+1 (212) 745-6670",
            "address": "750 3rd Avenue, Floor 14, New York, NY 10017",
            "tax_id": "US-NY-4481093",
        })

        c3 = await db.client.create(data={
            "name": "Elena Rostova",
            "company": "Aura Creative Agency",
            "email": "elena@auracreative.design",
            "phone": "+1 (312) 650-8912",
            "address": "220 N Green St, Chicago, IL 60607",
            "tax_id": "US-IL-3391024",
        })

        c4 = await db.client.create(data={
            "name": "Michael Chang",
            "company": "Vanguard FinTech Group",
            "email": "mchang@vanguardfin.com",
            "phone": "+1 (512) 309-8811",
            "address": "401 Congress Ave, Suite 2100, Austin, TX 78701",
            "tax_id": "US-TX-9981240",
        })

        # 2. Products / Services
        p1 = await db.product.create(data={
            "name": "Cloud Infrastructure & DevOps Setup",
            "sku": "SRV-DEVOPS-01",
            "description": "Kubernetes cluster setup, CI/CD pipeline automation, and monitoring configuration",
            "unit_price": 2500.0,
            "tax_rate": 10.0,
            "unit": "project",
        })

        p2 = await db.product.create(data={
            "name": "Full-Stack Web App Development",
            "sku": "SRV-DEV-HR",
            "description": "Senior full-stack engineering hours (Python, FastAPI, React)",
            "unit_price": 120.0,
            "tax_rate": 10.0,
            "unit": "hour",
        })

        p3 = await db.product.create(data={
            "name": "UI/UX Design System & Prototyping",
            "sku": "SRV-UIUX-01",
            "description": "High-fidelity Figma prototypes, component library, and user flow documentation",
            "unit_price": 1800.0,
            "tax_rate": 10.0,
            "unit": "module",
        })

        p4 = await db.product.create(data={
            "name": "Monthly Enterprise Support Retainer",
            "sku": "RET-MONTHLY-01",
            "description": "24/7 SLA, security patches, system health audits, and priority incident response",
            "unit_price": 950.0,
            "tax_rate": 5.0,
            "unit": "month",
        })

        p5 = await db.product.create(data={
            "name": "API Security & Penetration Audit",
            "sku": "SRV-SEC-AUDIT",
            "description": "Comprehensive penetration testing, vulnerability assessment, and compliance report",
            "unit_price": 3200.0,
            "tax_rate": 10.0,
            "unit": "audit",
        })

        now = datetime.now(timezone.utc)

        # Helper to create invoice with Prisma
        async def create_seeded_invoice(
            inv_num: str,
            client_id: int,
            issue_dt: datetime,
            due_dt: datetime,
            items_cfg: list,
            status_val: str,
            paid_val: float = 0.0,
            payment_info: dict = None
        ):
            items_create = [
                InvoiceItemCreate(
                    product_id=p["prod"].id,
                    description=p["prod"].name,
                    quantity=p["qty"],
                    unit_price=p["prod"].unit_price,
                    tax_rate=p["prod"].tax_rate,
                    discount=p.get("discount", 0.0),
                )
                for p in items_cfg
            ]

            totals = calculate_invoice_totals(
                items_data=items_create,
                discount_type="PERCENTAGE",
                discount_value=0.0,
                current_paid=paid_val
            )

            inv_items_data = []
            for item_in in items_create:
                _, _, line_tot = calculate_item_totals(item_in)
                inv_items_data.append({
                    "product_id": item_in.product_id,
                    "description": item_in.description,
                    "quantity": item_in.quantity,
                    "unit_price": item_in.unit_price,
                    "tax_rate": item_in.tax_rate,
                    "discount": item_in.discount,
                    "line_total": line_tot
                })

            inv = await db.invoice.create(
                data={
                    "invoice_number": inv_num,
                    "client_id": client_id,
                    "status": status_val,
                    "issue_date": issue_dt,
                    "due_date": due_dt,
                    "subtotal": totals["subtotal"],
                    "discount_type": "PERCENTAGE",
                    "discount_value": 0.0,
                    "discount_amount": 0.0,
                    "tax_amount": totals["tax_amount"],
                    "total_amount": totals["total_amount"],
                    "paid_amount": paid_val,
                    "balance_due": totals["balance_due"],
                    "payment_terms": "Net 30",
                    "notes": "Thank you for your business! Payment is appreciated within 30 days.",
                    "items": {
                        "create": inv_items_data
                    }
                }
            )

            if payment_info and paid_val > 0:
                await db.payment.create(
                    data={
                        "invoice_id": inv.id,
                        "amount": paid_val,
                        "payment_date": payment_info.get("date", now),
                        "payment_method": payment_info.get("method", "BANK_TRANSFER"),
                        "reference_number": payment_info.get("ref", "TRX-AUTO-01"),
                        "notes": payment_info.get("notes", "Payment received via wire transfer")
                    }
                )

            return inv

        # Invoice 1: PAID (Nexus Dynamic Labs)
        await create_seeded_invoice(
            inv_num="INV-2026-0001",
            client_id=c1.id,
            issue_dt=now - timedelta(days=45),
            due_dt=now - timedelta(days=15),
            items_cfg=[
                {"prod": p1, "qty": 1},  # $2500 + 10% = 2750
                {"prod": p2, "qty": 15}, # $1800 + 10% = 1980
            ],
            status_val="PAID",
            paid_val=4730.0,
            payment_info={"date": now - timedelta(days=20), "method": "BANK_TRANSFER", "ref": "WIRE-NX-99120"}
        )

        # Invoice 2: PARTIAL (Horizon Health)
        await create_seeded_invoice(
            inv_num="INV-2026-0002",
            client_id=c2.id,
            issue_dt=now - timedelta(days=25),
            due_dt=now + timedelta(days=5),
            items_cfg=[
                {"prod": p3, "qty": 1}, # 1800 + 10% = 1980
                {"prod": p4, "qty": 2}, # 1900 + 5% = 1995
            ],
            status_val="PARTIAL",
            paid_val=2000.0,
            payment_info={"date": now - timedelta(days=10), "method": "CARD", "ref": "CC-AUTH-88219"}
        )

        # Invoice 3: SENT (Pending payment) (Aura Creative)
        await create_seeded_invoice(
            inv_num="INV-2026-0003",
            client_id=c3.id,
            issue_dt=now - timedelta(days=10),
            due_dt=now + timedelta(days=20),
            items_cfg=[
                {"prod": p5, "qty": 1}, # 3200 + 10% = 3520
            ],
            status_val="SENT",
            paid_val=0.0
        )

        # Invoice 4: OVERDUE (Vanguard FinTech)
        await create_seeded_invoice(
            inv_num="INV-2026-0004",
            client_id=c4.id,
            issue_dt=now - timedelta(days=50),
            due_dt=now - timedelta(days=10),
            items_cfg=[
                {"prod": p2, "qty": 20}, # 2400 + 10% = 2640
            ],
            status_val="OVERDUE",
            paid_val=0.0
        )

        print("PostgreSQL seeded with realistic billing records via Prisma successfully!")
    except Exception as e:
        print(f"Error seeding data: {e}")
        raise
    finally:
        if should_disconnect:
            await db.disconnect()

if __name__ == "__main__":
    asyncio.run(seed_data())
