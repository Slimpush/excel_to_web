import logging
from io import BytesIO
from typing import List, Optional

import pandas as pd

from .models import Accounts, AccountData, UploadedFile


def save_uploaded_file(uploaded_file: BytesIO) -> str:
    """
    Сохраняет загруженный файл на диск.
    """
    file_name = uploaded_file.name
    with open(file_name, 'wb') as w:
        for chunk in uploaded_file.chunks():
            w.write(chunk)
    return file_name


def process_excel_file(uploaded_file: UploadedFile) -> UploadedFile:
    """
    Обрабатывает загруженный файл Excel.
    """
    content = uploaded_file.read()
    df = pd.read_excel(
        BytesIO(content), header=None,
        skiprows=9, thousands=' ', decimal=','
    )

    uploaded_file_obj = UploadedFile.objects.create(
        file_name=uploaded_file.name
    )

    unique_accounts = get_numeric_values(df.iloc[:, 0])
    for account in unique_accounts:
        Accounts.objects.get_or_create(account_number=account)

    for _, row in df.iterrows():
        if row[0] in ["ПО КЛАССУ", "БАЛАНС"]:
            logging.warning(
                f"Skipping row with special 'Б/сч' value: {row[0]}"
            )
            continue

        process_row_data(row)

    return uploaded_file_obj


def process_row_data(row: pd.Series) -> None:
    """
    Обрабатывает данные строки Excel и создает объект AccountData.
    """
    try:
        account_obj = Accounts.objects.get(account_number=row[0])
    except Accounts.DoesNotExist:
        logging.error(
            f"Error processing file: Account {row[0]} does not exist."
        )
        return

    if not is_row_numeric(row[1:]):
        return

    incoming_active = float(row[1]) if not pd.isna(row[1]) else 0
    incoming_passive = float(row[2]) if not pd.isna(row[2]) else 0
    debit_turnover = float(row[3]) if not pd.isna(row[3]) else 0
    credit_turnover = float(row[4]) if not pd.isna(row[4]) else 0
    outgoing_active = float(row[5]) if not pd.isna(row[5]) else 0
    outgoing_passive = float(row[6]) if not pd.isna(row[6]) else 0

    AccountData.objects.create(
        account=account_obj,
        incoming_active=incoming_active,
        incoming_passive=incoming_passive,
        debit_turnover=debit_turnover,
        credit_turnover=credit_turnover,
        outgoing_active=outgoing_active,
        outgoing_passive=outgoing_passive,
    )


def format_sum(value):
    return '{:,.2f}'.format(value).replace(',', ' ')


def get_numeric_values(series: pd.Series) -> List[Optional[str]]:
    return series[pd.to_numeric(series, errors='coerce').notna()].unique()


def is_row_numeric(row: pd.Series) -> bool:
    return pd.to_numeric(row, errors='coerce').notna().all()
