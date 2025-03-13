import questionary
from playwright._impl._errors import TargetClosedError
from questionary import Style
from rich.console import Console
from rich.table import Table

from algohealer.db.conn import SQLiteManager
from algohealer.db.enums import CATEGORIES, Category, Settings
from algohealer.navigators.instagram.instagram_navigator import InstagramNavigator

custom_style = Style(
    [
        ("qmark", "fg:#008700"),
        ("question", "fg:#00afaf"),
        ("answer", "fg:#e0ffff"),
        ("pointer", "fg:#00af87"),
        ("highlighted", "fg:#008700"),
    ]
)


class DataManager:
    NAVIGATORS = {
        "instagram": InstagramNavigator,
    }

    def __init__(self, site: str, db_conn: SQLiteManager):
        self.site = site
        self._db_conn = db_conn
        self._console = Console()

    def check_site(self) -> bool:
        chk = self.site in self.NAVIGATORS
        if not chk:
            self._console.print(
                f"[red]{self.site} not yet supported. Please choose from the following: {', '.join(self.NAVIGATORS.keys())}.[/red]"
            )
        return chk

    def interact(self):
        choices = [
            f"Start healing {self.site}'s algorithm",
            f"View {self.site} accounts",
            f"Add {self.site} account",
            f"Delete {self.site} account",
            "Update AlgoHealer settings",
            "Reset AlgoHealer",
            "Exit",
        ]
        while True:
            if not self._db_conn.check_settings_exist():
                # First time setup
                self._console.print(
                    "[yellow]No settings found. Please set default settings first.[/yellow]"
                )
                self._update_settings()
                self._db_conn.add_default_accounts()
            user_choice = questionary.select(
                "Please choose an option:",
                choices=choices,
                use_arrow_keys=True,
                style=custom_style,
            ).ask()

            if user_choice == choices[0]:
                _ran = self._run_healer()
                if _ran:
                    self._console.print(
                        f"[green]Completed healing {self.site}'s algorithm![/green]"
                    )
                    break
            elif user_choice == choices[2]:
                self._add_new_account()
            elif user_choice == choices[3]:
                self._delete_selected_accounts()
            elif user_choice == choices[1]:
                self._view_all_accounts()
            elif user_choice == choices[4]:
                self._update_settings()
            elif user_choice == choices[5]:
                if self._confirm_action("Reset the database"):
                    self._console.print(f"[red]Resetting {self.site} database...[/red]")
                    self._db_conn.drop_tables()
                    self._db_conn.initialize_tables()
                    if self._confirm_action("Add default accounts", default=True):
                        self._db_conn.add_default_accounts()
                else:
                    self._console.print("[yellow]Reset cancelled.[/yellow]")
            elif user_choice == choices[-1]:
                self._console.print("[blue]Exiting... Goodbye![/blue]")
                break

    @staticmethod
    def _confirm_action(action: str, default: bool = False) -> bool:
        return questionary.confirm(
            f"Are you sure you want to {action}?",
            default=default,
            style=custom_style,
        ).ask()

    def _run_healer(self) -> bool:
        if len(self._db_conn.get_all_accounts_for_site(self.site)) == 0:
            self._console.print(
                f"[red]No accounts found for {self.site}. Please add an account first.[/red]"
            )
            return False

        self._console.print(f"[blue]Healing {self.site} algorithm...[/blue]")
        settings: Settings = self._db_conn.get_settings()
        try:
            navigator = DataManager.NAVIGATORS[self.site](
                user_data_dir=settings.user_data_dir,
                channel=settings.channel,
                headless=settings.headless,
                db_conn=self._db_conn,
            )
            navigator.run()
            navigator.stop()
        except TargetClosedError:
            self._console.print(
                "[red]Please close all browser windows and try again.[/red]"
            )
            return False
        except Exception as e:
            self._console.print(f"[red]An error occurred: {e}[/red]")
            return False
        return True

    def _update_settings(self):
        settings: Settings = self._db_conn.get_settings()

        self._console.print("[yellow]Update AlgoHealer settings:[/yellow]")

        while True:
            choices = [
                questionary.Choice(
                    title=category,
                    checked=category in settings.interests,
                )
                for category in CATEGORIES
            ]
            selected_accounts = questionary.checkbox(
                "What types of content are you interested in (recommend selecting all):",
                choices=choices,
                use_arrow_keys=True,
                style=custom_style,
            ).ask()

            if selected_accounts:
                settings.interests = [Category(_) for _ in selected_accounts]
                break
            else:
                self._console.print(
                    "[red]Please select at least one category to continue.[/red]"
                )

        settings.headless = (
            questionary.select(
                "Run browser in headless mode (recommend yes):",
                choices=["yes", "no"],
                default="yes" if settings.headless else "no",
                use_arrow_keys=True,
                style=custom_style,
            ).ask()
            == "yes"
        )

        settings.channel = questionary.select(
            "Select your default browser (recommend chrome):",
            choices=["chrome", "chromium"],
            default=settings.channel,
            use_arrow_keys=True,
            style=custom_style,
        ).ask()

        settings.user_data_dir = questionary.text(
            "Path to browser's data directory:",
            default=settings.user_data_dir,
            style=custom_style,
        ).ask()
        self._db_conn.upsert_settings(settings)
        self._console.print("[green]Settings updated successfully![/green]\n")

    def _view_all_accounts(self):
        accounts = self._db_conn.get_all_accounts_for_site(self.site)
        if accounts:
            table = Table()
            table.add_column("Name", justify="left", style="green")
            table.add_column("Category", justify="left", style="cyan")

            for account in accounts:
                table.add_row(account["name"], account["category"])

            self._console.print(table)
        else:
            self._console.print(f"[red]No accounts found for {self.site}.[/red]")

    def _add_new_account(self):
        name = questionary.text("Enter the account name:", style=custom_style).ask()
        category = questionary.select(
            "Select a category:",
            choices=CATEGORIES,
            use_arrow_keys=True,
            style=custom_style,
        ).ask()

        self._db_conn.add_account(name, self.site, category)
        self._console.print(f"[green]Account '{name}' added successfully![/green]\n")

    def _delete_selected_accounts(self):
        accounts = self._db_conn.get_all_accounts_for_site(self.site)

        if not accounts:
            self._console.print(f"[red]No accounts found for {self.site}.[/red]")
            return

        self._console.print(
            "[yellow]Select accounts to delete. Use space to select and enter to confirm:[/yellow]"
        )

        choices = [
            {
                "name": f"{account['name']} ({account['category']})",
                "value": account["id"],
            }
            for account in accounts
        ]
        selected_accounts = questionary.checkbox(
            "Select accounts to delete:",
            choices=choices,
            use_arrow_keys=True,
            style=custom_style,
        ).ask()

        if not selected_accounts:
            self._console.print("[red]No accounts selected. Returning...[/red]")
            return

        self._db_conn.delete_accounts(selected_accounts)
        self._console.print("[green]Selected accounts deleted successfully.[/green]\n")
