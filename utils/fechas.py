from datetime import date, datetime

_FORMATOS_ENTRADA = (
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%d',
    '%d/%m/%Y %H:%M',
    '%d/%m/%Y',
)


def _parsear_fecha(valor):
    if valor is None or valor == '':
        return None
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, date):
        return datetime(valor.year, valor.month, valor.day)
    if isinstance(valor, str):
        texto = valor.strip().split('.')[0]
        for fmt in _FORMATOS_ENTRADA:
            try:
                return datetime.strptime(texto, fmt)
            except ValueError:
                continue
    return None


def _formatear(valor, con_hora=False):
    dt = _parsear_fecha(valor)
    if dt is None:
        return '-' if valor is None or valor == '' else str(valor)
    if con_hora:
        return dt.strftime('%d/%m/%Y %H:%M')
    return dt.strftime('%d/%m/%Y')


def format_fecha(valor):
    """Solo fecha: DD/MM/YYYY."""
    return _formatear(valor, con_hora=False)


def format_fecha_hora(valor):
    """Fecha y hora: DD/MM/YYYY HH:MM (sin segundos)."""
    return _formatear(valor, con_hora=True)
