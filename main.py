#!/usr/bin/env python3
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

# python3.13.exe c:/Users/Janez/Desktop/etoro_t212_edavki/main.py c:/Users/Janez/Desktop/etoro_t212_edavki/etoro.xml c:/Users/Janez/Desktop/etoro_t212_edavki/t212.xml

# Define namespaces
NAMESPACE = "http://edavki.durs.si/Documents/Schemas/Doh_KDVP_9.xsd"
EDP_NAMESPACE = "http://edavki.durs.si/Documents/Schemas/EDP-Common-1.xsd"
ET.register_namespace("", NAMESPACE)  # Default namespace
ET.register_namespace("edp", EDP_NAMESPACE)  # edp namespace

def apply_edp_prefix(elem, parent=None):
    """
    Recursively applies the 'edp:' namespace prefix to required elements,
    but ensures <DocumentWorkflowID> inside <Doh_KDVP> does NOT have 'edp:'.
    """
    edp_tags = {"Header", "taxpayer", "taxNumber", "taxpayerType",
                "Workflow", "AttachmentList", "Signatures", "bodyContent"}

    for subelem in list(elem):  # Iterate through child elements
        tag_name = subelem.tag.split("}")[-1]  # Extract tag name without namespace

        # Apply 'edp:' prefix to required elements
        if tag_name in edp_tags:
            subelem.tag = f"{{{EDP_NAMESPACE}}}{tag_name}"  # Apply edp namespace

        # Special case: <DocumentWorkflowID> should be prefixed ONLY inside <edp:Header>
        if tag_name == "DocumentWorkflowID":
            if parent is not None and parent.tag.endswith("Workflow"):  
                subelem.tag = f"{{{EDP_NAMESPACE}}}DocumentWorkflowID"  # Keep edp prefix
            else:
                subelem.tag = f"{{{NAMESPACE}}}DocumentWorkflowID"  # Remove edp prefix for <KDVP>

        # Recursively process child elements
        apply_edp_prefix(subelem, parent=subelem)  # Pass current element as parent



def remove_namespaces(elem):
    """
    Recursively strip any existing namespaces from the passed element.
    """
    for e in elem.iter():
        if '}' in e.tag:
            e.tag = e.tag.split('}', 1)[1]  # keep text after first '}'

def parse_date(row_elem):
    """
    Extracts and parses date from either a <Purchase> or <Sale> element.
    """
    purchase = row_elem.find('.//Purchase')
    sale = row_elem.find('.//Sale')

    if purchase is not None:
        date_str = purchase.find('F1').text.strip()
    elif sale is not None:
        date_str = sale.find('F6').text.strip()
    else:
        date_str = "9999-12-31"

    return date_str, datetime.strptime(date_str, "%Y-%m-%d")

def recompute_f8_and_relabel(rows):
    """
    Recalculates <F8> values (running quantity) and updates <ID> tags.
    """
    running_qty = 0.0
    for i, row in enumerate(rows):
        id_elem = row.find('ID')
        if id_elem is None:
            id_elem = ET.SubElement(row, 'ID')
        id_elem.text = str(i)

        purchase = row.find('Purchase')
        sale = row.find('Sale')

        if purchase is not None:
            f3 = float(purchase.find('F3').text)
            running_qty += f3
        elif sale is not None:
            f7 = float(sale.find('F7').text)
            running_qty -= f7

        f8_elem = row.find('F8')
        if f8_elem is None:
            f8_elem = ET.SubElement(row, 'F8')
        f8_elem.text = f"{running_qty:.8f}"

def merge_transactions(etoro_path, t212_path, merged_path, info_path, errors_path):
    try:
        # Parse eToro XML
        etoro_tree = ET.parse(etoro_path)
        etoro_root = etoro_tree.getroot()
        remove_namespaces(etoro_root)  # Remove existing namespaces

        # Parse T212 XML
        t212_tree = ET.parse(t212_path)
        t212_root = t212_tree.getroot()
        remove_namespaces(t212_root)  # Remove existing namespaces

        # Ensure Header has the edp: prefix
        header = etoro_root.find("Header")
        if header is not None:
            header.tag = f"{{{EDP_NAMESPACE}}}Header"

        # Apply edp prefix to required tags
        apply_edp_prefix(etoro_root)

        # Merge securities from T212 into eToro
        code_to_item = {}
        etoro_kdvp_items = etoro_root.findall(".//KDVPItem")

        for item in etoro_kdvp_items:
            sec_elem = item.find(".//Securities")
            if sec_elem is not None:
                code_elem = sec_elem.find("Code")
                if code_elem is not None:
                    code = code_elem.text.strip()
                    code_to_item[code] = item

        unmatched_codes = []
        matched_codes = []
        t212_kdvp_items = t212_root.findall(".//KDVPItem")

        for t212_item in t212_kdvp_items:
            sec_elem = t212_item.find(".//Securities")
            if sec_elem is None:
                continue
            code_elem = sec_elem.find("Code")
            if code_elem is None:
                continue
            code = code_elem.text.strip()

            if code not in code_to_item:
                unmatched_codes.append(code)
                continue

            matched_codes.append(code)
            t212_rows = sec_elem.findall(".//Row")
            etoro_item = code_to_item[code]
            etoro_sec_elem = etoro_item.find(".//Securities")
            if etoro_sec_elem is None:
                continue

            etoro_rows = etoro_sec_elem.findall(".//Row")
            combined_rows = etoro_rows + t212_rows

            # Sort rows by date
            wrapped = []
            for idx, r in enumerate(combined_rows):
                date_str, dt_obj = parse_date(r)
                wrapped.append((dt_obj, idx, r))

            wrapped.sort(key=lambda x: (x[0], x[1]))
            sorted_rows = [item[2] for item in wrapped]

            # Remove old rows and add new sorted rows
            for r in etoro_rows:
                etoro_sec_elem.remove(r)
            for r in t212_rows:
                parent = r.find('..')
                if parent is not None and parent != etoro_sec_elem:
                    parent.remove(r)

            recompute_f8_and_relabel(sorted_rows)

            for r in sorted_rows:
                etoro_sec_elem.append(r)

        # Write info
        with open(info_path, 'w', encoding='utf-8') as wf:
            for code in matched_codes:
                wf.write(f"Matched code {code} in eToro\n")
        # write errors
        with open(errors_path, 'w', encoding='utf-8') as wf:
            for code in unmatched_codes:
                wf.write(f"No match for code {code} in eToro\n")

        # Save the final merged XML
        etoro_tree.write(merged_path, encoding='utf-8', xml_declaration=True)
    
    except Exception as e:
        print(f"Error during merge process: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} etoro.xml t212.xml")
        print(f"example: {sys.argv[0]} c:/Users/Janez/Desktop/etoro_t212_edavki/etoro.xml c:/Users/Janez/Desktop/etoro_t212_edavki/t212.xml")
        sys.exit(1)

    etoro_xml = sys.argv[1]
    t212_xml = sys.argv[2]
    
    # Generate output paths in /output subdirectory
    base_dir = os.path.dirname(etoro_xml)
    output_dir = os.path.join(base_dir, "output")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    merged_xml = os.path.join(output_dir, "merged.xml")
    info_log = os.path.join(output_dir, "info.log")
    errors_log = os.path.join(output_dir, "errors.log")

    merge_transactions(etoro_xml, t212_xml, merged_xml, info_log, errors_log)
    print("Done merging.")
    print(f"Merged XML: {merged_xml}")
    print(f"Info:   {info_log}")
    print(f"Errors: {errors_log}")

if __name__ == "__main__":
    main()
