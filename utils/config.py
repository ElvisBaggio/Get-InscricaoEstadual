import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    TESSERACT_CMD: Optional[str] = None
    CADESP_URL: str = "https://www.cadesp.fazenda.sp.gov.br/(S(s0l453pgvcpvtglc3avqciub))/Pages/Cadastro/Consultas/ConsultaPublica/ConsultaPublica.aspx"
    CHROME_DRIVER_PATH: Optional[str] = None

    # Captcha recognition settings with optimized values from calibration
    CAPTCHA_PSM_MODE: int = 7  # Single line of text
    CAPTCHA_CONTRAST: float = 2.5
    CAPTCHA_THRESHOLD: int = 128
    CAPTCHA_APPLY_NOISE_REDUCTION: bool = True
    CAPTCHA_RESIZE_SMALL_IMAGES: bool = True
    
    # Captcha attempt logging settings
    CAPTCHA_SAVE_ATTEMPTS: bool = True
    CAPTCHA_ATTEMPTS_DIR: str = "captcha_attempts"
    
    # Selenium element IDs
    # Selenium element IDs
    TYPE_SELECT_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_tipoFiltroDropDownList"
    CNPJ_INPUT_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_valorFiltroTextBox"
    CAPTCHA_IMG_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_imagemDinamica"
    CAPTCHA_INPUT_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_imagemDinamicaTextBox"
    SEARCH_BUTTON_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_consultaPublicaButton"
    # Result page selectors
    CONTROL_CODE_ID: str = "ctl00_conteudoPaginaPlaceHolder_lblCodigoControleCertidao"
    RESULT_TABLE_XPATH: str = "//table[contains(@style, 'border:1px solid gray')]"
    RESULT_SECTIONS_XPATH: str = "//td[contains(@class, 'labelHeader')]"
    
    # Data fields classes and selectors
    LABEL_CLASS: str = "labelDetalhe"
    DATA_CLASS: str = "dadoDetalhe"
    
    # XPath expressions for IE number - based on actual HTML structure
    IE_XPATH: str = "//tr/td[@class='dadoDetalhe' and preceding-sibling::td[@class='labelDetalhe' and ./b[text()='IE: ']]]"
    IE_XPATH_FALLBACK1: str = "//tr[.//td[@class='labelDetalhe']//b[contains(text(), 'IE:')]]/td[@class='dadoDetalhe']"
    IE_XPATH_FALLBACK2: str = "//td[contains(@class, 'dadoDetalhe') and preceding-sibling::td[contains(text(), 'IE:')]]"
    
    # Error handling
    ERROR_MSG_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_MensagemErroFiltroLabel"
    NOT_FOUND_MSG_ID: str = "ctl00_conteudoPaginaPlaceHolder_filtroTabContainer_filtroEmitirCertidaoTabPanel_MensagemNadaEncontradoLabel"
    
    # IE number validation pattern
    IE_NUMBER_PATTERN: str = r"^\d{3}\.\d{3}\.\d{3}\.\d{3}$"
    
    def __post_init__(self):
        if 'TESSERACT_CMD' in os.environ:
            self.TESSERACT_CMD = os.environ['TESSERACT_CMD']
        if 'CHROME_DRIVER_PATH' in os.environ:
            self.CHROME_DRIVER_PATH = os.environ['CHROME_DRIVER_PATH']
            
        # Load captcha settings from environment
        if 'CAPTCHA_PSM_MODE' in os.environ:
            self.CAPTCHA_PSM_MODE = int(os.environ['CAPTCHA_PSM_MODE'])
        if 'CAPTCHA_CONTRAST' in os.environ:
            self.CAPTCHA_CONTRAST = float(os.environ['CAPTCHA_CONTRAST'])
        if 'CAPTCHA_THRESHOLD' in os.environ:
            self.CAPTCHA_THRESHOLD = int(os.environ['CAPTCHA_THRESHOLD'])
        if 'CAPTCHA_APPLY_NOISE_REDUCTION' in os.environ:
            self.CAPTCHA_APPLY_NOISE_REDUCTION = os.environ['CAPTCHA_APPLY_NOISE_REDUCTION'].lower() == 'true'
        if 'CAPTCHA_RESIZE_SMALL_IMAGES' in os.environ:
            self.CAPTCHA_RESIZE_SMALL_IMAGES = os.environ['CAPTCHA_RESIZE_SMALL_IMAGES'].lower() == 'true'
        if 'CAPTCHA_SAVE_ATTEMPTS' in os.environ:
            self.CAPTCHA_SAVE_ATTEMPTS = os.environ['CAPTCHA_SAVE_ATTEMPTS'].lower() == 'true'
        if 'CAPTCHA_ATTEMPTS_DIR' in os.environ:
            self.CAPTCHA_ATTEMPTS_DIR = os.environ['CAPTCHA_ATTEMPTS_DIR']

settings = Settings()
