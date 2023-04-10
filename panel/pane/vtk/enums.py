from collections import namedtuple
from enum import Enum


class TextPosition(Enum):
    LowerLeft = 0
    LowerRight = 1
    UpperLeft = 2
    UpperRight = 3
    LowerEdge = 4
    RightEdge = 5
    LeftEdge = 6
    UpperEdge = 7

SCALAR_MODE = namedtuple("SCALAR_MODE",
    "Default UsePointData UseCellData UsePointFieldData UseCellFieldData UseFieldData"
)(0, 1, 2, 3, 4, 5)

COLOR_MODE = namedtuple("COLOR_MODE", "DirectScalars MapScalars")(0, 1)

ACCESS_MODE = namedtuple("ACCESS_MODE", "ById ByName")(0, 1)

PRESET_CMAPS = [
    'KAAMS',
    'Cool to Warm',
    'Cool to Warm (Extended)',
    'Warm to Cool',
    'Warm to Cool (Extended)',
    'Rainbow Desaturated',
    'Cold and Hot',
    'Black-Body Radiation',
    'X Ray',
    'Grayscale',
    'BkRd',
    'BkGn',
    'BkBu',
    'BkMa',
    'BkCy',
    'Black, Blue and White',
    'Black, Orange and White',
    'Linear YGB 1211g',
    'Linear Green (Gr4L)',
    'Linear Blue (8_31f)',
    'Blue to Red Rainbow',
    'Red to Blue Rainbow',
    'Rainbow Blended White',
    'Rainbow Blended Grey',
    'Rainbow Blended Black',
    'Blue to Yellow',
    'blot',
    'CIELab Blue to Red',
    'jet',
    'rainbow',
    'erdc_rainbow_bright',
    'erdc_rainbow_dark',
    'nic_CubicL',
    'nic_CubicYF',
    'gist_earth',
    '2hot',
    'erdc_red2yellow_BW',
    'erdc_marine2gold_BW',
    'erdc_blue2gold_BW',
    'erdc_sapphire2gold_BW',
    'erdc_red2purple_BW',
    'erdc_purple2pink_BW',
    'erdc_pbj_lin',
    'erdc_blue2green_muted',
    'erdc_blue2green_BW',
    'GREEN-WHITE_LINEAR',
    'erdc_green2yellow_BW',
    'blue2cyan',
    'erdc_blue2cyan_BW',
    'erdc_blue_BW',
    'BLUE-WHITE',
    'erdc_purple_BW',
    'erdc_magenta_BW',
    'magenta',
    'RED-PURPLE',
    'erdc_red_BW',
    'RED_TEMPERATURE',
    'erdc_orange_BW',
    'heated_object',
    'erdc_gold_BW',
    'erdc_brown_BW',
    'copper_Matlab',
    'pink_Matlab',
    'bone_Matlab',
    'gray_Matlab',
    'Purples',
    'Blues',
    'Greens',
    'PuBu',
    'BuPu',
    'BuGn',
    'GnBu',
    'GnBuPu',
    'BuGnYl',
    'PuRd',
    'RdPu',
    'Oranges',
    'Reds',
    'RdOr',
    'BrOrYl',
    'RdOrYl',
    'CIELab_blue2red',
    'blue2yellow',
    'erdc_blue2gold',
    'erdc_blue2yellow',
    'erdc_cyan2orange',
    'erdc_purple2green',
    'erdc_purple2green_dark',
    'coolwarm',
    'BuRd',
    'Spectral_lowBlue',
    'GnRP',
    'GYPi',
    'GnYlRd',
    'GBBr',
    'PuOr',
    'PRGn',
    'PiYG',
    'OrPu',
    'BrBG',
    'GyRd',
    'erdc_divHi_purpleGreen',
    'erdc_divHi_purpleGreen_dim',
    'erdc_divLow_icePeach',
    'erdc_divLow_purpleGreen',
    'Haze_green',
    'Haze_lime',
    'Haze',
    'Haze_cyan',
    'nic_Edge',
    'erdc_iceFire_H',
    'erdc_iceFire_L',
    'hsv',
    'hue_L60',
    'Spectrum',
    'Warm',
    'Cool',
    'Blues',
    'Wild Flower',
    'Citrus',
    'Brewer Diverging Purple-Orange (11)',
    'Brewer Diverging Purple-Orange (10)',
    'Brewer Diverging Purple-Orange (9)',
    'Brewer Diverging Purple-Orange (8)',
    'Brewer Diverging Purple-Orange (7)',
    'Brewer Diverging Purple-Orange (6)',
    'Brewer Diverging Purple-Orange (5)',
    'Brewer Diverging Purple-Orange (4)',
    'Brewer Diverging Purple-Orange (3)',
    'Brewer Diverging Spectral (11)',
    'Brewer Diverging Spectral (10)',
    'Brewer Diverging Spectral (9)',
    'Brewer Diverging Spectral (8)',
    'Brewer Diverging Spectral (7)',
    'Brewer Diverging Spectral (6)',
    'Brewer Diverging Spectral (5)',
    'Brewer Diverging Spectral (4)',
    'Brewer Diverging Spectral (3)',
    'Brewer Diverging Brown-Blue-Green (11)',
    'Brewer Diverging Brown-Blue-Green (10)',
    'Brewer Diverging Brown-Blue-Green (9)',
    'Brewer Diverging Brown-Blue-Green (8)',
    'Brewer Diverging Brown-Blue-Green (7)',
    'Brewer Diverging Brown-Blue-Green (6)',
    'Brewer Diverging Brown-Blue-Green (5)',
    'Brewer Diverging Brown-Blue-Green (4)',
    'Brewer Diverging Brown-Blue-Green (3)',
    'Brewer Sequential Blue-Green (9)',
    'Brewer Sequential Blue-Green (8)',
    'Brewer Sequential Blue-Green (7)',
    'Brewer Sequential Blue-Green (6)',
    'Brewer Sequential Blue-Green (5)',
    'Brewer Sequential Blue-Green (4)',
    'Brewer Sequential Blue-Green (3)',
    'Brewer Sequential Yellow-Orange-Brown (9)',
    'Brewer Sequential Yellow-Orange-Brown (8)',
    'Brewer Sequential Yellow-Orange-Brown (7)',
    'Brewer Sequential Yellow-Orange-Brown (6)',
    'Brewer Sequential Yellow-Orange-Brown (5)',
    'Brewer Sequential Yellow-Orange-Brown (4)',
    'Brewer Sequential Yellow-Orange-Brown (3)',
    'Brewer Sequential Blue-Purple (9)',
    'Brewer Sequential Blue-Purple (8)',
    'Brewer Sequential Blue-Purple (7)',
    'Brewer Sequential Blue-Purple (6)',
    'Brewer Sequential Blue-Purple (5)',
    'Brewer Sequential Blue-Purple (4)',
    'Brewer Sequential Blue-Purple (3)',
    'Brewer Qualitative Accent',
    'Brewer Qualitative Dark2',
    'Brewer Qualitative Set2',
    'Brewer Qualitative Pastel2',
    'Brewer Qualitative Pastel1',
    'Brewer Qualitative Set1',
    'Brewer Qualitative Paired',
    'Brewer Qualitative Set3',
    'Traffic Lights',
    'Traffic Lights For Deuteranopes',
    'Traffic Lights For Deuteranopes 2',
    'Muted Blue-Green',
    'Green-Blue Asymmetric Divergent (62Blbc)',
    'Asymmtrical Earth Tones (6_21b)',
    'Yellow 15',
    'Magma (matplotlib)',
    'Inferno (matplotlib)',
    'Plasma (matplotlib)',
    'Viridis (matplotlib)',
    'BlueObeliskElements'
]
