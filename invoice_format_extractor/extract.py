# extract.py

import pdfplumber
import json
import re

def clean_currency(s):
    if s is None:
        return 0.0
    return float(s.replace(',', ''))

def yield_lines_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            for line in text.split('\n'):
                yield line.strip()

def parse_and_stream_pos(pdf_path, output_path):
    """
    Parses a PO report from a PDF and writes JSON to output_path.
    """
    current_po = None
    current_item = None
    parsing_detail_description = False
    parsing_item_category = False
    is_first_record = True
    record_count = 0

    # --- Regex Patterns ---
    po_start_re = re.compile(r"^Purchase Order ([\d-]+)\s+G/L Date ([\d/]+)\s+Amount ([\d,.]+)$")
    vendor_re = re.compile(r"^Vendor \d+\s+-\s+(.+?)(?:\s+Completed Date|\s+Printed Date|$)")
    po_desc_re = re.compile(r"^Description (.*?)\s+Deliver by Date")
    item_start_re = re.compile(r"^Item (\d+)\s+Description (.*?)(?:\s+Status|$)")
    quantity_re = re.compile(r"^Quantity\s+([\d,.]+)")
    unit_price_re = re.compile(r"^Price per Unit\s+(-?[\d,.]+)")
    detail_desc_re = re.compile(r"^Detail Description\s+(.*)")
    gl_account_line_re = re.compile(r"^\d{5}-\d{4}-\d{4}-\d{4}-\d{4}")

    stopper_keywords = [
        "Purchase Order", "G/L Date Range", "Sort by", "Detail Listing",
        "Department", "Vendor", "Type", "Status", "Item", "Quantity", "U/M",
        "Price per Unit", "G/L Account", "Encumbered", "Run by", "Detail Description"
    ]

    def cleanup_item_text(item):
        if item:
            if 'description' in item and item['description']:
                item['description'] = " ".join(item['description'].split())
            if 'category' in item and item['category']:
                item['category'] = " ".join(item['category'].split())
            if item.get('quantity') is not None and item.get('unit_price') is not None:
                total = item['quantity'] * item['unit_price']
                item['total_amount'] = round(total, 2)

    with open(output_path, 'w') as f_out:
        f_out.write('[\n')

        for line in yield_lines_from_pdf(pdf_path):
            if not line:
                continue


            if current_item and parsing_item_category:
                is_stopper = any(line.startswith(kw) for kw in stopper_keywords)
                if not is_stopper:
                    current_item['category'] += " " + line
                    continue
                else:
                    parsing_item_category = False

            if current_item and parsing_detail_description:
                is_stopper = any(line.startswith(kw) for kw in stopper_keywords) or gl_account_line_re.match(line)
                if not is_stopper:
                    current_item['description'] += " " + line
                    continue
                else:
                    parsing_detail_description = False

            po_match = po_start_re.match(line)
            if po_match:
                if current_po:
                    cleanup_item_text(current_item)
                    if not is_first_record:
                        f_out.write(',\n')
                    json.dump(current_po, f_out, indent=4)
                    is_first_record = False
                    record_count += 1

                current_po = {
                    "po_number": po_match.group(1), "po_date": po_match.group(2),
                    "amount": clean_currency(po_match.group(3)), "vendor_name": None,
                    "description": None, "items": []
                }
                current_item = None
                parsing_item_category = False
                parsing_detail_description = False
                continue

            if not current_po:
                continue

            vendor_match = vendor_re.match(line)
            po_desc_match = po_desc_re.match(line)
            item_match = item_start_re.match(line)
            quantity_match = quantity_re.match(line)
            price_match = unit_price_re.match(line)
            detail_desc_match = detail_desc_re.match(line)

            if vendor_match:
                current_po["vendor_name"] = vendor_match.group(1).strip()
            elif po_desc_match and not current_po["items"]:
                current_po["description"] = po_desc_match.group(1).strip()
            elif item_match:
                cleanup_item_text(current_item)
                current_item = {
                    "line_item_number": int(item_match.group(1)),
                    "category": item_match.group(2).strip(),
                    "description": "", "quantity": None, 
                    "unit_price": None,
                    "total_amount": None
                }
                current_po["items"].append(current_item)
                parsing_item_category = True
            elif quantity_match and current_item:
                current_item["quantity"] = clean_currency(quantity_match.group(1))
            elif price_match and current_item:
                current_item["unit_price"] = clean_currency(price_match.group(1))
            elif detail_desc_match and current_item:
                parsing_detail_description = True
                desc_text = detail_desc_match.group(1).strip()
                if desc_text.endswith("Remaining .00"):
                    desc_text = desc_text[:-len("Remaining .00")].strip()
                current_item["description"] = desc_text

        if current_po:
            cleanup_item_text(current_item)
            if not is_first_record:
                f_out.write(',\n')
            json.dump(current_po, f_out, indent=4)
            record_count += 1

        f_out.write('\n]')

    return record_count