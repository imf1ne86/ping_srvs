"""
* Опрос доступности серверов
* *************************
* Программа проверяет доступность серверов путём их
* пингования.
* Для работы программы требуется Python 3. Предварительно
* требуется установить необходимые библиотеки:
* $ pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org --upgrade pip
* $ pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org configparser
* Программа является кроссплатформенной. Она должна работать
* под Microsoft Windows, Linux, macOS и т.д.
*
* @author Ефремов А. В., 18.03.2026
"""

from dataclasses import dataclass
import argparse
from typing import List, Optional
import sys, configparser, time

from my_python_libs.miscellaneous import Miscellaneous
from my_python_libs.models import Constant

from networking import Networking

DELAY: float = 60 * 60 # задержка (1 час, или 3600 секунд)
is_logged: bool = True # признак логирования

@dataclass
class Mailing: # для почтовой рассылки (e-mail)
    host: str
    port: int
    subject: Optional[str] = None
    from_addr: Optional[str] = None
    to_addr: Optional[str] = None
    tls: bool = False
    user: Optional[str] = None
    password: Optional[str] = None

def parse_args(argv: List[str]):
    """
    * Разбор параметров программы
    *
    * @return Набор параметров
    """
    parser = argparse.ArgumentParser(description = "Параметры программы")
    parser.add_argument("--nolog", action = "store_true", dest = "nolog", required = False, help = "отключает любого вида логирование и уведомления")
    return parser.parse_args(argv)

def get_config() -> List[str]:
    """
    * Получение конфигурации
    *
    * @return Список серверов (хостов)
    """
    global is_logged
    SERVER_SECTION: str = "ping_servers"
    EMAIL_SECTION: str = "email"
    m_host: str = ""
    m_port: int = 25
    m_subject: Optional[str] = None
    m_from_addr: Optional[str] = None
    m_to_addr: Optional[str] = None
    m_tls: bool = False
    m_user: Optional[str] = None
    m_password: Optional[str] = None
    hosts: List[str] = []
    config = configparser.ConfigParser()
    try:
        with open(Constant.SETTINGS_FILE.value, 'r', encoding=Constant.GLOBAL_CODEPAGE.value) as f:
            config.read_file(f)
            if SERVER_SECTION in config:
                for section in config[SERVER_SECTION]:
                    hosts.append(config[SERVER_SECTION][section].strip())
                if EMAIL_SECTION in config:
                    m_sec = config[EMAIL_SECTION]
                    m_host = m_sec.get("host")
                    m_port = m_sec.getint("port", fallback = 25)
                    m_subject = m_sec.get("subject", fallback = None)
                    m_from_addr = m_sec.get("from", fallback = None)
                    m_to = m_sec.get("to", fallback = None)
                    m_tls_raw: str = m_sec.get("tls", fallback = "no").lower()
                    m_tls = True if m_tls_raw == "yes" else False
                    m_user = m_sec.get("user", fallback = None)
                    m_password = m_sec.get("password", fallback = None)
                else:
                    is_logged = False
                    Miscellaneous.print_message("Параметры почтовой рассылки не заданы.")
            else:
                Miscellaneous.print_message("Конфигурация не определена.")
    except FileNotFoundError:
        Miscellaneous.print_message(f"Ошибка: Файл настроек не найден: {Constant.SETTINGS_FILE.value}")
    except Exception as e:
        Miscellaneous.print_message(f"Ошибка при чтении файла настроек: {e}")
    return hosts, Mailing(host = m_host, port = m_port, subject = m_subject, from_addr = m_from_addr, to_addr = m_to, tls = m_tls, user = m_user, password = m_password,)

def main() -> None:
    global is_logged
    Miscellaneous.print_message("Опрос доступности серверов")
    Miscellaneous.print_message("*************************")
    args = parse_args(sys.argv[1:])
    if args.nolog:
        is_logged = False
        Miscellaneous.print_message("Логирование и уведомления отключены.")
    if Miscellaneous.is_file_readable(Constant.SETTINGS_FILE.value):
        Miscellaneous.print_message(f"Файл настроек найден: {Constant.SETTINGS_FILE.value}")
        srv, mailing = get_config()
        if len(srv) > 0:
            Miscellaneous.print_message(f"Количество отслеживаемых серверов: {len(srv)}.")
            try:
                while True:
                    bad_servers: List[str] = []
                    for s in srv:
                        Miscellaneous.print_message(f"Проверка доступности сервера {s}...")
                        is_available: bool = Networking.is_server_available(s)
                        if not is_available:
                            Miscellaneous.print_message(f"!!! Сервер {s} недоступен.")
                            bad_servers.append(s)
                        else:
                            Miscellaneous.print_message(f"Сервер {s} доступен.")
                    if len(bad_servers) > 0 and is_logged == True:
                        b_srv: str = ", ".join(bad_servers)
                        Miscellaneous.print_message(f"Итоговый список недоступных серверов: {b_srv}.")
                        Miscellaneous.print_message("Отправка электронной почты с уведомлением о проблемных серверах...")
                        is_sent: bool = Miscellaneous.send_email(
                            mailing.host, mailing.port,
                            mailing.subject,
                            f"Автоматическая рассылка. Следующие серверы на момент отправки письма недоступны в сети: {b_srv}. Они не ответили на запрос по протоколу ICMP (ping).",
                            mailing.from_addr, mailing.to_addr,
                            mailing.tls,
                            mailing.user, mailing.password
                        )
                        Miscellaneous.print_message("Письмо отправлено." if is_sent else "Ошибка отправки письма по e-mail.")
                    Miscellaneous.print_message(f"Пауза {DELAY} секунд (нажмите Cltr+C, чтобы завершить работу)...")
                    time.sleep(DELAY)
            except KeyboardInterrupt: # перехват Ctrl+C
                pass
        else:
            Miscellaneous.print_message("В конфигурации отсутствуют какие-либо серверы для проверки.")
    else:
        Miscellaneous.print_message(f"Ошибка: Файл настроек не найден: {Constant.SETTINGS_FILE.value}")
    Miscellaneous.print_message("Завершение работы программы.")
    return

# Точка запуска программы
if __name__ == "__main__":
    main()
