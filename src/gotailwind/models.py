"""Asynchronous Python client for Tailwind garage door openers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Self, TypeVar

from mashumaro import field_options
from mashumaro.config import BaseConfig
from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.types import SerializationStrategy

from gotailwind.const import (
    MIN_REQUIRED_FIRMWARE_VERSION,
    TailwindDoorOperationCommand,
    TailwindDoorState,
    TailwindRequestType,
    TailwindResponseResult,
)
from gotailwind.exceptions import (
    TailwindAuthenticationError,
    TailwindResponseError,
    TailwindUnsupportedFirmwareVersionError,
)
from gotailwind.util import tailwind_device_id_to_mac_address

_RequestData = TypeVar("_RequestData")
_ResponseT = TypeVar("_ResponseT")


class IntegerIsBoolean(SerializationStrategy):
    """Boolean serialization strategy for integers."""

    def serialize(self, value: bool) -> int:  # noqa: FBT001
        """Serialize a boolean to an integer."""
        return int(value)

    def deserialize(self, value: int) -> bool:
        """Deserialize an integer to a boolean."""
        return bool(value)


class BaseModel(DataClassORJSONMixin):
    """Base model for all Tailwind models."""

    # pylint: disable-next=too-few-public-methods
    class Config(BaseConfig):
        """Mashumaro configuration."""

        serialization_strategy = {bool: IntegerIsBoolean()}  # noqa: RUF012
        serialize_by_alias = True
        omit_none = True


@dataclass(kw_only=True)
class TailwindRequestData(BaseModel):
    """Request object for Tailwind devices."""

    request_type: TailwindRequestType = field(
        init=False,
        default=TailwindRequestType.GET,
        metadata=field_options(alias="type"),
    )
    name: str = field(init=False, default="dev_st")


@dataclass(kw_only=True)
class TailwindRequest(Generic[_RequestData, _ResponseT], BaseModel):
    """Base request object for Tailwind devices."""

    data: _RequestData
    version: str = "0.1"
    product: str | None = None

    @property
    def response_type(self) -> type[_ResponseT]:
        """Return the type of the response."""
        raise NotImplementedError


@dataclass(kw_only=True)
class TailwindResponse(BaseModel):
    """Base response object for Tailwind devices."""

    @classmethod
    def __pre_deserialize__(
        cls: type[Self],
        d: dict[Any, Any],
    ) -> dict[Any, Any]:
        """Raise when response was unexpected."""
        result = d.get("result")
        if result == TailwindResponseResult.OK:
            return d

        if result == TailwindResponseResult.AUTH_ERROR:
            msg = "Authentication error. Provided local token is not valid."
            raise TailwindAuthenticationError(msg)

        raise TailwindResponseError(
            d.get("message", d.get("Info", "Unknown error")),
        )


@dataclass(kw_only=True)
class TailwindDoor(BaseModel):
    """Object holding the door status of a Tailwind connected garage door."""

    disabled: bool
    door_id: str
    index: int
    locked_out: bool = field(metadata=field_options(alias="lockup"))
    state: TailwindDoorState = field(metadata=field_options(alias="status"))


@dataclass(kw_only=True)
class TailwindDeviceStatus(TailwindResponse):
    """Object holding the door status of a Tailwind connected garage doors."""

    device_id: str = field(metadata=field_options(alias="dev_id"))
    firmware_version: str = field(metadata=field_options(alias="fw_ver"))
    night_mode_enabled: bool = field(metadata=field_options(alias="night_mode_en"))
    product: str
    protocol_version: str = field(metadata=field_options(alias="proto_ver"))
    led_brightness: int

    number_of_doors: int = field(metadata=field_options(alias="door_num"))
    doors: dict[str, TailwindDoor] = field(
        metadata=field_options(alias="data"), default_factory=dict
    )

    @classmethod
    def __pre_deserialize__(
        cls: type[TailwindDeviceStatus], d: dict[Any, Any]
    ) -> dict[Any, Any]:
        """Modify data before deserialization."""
        if (version := d.get("fw_ver")) and version < MIN_REQUIRED_FIRMWARE_VERSION:
            msg = (
                f"Unsupported firmware version {version}. "
                f"Minimum required version is {MIN_REQUIRED_FIRMWARE_VERSION}. "
                f"Please update your Tailwind device."
            )
            raise TailwindUnsupportedFirmwareVersionError(msg)

        super().__pre_deserialize__(d)
        for door_id, door in d.get("data", {}).items():
            door["door_id"] = door_id
        return d

    @property
    def mac_address(self) -> str:
        """Return the mac address."""
        return tailwind_device_id_to_mac_address(self.device_id)


@dataclass(kw_only=True)
class TailwindDeviceStatusRequestData(TailwindRequestData):
    """Request object for Tailwind devices."""

    name = "dev_st"


@dataclass(kw_only=True)
class TailwindDeviceStatusRequest(
    TailwindRequest[TailwindDeviceStatusRequestData, TailwindDeviceStatus]
):
    """Request object for Tailwind devices."""

    data: TailwindDeviceStatusRequestData = field(
        default_factory=TailwindDeviceStatusRequestData
    )

    @property
    def response_type(self) -> type[TailwindDeviceStatus]:
        """Return the HTTP method for the request."""
        return TailwindDeviceStatus


@dataclass(kw_only=True)
class TailwindIdentifyRequestData(TailwindRequestData):
    """Request object for Tailwind devices."""

    request_type = TailwindRequestType.SET
    name = "identify"


@dataclass(kw_only=True)
class TailwindIdentifyRequest(
    TailwindRequest[TailwindIdentifyRequestData, TailwindResponse]
):
    """Request object for Tailwind devices."""

    data: TailwindIdentifyRequestData = field(
        default_factory=TailwindIdentifyRequestData
    )

    @property
    def response_type(self) -> type[TailwindResponse]:
        """Return the HTTP method for the request."""
        return TailwindResponse


@dataclass(kw_only=True)
class TailwindDoorOperationRequestDataValue(BaseModel):
    """Request object for Tailwind devices."""

    index: int = field(metadata=field_options(alias="door_idx"))
    operation: TailwindDoorOperationCommand = field(metadata=field_options(alias="cmd"))


@dataclass(kw_only=True)
class TailwindDoorOperationRequestData(TailwindRequestData):
    """Request object for Tailwind devices."""

    value: TailwindDoorOperationRequestDataValue
    request_type = TailwindRequestType.SET
    name = "door_op"


@dataclass(kw_only=True)
class TailwindDoorOperationRequest(
    TailwindRequest[TailwindDoorOperationRequestData, TailwindResponse]
):
    """Request object for Tailwind devices."""

    data: TailwindDoorOperationRequestData

    @property
    def response_type(self) -> type[TailwindResponse]:
        """Return the HTTP method for the request."""
        return TailwindResponse


@dataclass(kw_only=True)
class TailwindLEDBrightnessRequestDataValue(BaseModel):
    """Request object for Tailwind devices."""

    brightness: int


@dataclass(kw_only=True)
class TailwindLEDBrightnessRequestData(TailwindRequestData):
    """Request object for Tailwind devices."""

    value: TailwindLEDBrightnessRequestDataValue
    request_type = TailwindRequestType.SET
    name = "status_led"


@dataclass(kw_only=True)
class TailwindLEDBrightnessRequest(
    TailwindRequest[TailwindLEDBrightnessRequestData, TailwindResponse]
):
    """Request object for Tailwind devices."""

    data: TailwindLEDBrightnessRequestData

    @property
    def response_type(self) -> type[TailwindResponse]:
        """Return the HTTP method for the request."""
        return TailwindResponse
