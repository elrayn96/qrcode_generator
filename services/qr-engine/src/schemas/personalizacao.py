from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ModeloEstrito(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )

    @model_validator(mode="before")
    @classmethod
    def rejeitar_nulos(cls, dados):
        if isinstance(dados, dict) and any(valor is None for valor in dados.values()):
            raise ValueError("Null values are not supported")

        return dados


Cor = Annotated[
    str,
    Field(pattern=r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$"),
]

Forma = Literal["square", "rounded", "dots"]

Formato = Literal["png", "svg"]

CorrecaoErro = Literal["L", "M", "Q", "H"]


class PontoGradiente(ModeloEstrito):
    position: float = Field(ge=0, le=1)
    color: Cor


class Gradiente(ModeloEstrito):
    type: Literal["linear", "radial"]
    angle: int | None = Field(
        default=None,
        ge=0,
        le=360,
    )
    stops: list[PontoGradiente] = Field(
        min_length=2,
        max_length=8,
    )


class Modulos(ModeloEstrito):
    shape: Forma | None = None
    color: Cor | None = None
    gradient: Gradiente | None = None

    @model_validator(mode="after")
    def validar_preenchimento(self) -> Modulos:
        if self.color is not None and self.gradient is not None:
            raise ValueError("Color and gradient are mutually exclusive")

        return self


class Olhos(ModeloEstrito):
    outer: Modulos | None = None
    inner: Modulos | None = None


class Fundo(ModeloEstrito):
    color: Cor | None = None
    gradient: Gradiente | None = None
    transparent: bool | None = None


class Logotipo(ModeloEstrito):
    mediaType: Literal["image/png", "image/jpeg"]

    base64: str = Field(
        min_length=1,
        max_length=699052,
        pattern=r"^[A-Za-z0-9+/]+={0,2}$",
        repr=False,
    )

    scale: float | None = Field(
        default=None,
        ge=0.05,
        le=0.20,
    )

    padding: int | None = Field(
        default=None,
        ge=0,
        le=4,
    )


class Moldura(ModeloEstrito):
    color: Cor | None = None

    label: str | None = Field(
        default=None,
        min_length=1,
        max_length=80,
        repr=False,
    )

    position: Literal["top", "bottom"] | None = None

    textColor: Cor | None = None

    padding: int | None = Field(
        default=None,
        ge=0,
        le=16,
    )


class Personalizacao(ModeloEstrito):
    modules: Modulos | None = None
    eyes: Olhos | None = None
    background: Fundo | None = None
    logo: Logotipo | None = None
    frame: Moldura | None = None


class Saida(ModeloEstrito):
    format: Formato = "png"

    size: int = Field(
        default=512,
        ge=128,
        le=2048,
    )

    margin: int = Field(
        default=4,
        ge=4,
        le=32,
    )


class Opcoes(ModeloEstrito):
    errorCorrection: CorrecaoErro = "M"
