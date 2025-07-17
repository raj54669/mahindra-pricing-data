def convert_all_pdfs():
    import os
    import pandas as pd
    import pdfplumber

    all_data = []

    for filename in os.listdir("price-pdfs"):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join("price-pdfs", filename)
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        df["Source File"] = filename
                        all_data.append(df)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        output_path = "PV Price List Master.xlsx"
        combined_df.to_excel(output_path, index=False)
        return output_path
    return None
