import json
import frappe
import base64
from werkzeug.wrappers import Response, Request
import json
from frappe.utils import now_datetime


@frappe.whitelist(allow_guest=True)
def create_customer():

    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    required_fields = ["name", "phone", "email", "country_code"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return Response(
            json.dumps(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}
            ),
            status=400,
            mimetype="application/json",
        )

    existing_customer = frappe.get_all(
        "Customer",
        filters={
            "name": data.get("customer_id"),
        },
        fields=["name"],
        limit=1,
    )

    business_details = frappe.get_doc(
        {
            "doctype": "businessDetails",
            "title": data.get("name"),
            "vatnumber": data.get("vat_number"),
            "addressprooffront": data.get("address_proof_front"),
            "addressproofback": data.get("address_proof_back"),
            "crdocumentfront": data.get("cr_document_front"),
            "crdocumentback": data.get("cr_document_back"),
            "crnumber": data.get("cr_number"),
            "vatdocfront": data.get("vat_doc_front"),
            "vatdocback": data.get("vat_doc_back"),
            "idprooffront": data.get("id_proof_front"),
            "idproofback": data.get("id_proof_back"),
            "shopimagefront": data.get("shop_image_front"),
            "shopimageback": data.get("shop_image_back"),
        }
    )
    business_details.insert(ignore_permissions=True)

    customer_data = {
        "customer_name": data.get("name"),
        "mobile_no": data.get("phone"),
        "email_id": data.get("email"),
        "custom_country_code": data.get("country_code"),
        "custom_addedtype": data.get("added_type"),
        "custom_user_id_copy": data.get("user_id"),
        "custom_channelid": data.get("channel_id"),
        "custom_classification": data.get("classification"),
        "custom_profile_image": data.get("profile_image"),
        "custom_first_name": data.get("first_name"),
        "custom_last_name": data.get("last_name"),
        "customer_primary_address": data.get("address"),
        "custom_business_name": business_details.name,
    }

    if existing_customer:
        customer = frappe.get_doc("Customer", existing_customer[0].name)
        customer.update(customer_data)
        customer.save(ignore_permissions=True)
        message = "Customer updated successfully"
    else:
        user = frappe.get_doc(
            {
                "doctype": "User",
                "first_name": data.get("first_name") or data.get("name"),
                "last_name": data.get("last_name"),
                "email": data.get("email"),
                "mobile_no": data.get("phone"),
                "send_welcome_email": 0,
                "user_type": "Website User",
            }
        )
        user.insert(ignore_permissions=True)
        customer = frappe.get_doc({"doctype": "Customer", **customer_data})
        customer.insert(ignore_permissions=True)
        message = "Customer created successfully"

    response_data = {
        "customer_name": customer.customer_name,
        "customer_id": customer.name,
        "mobile_no": customer.mobile_no,
        "email_id": customer.email_id,
        "country_code": customer.custom_country_code,
        "profile_image": customer.custom_profile_image,
        "classification": customer.custom_classification,
        "added_type": customer.custom_addedtype,
        "user_id": customer.custom_user_id_copy,
        "channel_id": customer.custom_channelid,
        "first_name": customer.custom_first_name,
        "last_name": customer.custom_last_name,
        "address": customer.customer_primary_address,
        "business_details": {
            "business_id": business_details.name,
            "title": business_details.title,
            "vat_number": business_details.vatnumber,
            "cr_number": business_details.crnumber,
            "documents": {
                "address_proof_front": business_details.addressprooffront,
                "address_proof_back": business_details.addressproofback,
                "cr_document_front": business_details.crdocumentfront,
                "cr_document_back": business_details.crdocumentback,
                "vat_doc_front": business_details.vatdocfront,
                "vat_doc_back": business_details.vatdocback,
                "id_proof_front": business_details.idprooffront,
                "id_proof_back": business_details.idproofback,
                "shop_image_front": business_details.shopimagefront,
                "shop_image_back": business_details.shopimageback,
            },
        },
    }

    return Response(
        json.dumps({"message": message, "data": response_data}),
        status=200,
        mimetype="application/json",
    )


@frappe.whitelist(allow_guest=True)
def create_item():

    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    item_code = data.get("skuCode")
    if not item_code:
        return Response(
            json.dumps({"error": "skuCode (item_code) is required."}),
            status=400,
            mimetype="application/json",
        )

    existing_item = frappe.db.exists("Item", {"item_code": item_code})

    if existing_item:

        item = frappe.get_doc("Item", existing_item)

        field_mapping = {
            "nameEn": "item_name",
            "brand": "custom_brand_id",
            "descriptionEn": "description",
            "nameAr": "custom_name_arabic",
            "nameHi": "custom_namehi",
            "nameUr": "custom_nameur",
            "descriptionAr": "custom_descriptionar",
            "descriptionHi": "custom_descriptionhi",
            "descriptionUr": "custom_descriptionur",
        }

        for json_key, docfield in field_mapping.items():
            if json_key in data:
                item.set(docfield, data.get(json_key))

        if "channelCatSubCat" in data:
            item.set("custom_channelcatsubcat", [])
            for row in data.get("channelCatSubCat", []):
                item.append(
                    "custom_channelcatsubcat",
                    {
                        "doctype": "channelCatSubCat",
                        "channelid": row.get("channelid"),
                        "categoryid": row.get("categoryid"),
                        "subcategoryid": row.get("subCategoryid"),
                    },
                )

        if "subCatImg" in data:
            item.set("custom_subcatimg", [])
            for url in data.get("subCatImg", []):
                item.append("custom_subcatimg", {"doctype": "media", "media": url})

        item.save(ignore_permissions=True)
        message = "Item updated successfully"

    else:

        channel_cat_sub_cat_children = (
            [
                {
                    "doctype": "channelCatSubCat",
                    "channelid": row.get("channelid"),
                    "categoryid": row.get("categoryid"),
                    "subcategoryid": row.get("subCategoryid"),
                }
                for row in data.get("channelCatSubCat", [])
            ]
            if "channelCatSubCat" in data
            else []
        )

        media_children = (
            [
                {
                    "doctype": "media",
                    "media": url,
                }
                for url in data.get("subCatImg", [])
            ]
            if "subCatImg" in data
            else []
        )

        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": item_code,
                "item_group": "Products",
            }
        )

        field_mapping = {
            "nameEn": "item_name",
            "brand": "custom_brand_id",
            "descriptionEn": "description",
            "nameAr": "custom_name_arabic",
            "nameHi": "custom_namehi",
            "nameUr": "custom_nameur",
            "descriptionAr": "custom_descriptionar",
            "descriptionHi": "custom_descriptionhi",
            "descriptionUr": "custom_descriptionur",
        }

        for json_key, docfield in field_mapping.items():
            if json_key in data:
                item.set(docfield, data.get(json_key))

        for row in channel_cat_sub_cat_children:
            item.append("custom_channelcatsubcat", row)

        for media in media_children:
            item.append("custom_subcatimg", media)

        item.insert(ignore_permissions=True)
        message = "Item created successfully"

    channel_catsubcats = [
        {
            "channelid": row.channelid,
            "categoryid": row.categoryid,
            "subcategoryid": row.subcategoryid,
        }
        for row in item.custom_channelcatsubcat
    ]

    media_urls = [m.media for m in item.media]

    response_data = {
        "name": item.name,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "description": item.description,
        "brand": item.custom_brand_id,
        "channelCatSubCat": channel_catsubcats,
        "subcatimg": media_urls,
    }

    return Response(
        json.dumps({"message": message, "data": response_data}),
        status=200,
        mimetype="application/json",
    )


@frappe.whitelist(allow_guest=True)
def create_or_update_warehouse():
    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    warehouse_name = data.get("warehouse_name")
    if not warehouse_name:
        return Response(
            json.dumps({"error": "warehouse_name is required."}),
            status=400,
            mimetype="application/json",
        )

    existing_warehouse = frappe.db.exists(
        "Warehouse", {"warehouse_name": warehouse_name}
    )

    if existing_warehouse:

        warehouse = frappe.get_doc("Warehouse", existing_warehouse)

        if "address_line_1" in data:
            warehouse.address_line_1 = data.get("address_line_1")
        if "region" in data:
            warehouse.custom_region = data.get("region")
        if "warehouse_code" in data:
            warehouse.custom_warehouse_code = data.get("warehouse_code")

        warehouse.save(ignore_permissions=True)
        message = "Warehouse updated successfully"

    else:

        warehouse = frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": warehouse_name,
                "address_line_1": data.get("address_line_1", ""),
                "custom_region": data.get("region", ""),
                "custom_warehouse_code": data.get("warehouse_code", ""),
            }
        )

        warehouse.insert(ignore_permissions=True)
        message = "Warehouse created successfully"

    warehouse_data = {
        "name": warehouse.name,
        "warehouse_name": warehouse.warehouse_name,
        "address_line_1": warehouse.address_line_1,
        "region": warehouse.custom_region,
        "warehouse_code": warehouse.custom_warehouse_code,
    }

    return Response(
        json.dumps({"message": message, "data": warehouse_data}),
        status=200,
        mimetype="application/json",
    )


@frappe.whitelist(allow_guest=True)
def create_or_update_order():
    import json
    from frappe import _

    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    if not data.get("user_id"):
        return Response(
            json.dumps({"error": "user_id is required."}),
            status=400,
            mimetype="application/json",
        )

    if not data.get("items"):
        return Response(
            json.dumps({"error": "items list is required."}),
            status=400,
            mimetype="application/json",
        )

    invoice_items = []
    for item in data.get("items", []):
        if not frappe.db.exists("Item", {"name": item["item_code"]}):
            continue

        invoice_items.append(
            {
                "item_code": item["item_code"],
                "qty": item.get("quantity", 0),
                "rate": item.get("price", 0),
                "delivery_date": item.get("delivery_date", frappe.utils.nowdate()),
                "uom": item.get("uom", "Nos"),
                "warehouse": item.get("warehouse", "All Warehouses - erp"),
            }
        )

    if not invoice_items:
        return Response(
            json.dumps({"error": "No valid items found for order."}),
            status=400,
            mimetype="application/json",
        )

    sales_team = []
    if data.get("sales_man_name"):
        sales_team.append(
            {"sales_person": data.get("sales_man_name"), "allocated_percentage": 100}
        )
    existing_order = None
    if data.get("order_id"):
        existing_order = frappe.db.exists("Sales Order", {"name": data.get("order_id")})

    if existing_order:

        order = frappe.get_doc("Sales Order", existing_order)

        order.discount_amount = data.get("discount_amount", order.discount_amount)
        order.grand_total = data.get("total", order.grand_total)
        order.coupon_code = data.get("promotion_code", order.coupon_code)
        order.branch_id = data.get("branch_id", order.branch_id)
        order.custom_orderby = data.get("orderby", order.custom_orderby)
        order.address_display = data.get("address_display", order.address_display)
        order.shipping_address = data.get("shipping_address", order.shipping_address)
        order.custom_region = data.get("region", order.custom_region)
        order.custom_payment_options = data.get(
            "payment_options", order.custom_payment_options
        )

        order.set("items", [])
        for item in invoice_items:
            order.append("items", item)

        order.set("sales_team", [])
        for sales_person in sales_team:
            order.append("sales_team", sales_person)

        order.save(ignore_permissions=True)
        message = "Sales Order updated successfully"

    else:

        order = frappe.get_doc(
            {
                "doctype": "Sales Order",
                "customer": data.get("user_id"),
                "items": invoice_items,
                "discount_amount": data.get("discount_amount", 0),
                "grand_total": data.get("total", 0),
                "coupon_code": data.get("promotion_code"),
                "custom_orderby": data.get("orderby", 1),
                "custom_region": data.get("region", ""),
                "address_display": data.get("address_display", ""),
                "shipping_address": data.get("shipping_address", ""),
                "sales_team": sales_team,
                "custom_payment_options": data.get("payment_options", "COD"),
            }
        )

        order.insert(ignore_permissions=True)
        message = "Sales Order created successfully"

    items_data = [
        {
            "item_code": i.item_code,
            "qty": i.qty,
            "rate": i.rate,
            "uom": i.uom,
            "warehouse": i.warehouse,
        }
        for i in order.items
    ]

    sales_team_data = [
        {
            "sales_person": st.sales_person,
            "allocated_percentage": st.allocated_percentage,
        }
        for st in order.sales_team
    ]

    order_data = {
        "name": order.name,
        "customer": order.customer,
        "grand_total": order.grand_total,
        "total_qty": order.total_qty,
        "discount_amount": order.discount_amount,
        "status": order.status,
        "items": items_data,
        "sales_team": sales_team_data,
        "coupon_code": order.coupon_code,
        "orderby": order.custom_orderby,
        "billing address": order.address_display,
        "shipping_address": order.shipping_address,
        "region": order.custom_region,
        "payment_options": order.custom_payment_options,
    }

    return Response(
        json.dumps({"message": message, "data": order_data}),
        status=200,
        mimetype="application/json",
    )
