import logging
from typing import List, Dict, Union

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404

from .forms import UploadFileForm
from .models import AccountData, Accounts, UploadedFile
from .utils import format_sum, process_excel_file


def custom_sort(
    data: List[Dict[str, Union[int, str]]]
) -> List[Dict[str, Union[int, str]]]:
    sorted_data = sorted(data, key=lambda x: (
        int(str(x['account_number'])[:2]),
        int(str(x['account_number'])[2:])
        if len(str(x['account_number'])) > 2 else float('inf'),
        str(x['account_number'])
    ))
    return sorted_data


def initialize_class_sums() -> Dict[str, Dict[str, int]]:
    return {str(i): {
        'incoming_active': 0,
        'incoming_passive': 0,
        'debit_turnover': 0,
        'credit_turnover': 0,
        'outgoing_active': 0,
        'outgoing_passive': 0
    } for i in range(1, 10)}


def get_class_descriptions() -> Dict[str, str]:
    return {
        '1': 'Денежные средства, драгоценные металлы и межбанковские операции',
        '2': 'Кредитные и иные активные операции с клиентами',
        '3': 'Счета по операциям клиентов',
        '4': 'Ценные бумаги',
        '5': 'Долгосрочные финансовые вложения в уставные'
             'фонды юридических лиц, основные средства и прочее имущество',
        '6': 'Прочие активы и прочие пассивы',
        '7': 'Собственный капитал банка',
        '8': 'Доходы банка',
        '9': 'Расходы банка',
    }


def process_entry(entry, class_sums, class_description):
    """
    Обработка записи и обновление сумм по классам.
    """
    class_block = str(entry.account.class_block)
    class_sums[class_block]['incoming_active'] += entry.incoming_active or 0
    class_sums[class_block]['incoming_passive'] += entry.incoming_passive or 0
    class_sums[class_block]['debit_turnover'] += entry.debit_turnover or 0
    class_sums[class_block]['credit_turnover'] += entry.credit_turnover or 0
    class_sums[class_block]['outgoing_active'] += entry.outgoing_active or 0
    class_sums[class_block]['outgoing_passive'] += entry.outgoing_passive or 0


def add_class_summary(data, class_block, class_sums):
    """
    Добавление сводной информации по классу в данные.
    """
    data.append({
        'account_number': 'ПО КЛАССУ',
        'class_block': class_block,
        'is_header': True,
        'incoming_active': format_sum(
            class_sums[class_block]['incoming_active']),
        'incoming_passive': format_sum(
            class_sums[class_block]['incoming_passive']),
        'debit_turnover': format_sum(
            class_sums[class_block]['debit_turnover']),
        'credit_turnover': format_sum(
            class_sums[class_block]['credit_turnover']),
        'outgoing_active': format_sum(
            class_sums[class_block]['outgoing_active']),
        'outgoing_passive': format_sum(
            class_sums[class_block]['outgoing_passive']),
    })


def add_class_header(data, class_block, class_descriptions):
    """
    Добавление заголовка по классу в данные.
    """
    data.append({
        'account_number':
        f'КЛАСС {class_block} {class_descriptions.get(class_block, "")}',
        'class_block': None,
        'is_header': True,
        'incoming_active': None,
        'incoming_passive': None,
        'debit_turnover': None,
        'credit_turnover': None,
        'outgoing_active': None,
        'outgoing_passive': None,
    })


def add_data_entry(data, entry):
    """
    Добавление записи данных.
    """
    data.append({
        'account_number': entry.account.account_number,
        'class_block': entry.account.class_block,
        'incoming_active': format_sum(entry.incoming_active),
        'incoming_passive': format_sum(entry.incoming_passive),
        'debit_turnover': format_sum(entry.debit_turnover),
        'credit_turnover': format_sum(entry.credit_turnover),
        'outgoing_active': format_sum(entry.outgoing_active),
        'outgoing_passive': format_sum(entry.outgoing_passive),
        'is_header': False,
    })


def get_data(request):
    """
    Получение данных в JSON.
    """
    data = []
    file_id = request.GET.get('file_id')
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)

    current_class_block = None
    class_sums = initialize_class_sums()
    class_descriptions = get_class_descriptions()

    for entry in AccountData.objects.filter(file=uploaded_file):
        process_entry(entry, class_sums, class_descriptions)

        class_block = str(entry.account.class_block)
        if class_block != current_class_block:
            if current_class_block is not None:
                if any(
                    len(str(data_entry['account'])) == 2
                    for data_entry in data
                    if not data_entry['is_header']
                    and data_entry['class_block'] == current_class_block
                ):
                    add_class_summary(data, current_class_block, class_sums)

            add_class_header(data, class_block, class_descriptions)
            current_class_block = class_block

        if len(str(entry.account)) == 2:
            process_entry(entry, class_sums, class_descriptions)

        add_data_entry(data, entry)

    if current_class_block is not None:
        if any(
            len(str(data_entry['account'])) == 2
            for data_entry in data
            if not data_entry['is_header']
            and data_entry['class_block'] == current_class_block
        ):
            add_class_summary(data, current_class_block, class_sums)

    total_balance = {
        'account': 'БАЛАНС',
        'class_block': 'ВСЕ',
        'is_header': True,
        'incoming_active': format_sum(
            sum(entry['incoming_active'] for entry in class_sums.values())
        ),
        'incoming_passive': format_sum(
            sum(entry['incoming_passive'] for entry in class_sums.values())
        ),
        'debit_turnover': format_sum(
            sum(entry['debit_turnover'] for entry in class_sums.values())
        ),
        'credit_turnover': format_sum(
            sum(entry['credit_turnover'] for entry in class_sums.values())
        ),
        'outgoing_active': format_sum(
            sum(entry['outgoing_active'] for entry in class_sums.values())
        ),
        'outgoing_passive': format_sum(
            sum(entry['outgoing_passive'] for entry in class_sums.values())
        ),
    }
    data.append(total_balance)

    return JsonResponse({'data': data}, safe=False)


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                uploaded_file_obj = process_excel_file(request.FILES['file'])
                return redirect('uploaded_files')
            except Exception as e:
                logging.error(f"Ошибка обработки файла: {e}")
                return HttpResponse(
                    "Ошибка обработки файла. Пожалуйста, проверьте логи."
                    )
    else:
        form = UploadFileForm()

    return render(request, 'excel_app/upload_file.html', {'form': form})


def uploaded_files(request):
    files = UploadedFile.objects.all()
    return render(request, 'excel_app/uploaded_files.html', {'files': files})


def view_data(request, file_id):
    file = UploadedFile.objects.get(pk=file_id)
    account_obj, created = Accounts.objects.get_or_create(
        account_number=file.file_name
    )
    data = AccountData.objects.filter(account=account_obj)

    return render(request, 'excel_app/view_data.html',
                  {'file': file, 'data': data})
