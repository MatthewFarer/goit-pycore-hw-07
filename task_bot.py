from functools import wraps
from collections import UserDict
from datetime import datetime, date, timedelta

# Colors
RED = "\033[91m"
GREEN = "\033[92m"
GRAY = "\033[90m"
BLUE = "\033[94m"
RESET = "\033[0m"


# ── Classes ──────────────────────────────────────────────────────────────────

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not self.validate_phone(value):
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)

    @staticmethod
    def validate_phone(phone):
        return phone.isdigit() and len(phone) == 10


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number):
        phone = self.find_phone(phone_number)
        if phone:
            self.phones.remove(phone)

    def edit_phone(self, old_number, new_number):
        phone = self.find_phone(old_number)
        if not phone:
            raise ValueError(f"Phone {old_number} not found in record.")
        phone.value = Phone(new_number).value

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones) or "—"
        birthday = str(self.birthday) if self.birthday else "—"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = date.today()
        upcoming = []

        for record in self.data.values():
            if not record.birthday:
                continue

            bday = record.birthday.value
            bday_this_year = bday.replace(year=today.year)

            if bday_this_year < today:
                bday_this_year = bday_this_year.replace(year=today.year + 1)

            delta_days = (bday_this_year - today).days

            if 0 <= delta_days < 7:
                congratulation_date = bday_this_year
                if congratulation_date.weekday() >= 5:
                    congratulation_date += timedelta(days=7 - congratulation_date.weekday())

                upcoming.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y"),
                })

        return upcoming


# ── Decorator ────────────────────────────────────────────────────────────────

def input_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return f"\n{RED}Contact not found.{RESET}"
        except IndexError:
            return f"\n{RED}Enter the argument for the command.{RESET}"
        except ValueError as e:
            return f"\n{RED}{e}{RESET}"
    return inner


# ── Parser ───────────────────────────────────────────────────────────────────

def parse_input(user_input):
    parts = user_input.strip().split()
    if not parts:
        return "", []
    return parts[0].lower(), parts[1:]


# ── Help ─────────────────────────────────────────────────────────────────────

def show_help():
    return f"""
{GRAY}----------
Available commands:
hello                                    - greeting
add [name] [phone]                       - add contact or phone
change [name] [old] [new]                - change phone
phone [name]                             - show phone numbers
all                                      - show all contacts
add-birthday [name] [DD.MM.YYYY]         - add birthday
show-birthday [name]                     - show birthday
birthdays                                - upcoming birthdays (7 days)
close or exit                            - exit the program
----------{RESET}
"""


# ── Command handlers ──────────────────────────────────────────────────────────

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return f"\n{GREEN}{message}{RESET}"


@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise IndexError
    name, old_phone, new_phone = args[0], args[1], args[2]
    record = book.find(name)
    if not record:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return f"\n{GREEN}Contact updated.{RESET}"


@input_error
def show_phone(args, book: AddressBook):
    if len(args) < 1:
        raise IndexError
    record = book.find(args[0])
    if not record:
        raise KeyError
    if not record.phones:
        return f"\n{RED}No phones found.{RESET}"
    phones = "; ".join(p.value for p in record.phones)
    return f"\n{GREEN}{phones}{RESET}"


def show_all(book: AddressBook):
    if not book.data:
        return f"\n{RED}No contacts saved.{RESET}"
    result = "\n".join(str(r) for r in book.data.values())
    return "\n" + result


@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise IndexError
    name, bday = args[0], args[1]
    record = book.find(name)
    if not record:
        raise KeyError
    record.add_birthday(bday)
    return f"\n{GREEN}Birthday added.{RESET}"


@input_error
def show_birthday(args, book: AddressBook):
    if len(args) < 1:
        raise IndexError
    record = book.find(args[0])
    if not record:
        raise KeyError
    if not record.birthday:
        return f"\n{RED}No birthday set for this contact.{RESET}"
    return f"\n{GREEN}{record.birthday}{RESET}"


@input_error
def birthdays(_, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return f"\n{RED}No birthdays in the next 7 days.{RESET}"
    result = "\n".join(
        f"{item['name']} — {item['congratulation_date']}" for item in upcoming
    )
    return "\n" + result


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    book = AddressBook()
    print(f"\n{BLUE}Welcome to the assistant bot!{RESET}")

    while True:
        print(show_help())

        user_input = input("\nEnter a command: ")

        if not user_input.strip():
            print(f"\n{RED}Invalid command.{RESET}")
            continue

        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print(f"\n{BLUE}Good bye!{RESET}")
            break
        elif command == "hello":
            print(f"\n{GREEN}How can I help you?{RESET}")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print(f"\n{RED}Invalid command.{RESET}")


if __name__ == "__main__":
    main()