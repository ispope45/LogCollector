import re
import pandas as pd
from .constants import DEVICE_FORM, VALID_PARSE


class AppModel:
    def __init__(self):
        self.main_df = pd.DataFrame()

    def excel_to_df(self, excel_src):
        try:
            df = pd.read_excel(excel_src, usecols=range(0, 8))
            if len(df.columns) == len(DEVICE_FORM.keys()):
                df.columns = DEVICE_FORM.keys()
                for c in ["HOSTNAME", "IPADDR", "USERNAME", "PASSWORD", "ENABLE", "PLATFORM"]:
                    df[c] = df[c].astype(str).str.strip()
                invalid_index, data = self.valid_dataframe(df)
                return invalid_index, data, {"res": True}
            return [], pd.DataFrame(), {"res": False}
        except Exception as e:
            print(f"excel_to_df Error : {e}")
            return [], pd.DataFrame(), {"res": False}

    def valid_dataframe(self, df):
        df["PLATFORM"] = df["PLATFORM"].str.upper()
        df.loc[:, "is_valid"] = df.apply(self.validate_row, axis=1)
        invalid_index = df.query("is_valid == False").index.tolist()
        return invalid_index, df[df["is_valid"]].drop(columns=["is_valid"])

    def validate_row(self, row):
        return all([
            bool(re.match(VALID_PARSE["HOSTNAME"], str(row["HOSTNAME"]))),
            bool(re.match(VALID_PARSE["IPADDR"],   str(row["IPADDR"]))),
            row["PORT"] in range(1, 65534),
            bool(re.match(VALID_PARSE["USERNAME"], str(row["USERNAME"]))),
            bool(re.match(VALID_PARSE["PASSWORD"], str(row["PASSWORD"]))),
            bool(re.match(VALID_PARSE["ENABLE"],   str(row["ENABLE"]))),
            bool(re.match(VALID_PARSE["PLATFORM"], str(row["PLATFORM"]))),
        ])
