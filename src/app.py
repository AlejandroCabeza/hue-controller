# Python Imports
from enum import Enum, EnumMeta
from logging import getLogger, Logger
from logging.config import fileConfig
from pathlib import Path
from sys import argv
from typing import List, Any, ClassVar
# Framework Imports
# Third-Party Imports
from phue import Bridge, Light
# Project Imports


PROJECT_ROOT: Path = Path(__file__).parent.parent
LoggingConfFile: Path = PROJECT_ROOT.joinpath("logging.conf")

print(LoggingConfFile)
fileConfig(LoggingConfFile)
logger: Logger = getLogger(__name__)


class StrComparable(EnumMeta):

    @property
    def __names__(cls) -> List[str]:
        return [member.name for member in cls.__members__.values()]

    @property
    def __values__(cls) -> List[str]:
        return [member.value for member in cls.__members__.values()]

    def __contains__(cls, item: Any) -> bool:
        match item:
            case str():
                return item in cls.__values__
            case _:
                return super().__contains__(item)


class StrEnum(str, Enum, metaclass=StrComparable):
    pass


class BrightnessConfigurationCommand(StrEnum):
    SET: "BrightnessConfigurationCommand" = "set"
    INCREASE: "BrightnessConfigurationCommand" = "increase"
    DECREASE: "BrightnessConfigurationCommand" = "decrease"

    def __eq__(self, obj: Any) -> bool:
        match obj:
            case str():
                return obj == self.value
            case _:
                return super().__eq__(obj)


class HueBridge(Bridge):

    MAX_BRIGHTNESS_VALUE: ClassVar[int] = 254
    MIN_BRIGHTNESS_VALUE: ClassVar[int] = 0
    BRIGHTNESS_INTERVAL: ClassVar[int] = 20

    lights: List[Light]

    def __init__(
            self, ip=None, username=None, config_file_path=None, _light_name_for_brightness_reference: str = "Computer"
    ):
        super().__init__(ip, username, config_file_path)
        self._light_for_brightness_reference: Light = self[_light_name_for_brightness_reference]
        self._brightness = self.clamp_brightness(self._light_for_brightness_reference.brightness)

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        self._brightness: int = self.clamp_brightness(value)
        for light in self.lights:
            light.brightness = self._brightness

    def turn_on(self):
        for light in self.lights:
            light.on = True

    def turn_off(self):
        for light in self.lights:
            light.on = False

    def clamp_brightness(self, brightness: int) -> int:
        return max(self.__class__.MIN_BRIGHTNESS_VALUE, min(self.__class__.MAX_BRIGHTNESS_VALUE, brightness))

    def brightness_reduce(self):
        self.brightness = self.brightness - self.__class__.BRIGHTNESS_INTERVAL

    def brightness_increase(self):
        self.brightness = self.brightness + self.__class__.BRIGHTNESS_INTERVAL

    def brightness_regulate(self, command: BrightnessConfigurationCommand):
        match command:
            case BrightnessConfigurationCommand.DECREASE:
                self.brightness_reduce()
            case BrightnessConfigurationCommand.INCREASE:
                self.brightness_increase()

    @classmethod
    def parse_brightness_set(cls, value: str) -> int | None:
        if value.isdigit() and (cls.MIN_BRIGHTNESS_VALUE <= (_value := int(value)) <= cls.MAX_BRIGHTNESS_VALUE):
            return _value
        return None

    def hue_controller(self, arguments: List[str]) -> None:
        logger.info(f"Application Arguments: {' '.join(arguments)}")
        match arguments:
            case ["on"]:
                self.turn_on()
            case ["off"]:
                self.turn_off()
            case ["brightness", str(command), str(value)] if (
                    command == BrightnessConfigurationCommand.SET and (_value := self.parse_brightness_set(value))
            ):
                self.brightness = _value
            case ["brightness", str(command)] if command in BrightnessConfigurationCommand:
                self.brightness_regulate(command)
            case _:
                logger.error("Command has not been implemented.")
                return


if __name__ == "__main__":
    HUE_IP: str = "192.168.0.12"
    bridge: HueBridge = HueBridge(HUE_IP)
    bridge.connect()
    bridge.hue_controller(argv[1:])
