import os
import pandas as pd
import pdfplumber

def convert_all_pdfs(pdf_dir):
    rows = []
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, filename)
            print(f"Processing {pdf_path}")
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                    lines = text.split('\n')
                    for line in lines:
                        # Skip header lines
                        if line.strip().startswith("MODEL NAME") or "Insurance" in line:
                            continue
                        # Heuristics: if line contains ₹ more than once, assume it's a data row
                        if line.count("₹") >= 2:
                            rows.append(parse_line(line))
    if not rows:
        print("No rows found.")
        return None

    df = pd.DataFrame(rows)
    excel_path = os.path.join(pdf_dir, "master_sheet.xlsx")
    df.to_excel(excel_path, index=False)
    print(f"Saved to {excel_path}")
    return excel_path


def parse_line(line):
    """
    Example line:
    MX1 PM MT ₹ 7,99,000 ₹ 0 ₹ 55,729 ₹ 25,000 ₹ 19,975 ₹ 15,500 ₹ 25,999 ₹ 3,020 ₹ …
    """
    parts = line.split()
    model = []
    numbers = []
    for part in parts:
        if "₹" in part or part.replace(",", "").isdigit():
            numbers.append(part)
        else:
            model.append(part)

    return {
        "Model": " ".join(model),
        "Values": " ".join(numbers)
    }
