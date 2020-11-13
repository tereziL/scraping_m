#!/usr/bin/env python
# coding: utf-8
import logging
import time
from datetime import date, datetime, timedelta

import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from twilio.rest import Client

linky = pd.read_csv("Linky.csv", sep=";")

logging.basicConfig()
logging.getLogger("apscheduler").setLevel(logging.DEBUG)


def get_home_team(driver):
    specific_match = BeautifulSoup(driver.page_source, "html.parser")
    home_team = specific_match.find("span", class_="LSA_TeamNameHome").get_text()
    return home_team


def get_guest_team(driver):
    specific_match = BeautifulSoup(driver.page_source, "html.parser")
    guest_team = specific_match.find("span", class_="LSA_TeamNameGuest").get_text()
    return guest_team


def field_function(driver, table_to_check, gender, home_team, guest_team):
    specific_match = BeautifulSoup(driver.page_source, "html.parser")

    guest_players_on_the_field_df = pd.DataFrame(columns=["team", "player_number"])
    home_players_on_the_field_df = pd.DataFrame(columns=["team", "player_number"])

    home_players_on_the_field = specific_match.find_all(
        "span", id=lambda x: x and x.startswith("GV_RosterHome_LBL_PlayerNumber")
    )
    guest_players_on_the_field = specific_match.find_all(
        "span", id=lambda x: x and x.startswith("GV_RosterGuest_LBL_PlayerNumber")
    )

    for player_number_on_the_field in home_players_on_the_field:
        home_players_on_the_field_df = home_players_on_the_field_df.append(
            {
                "team": home_team,
                "player_number": player_number_on_the_field.text.strip(),
            },
            ignore_index=True,
        )

    for player_number_on_the_field in guest_players_on_the_field:
        guest_players_on_the_field_df = guest_players_on_the_field_df.append(
            {
                "team": guest_team,
                "player_number": player_number_on_the_field.text.strip(),
            },
            ignore_index=True,
        )

    missing_players_home_on_the_field = home_team + ": "
    missing_players_guest_on_the_field = guest_team + ": "
    distinct_field_player_numbers_home = []
    distinct_field_player_numbers_guest = []

    for player in table_to_check.loc[table_to_check.team == home_team]["player_name"]:
        if (
            player not in home_players_on_the_field_df.player_number.values
            and player not in distinct_field_player_numbers_home
        ):
            try:
                note = table_to_check.loc[
                    (table_to_check.player_name == player)
                    & (table_to_check.team == home_team)
                    & (table_to_check.gender == gender)
                ]["notes"].item()
                missing_players_home_on_the_field += f"""Player: {player}, Note: {note} ,
                    """
                distinct_field_player_numbers_home.append(player)
            except ValueError:
                print(player)
    for player in table_to_check.loc[table_to_check.team == guest_team]["player_name"]:
        if (
            player not in guest_players_on_the_field_df.player_number.values
            and player not in distinct_field_player_numbers_guest
        ):
            try:
                note = table_to_check.loc[
                    (table_to_check.player_name == player)
                    & (table_to_check.team == guest_team)
                    & (table_to_check.gender == gender)
                ]["notes"].item()
                missing_players_guest_on_the_field += f"""Player: {player}, Note: {note} ,
                    """
                distinct_field_player_numbers_guest.append(player)
            except ValueError:
                print(player)

    missing_players_on_the_field = f"""{missing_players_home_on_the_field}
            {missing_players_guest_on_the_field}
            """
    account_sid = "AC73f3c1e258b6c6d21a596e5682315c96"
    auth_token = "d7104da5ea2b1e375b98f3816295fec6"
    client = Client(account_sid, auth_token)

    client.messages.create(
        body=missing_players_on_the_field,
        from_="whatsapp:+14155238886",
        to="whatsapp:" + phone_number,
    )


def get_players_on_the_field(men_competition_url, button_index, gender):
    current_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M:%S")
    driver = webdriver.Chrome(executable_path=chrome_path)
    driver.get(men_competition_url)
    time.sleep(15)
    website_button = driver.find_elements_by_xpath(
        "//*[starts-with(@id, 'Content_Main_RLV_MatchList_DIV_Live_Advanced')]"
    )
    try:
        driver.execute_script("arguments[0].click();", website_button[button_index])
    except IndexError:
        driver.execute_script("arguments[0].click();", website_button[button_index - 1])
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    time.sleep(15)

    home_team = get_home_team(driver)
    guest_team = get_guest_team(driver)

    table_to_check = pd.read_csv("Teams_to_check9.csv", sep=";")
    table_to_check["player_name"] = table_to_check["player_name"].astype(str)
    table_to_check["team"] = table_to_check["team"].astype(str)
    table_to_check["notes"] = table_to_check["notes"].astype(str)

    if version == 1:
        field_function(driver, table_to_check, gender, home_team, guest_team)

    player_team_number_df = scrape_the_content(driver)

    while (
        player_team_number_df["player_name"].last_valid_index() != 11
        or not player_team_number_df["player_name"][0]
    ):
        time.sleep(10)
        player_team_number_df = scrape_the_content(driver)
        if datetime.now().strftime("%H:%M:%S") > current_time:
            break

    if (
        player_team_number_df["player_name"].last_valid_index() != 11
        or not player_team_number_df["player_name"][0]
    ):
        driver.close()
    else:
        missing_players_home = home_team + ": "
        missing_players_guest = guest_team + ": "

        distinct_player_numbers_home = []
        distinct_player_numbers_guest = []

        for player_number in table_to_check.loc[table_to_check.team == home_team][
            "player_name"
        ]:
            if (
                player_number
                not in player_team_number_df.loc[
                    player_team_number_df.team == home_team
                ]["player_number"].values
            ) and player_number not in distinct_player_numbers_home:
                try:
                    note = table_to_check.loc[
                        (table_to_check.player_name == player_number)
                        & (table_to_check.team == home_team)
                        & (table_to_check.gender == gender)
                    ]["notes"].item()
                    missing_players_home += f"""Player: {player_number}, Note: {note} ,
                        """
                    distinct_player_numbers_home.append(player_number)
                except ValueError:
                    print(player_number)

        for player_number in table_to_check.loc[table_to_check.team == guest_team][
            "player_name"
        ]:
            if (
                player_number
                not in player_team_number_df.loc[
                    player_team_number_df.team == guest_team
                ]["player_number"].values
            ) and player_number not in distinct_player_numbers_guest:
                try:
                    note = table_to_check.loc[
                        (table_to_check.player_name == player_number)
                        & (table_to_check.team == guest_team)
                        & (table_to_check.gender == gender)
                    ]["notes"].item()
                    missing_players_guest += f"""Player: {player_number}, Note: {note} ,
                        """
                    distinct_player_numbers_guest.append(player_number)
                except ValueError:
                    print(player_number)
        missing_players = f"""{missing_players_home}
            {missing_players_guest}
            """
        account_sid = "AC73f3c1e258b6c6d21a596e5682315c96"
        auth_token = "d7104da5ea2b1e375b98f3816295fec6"
        client = Client(account_sid, auth_token)

        client.messages.create(
            body=missing_players,
            from_="whatsapp:+14155238886",
            to="whatsapp:" + phone_number,
        )
        driver.close()


def scrape_the_content(driver):
    df = pd.DataFrame()
    specific_match = BeautifulSoup(driver.page_source, "html.parser")

    home_team = get_home_team(driver)
    guest_team = get_guest_team(driver)

    player_container = specific_match.find("div", class_="LSA_DIV_Court")

    player_names = player_container.find_all("p", class_="LSA_p_PlayerName")
    for player in player_names:
        if player.find("span", id=lambda x: x and x.startswith("Home")):
            df = df.append(
                {"team": home_team, "player_name": player.text.strip()},
                ignore_index=True,
            )
        else:
            df = df.append(
                {"team": guest_team, "player_name": player.text.strip()},
                ignore_index=True,
            )
    player_numbers_list = player_container.find_all(
        "span",
        id=lambda x: x
        and (x.startswith("Home") or x.startswith("Guest"))
        and len(x) < 8,
    )

    player_numbers_df = pd.DataFrame()
    for player_number in player_numbers_list:
        player_numbers_df = player_numbers_df.append(
            {"player_number": player_number.text.strip()}, ignore_index=True
        )
    player_team_number_df = pd.merge(
        df, player_numbers_df, left_index=True, right_index=True
    )
    return player_team_number_df


def open_urls(specific_url_from_df, gender):
    this_day = date.today().strftime("%Y-%m-%d")
    driver = webdriver.Chrome(executable_path=chrome_path)
    driver.get(specific_url_from_df)
    time.sleep(15)
    try:
        live_score_button_men = driver.find_element_by_xpath(
            '//a[contains(@href,"LiveScore")]'
        )
        live_score_button_men.click()
        # empty list for the time_schedule
        time_schedules_field = []

        # find the button where to click to be redirected to the another page
        time.sleep(5)
        time_html_men = BeautifulSoup(driver.page_source, "html.parser")

        # get the time of the specific match
        for specific_time in time_html_men.find_all(
            "span",
            id=lambda x: x and x.startswith("Content_Main_RLV_MatchList_LB_Ora_Today"),
        ):
            stripped_time = specific_time.text.strip()

            time_to_schedule_field = datetime.strptime(
                str(stripped_time).replace(".", ":"), "%H:%M"
            ) - timedelta(minutes=13)
            time_schedules_field.append(time_to_schedule_field.time())

        for index_time, specific_time in enumerate(time_schedules_field):
            time_to_schedule = this_day + " " + str(specific_time)
            print(time_to_schedule)
            sched.add_job(
                get_players_on_the_field,
                run_date=time_to_schedule,
                args=[driver.current_url, index_time, gender, chrome_path],
            )

    except NoSuchElementException:
        print("No such element to be found on the men page")
    driver.close()


if __name__ == "__main__":
    sched = BlockingScheduler()
    chrome_path = r"/usr/local/bin/chromedriver"
    version = 0
    while version not in (1, 2):
        version = int(input("What version do you want to run? (1 or 2) "))

    phone_number = "0"
    while not (len(str(phone_number)) == 9 and str(phone_number[0]) == "9"):
        phone_number = input(
            "What number do you want me to send a whatsapp message? (+421)"
        )
    phone_number = "+421" + str(phone_number)

    for index, row in linky.iterrows():
        if index < 7:
            sched.add_job(
                open_urls,
                "interval",
                days=1,
                start_date=(datetime.today() + timedelta(minutes=1)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                end_date="2030-06-15 11:00:00",
                args=[row["url"], row["gender"], chrome_path],
            )
        elif index < 13:
            sched.add_job(
                open_urls,
                "interval",
                days=1,
                start_date=(datetime.today() + timedelta(minutes=3)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                end_date="2030-06-15 11:00:00",
                args=[row["url"], row["gender"], chrome_path],
            )
        elif index < 19:
            sched.add_job(
                open_urls,
                "interval",
                days=1,
                start_date=(datetime.today() + timedelta(minutes=5)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                end_date="2030-06-15 11:00:00",
                args=[row["url"], row["gender"], chrome_path],
            )
        elif index < 25:
            sched.add_job(
                open_urls,
                "interval",
                days=1,
                start_date=(datetime.today() + timedelta(minutes=7)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                end_date="2030-06-15 11:00:00",
                args=[row["url"], row["gender"], chrome_path],
            )
        elif index < 31:
            sched.add_job(
                open_urls,
                "interval",
                days=1,
                start_date=(datetime.today() + timedelta(minutes=9)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                end_date="2030-06-15 11:00:00",
                args=[row["url"], row["gender"], chrome_path],
            )
        elif index < 37:
            sched.add_job(
                open_urls,
                "interval",
                days=1,
                start_date=(datetime.today() + timedelta(minutes=11)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                end_date="2030-06-15 11:00:00",
                args=[row["url"], row["gender"], chrome_path],
            )
        elif index < 43:
            sched.add_job(
                open_urls,
                "interval",
                days=1,
                start_date=(datetime.today() + timedelta(minutes=13)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                end_date="2030-06-15 11:00:00",
                args=[row["url"], row["gender"], chrome_path],
            )
        elif index < 49:
            sched.add_job(
                open_urls,
                "interval",
                days=1,
                start_date=(datetime.today() + timedelta(minutes=15)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                end_date="2030-06-15 11:00:00",
                args=[row["url"], row["gender"], chrome_path],
            )
        elif index < 56:
            sched.add_job(
                open_urls,
                "interval",
                days=1,
                start_date=(datetime.today() + timedelta(minutes=17)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                end_date="2030-06-15 11:00:00",
                args=[row["url"], row["gender"], chrome_path],
            )
        elif index < 63:
            sched.add_job(
                open_urls,
                "interval",
                days=1,
                start_date=(datetime.today() + timedelta(minutes=19)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                end_date="2030-06-15 11:00:00",
                args=[row["url"], row["gender"], chrome_path],
            )
        else:
            sched.add_job(
                open_urls,
                "interval",
                days=1,
                start_date=(datetime.today() + timedelta(minutes=21)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                end_date="2030-06-15 11:00:00",
                args=[row["url"], row["gender"], chrome_path],
            )

    sched.start()

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(5)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        sched.shutdown()
