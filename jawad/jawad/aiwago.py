import json
import frappe
import base64
from werkzeug.wrappers import Response, Request
import json
from frappe.utils import now_datetime

from frappe.model.mapper import get_mapped_doc
from frappe.utils import now_datetime
from werkzeug.wrappers import Response
import frappe
import json


@frappe.whitelist(allow_guest=False)
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
            "mobile_no": data.get("phone"),
        },
        fields=["name"],
        limit=1,
    )

    existing_email_customer = frappe.get_all(
        "Customer",
        filters={
            "email_id": data.get("email"),
        },
        fields=["name"],
        limit=1,
    )
    exsisting_business_details = frappe.get_all(
        "businessDetails",
        filters={
            "title": data.get("name"),
            "vatnumber": data.get("vat_number"),
            "crnumber": data.get("cr_number"),
        },
        fields=["name"],
        limit=1,
    )
    if exsisting_business_details:
        return Response(
            json.dumps(
                {
                    "error": f"A business with this name and VAT/CR number already exists: {data.get('name')}"
                }
            ),
            status=400,
            mimetype="application/json",
        )
    if existing_customer:
        return Response(
            json.dumps(
                {
                    "error": f"A customer with this phone number already exists: {data.get('phone')}"
                }
            ),
            status=400,
            mimetype="application/json",
        )

    if existing_email_customer:
        return Response(
            json.dumps(
                {
                    "error": f"A customer with this email address already exists: {data.get('email')}"
                }
            ),
            status=400,
            mimetype="application/json",
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


@frappe.whitelist(allow_guest=False)
def delete_customer():
    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    customer_id = data.get("customer_id")
    if not customer_id:
        return Response(
            json.dumps({"error": "customer_id is required."}),
            status=400,
            mimetype="application/json",
        )

    if not frappe.db.exists("Customer", customer_id):
        return Response(
            json.dumps({"error": f"Customer '{customer_id}' does not exist."}),
            status=404,
            mimetype="application/json",
        )

    try:

        customer = frappe.get_doc("Customer", customer_id)
        user_email = customer.email_id

        frappe.delete_doc("Customer", customer_id, ignore_permissions=True)

        if user_email and frappe.db.exists("User", user_email):
            frappe.delete_doc("User", user_email, ignore_permissions=True)

        return Response(
            json.dumps(
                {
                    "message": f"Customer '{customer_id}' and linked user deleted successfully."
                }
            ),
            status=200,
            mimetype="application/json",
        )

    except Exception as e:
        frappe.log_error(str(e), "Delete Customer and User Error")
        return Response(
            json.dumps({"error": f"Failed to delete: {str(e)}"}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=False)
def create_item():
    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    item_code = data.get("item_code")
    if not item_code:
        return Response(
            json.dumps({"error": "item_code is required."}),
            status=400,
            mimetype="application/json",
        )

    existing_item = frappe.db.exists("Item", {"item_code": item_code})

    if existing_item:
        item = frappe.get_doc("Item", existing_item)
        return Response(
            json.dumps({"error": f"Item with item_code {item_code} already exists."}),
            status=400,
            mimetype="application/json",
        )
    else:
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": item_code,
                "item_group": "Products",
                "custom_company": data.get("company"),
            }
        )
        message = "Item created successfully"

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

    item.insert(ignore_permissions=True)

    channel_catsubcats = [
        {
            "channelid": row.channelid,
            "categoryid": row.categoryid,
            "subcategoryid": row.subcategoryid,
        }
        for row in item.custom_channelcatsubcat
    ]

    media_urls = [m.media for m in item.custom_subcatimg]

    response_data = {
        "id": item.name,
        "name": item.name,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "description": item.description,
        "nameAr": item.custom_name_arabic,
        "nameHi": item.custom_namehi,
        "nameUr": item.custom_nameur,
        "descriptionAr": item.custom_descriptionar,
        "descriptionHi": item.custom_descriptionhi,
        "descriptionUr": item.custom_descriptionur,
        "brand": item.custom_brand_id,
        "channelCatSubCat": channel_catsubcats,
        "subcatimg": media_urls,
    }

    return Response(
        json.dumps({"message": message, "data": response_data}),
        status=200,
        mimetype="application/json",
    )


@frappe.whitelist(allow_guest=False)
def update_item():

    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    item_code = data.get("item_code")
    if not item_code:
        return Response(
            json.dumps({"error": "item_code is required."}),
            status=400,
            mimetype="application/json",
        )

    existing_item = frappe.db.exists("Item", {"item_code": item_code})
    if not existing_item:
        return Response(
            json.dumps({"error": f"Item with item_code '{item_code}' does not exist."}),
            status=404,
            mimetype="application/json",
        )

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
            item.append(
                "custom_subcatimg",
                {
                    "doctype": "media",
                    "media": url,
                },
            )

    item.save(ignore_permissions=True)

    channel_catsubcats = [
        {
            "channelid": row.channelid,
            "categoryid": row.categoryid,
            "subcategoryid": row.subcategoryid,
        }
        for row in item.custom_channelcatsubcat
    ]

    media_urls = [m.media for m in item.custom_subcatimg]

    response_data = {
        "id": item.name,
        "name": item.name,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "description": item.description,
        "nameAr": item.custom_name_arabic,
        "nameHi": item.custom_namehi,
        "nameUr": item.custom_nameur,
        "descriptionAr": item.custom_descriptionar,
        "descriptionHi": item.custom_descriptionhi,
        "descriptionUr": item.custom_descriptionur,
        "brand": item.custom_brand_id,
        "channelCatSubCat": channel_catsubcats,
        "subcatimg": media_urls,
    }

    return Response(
        json.dumps({"message": "Item updated successfully", "data": response_data}),
        status=200,
        mimetype="application/json",
    )


@frappe.whitelist(allow_guest=False)
def delete_item():
    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    item_code = data.get("item_code")
    if not item_code:
        return Response(
            json.dumps({"error": "item_code is required."}),
            status=400,
            mimetype="application/json",
        )

    if not frappe.db.exists("Item", {"item_code": item_code}):
        return Response(
            json.dumps({"error": f"Item with code '{item_code}' does not exist."}),
            status=404,
            mimetype="application/json",
        )

    try:

        item_name = frappe.db.get_value("Item", {"item_code": item_code}, "name")

        frappe.delete_doc("Item", item_name, ignore_permissions=True)

        return Response(
            json.dumps({"message": f"Item '{item_code}' deleted successfully."}),
            status=200,
            mimetype="application/json",
        )

    except Exception as e:
        frappe.log_error(str(e), "Delete Item Error")
        return Response(
            json.dumps({"error": f"Failed to delete Item: {str(e)}"}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=False)
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


@frappe.whitelist(allow_guest=False)
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
                "warehouse": item.get("warehouse", "Stores - A"),
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


@frappe.whitelist(allow_guest=False)
def create_invoice():
    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    sales_order_id = data.get("sales_order")
    if not sales_order_id:
        return Response(
            json.dumps({"error": "Sales Order ID is required"}),
            status=400,
            mimetype="application/json",
        )

    try:

        doc = get_mapped_doc(
            "Sales Order",
            sales_order_id,
            {
                "Sales Order": {
                    "doctype": "Sales Invoice",
                    "field_map": {
                        "name": "sales_order",
                        "transaction_date": "posting_date",
                    },
                },
                "Sales Order Item": {
                    "doctype": "Sales Invoice Item",
                    "field_map": {"name": "so_detail", "parent": "sales_order"},
                },
            },
            ignore_permissions=True,
        )

        doc.customer = data.get("user_id", doc.customer)
        doc.due_date = now_datetime()

        doc.insert(ignore_permissions=True)
        response_data = {
            "invoice_name": doc.name,
            "customer": doc.customer,
            "due_date": str(doc.due_date),
            "grand_total": doc.grand_total,
            "items": [
                {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "rate": item.rate,
                    "amount": item.amount,
                }
                for item in doc.items
            ],
        }

        return Response(
            json.dumps(
                {"message": "Invoice created successfully", "data": response_data}
            ),
            status=200,
            mimetype="application/json",
        )

    except Exception as e:
        frappe.log_error(message=str(e), title="Create Invoice Failed")
        return e


@frappe.whitelist(allow_guest=False)
def create_brand():
    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    try:

        default_company = frappe.db.get_single_value(
            "Global Defaults", "default_company"
        )
        default_warehouse = frappe.db.get_value(
            "Warehouse", {"company": default_company}, "name"
        )

        doc = frappe.get_doc(
            {
                "doctype": "Brand",
                "brand": data.get("brand_name"),
                "description": data.get("brand_description", ""),
                "brand_defaults": [
                    {
                        "company": default_company,
                        "default_warehouse": default_warehouse,
                    }
                ],
            }
        )

        doc.insert(ignore_permissions=True)
        response_data = {
            "id": doc.name,
            "brand_name": doc.name,
            "brand_description": doc.description,
            "brand_defaults": [
                {
                    "company": d.company,
                    "default_warehouse": d.default_warehouse,
                    "default_price_list": d.default_price_list,
                }
                for d in doc.brand_defaults
            ],
        }

        return Response(
            json.dumps(
                {"message": "Brand created successfully", "data": response_data}
            ),
            status=200,
            mimetype="application/json",
        )

    except Exception as e:
        frappe.log_error(str(e), "Create Brand Error")
        return Response(
            json.dumps({"error": f"Failed to create Brand: {str(e)}"}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=False)
def update_brand():
    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    brand_id = data.get("brand_id")
    if not brand_id:
        return Response(
            json.dumps({"error": "brand_id is required."}),
            status=400,
            mimetype="application/json",
        )

    if not frappe.db.exists("Brand", brand_id):
        return Response(
            json.dumps({"error": f"Brand '{brand_id}' does not exist."}),
            status=404,
            mimetype="application/json",
        )

    try:
        brand = frappe.get_doc("Brand", brand_id)
        if "brand_description" in data:
            brand.description = data.get("brand_description")

        brand.save(ignore_permissions=True)

        response_data = {
            "id": brand.name,
            "brand_name": brand.name,
            "brand_description": brand.description,
            "brand_defaults": [
                {
                    "company": d.company,
                    "default_warehouse": d.default_warehouse,
                    "default_price_list": d.default_price_list,
                }
                for d in brand.brand_defaults
            ],
        }

        return Response(
            json.dumps(
                {"message": "Brand updated successfully", "data": response_data}
            ),
            status=200,
            mimetype="application/json",
        )

    except Exception as e:
        frappe.log_error(str(e), "Update Brand Error")
        return Response(
            json.dumps({"error": f"Failed to update Brand: {str(e)}"}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=False)
def get_brand_list(id=None):
    try:
        brands = frappe.get_all(
            "Brand",
            fields=["name", "brand", "description"],
            order_by="creation desc",
            filters={"name": id} if id else None,
        )
        if not brands:
            return Response(
                json.dumps({"error": "No brands found."}),
                status=404,
                mimetype="application/json",
            )

        response_data = [
            {
                "id": brand.name,
                "brand_name": brand.brand,
                "description": brand.description,
            }
            for brand in brands
        ]

        return Response(
            json.dumps({"data": response_data}),
            status=200,
            mimetype="application/json",
        )

    except Exception as e:
        frappe.log_error(str(e), "Brand List Error")
        return Response(
            json.dumps({"error": f"Failed to fetch brands: {str(e)}"}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=False)
def delete_brand():
    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    brand_name = data.get("brand_name")
    if not brand_name:
        return Response(
            json.dumps({"error": "brand_name is required."}),
            status=400,
            mimetype="application/json",
        )

    if not frappe.db.exists("Brand", brand_name):
        return Response(
            json.dumps({"error": f"Brand '{brand_name}' does not exist."}),
            status=404,
            mimetype="application/json",
        )

    try:

        frappe.delete_doc("Brand", brand_name, ignore_permissions=True)

        return Response(
            json.dumps({"message": f"Brand '{brand_name}' deleted successfully."}),
            status=200,
            mimetype="application/json",
        )

    except Exception as e:
        frappe.log_error(str(e), "Delete Brand Error")
        return Response(
            json.dumps({"error": f"Failed to delete Brand: {str(e)}"}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=False)
def get_item_list(id=None):
    try:

        filters = {}
        if id:
            filters["name"] = id

        item_names = frappe.get_all("Item", filters=filters, pluck="name")
        if not item_names:
            return Response(
                json.dumps({"error": "No items found."}),
                status=404,
                mimetype="application/json",
            )
        items = []
        for name in item_names:
            item = frappe.get_doc("Item", name)

            channel_catsubcats = [
                {
                    "channelid": row.channelid,
                    "categoryid": row.categoryid,
                    "subcategoryid": row.subcategoryid,
                }
                for row in item.custom_channelcatsubcat
            ]

            media_urls = [m.media for m in item.custom_subcatimg]

            item_data = {
                "id": item.name,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "description": item.description,
                "nameAr": item.custom_name_arabic,
                "nameHi": item.custom_namehi,
                "nameUr": item.custom_nameur,
                "descriptionAr": item.custom_descriptionar,
                "descriptionHi": item.custom_descriptionhi,
                "descriptionUr": item.custom_descriptionur,
                "brand": item.custom_brand_id,
                "channelCatSubCat": channel_catsubcats,
                "subcatimg": media_urls,
            }

            items.append(item_data)

        return Response(
            json.dumps({"data": items}),
            status=200,
            mimetype="application/json",
        )

    except Exception as e:
        return Response(
            json.dumps({"error": f"Error: {str(e)}"}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=False)
def update_customer():
    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    customer_id = data.get("customer_email")
    if not customer_id:
        return Response(
            json.dumps({"error": "Missing required field: customer_email"}),
            status=400,
            mimetype="application/json",
        )

    try:
        customer_email = frappe.db.get_value(
            "Customer",
            {"email_id": customer_id},
        )
        customer = frappe.get_doc("Customer", customer_email)
    except frappe.DoesNotExistError:
        return Response(
            json.dumps({"error": f"Customer with ID {customer_id} not found."}),
            status=404,
            mimetype="application/json",
        )

    update_values = {}

    if data.get("name"):
        update_values["customer_name"] = data.get("name")
    if data.get("phone"):
        update_values["mobile_no"] = data.get("phone")
    if data.get("email"):
        update_values["email_id"] = data.get("email")
    if data.get("country_code"):
        update_values["custom_country_code"] = data.get("country_code")
    if data.get("added_type"):
        update_values["custom_addedtype"] = data.get("added_type")
    if data.get("user_id"):
        update_values["custom_user_id_copy"] = data.get("user_id")
    if data.get("channel_id"):
        update_values["custom_channelid"] = data.get("channel_id")
    if data.get("classification"):
        update_values["custom_classification"] = data.get("classification")
    if data.get("profile_image"):
        update_values["custom_profile_image"] = data.get("profile_image")
    if data.get("first_name"):
        update_values["custom_first_name"] = data.get("first_name")
    if data.get("last_name"):
        update_values["custom_last_name"] = data.get("last_name")
    if data.get("address"):
        update_values["customer_primary_address"] = data.get("address")

    if not update_values:
        return Response(
            json.dumps({"error": "No valid fields provided for update."}),
            status=400,
            mimetype="application/json",
        )

    customer.update(update_values)
    customer.save(ignore_permissions=True)

    if customer.email_id:
        user_name = frappe.db.get_value("User", {"email": customer.email_id})
        if user_name:
            user_doc = frappe.get_doc("User", user_name)
            user_updates = {}

            if data.get("first_name"):
                user_updates["first_name"] = data.get("first_name")
            if data.get("last_name"):
                user_updates["last_name"] = data.get("last_name")
            if data.get("email"):
                user_updates["email"] = data.get("email")
            if data.get("phone"):
                user_updates["mobile_no"] = data.get("phone")

            if user_updates:
                user_doc.update(user_updates)
                user_doc.save(ignore_permissions=True)

    frappe.db.commit()

    return Response(
        json.dumps({"message": "Customer and User updated successfully."}),
        status=200,
        mimetype="application/json",
    )
