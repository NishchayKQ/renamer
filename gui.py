import os
import time
import re
from enum import Enum, unique
from typing import Callable, Union
from shutil import copy2, copytree

START_OF_PROPERTIES = 3


class Value:
    def __init__(self, value: int | bool | str):
        self.value = value


# default values of properties to compare with
@unique
class Keys(Enum):
    COUNT = Value(1)
    RENAME_DIRECTORY = Value(False)
    RENAME_HIDDEN_DIRECTORY = Value(False)
    APPEND_COUNTER = Value(False)
    BACKUP = Value("guiBackup")


class Property:
    i = START_OF_PROPERTIES

    # add self.dependency which will list the property which must be enabled for current setting to have effect
    def __init__(self, description: str, value: Union[int, bool, str], setter: Callable[[Keys], bool]):
        self.description = description
        self.setter = setter
        self.count = Property.i
        self.value = value
        Property.i = Property.i + 1


class Options:
    err = ""

    @classmethod
    def toggleSpecifiedOption(cls, key: Keys) -> bool:
        cls.currentSettings[key].value = not cls.currentSettings[key].value
        return True

    @classmethod
    def setANewValueForIntOption(cls, key: Keys) -> bool:
        value = input("enter new value : ")
        try:
            cls.currentSettings[key].value = int(value)
            return True
        except ValueError:
            return False

    @classmethod
    def printColoredSettingList(cls) -> None:
        os.system('cls||clear')
        print(f"directory to rename = {os.getcwd()}")
        if cls.err:
            print('\033[38;2;255;0;0m' + cls.err + '\033[0m')
            cls.err = ""
        for ara in cls.currentSettings.items():
            key = ara[0]
            valueProperty = ara[1]
            if valueProperty.value == key.value.value:
                print(f"\033[38;2;255;0;255m{valueProperty.count} {valueProperty.description}\033[0m :"
                      f" \033[38;2;0;170;0m{valueProperty.value}\033[0m")
            else:
                print(f"\033[38;2;255;0;255m{valueProperty.count} {valueProperty.description}\033[0m :"
                      f" \033[38;2;170;85;0m{valueProperty.value}\033[0m")
        print("with current options files found are :")
        for ara in returnSortedTupleOfTimeAndFile()[1].items():
            print(f"{ara[0]} : {ara[1]}")
        print()
        printExitCommands()

    @classmethod
    def setANewValueForStringOption(cls, key: Keys) -> bool:
        value = input("enter new value: ")
        cls.currentSettings[key].value = value
        return True

    currentSettings = {
        Keys.COUNT: Property(
            description="counter number to be appended before file name",
            value=Keys.COUNT.value.value,
            setter=setANewValueForIntOption
        ),
        Keys.RENAME_HIDDEN_DIRECTORY: Property(
            description="rename hidden directories",
            value=Keys.RENAME_HIDDEN_DIRECTORY.value.value,
            setter=toggleSpecifiedOption
        ),
        Keys.RENAME_DIRECTORY: Property(
            description="Rename Directories",
            value=Keys.RENAME_DIRECTORY.value.value,
            setter=toggleSpecifiedOption
        ),
        Keys.APPEND_COUNTER: Property(
            description="if enabled a counter number will append to the file name",
            value=Keys.APPEND_COUNTER.value.value,
            setter=toggleSpecifiedOption
        ),
        Keys.BACKUP: Property(
            description="non empty Backup directory name will make backup, enabled by default",
            value=Keys.BACKUP.value.value,
            setter=setANewValueForStringOption
        )
    }


def printExitCommands() -> None:
    print("'0' exit without renaming")
    print("'1' rename file(s) with the selected options")
    print("'2' show all files with the current settings selected")


# noinspection SpellCheckingInspection
def returnSortedTupleOfTimeAndFile() -> tuple[list[tuple[float, str, str | None]], dict[str, int], dict[str, list]]:
    allFiles = []
    fileExts: dict[str, int] = {"folders": 0}
    listOfFilesForEachExtenion: dict[str, list] = {"folders": []}
    pwd = os.getcwd()
    shouldMatch = None
    fileExtPattern = re.compile(r".*\.(\w+)$")
    if (Options.currentSettings[Keys.RENAME_DIRECTORY].value
            and not Options.currentSettings[Keys.RENAME_HIDDEN_DIRECTORY].value):
        shouldMatch = re.compile(r"^\.")
    for file in os.listdir(pwd):
        # time_mod = os.path.getmtime("/storage/emulated/0/DCIM/Screen recordings/" + file)
        if os.path.realpath(file) == __file__:
            continue
        temp = None
        if Options.currentSettings[Keys.RENAME_DIRECTORY].value:
            if Options.currentSettings[Keys.RENAME_HIDDEN_DIRECTORY].value:
                pass
            else:
                # if they don't want to rename hidden directories filter them out
                if os.path.isfile(os.path.join(pwd, file)):
                    pass
                else:
                    if shouldMatch.search(file):
                        continue
        else:
            if os.path.isfile(os.path.join(pwd, file)):
                pass
            else:
                continue

        # adding the current file or folder to number of folder/files with associated with current extension
        if os.path.isfile(os.path.join(pwd, file)):
            temp = fileExtPattern.search(file)
            try:
                fileExts[temp[1]] += 1
            except KeyError:
                fileExts[temp[1]] = 1
            try:
                listOfFilesForEachExtenion[temp[1]].append(file)
            except KeyError:
                listOfFilesForEachExtenion[temp[1]] = [file]

        else:
            fileExts["folders"] += 1
            listOfFilesForEachExtenion["folders"].append(file)

        time_mod = os.path.getmtime(file)
        # print(time.strftime("%d %b %I %M %p",time.localtime(time_mod)))
        if temp:
            allFiles.append((time_mod, file, temp[1]))
        else:
            allFiles.append((time_mod, file, None))
    allFiles.sort()
    return allFiles, fileExts, listOfFilesForEachExtenion


def renameFilesWithCurrentOptions(all_files: list[tuple[float, str, None | str]]) -> int:
    pwd = os.getcwd()
    noOfRenamedFiles = 0

    countToAppend = ""
    if Options.currentSettings[Keys.APPEND_COUNTER].value:
        countToAppend = str(Options.currentSettings[Keys.COUNT].value) + " "

    backupDirName = Options.currentSettings[Keys.BACKUP].value
    if backupDirName:
        while True:
            try:
                os.mkdir(pwd + r"/" + backupDirName)
                pwdWithBackupPathAppended = pwd + r"/" + backupDirName
                break
            except FileExistsError:
                backupDirName = backupDirName + " (1)"

        for ara in all_files:
            if ara[2]:
                copy2(f"{pwd}/{ara[1]}",
                      f"{pwdWithBackupPathAppended}/{countToAppend}{time.strftime('%d %b %I %M %p',
                                                                                  time.localtime(ara[0]))}.{ara[2]}"
                      )
            else:
                copytree(f"{pwd}/{ara[1]}",
                         f"{pwdWithBackupPathAppended}/{countToAppend}{time.strftime('%d %b %I %M %p',
                                                                                     time.localtime(ara[0]))}"
                         )
            noOfRenamedFiles += 1
    else:
        for ara in all_files:
            if ara[2]:
                os.rename(f"{pwd}/{ara[1]}",
                          f"{pwd}/{countToAppend}{time.strftime('%d %b %I %M %p', time.localtime(ara[0]))}.{ara[2]}")
            else:
                os.rename(f"{pwd}/{ara[1]}",
                          f"{pwd}/{countToAppend}{time.strftime('%d %b %I %M %p', time.localtime(ara[0]))}")
            noOfRenamedFiles += 1

    return noOfRenamedFiles


def get_key_for_count(dictionary: dict[Keys, Property], count) -> Keys:
    for key, value in dictionary.items():
        if value.count == count:
            return key


while True:
    Options.printColoredSettingList()
    userInput = input(": ")
    while True:
        try:
            userInput = int(userInput)
            break
        except ValueError:
            print("invalid input!")
    match userInput:
        case 0:
            break
        case 1:
            renameFilesWithCurrentOptions(returnSortedTupleOfTimeAndFile()[0])
        case _ if START_OF_PROPERTIES <= userInput <= Property.i:
            cKey = get_key_for_count(Options.currentSettings, userInput)
            currentSetting = Options.currentSettings[cKey]

            if not currentSetting.setter.__func__(Options, cKey):
                Options.err = "invalid input for the selected option!"

        case _:
            Options.err = "out of range of numbers!"
